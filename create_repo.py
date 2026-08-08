#!/usr/bin/env python3
"""Create GitHub repo ai-agent-team and push. Token'i ~/.git-credentials'tan okur, asla yazdırmaz."""
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error

cred_file = os.path.expanduser("~/.git-credentials")
if not os.path.exists(cred_file):
    # git credential store default path; fallback: ask git
    r = subprocess.run(["git", "config", "--global", "credential.helper"], capture_output=True, text=True)
    print("credential.helper:", r.stdout.strip())
    print("NO CRED FILE at", cred_file)
    sys.exit(1)

cred = open(cred_file).read().strip()
m = re.match(r"https://([^:]+):([^@]+)@github\.com", cred)
if not m:
    print("CRED FORMAT UNEXPECTED")
    sys.exit(1)
user, token = m.group(1), m.group(2)
print("user:", user, "| token_len:", len(token))

def gh(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"https://api.github.com{path}", data=data, method=method,
                                 headers={"Authorization": f"Bearer {token}", "User-Agent": "hermes",
                                          "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read()) if r.status != 204 else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.headers.get("Content-Type", "").startswith("application/json") else e.read().decode()

s, d = gh("GET", "/user")
if s != 200:
    print("AUTH FAIL:", s, d)
    sys.exit(1)
login = d["login"]
print("GitHub user:", login)

s, d = gh("GET", f"/repos/{login}/ai-agent-team")
if s == 200:
    print("Repo zaten var:", d["html_url"])
elif s == 404:
    s, d = gh("POST", "/user/repos", {"name": "ai-agent-team",
                                      "description": "AI Agent Team + Shared Memory (Claude Code + Hermes)",
                                      "private": True})
    if s == 201:
        print("Repo oluşturuldu:", d["html_url"])
    else:
        print("REPO CREATE FAIL:", s, d)
        sys.exit(1)
else:
    print("UNEXPECTED:", s, d)
    sys.exit(1)

os.chdir("/opt/data/ai-agent-team")
subprocess.run(["git", "remote", "set-url", "origin", f"https://{user}:{token}@github.com/{login}/ai-agent-team.git"],
               check=True, capture_output=True)
r = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True, timeout=120)
print("PUSH rc:", r.returncode)
if r.returncode != 0:
    print(r.stderr[-800:])
sys.exit(r.returncode)
