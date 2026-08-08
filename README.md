# AI Agent Team + Shared Memory

Claude Code + Hermes Agent için merkezi agent knowledge ve shared memory altyapısı.

```
            USER
         /        \
    VS Code      Telegram
       |            |
  Claude Code     Hermes
       |            |
       +-----+------+
             |
    Shared Agent Knowledge  (bu repo)
             |
    Shared Memory API       (memory-api/)
             |
    PostgreSQL + pgvector
             |
      Project Registry
```

## Bileşenler

| Bileşen | Konum | Açıklama |
|---------|-------|----------|
| Agent tanımları | `agents/<name>/{ROLE,RULES,PROCEDURES}.md` | 10 uzman (lead, developer, architect, devops, database, security, qa, researcher, documentation, debugger) |
| Skill'ler | `skills/<domain>/SKILL.md` | Platform bağımsız uzmanlık bilgisi |
| Policy'ler | `policies/` | security, memory, project, delegation |
| Schema'lar | `schemas/` | memory + project kayıt şeması |
| Memory API | `memory-api/` | FastAPI + pgvector servisi |
| Testler | `tests/` | API + isolation testleri |

## Memory API

Endpoints: `/v1/memory` (CRUD+search+bulk+supersede), `/v1/projects`, `/v1/events`, `/v1/audit`, `/health`, `/ready`

Auth: `X-API-Key` header (çoklu key destekli).

## Deployment

Dokploy üzerinden `memory-api/docker-compose.yml` deploy edilir.
Gerekli env değişkenleri: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `MEMORY_API_KEYS` (virgülle ayrılmış).

**DİKKAT**: compose'da `dokploy-network` KULLANILMAZ (2026-08-08'de tefas DNS çakışmasına yol açtı).
Servisler `shared-memory-internal` + `hermes-net` (hermes-isolated) ağlarında.

## Backup

`backup` servisi her 24 saatte bir pg_dump alır (gzip), `shared_memory_backups` volume'ünde saklar,
7 günden eski dump'ları siler. Restore: `gunzip -c memory_*.sql.gz | psql -U memory -d memory`.

## Handoff

Claude Code kurulumu için `HANDOFF.md` bölümüne bakınız (kurulum sonrası doldurulur).
