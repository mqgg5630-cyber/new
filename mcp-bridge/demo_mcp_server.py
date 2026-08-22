#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_mcp_server.py —— 一个零依赖的最小 MCP (stdio) 服务器，用来验证 mcp-bridge 通路。
换成你自己的 MCP 之前，先用它跑通「网关 → 隧道 → 我这边调用」整条链路。

工具:
  echo(text)             回显
  sum(numbers[])         求和
  now()                  当前时间
  list_dir(path)         列目录（只读）
  read_text(path, max_bytes)  读文本文件（只读）
  danger_write(path)     故意的"写操作"，用来验证只读策略确实拦得住
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {"name": "echo", "description": "原样回显一段文本",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}},
                     "required": ["text"]}},
    {"name": "sum", "description": "对一组数字求和",
     "inputSchema": {"type": "object",
                     "properties": {"numbers": {"type": "array", "items": {"type": "number"}}},
                     "required": ["numbers"]}},
    {"name": "now", "description": "返回服务器当前 UTC 时间",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_dir", "description": "列出目录内容（只读）",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}},
                     "required": ["path"]}},
    {"name": "read_text", "description": "读取文本文件内容（只读）",
     "inputSchema": {"type": "object",
                     "properties": {"path": {"type": "string"},
                                    "max_bytes": {"type": "integer", "default": 20000}},
                     "required": ["path"]}},
    {"name": "danger_write", "description": "演示用的写操作，应该被网关只读策略拦截",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}},
                     "required": ["path"]}},
]


def text_result(s: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": s}], "isError": is_error}


def call_tool(name: str, args: dict) -> dict:
    if name == "echo":
        return text_result(str(args.get("text", "")))
    if name == "sum":
        nums = args.get("numbers") or []
        return text_result(str(sum(float(n) for n in nums)))
    if name == "now":
        return text_result(datetime.now(timezone.utc).isoformat(timespec="seconds"))
    if name == "list_dir":
        p = args.get("path") or "."
        if not os.path.isdir(p):
            return text_result(f"不是目录: {p}", True)
        items = sorted(os.listdir(p))[:500]
        return text_result("\n".join(items) or "(空目录)")
    if name == "read_text":
        p = args.get("path") or ""
        n = int(args.get("max_bytes") or 20000)
        if not os.path.isfile(p):
            return text_result(f"文件不存在: {p}", True)
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return text_result(f.read(n))
    if name == "danger_write":
        return text_result("如果你看到这行，说明只读策略没生效！", True)
    return text_result(f"未知工具: {name}", True)


def handle(msg: dict):
    method = msg.get("method")
    mid = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        result = {"protocolVersion": PROTOCOL_VERSION,
                  "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": "demo-mcp-server", "version": "1.0.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        result = call_tool(params.get("name", ""), params.get("arguments") or {})
    elif method and method.startswith("notifications/"):
        return None
    else:
        if mid is None:
            return None
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"Method not found: {method}"}}

    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            resp = handle(msg)
        except Exception as e:  # noqa: BLE001
            resp = {"jsonrpc": "2.0", "id": msg.get("id"),
                    "error": {"code": -32603, "message": str(e)}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
