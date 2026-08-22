#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smoke_test.py —— 端到端自检：拉起网关 + demo MCP，验证鉴权/白名单/只读/限速/调用。
用法: python smoke_test.py            (自测本地)
      python smoke_test.py --remote   (测已配置好的 MCP_BRIDGE_URL 远程隧道)
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable
PASS, FAIL = 0, 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}  {detail}")


def main() -> int:
    remote = "--remote" in sys.argv
    proc = None
    port = 8799

    if not remote:
        token = secrets.token_urlsafe(32)
        cfg = {
            "bind": {"host": "127.0.0.1", "port": port},
            "auth": {"token_env": "MCP_BRIDGE_TOKEN"},
            "rate_limit": {"per_minute": 600, "burst": 50},
            "logging": {"level": "warn", "audit_file": "smoke_audit.jsonl"},
            "servers": {
                "demo": {
                    "command": [PY, str(HERE / "demo_mcp_server.py")],
                    "read_only": True,
                    "allow_tools": ["echo", "sum", "now", "list_dir", "read_text"],
                    "timeout_seconds": 30,
                }
            },
        }
        cfg_path = HERE / "logs" / "smoke_config.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

        env = os.environ.copy()
        env["MCP_BRIDGE_TOKEN"] = token
        proc = subprocess.Popen([PY, str(HERE / "gateway.py"), "-c", str(cfg_path)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace")
        os.environ["MCP_BRIDGE_TOKEN"] = token
        os.environ["MCP_BRIDGE_URL"] = f"http://127.0.0.1:{port}"

    sys.path.insert(0, str(HERE))
    import client  # noqa: E402

    print("\n== mcp-bridge 端到端自检 ==\n")
    try:
        # 等待就绪
        ready = False
        for _ in range(60):
            code, body = client.health()
            if code == 200:
                ready = True
                break
            time.sleep(0.5)
        check("网关健康检查 /healthz", ready, str(body))
        if not ready:
            return 1

        code, body = client.servers()
        check("Bearer token 鉴权通过", code == 200 and body.get("ok"), str(body))

        # 错误 token 必须 401
        good = os.environ["MCP_BRIDGE_TOKEN"]
        os.environ["MCP_BRIDGE_TOKEN"] = "wrong-token-wrong-token-wrong-x"
        code, _ = client.servers()
        check("错误 token 被拒绝 (401)", code == 401, f"实际 {code}")
        os.environ["MCP_BRIDGE_TOKEN"] = good

        # 无 token 必须 401
        code, _ = client._req("GET", "/v1/servers", need_auth=False)
        check("无 token 被拒绝 (401)", code == 401, f"实际 {code}")

        code, body = client.tools("demo")
        names = [t["name"] for t in body.get("tools", [])]
        check("tools/list 可用", code == 200 and "echo" in names, str(body)[:300])
        check("危险工具 danger_write 已被策略隐藏",
              "danger_write" not in names and "danger_write" in body.get("hidden_by_policy", []),
              str(body.get("hidden_by_policy")))

        code, body = client.call("demo", "echo", {"text": "内网穿透打通了"})
        txt = json.dumps(body, ensure_ascii=False)
        check("调用 echo 成功", code == 200 and "内网穿透打通了" in txt, txt[:300])

        code, body = client.call("demo", "sum", {"numbers": [1, 2, 3.5]})
        check("调用 sum 成功", "6.5" in json.dumps(body), json.dumps(body)[:200])

        code, body = client.call("demo", "danger_write", {"path": "x"})
        check("只读策略拦截写操作 (403)", code == 403, f"实际 {code} {body}")

        code, body = client.rpc("demo", "tools/list", {})
        check("原生 JSON-RPC 透传可用", code == 200 and body.get("ok"), str(body)[:200])

        code, body = client.rpc("demo", "resources/subscribe", {})
        check("非白名单 method 被拒 (403)", code == 403, f"实际 {code}")

        audit = HERE / "logs" / "smoke_audit.jsonl"
        check("审计日志已写入", audit.exists() and audit.stat().st_size > 0, str(audit))

    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

    print(f"\n结果: {PASS} 通过 / {FAIL} 失败\n")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
