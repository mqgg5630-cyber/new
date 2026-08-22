#!/usr/bin/env python3
"""
示例 1：论文检索 GUI（无 AI 版）
把 paper-search-mcp 的检索能力包成 Streamlit 网页 —— 不依赖任何 LLM/AI。

用法：
    pip install streamlit mcp
    streamlit run examples/paper_search_gui.py

依赖说明：
    - paper-search-mcp（由本脚本自动用 uvx 拉起，无需手动安装）
    - streamlit、mcp（Python 包）
"""
import asyncio

import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_SERVER = StdioServerParameters(command="uvx", args=["paper-search-mcp"])


async def search_papers(query: str, max_results: int) -> list[dict]:
    """通过 MCP 协议调用 paper-search-mcp 的 search_papers 工具（无 LLM）。"""
    async with stdio_client(MCP_SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            tool = "search_papers" if "search_papers" in names else names[0]
            result = await session.call_tool(
                tool,
                {"query": query, "max_results": max_results},
            )
            # 解析返回内容为可展示的表格行
            rows = []
            for item in result.content:
                text = getattr(item, "text", None) or str(item)
                rows.append({"结果": text})
            return rows


st.set_page_config(page_title="论文检索工具（无AI版）", layout="wide")
st.title("📚 论文检索工具（无AI版）")
st.caption("底层走 paper-search-mcp（arXiv / PubMed / Semantic Scholar / Crossref 等 20+ 源），本页面不调用任何大模型。")

query = st.text_input("检索关键词", value="retrieval augmented generation")
max_results = st.slider("返回条数", 1, 20, 5)

if st.button("🔍 检索", type="primary"):
    if not query.strip():
        st.warning("请输入关键词")
    else:
        with st.spinner("检索中…（首次运行会通过 uvx 下载 paper-search-mcp）"):
            try:
                rows = asyncio.run(search_papers(query.strip(), max_results))
                st.success(f"共返回 {len(rows)} 条结果")
                st.dataframe(rows, use_container_width=True)
                st.download_button(
                    "导出 CSV",
                    data="\n".join(r["结果"] for r in rows),
                    file_name="papers.csv",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"检索失败：{exc}")
                st.info("提示：请确认已安装 uv（https://docs.astral.sh/uv/），并联网。")
