"""Shared Memory API — main FastAPI application.

Merkezi Shared Memory servisi: Claude Code + Hermes arasında paylaşılan
proje hafızası. PostgreSQL + pgvector üzerinde çalışır.

Endpoints:
  POST   /v1/memory              -> yeni kayıt (dedup + conflict kontrolü)
  POST   /v1/memory/search       -> semantic + metadata arama
  GET    /v1/memory/{id}         -> kayıt getir
  PUT    /v1/memory/{id}         -> kayıt güncelle
  DELETE /v1/memory/{id}         -> soft delete (archive)
  POST   /v1/memory/bulk         -> toplu yazma
  POST   /v1/memory/dedup        -> aynı kaydı tekrar ekleme kontrolü
  POST   /v1/projects            -> proje kaydet
  GET    /v1/projects            -> proje listesi
  GET    /v1/projects/{id}       -> proje getir
  POST   /v1/events              -> event yaz
  GET    /v1/events              -> son eventler
  GET    /health, /ready         -> health checks
"""

import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pgvector.psycopg import register_vector
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("shared-memory")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://memory:memory@postgres:5432/memory")
API_KEYS_RAW = os.getenv("MEMORY_API_KEYS", "dev-key-1,dev-key-2")
API_KEYS = {k.strip() for k in API_KEYS_RAW.split(",") if k.strip()}
# Service identity (kim yazıyor)
SERVICE_ID = os.getenv("MEMORY_SERVICE_ID", "memory-api")

app = FastAPI(title="Shared Memory API", version="1.0.0")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def get_conn():
    conn = psycopg.connect(DATABASE_URL, autocommit=False)
    try:
        register_vector(conn)
    except Exception as e:
        # vector extension henüz kurulmamış olabilir; ensure_schema() kuracak.
        # SQL'de ::vector cast kullanıldığı için adapter'sız da çalışır.
        logger.warning("register_vector başarısız (%s) — ::vector cast ile devam", e)
    return conn


def ensure_schema(conn):
    with conn.cursor() as cur:
        # pgvector extension'ı açıkça public schema'ya kur (search_path güvenliği)
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;")
        cur.execute("SET search_path TO public;")
        # Extension kurulduktan sonra vector tipini bu bağlantıya kaydet
        register_vector(conn)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id TEXT NOT NULL DEFAULT 'global',
                domain TEXT NOT NULL DEFAULT 'general',
                type TEXT NOT NULL DEFAULT 'finding',
                content TEXT NOT NULL,
                summary TEXT,
                source TEXT NOT NULL DEFAULT 'unknown',
                agent TEXT NOT NULL DEFAULT 'unknown',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                importance FLOAT NOT NULL DEFAULT 0.5,
                confidence FLOAT NOT NULL DEFAULT 0.5,
                tags TEXT[] NOT NULL DEFAULT '{}',
                embedding vector(1536),
                status TEXT NOT NULL DEFAULT 'current',
                supersedes UUID,
                superseded_by UUID,
                persist BOOLEAN NOT NULL DEFAULT TRUE,
                ttl TIMESTAMPTZ
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                github_url TEXT,
                default_branch TEXT DEFAULT 'main',
                local_paths TEXT[] NOT NULL DEFAULT '{}',
                remote_paths TEXT[] NOT NULL DEFAULT '{}',
                tags TEXT[] NOT NULL DEFAULT '{}',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id TEXT,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                agent TEXT,
                summary TEXT,
                memory_id UUID,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
                service TEXT NOT NULL,
                agent TEXT,
                project_id TEXT,
                operation TEXT NOT NULL,
                memory_id TEXT
            );
            """
        )
        # Indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_project ON memory(project_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_domain ON memory(domain);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_status ON memory(status);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_updated ON memory(updated_at DESC);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(active);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);")
        # HNSW vector index (1536 dim)
        try:
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory USING hnsw (embedding vector_cosine_ops);"
            )
        except Exception as e:
            logger.warning("HNSW index oluşturulamadı (dev ortamı olabilir): %s", e)
    conn.commit()


# ---------------------------------------------------------------------------
# Embedding (gerçek embedding API'si varsa onu kullanır, yoksa hash fallback)
# ---------------------------------------------------------------------------
def embed_text(text: str) -> Optional[list]:
    """Embedding üretir.

    EMBEDDING_API_URL + EMBEDDING_API_KEY set ise OpenAI-uyumlu /embeddings uç noktasını
    çağırır (Gemini, NVIDIA vb.). 1536 boyut zorunludur (schema vector(1536)) — bu yüzden
    `dimensions: 1536` ve model adı her zaman isteğe eklenir. API yoksa deterministic hash
    fallback (dev/test için).
    """
    emb = os.getenv("EMBEDDING_API_URL")
    key = os.getenv("EMBEDDING_API_KEY")
    model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    dims = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
    if emb and key:
        try:
            import urllib.request

            payload = {"input": text, "model": model, "dimensions": dims}
            req = urllib.request.Request(
                emb,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
                vector = data["data"][0]["embedding"]
                # Boyut güvencesi: API istenileni döndürmezse vektörü uyarlama
                if len(vector) != dims:
                    logger.warning("Embedding boyutu %d (istenen %d) — hash fallback'e düşme",
                                   len(vector), dims)
                    raise ValueError(f"unexpected embedding dim {len(vector)}")
                # Kosinüs benzerliği için normalize (pgvector cosine_ops ile tutarlı)
                norm = sum(v * v for v in vector) ** 0.5 or 1.0
                return [v / norm for v in vector]
        except Exception as e:
            logger.warning("Embedding API çağrılamadı, hash fallback: %s", e)
    # Deterministic 1536-dim fallback (konsistens için normalize edilmiş hash)
    vec = []
    for i in range(1536):
        h = hashlib.sha256(f"{text}::{i}".encode()).digest()
        vec.append(int.from_bytes(h[:4], "big") / 2**32 - 0.5)
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
def audit(conn, operation: str, project_id: Optional[str] = None,
          agent: Optional[str] = None, memory_id: Optional[str] = None):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_log (service, agent, project_id, operation, memory_id) VALUES (%s,%s,%s,%s,%s)",
                (SERVICE_ID, agent, project_id, operation, str(memory_id) if memory_id else None),
            )
        conn.commit()
    except Exception as e:
        logger.warning("audit yazılamadı: %s", e)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class MemoryCreate(BaseModel):
    project_id: str = "global"
    domain: str = "general"
    type: str = "finding"
    content: str = Field(..., min_length=1)
    summary: Optional[str] = None
    source: str = "unknown"
    agent: str = "unknown"
    importance: float = Field(0.5, ge=0.0, le=1.0)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    tags: list[str] = []
    persist: bool = True
    ttl: Optional[str] = None  # ISO datetime


class MemorySearch(BaseModel):
    query: str
    project_id: Optional[str] = None
    domains: Optional[list[str]] = None
    types: Optional[list[str]] = None
    agents: Optional[list[str]] = None
    min_importance: float = 0.0
    limit: int = Field(10, ge=1, le=50)
    include_archived: bool = False


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    importance: Optional[float] = None
    confidence: Optional[float] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None  # current|superseded|archived|stale


class ProjectCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    default_branch: str = "main"
    local_paths: list[str] = []
    remote_paths: list[str] = []
    tags: list[str] = []
    active: bool = True


class EventCreate(BaseModel):
    project_id: Optional[str] = None
    event_type: str
    source: str
    agent: Optional[str] = None
    summary: str
    memory_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
def require_key(x_api_key: str = Header(default="")):
    if not API_KEYS or x_api_key in API_KEYS:
        return x_api_key
    raise HTTPException(status_code=401, detail="invalid api key")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup():
    """DB bağlantısı + schema kurulumu. Hata olursa process ölmez; /health'ten görünür."""
    try:
        conn = get_conn()
        ensure_schema(conn)
        conn.close()
        app.state.startup_error = None
        logger.info("Schema hazır. DB=%s", DATABASE_URL.split("@")[-1])
    except Exception as e:
        import traceback
        app.state.startup_error = f"{type(e).__name__}: {e}"
        logger.error("Startup DB hatası: %s\n%s", e, traceback.format_exc())
        # Uvicorn exit 3 ile restart loop'a girmemesi için exception'ı yutuyoruz.
        # /health üzerinden hata görünür; DB gelince tekrar denenir.


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    err = getattr(app.state, "startup_error", None)
    return {
        "status": "degraded" if err else "ok",
        "service": "shared-memory-api",
        "startup_error": err,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    try:
        conn = get_conn()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ready", "db": "up"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"db down: {e}")


# ---------------------------------------------------------------------------
# Memory CRUD
# ---------------------------------------------------------------------------
@app.post("/v1/memory")
def create_memory(item: MemoryCreate, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # --- DEDUP: aynı project+domain+type+content (normalize) varsa güncelle ---
            cur.execute(
                """
                SELECT id FROM memory
                WHERE project_id=%s AND domain=%s AND type=%s
                  AND lower(content)=lower(%s) AND status='current'
                ORDER BY updated_at DESC LIMIT 1
                """,
                (item.project_id, item.domain, item.type, item.content),
            )
            dup = cur.fetchone()
            if dup:
                mid = dup[0]
                cur.execute(
                    """
                    UPDATE memory SET summary=%s, tags=%s, importance=%s, confidence=%s,
                                      updated_at=now(), source=%s, agent=%s
                    WHERE id=%s RETURNING id
                    """,
                    (item.summary, item.tags, item.importance, item.confidence,
                     item.source, item.agent, mid),
                )
                conn.commit()
                audit(conn, "UPDATE_DEDUP", item.project_id, item.agent, mid)
                return {"id": str(mid), "deduplicated": True}

            # --- INSERT + embedding ---
            emb = embed_text(item.content + " " + (item.summary or ""))
            cur.execute(
                """
                INSERT INTO memory (project_id, domain, type, content, summary, source, agent,
                                    importance, confidence, tags, embedding, persist, ttl)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,%s,%s)
                RETURNING id
                """,
                (item.project_id, item.domain, item.type, item.content, item.summary,
                 item.source, item.agent, item.importance, item.confidence, item.tags,
                 emb, item.persist, item.ttl),
            )
            mid = cur.fetchone()[0]
        conn.commit()
        audit(conn, "CREATE", item.project_id, item.agent, mid)
        return {"id": str(mid), "deduplicated": False}
    except Exception as e:
        logger.exception("create_memory hatası")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/v1/memory/search")
def search_memory(item: MemorySearch, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        emb = embed_text(item.query)
        clauses = ["status = 'current'"]
        params: list[Any] = []
        if item.project_id:
            clauses.append("project_id = %s")
            params.append(item.project_id)
        if item.domains:
            clauses.append("domain = ANY(%s)")
            params.append(item.domains)
        if item.types:
            clauses.append("type = ANY(%s)")
            params.append(item.types)
        if item.agents:
            clauses.append("agent = ANY(%s)")
            params.append(item.agents)
        if item.min_importance > 0:
            clauses.append("importance >= %s")
            params.append(item.min_importance)
        if not item.include_archived:
            clauses.append("status != 'archived'")
        where = " AND ".join(clauses)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, project_id, domain, type, content, summary, source, agent,
                       created_at, updated_at, importance, confidence, tags, status,
                       1 - (embedding <=> %s::vector) AS score
                FROM memory
                WHERE {where}
                ORDER BY score DESC, importance DESC, updated_at DESC
                LIMIT %s
                """,
                (emb, *params, item.limit),
            )
            rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "id": str(r[0]), "project_id": r[1], "domain": r[2], "type": r[3],
                "content": r[4], "summary": r[5], "source": r[6], "agent": r[7],
                "created_at": r[8].isoformat(), "updated_at": r[9].isoformat(),
                "importance": r[10], "confidence": r[11], "tags": r[12], "status": r[13],
                "score": round(float(r[14]), 4) if r[14] is not None else None,
            })
        return {"results": result, "count": len(result)}
    except Exception as e:
        logger.exception("search_memory hatası")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/v1/memory/{memory_id}")
def get_memory(memory_id: str, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, project_id, domain, type, content, summary, source, agent,
                       created_at, updated_at, importance, confidence, tags, status,
                       supersedes, superseded_by, persist
                FROM memory WHERE id=%s
                """,
                (memory_id,),
            )
            r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="memory not found")
        return {
            "id": str(r[0]), "project_id": r[1], "domain": r[2], "type": r[3],
            "content": r[4], "summary": r[5], "source": r[6], "agent": r[7],
            "created_at": r[8].isoformat(), "updated_at": r[9].isoformat(),
            "importance": r[10], "confidence": r[11], "tags": r[12], "status": r[13],
            "supersedes": str(r[14]) if r[14] else None,
            "superseded_by": str(r[15]) if r[15] else None,
            "persist": r[16],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.put("/v1/memory/{memory_id}")
def update_memory(memory_id: str, item: MemoryUpdate, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        fields = []
        params: list[Any] = []
        if item.content is not None:
            fields.append("content=%s")
            params.append(item.content)
        if item.summary is not None:
            fields.append("summary=%s")
            params.append(item.summary)
        if item.importance is not None:
            fields.append("importance=%s")
            params.append(item.importance)
        if item.confidence is not None:
            fields.append("confidence=%s")
            params.append(item.confidence)
        if item.tags is not None:
            fields.append("tags=%s")
            params.append(item.tags)
        if item.status is not None:
            fields.append("status=%s")
            params.append(item.status)
        if not fields:
            return {"id": memory_id, "updated": False}
        fields.append("updated_at=now()")
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE memory SET {', '.join(fields)} WHERE id=%s RETURNING project_id, agent",
                (*params, memory_id),
            )
            r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="memory not found")
        conn.commit()
        audit(conn, "UPDATE", r[0], r[1], memory_id)
        return {"id": memory_id, "updated": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.delete("/v1/memory/{memory_id}")
def delete_memory(memory_id: str, _: str = Depends(require_key)):
    """Soft delete -> archived."""
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE memory SET status='archived', updated_at=now() WHERE id=%s RETURNING project_id, agent",
                (memory_id,),
            )
            r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="memory not found")
        conn.commit()
        audit(conn, "DELETE_SOFT", r[0], r[1], memory_id)
        return {"id": memory_id, "deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/v1/memory/supersede/{old_id}")
def supersede_memory(old_id: str, new_id: str, _: str = Depends(require_key)):
    """Conflict yönetimi: eski kayıt silinmez, superseded işaretlenir."""
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE memory SET status='superseded', superseded_by=%s, updated_at=now() WHERE id=%s RETURNING project_id, agent",
                (new_id, old_id),
            )
            r = cur.fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="old memory not found")
            cur.execute(
                "UPDATE memory SET supersedes=%s WHERE id=%s",
                (old_id, new_id),
            )
        conn.commit()
        audit(conn, "SUPERSEDE", r[0], r[1], old_id)
        return {"superseded": old_id, "by": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/v1/memory/bulk")
def bulk_create(items: list[MemoryCreate], _: str = Depends(require_key)):
    results = []
    for item in items:
        try:
            res = create_memory(item, _="")
            results.append({"content": item.content[:60], "id": res["id"], "deduplicated": res["deduplicated"]})
        except Exception as e:
            results.append({"content": item.content[:60], "error": str(e)})
    return {"results": results, "count": len(results)}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@app.post("/v1/projects")
def create_project(item: ProjectCreate, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (id, name, description, github_url, default_branch,
                                      local_paths, remote_paths, tags, active)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    name=EXCLUDED.name, description=EXCLUDED.description,
                    github_url=EXCLUDED.github_url, default_branch=EXCLUDED.default_branch,
                    local_paths=EXCLUDED.local_paths, remote_paths=EXCLUDED.remote_paths,
                    tags=EXCLUDED.tags, active=EXCLUDED.active, updated_at=now()
                """,
                (item.id, item.name, item.description, item.github_url, item.default_branch,
                 item.local_paths, item.remote_paths, item.tags, item.active),
            )
        conn.commit()
        audit(conn, "PROJECT_UPSERT", item.id, None, None)
        return {"id": item.id, "upserted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/v1/projects")
def list_projects(active: bool = Query(True), _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, description, github_url, default_branch, local_paths, remote_paths, tags, active, created_at, updated_at FROM projects WHERE active=%s ORDER BY name",
                (active,),
            )
            rows = cur.fetchall()
        return [{
            "id": r[0], "name": r[1], "description": r[2], "github_url": r[3],
            "default_branch": r[4], "local_paths": r[5], "remote_paths": r[6],
            "tags": r[7], "active": r[8], "created_at": r[9].isoformat(), "updated_at": r[10].isoformat(),
        } for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/v1/projects/{project_id}")
def get_project(project_id: str, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
            r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="project not found")
        cols = [d.name for d in cur.description]
        return {c: (v.isoformat() if hasattr(v, "isoformat") else v) for c, v in zip(cols, r)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
@app.post("/v1/events")
def create_event(item: EventCreate, _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO events (project_id, event_type, source, agent, summary, memory_id) VALUES (%s,%s,%s,%s,%s,%s)",
                (item.project_id, item.event_type, item.source, item.agent, item.summary, item.memory_id),
            )
        conn.commit()
        return {"created": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/v1/events")
def list_events(project_id: Optional[str] = None, limit: int = Query(20, le=100), _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            if project_id:
                cur.execute(
                    "SELECT id, project_id, event_type, source, agent, summary, memory_id, created_at FROM events WHERE project_id=%s ORDER BY created_at DESC LIMIT %s",
                    (project_id, limit),
                )
            else:
                cur.execute(
                    "SELECT id, project_id, event_type, source, agent, summary, memory_id, created_at FROM events ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            rows = cur.fetchall()
        return [{
            "id": str(r[0]), "project_id": r[1], "event_type": r[2], "source": r[3],
            "agent": r[4], "summary": r[5], "memory_id": str(r[6]) if r[6] else None,
            "created_at": r[7].isoformat(),
        } for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Audit log view (admin)
# ---------------------------------------------------------------------------
@app.get("/v1/audit")
def list_audit(limit: int = Query(50, le=200), _: str = Depends(require_key)):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT timestamp, service, agent, project_id, operation, memory_id FROM audit_log ORDER BY timestamp DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        return [{
            "timestamp": r[0].isoformat(), "service": r[1], "agent": r[2],
            "project_id": r[3], "operation": r[4], "memory_id": r[5],
        } for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
