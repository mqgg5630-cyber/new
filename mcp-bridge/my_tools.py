# -*- coding: utf-8 -*-
"""
my_tools.py —— 在这里写你自己的能力，**普通 Python 函数即可，不需要懂 MCP**。

写函数的三条规矩（照抄示例就行）:
  1. 函数名 = 工具名，不要以 _ 开头
  2. 写 docstring，第一段会成为工具描述（Agent 靠它决定何时调用）
  3. 参数加类型注解 (str/int/float/bool/list/dict)，有默认值 = 可选参数

改完这个文件后，重启网关（Ctrl+C 再跑 start-gateway.ps1）即可生效。

⚠ 安全提醒：这里的函数会真的在你电脑上执行。
   - 涉及写入/删除的函数，函数名里带 write/delete 等词会被网关只读模式自动拦截
   - 想放行就在 bridge_config.json 的 allow_tools 里显式列出该函数名
"""

from __future__ import annotations

import csv
import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path

# ============================================================
# 在这里改成你自己的工作目录（所有文件操作都限制在这个目录内）
# ============================================================
WORKSPACE = Path(os.environ.get("MY_TOOLS_WORKSPACE", r"E:\0mcp-agv\workspace"))


def _safe(path: str) -> Path:
    """把相对路径限制在 WORKSPACE 内，防止路径穿越（内部函数，不会暴露为工具）。"""
    p = (WORKSPACE / path).resolve()
    if not str(p).startswith(str(WORKSPACE.resolve())):
        raise ValueError(f"路径越界，只允许访问 {WORKSPACE} 内的文件")
    return p


# ------------------------------------------------------------------
# 示例 1：环境信息
# ------------------------------------------------------------------
def machine_info() -> dict:
    """返回这台电脑的基本信息（系统、Python 版本、工作目录、当前时间）。"""
    return {
        "system": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "workspace": str(WORKSPACE),
        "workspace_exists": WORKSPACE.exists(),
        "time": datetime.now().isoformat(timespec="seconds"),
    }


# ------------------------------------------------------------------
# 示例 2：找文件（科研常用：在一堆资料里定位）
# ------------------------------------------------------------------
def find_files(pattern: str = "*", subdir: str = ".", limit: int = 100) -> dict:
    """在工作目录里按通配符查找文件，例如 pattern='*.pdf' 或 '*2024*.xlsx'。"""
    base = _safe(subdir)
    hits = []
    for p in sorted(base.rglob(pattern)):
        if p.is_file():
            hits.append({
                "path": str(p.relative_to(WORKSPACE)),
                "size_kb": round(p.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes"),
            })
            if len(hits) >= limit:
                break
    return {"count": len(hits), "files": hits}


# ------------------------------------------------------------------
# 示例 3：读文本 / CSV 摘要（办公常用）
# ------------------------------------------------------------------
def read_text(path: str, max_chars: int = 20000) -> str:
    """读取工作目录内一个文本文件的内容。"""
    return _safe(path).read_text(encoding="utf-8", errors="replace")[:max_chars]


def csv_summary(path: str, rows: int = 5) -> dict:
    """读取 CSV 文件，返回列名、总行数和前几行样例，用于快速了解数据结构。"""
    p = _safe(path)
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return {"columns": [], "total_rows": 0, "sample": []}
        sample, total = [], 0
        for i, row in enumerate(reader):
            total += 1
            if i < rows:
                sample.append(dict(zip(header, row)))
    return {"columns": header, "total_rows": total, "sample": sample}


# ------------------------------------------------------------------
# 示例 4：调用你已有的本地脚本（把任何 .py / .exe 变成 Agent 能用的能力）
# ------------------------------------------------------------------
def run_agv_script(script: str, args: str = "", timeout_seconds: int = 120) -> dict:
    """运行工作目录内一个 Python 脚本并返回它的输出。

    注意：函数名含 'run'，默认会被只读模式放行（run 不在拦截词表里），
    但仍建议在 bridge_config.json 的 allow_tools 里显式控制。
    """
    p = _safe(script)
    if p.suffix != ".py":
        raise ValueError("只允许运行 .py 脚本")
    cmd = ["python", str(p)] + (args.split() if args else [])
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=timeout_seconds, cwd=str(WORKSPACE))
    return {"returncode": r.returncode,
            "stdout": r.stdout[-8000:],
            "stderr": r.stderr[-4000:]}


# ------------------------------------------------------------------
# 示例 5：一个写操作（默认会被只读模式拦截，演示用）
# ------------------------------------------------------------------
def write_note(filename: str, content: str) -> str:
    """把一段文字写入工作目录下的文件（函数名含 write，默认被只读策略拦截）。"""
    p = _safe(filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"已写入 {p} ({len(content)} 字符)"


# ------------------------------------------------------------------
# 你的能力从这里往下加 ↓↓↓
# ------------------------------------------------------------------
