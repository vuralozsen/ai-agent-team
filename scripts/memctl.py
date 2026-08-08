#!/usr/bin/env python3
"""memctl — Shared Memory API CLI (Claude Code + Hermes ortak kullanımı)

Kullanım:
  memctl health
  memctl ready
  memctl write --project <id> --domain <d> --type <t> --content "..." [--summary s] [--agent a] [--source s] [--importance 0.8] [--tags a,b,c] [--no-persist]
  memctl search "query" [--project id] [--domain d1,d2] [--type t1,t2] [--limit 10] [--min-importance 0.5]
  memctl get <memory_id>
  memctl update <memory_id> [--content ...] [--status current|superseded|archived|stale]
  memctl delete <memory_id>
  memctl supersede <old_id> <new_id>
  memctl projects
  memctl project-add --id x --name y [--github-url u] [--tags a,b]
  memctl events [--project id] [--limit 20]
  memctl audit [--limit 50]

Env:
  MEMORY_API_URL   (varsayılan: http://memory-api:8000)
  MEMORY_API_KEY   (varsayılan: boş — zorunlu)
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.getenv("MEMORY_API_URL", "http://memory-api:8000").rstrip("/")
API_KEY = os.getenv("MEMORY_API_KEY", "")


def call(method, path, body=None):
    url = f"{API_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"detail": raw.decode()[:300]}


def pprint(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main():
    if not API_KEY:
        print("HATA: MEMORY_API_KEY env değişkeni gerekli.", file=sys.stderr)
        sys.exit(2)

    ap = argparse.ArgumentParser(description="Shared Memory CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")
    sub.add_parser("ready")

    p = sub.add_parser("write")
    p.add_argument("--project", required=True)
    p.add_argument("--domain", default="general")
    p.add_argument("--type", default="finding")
    p.add_argument("--content", required=True)
    p.add_argument("--summary")
    p.add_argument("--agent", default="unknown")
    p.add_argument("--source", default="cli")
    p.add_argument("--importance", type=float, default=0.5)
    p.add_argument("--confidence", type=float, default=0.5)
    p.add_argument("--tags", default="")
    p.add_argument("--no-persist", action="store_true")

    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--project")
    p.add_argument("--domain")
    p.add_argument("--type")
    p.add_argument("--agent")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--min-importance", type=float, default=0.0)

    p = sub.add_parser("get")
    p.add_argument("memory_id")

    p = sub.add_parser("update")
    p.add_argument("memory_id")
    p.add_argument("--content")
    p.add_argument("--summary")
    p.add_argument("--importance", type=float)
    p.add_argument("--status", choices=["current", "superseded", "archived", "stale"])

    p = sub.add_parser("delete")
    p.add_argument("memory_id")

    p = sub.add_parser("supersede")
    p.add_argument("old_id")
    p.add_argument("new_id")

    sub.add_parser("projects")
    p = sub.add_parser("project-add")
    p.add_argument("--id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--github-url")
    p.add_argument("--tags", default="")

    p = sub.add_parser("events")
    p.add_argument("--project")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("audit")
    p.add_argument("--limit", type=int, default=50)

    args = ap.parse_args()
    s = 0

    if args.cmd == "health":
        s, d = call("GET", "/health")
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "ready":
        s, d = call("GET", "/ready")
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "write":
        body = {
            "project_id": args.project,
            "domain": args.domain,
            "type": args.type,
            "content": args.content,
            "summary": args.summary,
            "source": args.source,
            "agent": args.agent,
            "importance": args.importance,
            "confidence": args.confidence,
            "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "persist": not args.no_persist,
        }
        s, d = call("POST", "/v1/memory", body)
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "search":
        body = {"query": args.query, "limit": args.limit, "min_importance": args.min_importance}
        if args.project:
            body["project_id"] = args.project
        if args.domain:
            body["domains"] = [x.strip() for x in args.domain.split(",")]
        if args.type:
            body["types"] = [x.strip() for x in args.type.split(",")]
        if args.agent:
            body["agents"] = [x.strip() for x in args.agent.split(",")]
        s, d = call("POST", "/v1/memory/search", body)
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "get":
        s, d = call("GET", f"/v1/memory/{args.memory_id}")
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "update":
        body = {}
        for k in ("content", "summary", "importance", "status"):
            v = getattr(args, k, None)
            if v is not None:
                body[k] = v
        s, d = call("PUT", f"/v1/memory/{args.memory_id}", body)
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "delete":
        s, d = call("DELETE", f"/v1/memory/{args.memory_id}")
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "supersede":
        s, d = call("POST", f"/v1/memory/supersede/{args.old_id}?new_id={args.new_id}")
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "projects":
        s, d = call("GET", "/v1/projects")
        print(json.dumps({"status_code": s, "count": len(d) if isinstance(d, list) else 0, "projects": d}, ensure_ascii=False))
    elif args.cmd == "project-add":
        body = {"id": args.id, "name": args.name, "description": args.description,
                "github_url": args.github_url, "tags": [t.strip() for t in args.tags.split(",") if t.strip()]}
        s, d = call("POST", "/v1/projects", body)
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "events":
        path = "/v1/events"
        qs = []
        if args.project:
            qs.append(f"project_id={args.project}")
        if args.limit:
            qs.append(f"limit={args.limit}")
        if qs:
            path += "?" + "&".join(qs)
        s, d = call("GET", path)
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))
    elif args.cmd == "audit":
        s, d = call("GET", f"/v1/audit?limit={args.limit}")
        print(json.dumps({"status_code": s, **d}, ensure_ascii=False))

    sys.exit(0 if s < 400 else 1)


if __name__ == "__main__":
    main()
