#!/usr/bin/env python3
"""
n8n 去AI化 GUI：一个按钮触发 n8n 的 CrossRef 文献 BibTeX 工作流（不依赖任何 AI/LLM）。

用法：
    pip install streamlit requests
    streamlit run examples/n8n_crossref_gui.py

前提：
    1. n8n 正在运行（http://localhost:5678）
    2. 工作流第一个节点是 Webhook 节点，且已激活
    3. 把下面 WEBHOOK_URL 改成你的实际地址：
       http://localhost:5678/webhook/<Webhook节点里的Path>
"""
import streamlit as st
import requests

# TODO: 改成你自己的（打开工作流 → 看 Webhook 节点的 Path 字段）
WEBHOOK_URL = "http://localhost:5678/webhook/crossref-bibtex"

st.set_page_config(page_title="文献 BibTeX 生成（n8n · 无AI版）", layout="centered")
st.title("📖 文献 BibTeX 生成器")
st.caption("底层调用本地 n8n 工作流（Webhook 触发），全程不经过任何大模型。")

query = st.text_input("输入论文标题 / 关键词", value="AlphaFold protein structure prediction")

if st.button("🚀 生成 BibTeX", type="primary"):
    if not query.strip():
        st.warning("请输入关键词")
    else:
        try:
            with st.spinner("n8n 正在执行工作流…"):
                r = requests.post(WEBHOOK_URL, json={"query": query.strip()}, timeout=60)
                r.raise_for_status()
            st.success("✅ n8n 工作流执行成功（可在 n8n → Executions 查看记录）")
            st.markdown(r.text)
        except requests.exceptions.ConnectionError:
            st.error("连不上 n8n，请确认 Docker 容器在运行（docker ps）")
        except requests.exceptions.HTTPError as e:
            st.error(f"n8n 返回错误：{e}")
            st.info("确认：工作流已激活？Webhook 节点的 Path 和 WEBHOOK_URL 一致？")
        except Exception as e:  # noqa: BLE001
            st.error(f"调用失败：{e}")
