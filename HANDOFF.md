# HANDOFF — Claude Code Kurulum Rehberi

> Bu dosya Hermes tarafından üretilmiştir (2026-08-08).
> Amaç: Claude Code'un paylaşılan agent knowledge + shared memory'yi kullanması.

## SYSTEM NAME
AI Agent Team + Shared Memory (Claude Code + Hermes ortak)

## MEMORY API URL
- VPS içi (Hermes container): `http://memory-api:8000`
- Dış erişim: **henüz public domain yok** — HTTPS domain istenirse Dokploy'dan `memory.vuralozsen.com.tr` eklenebilir.

## AUTH METHOD
- Header: `X-API-Key: <key>`
- Claude Code key'i: **secret env'de** — `.env` / secret manager'da tutulur.
- Key'ler: Claude ve Hermes için ayrı (rotation destekli).

## ENVIRONMENT VARIABLES NEEDED
```
MEMORY_API_URL=http://memory-api:8000
MEMORY_API_KEY=<SET_IN_SECRET_ENV>   # Claude için ayrı key
```

## AGENT KNOWLEDGE REPOSITORY
- GitHub: `https://github.com/vuralozsen/ai-agent-team` (public)
- Yapı: `agents/<name>/{ROLE,RULES,PROCEDURES}.md`, `skills/<domain>/SKILL.md`, `policies/`, `schemas/`
- Claude Code kullanımı: repo'yu clone et, `agents/` + `skills/` içeriğini Claude Code projesine bağla (ör. `.claude/` wrapper'ları veya CLAUDE.md içinde yönlendirme).

## PROJECT REGISTRY METHOD
- HTTP API: `POST/GET /v1/projects`
- Mevcut projeler: x-automation, kolayportfoy, hermes-org, tefas, cmdc, linde-pivot, ozelasistan
- Kayıt şeması: `schemas/project-schema.md`

## MEMORY API TEST RESULT
- `GET /health` → 200 ok
- `GET /ready` → 200 ready
- 19/19 API test PASS (write/read/dedup/search/isolation/domain/supersede/one-off/projects/events/audit)
- Cross-platform: Claude key ile yazılan kayıt Hermes key ile okundu ✅

## SUPPORTED FEATURES
- CRUD: create/get/update/soft-delete
- Semantic search (1536-dim embedding, HNSW index; hash-tabanlı embedding — LLM embedding API opsiyonel)
- Project isolation (project_id filtresi)
- Domain/type/agent/importance filtering
- Dedup (aynı content+project+domain+type → update)
- Conflict/supersession (supersedes/superseded_by)
- One-off (persist=false)
- Events (structured agent arası haberleşme)
- Audit log (`GET /v1/audit`)
- Auth: X-API-Key (çoklu key, 401 koruması)

## KNOWN LIMITATIONS
1. **Embedding hash-tabanlı** — gerçek LLM embedding'i yok. Semantik arama deterministik, orta kalite. `EMBEDDING_API_URL` + `EMBEDDING_API_KEY` env'leri ile OpenAI-compatible embedding API eklenebilir.
2. **Public HTTPS domain yok** — Claude Code PC'den dışarıdan erişecekse Dokploy'dan domain + TLS gerekir.
3. **Rate limiting yok** — API'de rate limit middleware'i henüz yok.
4. **Nested delegation** — Hermes'te max_spawn_depth=1 (orchestrator→leaf). Derin nested yok; paralel leaf'ler destekli.
5. **Secret redaction** — memory API'de secret yazma engeli yok (policy-level). Agentlar sorumlu.
6. **Dokploy container logs** — MCP'den okunamıyor; panelden bakılır.

## NEXT PLATFORM SETUP STEPS (Claude Code)
1. Repo'yu clone et: `git clone https://github.com/vuralozsen/ai-agent-team`
2. `agents/` + `skills/` + `policies/` içeriğini Claude Code'a bağla (CLAUDE.md veya .claude/agents yapısı).
3. Memory API erişimi:
   - **Opsiyon A (MCP):** `claude mcp add shared-memory -- curl -s -X POST <API_URL>/v1/memory/search -H "X-API-Key: $MEMORY_API_KEY" -H "Content-Type: application/json" -d '{"query":"...","project_id":"..."}'` — memory_search/write/get/project_search şeklinde tool'lar.
   - **Opsiyon B (CLI):** `python3 scripts/memctl.py search "..." --project <id>` (repo içinde).
4. Env: `MEMORY_API_URL` + `MEMORY_API_KEY` (Claude key) → shell env / .env.
5. Project detection: cwd/git remote → `memctl projects` ile eşleştir.
6. Görev başı: `memctl search "<görev>" --project <id> --limit 5`.
7. Görev sonu: önemli sonuçları `memctl write --project <id> --domain <d> --type <t> --content "..."`.

## COMPATIBILITY NOTES
- API tamamen HTTP JSON — MCP zorunlu değil, doğrudan REST de kullanılabilir.
- Claude Code'un memory'si ile bu Shared Memory birbirinin yerine geçmez:
  - Claude Code native memory: oturum bağlamı.
  - Shared Memory: Claude + Hermes arası paylaşılan proje bilgisi (source of truth).
