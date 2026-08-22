#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp-bridge gateway — 把本地 stdio MCP 服务器安全地暴露成一个 HTTP 接口。

设计原则（安全优先）:
  1. 真正的 MCP 进程是子进程(stdio)，永远不监听任何端口。
  2. 网关默认只绑定 127.0.0.1，公网入口交给 Cloudflare Tunnel。
  3. 每个请求必须带 Authorization: Bearer <token>，常数时间比对。
  4. 工具白名单 + 只读模式 + 危险工具黑名单，三层拦截。
  5. 令牌桶限速 + 全量审计日志(JSONL)。
  6. 零第三方依赖，Windows / Linux / macOS 上 `python gateway.py` 直接跑。

用法:
    set MCP_BRIDGE_TOKEN=<你的长随机token>        (Windows CMD)
    $env:MCP_BRIDGE_TOKEN="<token>"                (PowerShell)
    python gateway.py --config bridge_config.json
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import queue
import secrets
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"

# 只读模式下默认拦截的工具名关键字（大小写不敏感，子串匹配）
DEFAULT_WRITE_PATTERNS = [
    "write", "create", "delete", "remove", "move", "rename", "edit",
    "update", "insert", "put", "patch", "drop", "truncate", "exec",
    "run_command", "shell", "terminal", "kill", "install", "upload",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# --------------------------------------------------------------------------
# MCP stdio 客户端：管理一个 MCP 子进程，做 initialize 握手，转发 JSON-RPC
# --------------------------------------------------------------------------
class StdioMCPClient:
    def __init__(self, name: str, spec: Dict[str, Any], logger):
        self.name = name
        self.spec = spec
        self.log = logger
        self.proc: Optional[subprocess.Popen] = None
        # RLock: start() 持锁期间会调用 _handshake() -> request()，必须可重入
        self.lock = threading.RLock()
        self._id_lock = threading.Lock()
        self._id = 0
        self._pending: Dict[Any, "queue.Queue[dict]"] = {}
        self._pending_lock = threading.Lock()
        self._reader: Optional[threading.Thread] = None
        self._alive = False
        self.server_info: Dict[str, Any] = {}
        self.timeout = float(spec.get("timeout_seconds", 120))

    # ---- 生命周期 ----
    def start(self) -> None:
        with self.lock:
            if self._alive and self.proc and self.proc.poll() is None:
                return
            cmd = self.spec["command"]
            if isinstance(cmd, str):
                cmd = [cmd]
            env = os.environ.copy()
            env.update({str(k): str(v) for k, v in (self.spec.get("env") or {}).items()})
            env.setdefault("PYTHONIOENCODING", "utf-8")
            cwd = self.spec.get("cwd") or None
            self.log.info(f"[{self.name}] 启动 MCP 子进程: {' '.join(cmd)}")
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            self._alive = True
            self._reader = threading.Thread(target=self._read_loop, daemon=True)
            self._reader.start()
            threading.Thread(target=self._stderr_loop, daemon=True).start()
            self._handshake()

    def stop(self) -> None:
        self._alive = False
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

    def healthy(self) -> bool:
        return bool(self._alive and self.proc and self.proc.poll() is None)

    # ---- IO ----
    def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                self.log.warn(f"[{self.name}] 非 JSON 输出被忽略: {line[:200]}")
                continue
            mid = msg.get("id")
            if mid is not None:
                with self._pending_lock:
                    q = self._pending.pop(mid, None)
                if q:
                    q.put(msg)
        self._alive = False
        self.log.warn(f"[{self.name}] 子进程 stdout 已关闭")

    def _stderr_loop(self) -> None:
        assert self.proc and self.proc.stderr
        for line in self.proc.stderr:
            line = line.rstrip()
            if line:
                self.log.debug(f"[{self.name}][stderr] {line}")

    def _send(self, payload: dict) -> None:
        if not (self.proc and self.proc.stdin):
            raise RuntimeError("MCP 子进程未运行")
        data = json.dumps(payload, ensure_ascii=False) + "\n"
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def request(self, method: str, params: Optional[dict] = None, timeout: Optional[float] = None) -> dict:
        if not self.healthy():
            self.start()
        with self._id_lock:
            self._id += 1
            rid = self._id
        q: "queue.Queue[dict]" = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[rid] = q
        payload = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        try:
            return q.get(timeout=timeout or self.timeout)
        except queue.Empty:
            with self._pending_lock:
                self._pending.pop(rid, None)
            raise TimeoutError(f"MCP 服务器 '{self.name}' 调用 {method} 超时")

    def notify(self, method: str, params: Optional[dict] = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def _handshake(self) -> None:
        resp = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                "clientInfo": {"name": "mcp-bridge-gateway", "version": VERSION},
            },
            timeout=60,
        )
        if "error" in resp:
            raise RuntimeError(f"initialize 失败: {resp['error']}")
        self.server_info = resp.get("result", {})
        self.notify("notifications/initialized")
        self.log.info(f"[{self.name}] 握手成功: {self.server_info.get('serverInfo', {})}")


# --------------------------------------------------------------------------
# 策略引擎
# --------------------------------------------------------------------------
class Policy:
    def __init__(self, spec: Dict[str, Any]):
        self.read_only: bool = bool(spec.get("read_only", True))
        self.allow_tools: List[str] = list(spec.get("allow_tools") or [])
        self.deny_tools: List[str] = list(spec.get("deny_tools") or [])
        self.write_patterns: List[str] = [
            p.lower() for p in (spec.get("write_patterns") or DEFAULT_WRITE_PATTERNS)
        ]
        self.allow_methods: List[str] = list(
            spec.get("allow_methods")
            or ["initialize", "ping", "tools/list", "tools/call",
                "resources/list", "resources/read", "resources/templates/list",
                "prompts/list", "prompts/get"]
        )

    def check_method(self, method: str) -> Optional[str]:
        if method not in self.allow_methods:
            return f"方法 '{method}' 不在 allow_methods 白名单内"
        return None

    def check_tool(self, tool: str) -> Optional[str]:
        low = tool.lower()
        for d in self.deny_tools:
            if d.lower() == low:
                return f"工具 '{tool}' 在 deny_tools 黑名单内"
        if self.allow_tools and not any(a.lower() == low for a in self.allow_tools):
            return f"工具 '{tool}' 不在 allow_tools 白名单内"
        if self.read_only:
            for pat in self.write_patterns:
                if pat in low:
                    # 显式白名单可以豁免只读拦截
                    if any(a.lower() == low for a in self.allow_tools):
                        return None
                    return f"只读模式拦截: 工具 '{tool}' 命中写操作特征 '{pat}'"
        return None

    def visible(self, tool: str) -> bool:
        return self.check_tool(tool) is None


# --------------------------------------------------------------------------
# 限速
# --------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, per_minute: int, burst: int):
        self.rate = max(per_minute, 1) / 60.0
        self.burst = max(burst, 1)
        self.buckets: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            tokens, last = self.buckets.get(key, [float(self.burst), now])
            tokens = min(self.burst, tokens + (now - last) * self.rate)
            if tokens < 1.0:
                self.buckets[key] = [tokens, now]
                return False
            self.buckets[key] = [tokens - 1.0, now]
            return True


# --------------------------------------------------------------------------
# 日志
# --------------------------------------------------------------------------
class Logger:
    LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40}

    def __init__(self, level: str = "info", audit_path: Optional[Path] = None):
        self.level = self.LEVELS.get(level, 20)
        self.audit_path = audit_path
        self.lock = threading.Lock()
        if audit_path:
            audit_path.parent.mkdir(parents=True, exist_ok=True)

    def _emit(self, lvl: str, msg: str) -> None:
        if self.LEVELS[lvl] >= self.level:
            print(f"{utcnow()} [{lvl.upper():5}] {msg}", file=sys.stderr, flush=True)

    def debug(self, m): self._emit("debug", m)
    def info(self, m): self._emit("info", m)
    def warn(self, m): self._emit("warn", m)
    def error(self, m): self._emit("error", m)

    def audit(self, record: dict) -> None:
        record = {"ts": utcnow(), **record}
        self._emit("info", "AUDIT " + json.dumps(record, ensure_ascii=False))
        if not self.audit_path:
            return
        with self.lock:
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------
# 网关
# --------------------------------------------------------------------------
class Gateway:
    def __init__(self, config: Dict[str, Any], config_path: Path):
        self.config = config
        self.config_path = config_path
        logcfg = config.get("logging", {})
        audit = logcfg.get("audit_file", "logs/audit.jsonl")
        audit_path = (config_path.parent / audit) if audit else None
        self.log = Logger(logcfg.get("level", "info"), audit_path)

        auth = config.get("auth", {})
        token = os.environ.get(auth.get("token_env", "MCP_BRIDGE_TOKEN"), "")
        if not token:
            token = auth.get("token", "")
        if not token:
            token = secrets.token_urlsafe(32)
            self.log.warn("=" * 68)
            self.log.warn("未配置 token，已自动生成一次性 token（重启会变）：")
            self.log.warn(f"    {token}")
            self.log.warn("请设置环境变量 MCP_BRIDGE_TOKEN 固化它。")
            self.log.warn("=" * 68)
        if len(token) < 24:
            raise SystemExit("拒绝启动: token 长度必须 >= 24 字符")
        self.token = token
        self.ip_allowlist: List[str] = list(auth.get("ip_allowlist") or [])

        rl = config.get("rate_limit", {})
        self.limiter = RateLimiter(rl.get("per_minute", 60), rl.get("burst", 20))

        self.servers: Dict[str, StdioMCPClient] = {}
        self.policies: Dict[str, Policy] = {}
        for name, spec in (config.get("servers") or {}).items():
            if not spec.get("enabled", True):
                continue
            self.servers[name] = StdioMCPClient(name, spec, self.log)
            self.policies[name] = Policy(spec)
        if not self.servers:
            raise SystemExit("拒绝启动: bridge_config.json 里没有启用任何 servers")

    def check_auth(self, header: Optional[str]) -> bool:
        if not header or not header.startswith("Bearer "):
            return False
        return hmac.compare_digest(header[7:].strip(), self.token)

    def ip_ok(self, ip: str) -> bool:
        return (not self.ip_allowlist) or ip in self.ip_allowlist

    def shutdown(self) -> None:
        for c in self.servers.values():
            c.stop()


class Handler(BaseHTTPRequestHandler):
    gateway: Gateway = None  # type: ignore
    server_version = f"mcp-bridge/{VERSION}"
    protocol_version = "HTTP/1.1"

    # 静音默认访问日志（我们有审计日志）
    def log_message(self, fmt, *args):
        self.gateway.log.debug("http " + (fmt % args))

    # ---- helpers ----
    def _json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code: int, message: str, **extra) -> None:
        self._json(code, {"ok": False, "error": message, **extra})

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        if n > 8 * 1024 * 1024:
            raise ValueError("请求体过大 (>8MB)")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def _client_ip(self) -> str:
        return self.client_address[0]

    def _guard(self) -> bool:
        """鉴权 + 限速。通过返回 True。"""
        g = self.gateway
        ip = self._client_ip()
        if not g.ip_ok(ip):
            g.log.audit({"event": "deny_ip", "ip": ip, "path": self.path})
            self._err(403, "IP 不在允许列表内")
            return False
        if not g.check_auth(self.headers.get("Authorization")):
            g.log.audit({"event": "deny_auth", "ip": ip, "path": self.path})
            time.sleep(0.3)  # 轻微延迟，削弱暴力猜测
            self._err(401, "未授权：缺少或错误的 Bearer token")
            return False
        if not g.limiter.allow(ip):
            g.log.audit({"event": "deny_rate", "ip": ip, "path": self.path})
            self._err(429, "请求过于频繁，请稍后重试")
            return False
        return True

    # ---- routes ----
    def do_GET(self):
        g = self.gateway
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path in ("/healthz", "/"):
            self._json(200, {
                "ok": True, "service": "mcp-bridge", "version": VERSION,
                "time": utcnow(),
                "servers": {n: c.healthy() for n, c in g.servers.items()},
            })
            return

        if not self._guard():
            return

        if path == "/v1/servers":
            out = []
            for name, c in g.servers.items():
                p = g.policies[name]
                out.append({
                    "name": name,
                    "healthy": c.healthy(),
                    "read_only": p.read_only,
                    "allow_tools": p.allow_tools or "(未限制，仅只读规则生效)",
                    "deny_tools": p.deny_tools,
                    "serverInfo": c.server_info.get("serverInfo", {}),
                })
            self._json(200, {"ok": True, "servers": out})
            return

        parts = [x for x in path.split("/") if x]
        # /v1/servers/<name>/tools
        if len(parts) == 4 and parts[:2] == ["v1", "servers"] and parts[3] == "tools":
            name = parts[2]
            if name not in g.servers:
                self._err(404, f"未知的 MCP 服务器 '{name}'")
                return
            try:
                resp = g.servers[name].request("tools/list", {})
            except Exception as e:
                self._err(502, f"上游 MCP 错误: {e}")
                return
            tools = (resp.get("result") or {}).get("tools", [])
            pol = g.policies[name]
            visible = [t for t in tools if pol.visible(t.get("name", ""))]
            hidden = [t.get("name") for t in tools if not pol.visible(t.get("name", ""))]
            g.log.audit({"event": "tools_list", "ip": self._client_ip(),
                         "server": name, "visible": len(visible), "hidden": len(hidden)})
            self._json(200, {"ok": True, "server": name, "tools": visible,
                             "hidden_by_policy": hidden})
            return

        self._err(404, f"未知路径 {path}")

    def do_POST(self):
        g = self.gateway
        path = self.path.split("?")[0].rstrip("/")
        if not self._guard():
            return
        try:
            body = self._body()
        except Exception as e:
            self._err(400, f"请求体解析失败: {e}")
            return

        parts = [x for x in path.split("/") if x]
        if len(parts) < 4 or parts[:2] != ["v1", "servers"]:
            self._err(404, f"未知路径 {path}")
            return
        name = parts[2]
        if name not in g.servers:
            self._err(404, f"未知的 MCP 服务器 '{name}'")
            return
        client, pol = g.servers[name], g.policies[name]
        req_id = str(uuid.uuid4())[:8]

        # /v1/servers/<name>/rpc  —— 原生 JSON-RPC 透传
        if parts[3] == "rpc" and len(parts) == 4:
            method = body.get("method")
            params = body.get("params") or {}
            if not method:
                self._err(400, "缺少 method 字段")
                return
            reason = pol.check_method(method)
            if reason:
                g.log.audit({"event": "deny_policy", "req": req_id, "ip": self._client_ip(),
                             "server": name, "method": method, "reason": reason})
                self._err(403, reason)
                return
            if method == "tools/call":
                tool = params.get("name", "")
                reason = pol.check_tool(tool)
                if reason:
                    g.log.audit({"event": "deny_policy", "req": req_id, "ip": self._client_ip(),
                                 "server": name, "method": method, "tool": tool, "reason": reason})
                    self._err(403, reason)
                    return
            return self._forward(client, name, method, params, req_id)

        # /v1/servers/<name>/tools/<tool>/call —— 便捷调用
        if len(parts) == 6 and parts[3] == "tools" and parts[5] == "call":
            tool = parts[4]
            reason = pol.check_tool(tool)
            if reason:
                g.log.audit({"event": "deny_policy", "req": req_id, "ip": self._client_ip(),
                             "server": name, "tool": tool, "reason": reason})
                self._err(403, reason)
                return
            args = body.get("arguments", body.get("args", {}))
            return self._forward(client, name, "tools/call",
                                 {"name": tool, "arguments": args}, req_id)

        self._err(404, f"未知路径 {path}")

    def _forward(self, client: StdioMCPClient, name: str, method: str,
                 params: dict, req_id: str) -> None:
        g = self.gateway
        t0 = time.time()
        try:
            resp = client.request(method, params)
        except Exception as e:
            g.log.audit({"event": "error", "req": req_id, "ip": self._client_ip(),
                         "server": name, "method": method, "error": str(e)})
            self._err(502, f"上游 MCP 错误: {e}")
            return
        ms = int((time.time() - t0) * 1000)
        g.log.audit({
            "event": "call", "req": req_id, "ip": self._client_ip(), "server": name,
            "method": method, "tool": params.get("name") if method == "tools/call" else None,
            "ms": ms, "ok": "error" not in resp,
        })
        if "error" in resp:
            self._json(200, {"ok": False, "server": name, "req": req_id,
                             "error": resp["error"], "elapsed_ms": ms})
        else:
            self._json(200, {"ok": True, "server": name, "req": req_id,
                             "result": resp.get("result"), "elapsed_ms": ms})


def main() -> None:
    ap = argparse.ArgumentParser(description="mcp-bridge 安全网关")
    ap.add_argument("--config", "-c", default="bridge_config.json", help="配置文件路径")
    ap.add_argument("--host", default=None, help="覆盖绑定地址")
    ap.add_argument("--port", type=int, default=None, help="覆盖端口")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        raise SystemExit(f"配置文件不存在: {cfg_path}\n提示: 复制 bridge_config.example.json 为 bridge_config.json")
    config = json.loads(cfg_path.read_text(encoding="utf-8"))

    gw = Gateway(config, cfg_path)
    host = args.host or config.get("bind", {}).get("host", "127.0.0.1")
    port = args.port or int(config.get("bind", {}).get("port", 8787))

    if host not in ("127.0.0.1", "localhost", "::1"):
        gw.log.warn(f"⚠ 你把网关绑定在 {host}，它将对局域网/公网可见。"
                    f"推荐 127.0.0.1 + Cloudflare Tunnel。")

    # 预热子进程
    for n, c in gw.servers.items():
        try:
            c.start()
        except Exception as e:
            gw.log.error(f"[{n}] 启动失败: {e}")

    Handler.gateway = gw
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    gw.log.info(f"mcp-bridge {VERSION} 已启动 → http://{host}:{port}")
    gw.log.info(f"已加载 MCP 服务器: {', '.join(gw.servers)}")
    gw.log.info("健康检查(免鉴权): GET /healthz")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        gw.log.info("收到 Ctrl+C，正在关闭…")
    finally:
        gw.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    main()
