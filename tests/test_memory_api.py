"""Memory API end-to-end test suite (local, DB gerekli)."""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = os.getenv("MEMORY_TEST_URL", "http://localhost:8000")
KEY = os.getenv("MEMORY_TEST_KEY", "dev-key-1")
HEADERS = {"Content-Type": "application/json", "X-API-Key": KEY}
RUN_ID = uuid.uuid4().hex[:8]  # her çalıştırmada unique content -> dedup çakışması yok

passed = 0
failed = 0


def api(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {detail}")


def main():
    print("== Health ==")
    s, d = api("GET", "/health")
    check("health 200", s == 200, str(d))
    s, d = api("GET", "/ready")
    check("ready 200", s == 200, str(d))

    print("== Auth ==")
    req = urllib.request.Request(BASE + "/v1/projects", headers={"Content-Type": "application/json"}, method="GET")
    try:
        urllib.request.urlopen(req, timeout=10)
        check("no-key rejected", False, "request unexpectedly succeeded")
    except urllib.error.HTTPError as e:
        check("no-key rejected 401", e.code == 401, str(e.code))

    print("== Memory write/read ==")
    s, d = api("POST", "/v1/memory", {
        "project_id": "test-proj-a", "domain": "database", "type": "change",
        "content": f"users tablosuna tenant_id eklendi (test-{RUN_ID})",
        "summary": "multi-tenant test", "source": "test", "agent": "tester",
        "importance": 0.8, "tags": ["postgres", "test"],
    })
    check("create 200", s == 200 and not d.get("deduplicated"), str(d))
    mid = d["id"]
    s, d = api("GET", f"/v1/memory/{mid}")
    check("get 200", s == 200 and d["content"].startswith("users"), str(d))

    print("== Dedup ==")
    s, d = api("POST", "/v1/memory", {
        "project_id": "test-proj-a", "domain": "database", "type": "change",
        "content": f"users tablosuna tenant_id eklendi (test-{RUN_ID})",
        "summary": "güncellendi", "source": "test", "agent": "tester",
    })
    check("dedup detected", s == 200 and d.get("deduplicated") is True, str(d))

    print("== Semantic search ==")
    s, d = api("POST", "/v1/memory/search", {"query": "tenant multi-tenant users table", "limit": 5})
    check("search 200", s == 200, str(d))
    check("search finds record", any(r["id"] == mid for r in d["results"]), str(d))

    print("== Project isolation ==")
    s, d = api("POST", "/v1/memory", {
        "project_id": "test-proj-b", "domain": "devops", "type": "deployment",
        "content": "test-proj-b deployment değişikliği", "agent": "tester",
    })
    check("proj B create", s == 200, str(d))
    s, d = api("POST", "/v1/memory/search", {"query": "tenant", "project_id": "test-proj-b", "limit": 5})
    check("proj B isolation (no A records)", not any(r["project_id"] == "test-proj-a" for r in d["results"]), str(d))

    print("== Domain filtering ==")
    s, d = api("POST", "/v1/memory/search", {"query": "tenant", "project_id": "test-proj-a", "domains": ["security"], "limit": 5})
    check("domain filter excludes database", all(r["domain"] != "database" for r in d["results"]), str(d))

    print("== Supersede ==")
    s, d = api("POST", "/v1/memory", {
        "project_id": "test-proj-a", "domain": "database", "type": "configuration",
        "content": "Redis port 6380 (yeni)", "agent": "tester",
    })
    new_id = d["id"]
    s, d = api("POST", f"/v1/memory/supersede/{mid}?new_id={new_id}")
    check("supersede 200", s == 200, str(d))
    s, d = api("GET", f"/v1/memory/{mid}")
    check("old marked superseded", d["status"] == "superseded", str(d))

    print("== One-off persist=false ==")
    s, d = api("POST", "/v1/memory", {
        "project_id": "test-proj-a", "domain": "general", "type": "finding",
        "content": "geçici task notu", "persist": False, "agent": "tester",
    })
    check("one-off create", s == 200, str(d))

    print("== Projects registry ==")
    s, d = api("POST", "/v1/projects", {"id": "test-proj-a", "name": "Test Project A", "tags": ["test"]})
    check("project upsert", s == 200, str(d))
    s, d = api("GET", "/v1/projects")
    check("projects list", s == 200 and any(p["id"] == "test-proj-a" for p in d), str(d))

    print("== Events ==")
    s, d = api("POST", "/v1/events", {"project_id": "test-proj-a", "event_type": "database_schema_changed",
                                      "source": "test", "agent": "tester", "summary": "test event", "memory_id": mid})
    check("event create", s == 200, str(d))
    s, d = api("GET", "/v1/events?project_id=test-proj-a")
    check("event list", s == 200 and len(d) > 0, str(d))

    print("== Audit ==")
    s, d = api("GET", "/v1/audit")
    check("audit log", s == 200 and len(d) > 0, str(d))

    print(f"\n== SONUÇ: {passed} PASS, {failed} FAIL ==")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
