#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
client.py —— mcp-bridge 客户端。你本地自测用，我（Agent）在沙箱里也用它调你的 MCP。

环境变量:
  MCP_BRIDGE_URL    例: https://mcp-agv.example.com  或 http://127.0.0.1:8787
  MCP_BRIDGE_TOKEN  与网关一致的 Bearer token

示例:
  python client.py health
  python client.py servers
  python client.py tools demo
  python client.py call demo echo '{"text":"hello"}'
  python client.py call demo danger_write '{"path":"x"}'     # 应被 403 拦截
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

TIMEOUT = 180


def _req(method: str, path: str, payload: dict | None = None, need_auth: bool = True):
    base = (os.environ.get("MCP_BRIDGE_URL") or "http://127.0.0.1:8787").rstrip("/")
    token = os.environ.get("MCP_BRIDGE_TOKEN", "")
    if need_auth and not token:
        sys.exit("缺少环境变量 MCP_BRIDGE_TOKEN")
    data = json.dumps(payload or {}).encode() if method == "POST" else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if need_auth:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"ok": False, "error": raw}
    except Exception as e:  # noqa: BLE001
        return 0, {"ok": False, "error": f"{type(e).__name__}: {e}"}


def health():
    return _req("GET", "/healthz", need_auth=False)


def servers():
    return _req("GET", "/v1/servers")


def tools(server: str):
    return _req("GET", f"/v1/servers/{server}/tools")


def call(server: str, tool: str, arguments: dict):
    return _req("POST", f"/v1/servers/{server}/tools/{tool}/call", {"arguments": arguments})


def rpc(server: str, method: str, params: dict):
    return _req("POST", f"/v1/servers/{server}/rpc", {"method": method, "params": params})


def _print(code, body):
    print(f"HTTP {code}")
    print(json.dumps(body, ensure_ascii=False, indent=2))
    return 0 if 200 <= code < 300 and body.get("ok", True) else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == "health":
        return _print(*health())
    if cmd == "servers":
        return _print(*servers())
    if cmd == "tools":
        return _print(*tools(sys.argv[2]))
    if cmd == "call":
        args = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        return _print(*call(sys.argv[2], sys.argv[3], args))
    if cmd == "rpc":
        params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        return _print(*rpc(sys.argv[2], sys.argv[3], params))
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
