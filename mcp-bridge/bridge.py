#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bridge.py —— 一条命令搞定一切（不依赖 PowerShell，Windows/Linux/macOS 通用）

    python bridge.py up          ⭐ 最常用：起网关 + 起隧道，打印 URL 和 TOKEN
    python bridge.py check       自检（12 项）
    python bridge.py serve       只起网关（127.0.0.1:8787）
    python bridge.py tunnel      只起隧道（网关需已在运行）
    python bridge.py token       查看当前 token
    python bridge.py token --new 重新生成 token
    python bridge.py tools       列出当前可用的工具

token 保存在 .bridge_token（已在 .gitignore 里，不会被提交）。
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable or "python"
TOKEN_FILE = HERE / ".bridge_token"
CONFIG = HERE / "bridge_config.json"
EXAMPLE = HERE / "bridge_config.example.json"
BIN = HERE / "bin"
CONN_FILE = HERE / "logs" / "connection.txt"

URL_RE = re.compile(r"https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com")

C_OK, C_WARN, C_ERR, C_HL, C_OFF = "\033[92m", "\033[93m", "\033[91m", "\033[96m", "\033[0m"
if os.name == "nt" and not os.environ.get("WT_SESSION"):
    try:  # Windows 10+ 开启 ANSI
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        C_OK = C_WARN = C_ERR = C_HL = C_OFF = ""


def say(msg: str, color: str = "") -> None:
    print(f"{color}{msg}{C_OFF}", flush=True)


# --------------------------------------------------------------------- token
def get_token(new: bool = False) -> str:
    if not new:
        env = os.environ.get("MCP_BRIDGE_TOKEN")
        if env and len(env) >= 24:
            return env
        if TOKEN_FILE.exists():
            t = TOKEN_FILE.read_text(encoding="utf-8").strip()
            if len(t) >= 24:
                return t
    t = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(t, encoding="utf-8")
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except Exception:
        pass
    say(f"[token] 已生成新 token 并保存到 {TOKEN_FILE.name}", C_OK)
    return t


def ensure_config() -> None:
    if not CONFIG.exists():
        shutil.copy(EXAMPLE, CONFIG)
        say(f"[配置] 已生成 {CONFIG.name}（可按需修改 servers 段）", C_OK)


def get_port() -> int:
    try:
        return int(json.loads(CONFIG.read_text(encoding="utf-8"))
                   .get("bind", {}).get("port", 8787))
    except Exception:
        return 8787


# ------------------------------------------------------------------- gateway
def wait_health(port: int, timeout: float = 40) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/healthz", timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def start_gateway(token: str, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["MCP_BRIDGE_TOKEN"] = token
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen([PY, str(HERE / "gateway.py"), "-c", str(CONFIG)],
                            cwd=str(HERE), env=env)


# -------------------------------------------------------------------- tunnel
def _download(url: str, dest: Path, attempts: int = 3) -> None:
    """带重试的下载；urllib 失败时回退到 curl / PowerShell。"""
    last = None
    for i in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mcp-bridge"})
            with urllib.request.urlopen(req, timeout=300) as r, dest.open("wb") as f:
                shutil.copyfileobj(r, f, length=1024 * 256)
            if dest.stat().st_size > 1_000_000:
                return
            last = RuntimeError(f"文件过小 ({dest.stat().st_size} 字节)，可能被截断")
        except Exception as e:  # noqa: BLE001
            last = e
        say(f"[下载] 第 {i} 次失败: {last}", C_WARN)
        time.sleep(2 * i)

    # 回退方案
    for cmd in (["curl", "-fsSL", "--retry", "3", "-o", str(dest), url],
                ["powershell", "-NoProfile", "-Command",
                 f"Invoke-WebRequest -Uri '{url}' -OutFile '{dest}' -UseBasicParsing"]):
        if not shutil.which(cmd[0]):
            continue
        say(f"[下载] 改用 {cmd[0]} 重试 …", C_WARN)
        if subprocess.call(cmd) == 0 and dest.exists() and dest.stat().st_size > 1_000_000:
            return
    raise RuntimeError(
        f"cloudflared 下载失败: {last}\n"
        f"请手动下载 {url}\n"
        f"另存为 {dest} 后重新运行。")


def cloudflared_path() -> Path:
    system, machine = platform.system().lower(), platform.machine().lower()
    if system == "windows":
        name, asset = "cloudflared.exe", "cloudflared-windows-amd64.exe"
    elif system == "darwin":
        name, asset = "cloudflared", "cloudflared-darwin-amd64.tgz"
    else:
        arch = "arm64" if machine in ("aarch64", "arm64") else "amd64"
        name, asset = "cloudflared", f"cloudflared-linux-{arch}"

    exe = BIN / name
    if exe.exists():
        return exe
    found = shutil.which(name)
    if found:
        return Path(found)

    BIN.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/{asset}"
    say(f"[下载] cloudflared ... ({asset})", C_WARN)
    tmp = BIN / (asset if asset.endswith(".tgz") else name)
    _download(url, tmp)
    if asset.endswith(".tgz"):
        import tarfile
        with tarfile.open(tmp) as tf:
            tf.extractall(BIN)
        tmp.unlink(missing_ok=True)
    if os.name != "nt":
        os.chmod(exe, 0o755)
    say(f"[下载] 完成 -> {exe} ({exe.stat().st_size // 1024 // 1024} MB)", C_OK)
    return exe


def start_tunnel(port: int, named: str = "") -> tuple[subprocess.Popen, "list[str]"]:
    exe = cloudflared_path()
    if named:
        cmd = [str(exe), "tunnel", "--no-autoupdate", "run",
               "--url", f"http://127.0.0.1:{port}", named]
    else:
        cmd = [str(exe), "tunnel", "--no-autoupdate",
               "--url", f"http://127.0.0.1:{port}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", bufsize=1)
    found: list[str] = []

    def reader() -> None:
        assert proc.stdout
        for line in proc.stdout:
            line = line.rstrip()
            m = URL_RE.search(line)
            if m and not found:
                found.append(m.group(0))
            low = line.lower()
            if any(k in low for k in ("error", "failed", "warn")) or m:
                print("  [cloudflared] " + line, flush=True)

    threading.Thread(target=reader, daemon=True).start()
    return proc, found


# -------------------------------------------------------------------- 命令
def cmd_up(args) -> int:
    ensure_config()
    token, port = get_token(), get_port()

    say("\n[1/3] 启动本地网关 …", C_HL)
    gw = start_gateway(token, port)
    if not wait_health(port):
        say("[错误] 网关未能在 40 秒内就绪。请单独运行 `python bridge.py serve` 看报错。", C_ERR)
        gw.terminate()
        return 1
    say(f"      网关在线 http://127.0.0.1:{port}", C_OK)

    say("\n[2/3] 建立 Cloudflare 隧道 …", C_HL)
    try:
        tn, found = start_tunnel(port, args.named)
    except Exception as e:
        say(f"[错误] 隧道启动失败: {e}", C_ERR)
        gw.terminate()
        return 1

    url = ""
    if args.named:
        url = args.named
    else:
        for _ in range(120):
            if found:
                url = found[0]
                break
            if tn.poll() is not None:
                break
            time.sleep(0.5)

    say("\n[3/3] 就绪", C_HL)
    if not url:
        say("[警告] 没抓到公网地址，请看上面 cloudflared 的输出。", C_WARN)
    else:
        CONN_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONN_FILE.write_text(f"URL:   {url}\nTOKEN: {token}\n", encoding="utf-8")
        bar = "=" * 64
        print(f"\n{C_HL}{bar}")
        print("  把下面两行发给 Agent：")
        print(bar + C_OFF)
        print(f"  URL:   {C_OK}{url}{C_OFF}")
        print(f"  TOKEN: {C_OK}{token}{C_OFF}")
        print(f"{C_HL}{bar}{C_OFF}")
        print(f"  （也已保存到 {CONN_FILE.relative_to(HERE)}）")
        print(f"  按 Ctrl+C 关闭，公网入口立即失效。\n")

    try:
        while True:
            time.sleep(1)
            if gw.poll() is not None:
                say("[退出] 网关进程已结束", C_ERR)
                break
            if tn.poll() is not None:
                say("[退出] 隧道进程已结束", C_ERR)
                break
    except KeyboardInterrupt:
        say("\n[关闭] 收到 Ctrl+C …", C_WARN)
    finally:
        for p in (tn, gw):
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        say("[关闭] 网关与隧道均已停止，公网入口已消失。", C_OK)
    return 0


def cmd_serve(args) -> int:
    ensure_config()
    token = get_token()
    say(f"TOKEN: {token}", C_OK)
    env = os.environ.copy()
    env["MCP_BRIDGE_TOKEN"] = token
    return subprocess.call([PY, str(HERE / "gateway.py"), "-c", str(CONFIG)],
                           cwd=str(HERE), env=env)


def cmd_tunnel(args) -> int:
    port = get_port()
    if not wait_health(port, timeout=5):
        say(f"[错误] http://127.0.0.1:{port} 无响应，请先 `python bridge.py serve`", C_ERR)
        return 1
    tn, found = start_tunnel(port, args.named)
    for _ in range(120):
        if found:
            say(f"\n  URL: {found[0]}\n  TOKEN: {get_token()}\n", C_OK)
            break
        time.sleep(0.5)
    try:
        tn.wait()
    except KeyboardInterrupt:
        tn.terminate()
    return 0


def cmd_check(args) -> int:
    return subprocess.call([PY, str(HERE / "smoke_test.py")], cwd=str(HERE))


def cmd_token(args) -> int:
    t = get_token(new=args.new)
    print(t)
    return 0


def cmd_tools(args) -> int:
    ensure_config()
    port, token = get_port(), get_token()
    if not wait_health(port, timeout=3):
        say("[提示] 网关未运行，临时启动一个来枚举工具 …", C_WARN)
        gw = start_gateway(token, port)
        ok = wait_health(port)
    else:
        gw, ok = None, True
    if not ok:
        say("[错误] 网关启动失败", C_ERR)
        return 1
    try:
        env = {"MCP_BRIDGE_URL": f"http://127.0.0.1:{port}", "MCP_BRIDGE_TOKEN": token}
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/servers")
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            servers = json.loads(r.read())["servers"]
        for s in servers:
            name = s["name"]
            say(f"\n■ {name}  (只读={s['read_only']}, 存活={s['healthy']})", C_HL)
            req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/servers/{name}/tools")
            req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read())
            for t in d.get("tools", []):
                say(f"   ✔ {t['name']:<24} {t.get('description','')[:60]}", C_OK)
            for h in d.get("hidden_by_policy", []):
                say(f"   ✖ {h:<24} (被策略拦截)", C_WARN)
        _ = env
    finally:
        if gw:
            gw.terminate()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="mcp-bridge 一键工具",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("up", help="起网关+隧道（最常用）")
    p.add_argument("--named", default="", help="使用命名隧道（需先 cloudflared tunnel create）")
    p.set_defaults(func=cmd_up)

    p = sub.add_parser("serve", help="只起网关")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("tunnel", help="只起隧道")
    p.add_argument("--named", default="")
    p.set_defaults(func=cmd_tunnel)

    sub.add_parser("check", help="自检").set_defaults(func=cmd_check)
    sub.add_parser("tools", help="列出可用工具").set_defaults(func=cmd_tools)

    p = sub.add_parser("token", help="查看/重置 token")
    p.add_argument("--new", action="store_true", help="重新生成")
    p.set_defaults(func=cmd_token)

    args = ap.parse_args()
    if not getattr(args, "func", None):
        ap.print_help()
        return 2
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
