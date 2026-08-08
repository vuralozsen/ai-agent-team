# MEMORY SCHEMA
id, project_id, domain, type, content, summary, source, agent, created_at, updated_at,
importance (0-1), confidence (0-1), tags[], embedding, status (current|superseded|archived|stale),
supersedes, superseded_by, persist (bool), ttl

type değerleri: decision, architecture, change, deployment, bug, incident, solution, finding,
constraint, preference, integration, configuration, api, security, database, research, lesson, procedure

Örnek:
{"project_id":"borsa-mcp","domain":"database","type":"change","content":"users tablosuna tenant_id eklendi.",
 "summary":"users table multi-tenant yapıldı","source":"claude-code","agent":"developer",
 "importance":0.8,"confidence":0.95,"tags":["postgres","schema","multi-tenant"]}
