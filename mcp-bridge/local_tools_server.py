#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_tools_server.py —— 「不用懂 MCP」适配器。

你只需要在 my_tools.py 里写**普通 Python 函数**，这个文件会自动把它们
变成标准 MCP 工具，接到 mcp-bridge 网关上，享受同一套安全策略
（Token / 白名单 / 只读 / 限速 / 审计）。

规则:
  - my_tools.py 里所有不以 _ 开头的顶层函数都会被自动注册成工具
  - 函数的 docstring = 工具描述（Agent 靠它判断什么时候用）
  - 类型注解 (str/int/float/bool/list/dict) = 参数 schema
  - 有默认值的参数 = 可选参数
  - 返回值会被 str() 后返回；返回 dict/list 则以 JSON 呈现

在 bridge_config.json 里这样挂载:
  "mytools": {
    "enabled": true,
    "command": ["python", "local_tools_server.py"],
    "cwd": "E:\\\\0mcp-agv\\\\new1\\\\mcp-bridge",
    "read_only": true,
    "allow_tools": []
  }
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List

PROTOCOL_VERSION = "2024-11-05"

TYPE_MAP = {
    str: "string", int: "integer", float: "number",
    bool: "boolean", list: "array", dict: "object",
}
# 兼容 `from __future__ import annotations`：此时注解是字符串而非类型对象
TYPE_MAP_STR = {
    "str": "string", "int": "integer", "float": "number",
    "bool": "boolean", "list": "array", "dict": "object",
    "Any": "string",
}


def json_type(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "string"
    if isinstance(annotation, str):
        base = annotation.strip().split("[")[0].split(".")[-1]
        return TYPE_MAP_STR.get(base, "string")
    return TYPE_MAP.get(annotation, "string")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("my_tools", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载 {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["my_tools"] = mod
    spec.loader.exec_module(mod)
    return mod


def build_schema(fn: Callable) -> Dict[str, Any]:
    sig = inspect.signature(fn)
    props: Dict[str, Any] = {}
    required: List[str] = []
    for name, p in sig.parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        jtype = json_type(p.annotation)
        entry: Dict[str, Any] = {"type": jtype}
        if p.default is not p.empty:
            entry["default"] = p.default
        else:
            required.append(name)
        props[name] = entry
    schema: Dict[str, Any] = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def discover(mod) -> Dict[str, Callable]:
    out: Dict[str, Callable] = {}
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
            out[name] = obj
    return out


def text_result(s: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": s}], "isError": is_error}


def main() -> None:
    here = Path(__file__).parent
    tools_file = Path(os.environ.get("LOCAL_TOOLS_FILE") or (here / "my_tools.py"))
    if not tools_file.exists():
        print(f"[local_tools_server] 找不到 {tools_file}", file=sys.stderr)
        sys.exit(1)

    mod = load_module(tools_file)
    funcs = discover(mod)
    print(f"[local_tools_server] 已注册 {len(funcs)} 个工具: {', '.join(funcs) or '(无)'}",
          file=sys.stderr, flush=True)

    tool_defs = [
        {"name": n,
         "description": (inspect.getdoc(f) or f"本地函数 {n}").strip().split("\n\n")[0],
         "inputSchema": build_schema(f)}
        for n, f in funcs.items()
    ]

    def handle(msg: dict):
        method, mid = msg.get("method"), msg.get("id")
        params = msg.get("params") or {}

        if method == "initialize":
            result = {"protocolVersion": PROTOCOL_VERSION,
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "local-tools-server", "version": "1.0.0"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_defs}
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments") or {}
            fn = funcs.get(name)
            if not fn:
                result = text_result(f"未知工具: {name}", True)
            else:
                try:
                    ret = fn(**args)
                    if isinstance(ret, (dict, list)):
                        ret = json.dumps(ret, ensure_ascii=False, indent=2, default=str)
                    result = text_result("" if ret is None else str(ret))
                except Exception:
                    result = text_result(traceback.format_exc(limit=3), True)
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
