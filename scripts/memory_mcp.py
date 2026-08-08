#!/usr/bin/env python3
"""Claude Code MCP-compatible bridge for Shared Memory API.

Claude Code MCP config:
  claude mcp add shared-memory -- python3 /path/to/ai-agent-team/scripts/memory_mcp.py

Bu script stdio MCP server gibi davranır: JSON-RPC 2.0 mesajları alır,
memory_search / memory_write / memory_get / project_search / recent_events
tool'larını sunar.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.getenv("MEMORY_API_URL", "http://memory-api:8000").rstrip("/")
API_KEY = os.getenv("MEMORY_API_KEY", "")

TOOLS = [
    {
        "name": "memory_search",
        "description": "Shared memory'de semantic arama yap. project_id opsiyonel (izolasyon için önerilir).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "project_id": {"type": "string"},
                "domains": {"type": "array", "items": {"type": "string"}},
                "types": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_write",
        "description": "Shared memory'ye kayıt yaz. Kalıcı kararlar/change/deployment/bug için; one-off görevde persist=false.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "domain": {"type": "string", "default": "general"},
                "type": {"type": "string", "default": "finding"},
                "content": {"type": "string"},
                "summary": {"type": "string"},
                "importance": {"type": "number", "default": 0.5},
                "tags": {"type": "array", "items": {"type": "string"}},
                "persist": {"type": "boolean", "default": True},
            },
            "required": ["project_id", "content"],
        },
    },
    {
        "name": "memory_get",
        "description": "Memory kaydını id ile getir.",
        "inputSchema": {
            "type": "object",
            "properties": {"memory_id": {"type": "string"}},
            "required": ["memory_id"],
        },
    },
    {
        "name": "project_search",
        "description": "Project registry'de proje ara.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "recent_events",
        "description": "Son event'leri getir (agent arası haberleşme).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
]


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    req = urllib.request.Request(API_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:300]}


def handle_tool(name, args):
    if name == "memory_search":
        body = {"query": args.get("query", ""), "limit": args.get("limit", 10)}
        for k in ("project_id", "domains", "types"):
            if args.get(k):
                body[k] = args[k]
        return call("POST", "/v1/memory/search", body)
    if name == "memory_write":
        return call("POST", "/v1/memory", {
            "project_id": args.get("project_id", "global"),
            "domain": args.get("domain", "general"),
            "type": args.get("type", "finding"),
            "content": args["content"],
            "summary": args.get("summary"),
            "importance": args.get("importance", 0.5),
            "tags": args.get("tags", []),
            "persist": args.get("persist", True),
        })
    if name == "memory_get":
        return call("GET", f"/v1/memory/{args['memory_id']}")
    if name == "project_search":
        return {"projects": call("GET", "/v1/projects")}
    if name == "recent_events":
        path = "/v1/events"
        qs = []
        if args.get("project_id"):
            qs.append(f"project_id={args['project_id']}")
        if args.get("limit"):
            qs.append(f"limit={args['limit']}")
        if qs:
            path += "?" + "&".join(qs)
        return {"events": call("GET", path)}
    return {"error": f"unknown tool: {name}"}


def main():
    if not API_KEY:
        sys.stderr.write("HATA: MEMORY_API_KEY env gerekli\n")
        sys.exit(2)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg_id = msg.get("id")
        method = msg.get("method")
        if method == "initialize":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "shared-memory", "version": "1.0.0"}},
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/list":
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            params = msg.get("params", {})
            result = handle_tool(params.get("name", ""), params.get("arguments", {}))
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]},
            }) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            pass
        else:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"method not found: {method}"}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
