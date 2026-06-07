"""
InventoryIQ — local Streamlit chat over the mock lakehouse (DuckDB).

This is the runnable artifact for reviewers without an M365 Copilot tenant.
It uses the same grounding-function shapes the Foundry IQ deployment will use,
so the demo and the real agent answer the same questions the same way.
"""

from __future__ import annotations
import json
import os
import traceback
import streamlit as st
from dotenv import load_dotenv

import grounding
import theme as ui

# Load .env from repo root (parent of demo/)
_HERE = os.path.dirname(__file__)
load_dotenv(os.path.join(_HERE, "..", ".env"))

st.set_page_config(page_title="InventoryIQ", page_icon="🛰️", layout="wide",
                   initial_sidebar_state="expanded")

# Theme bootstrap
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
ui.inject_css()
ui.render_hero()

# ---------- LLM client ----------

USE_AZURE = bool(os.environ.get("AZURE_OPENAI_ENDPOINT") and os.environ.get("AZURE_OPENAI_API_KEY"))

if USE_AZURE:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
    MODEL = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
else:
    client = None
    MODEL = None

SYSTEM = """You are InventoryIQ, an enterprise IT-asset reasoning agent.
You answer questions about an IT estate (servers, laptops, network gear, blueprints, alerts).
You ALWAYS ground answers by calling the provided tools. Never invent rows.
After tool calls, summarize crisply, cite counts, and offer a follow-up suggestion.
If a question is ambiguous, ask one clarifying question before calling tools."""

# ---------- sidebar ----------
with st.sidebar:
    st.markdown("### Try a question")
    samples = [
        "Summarize the IT estate health right now.",
        "Which servers in Building B raised critical alerts in the last 24 hours?",
        "Show laptops assigned to Finance that haven't checked in for 7 days.",
        "Which assets are on the Building A – Floor 2 blueprint?",
        "Which assets are running unsupported OS versions? Group by building.",
        "Whose warranty expires in the next 90 days?",
    ]
    for s in samples:
        if st.button(s, use_container_width=True, key=f"s_{hash(s)}"):
            st.session_state["pending"] = s
    st.divider()
    st.markdown("### Session")
    if st.button("🧹 Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending = None
        st.rerun()
    ui.render_theme_toggle()
    st.divider()
    st.markdown("### About")
    st.caption(
        "InventoryIQ is a Microsoft 365 Copilot declarative agent "
        "for IT asset reasoning, grounded in **Foundry IQ** over an "
        "Azure AI Search index mirrored from InventoryMapper. "
        "This Streamlit surface is the local demo for judges without an M365 tenant."
    )

# Status pills row
ui.render_status_pills()

# ---------- chat state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None


def _render_tool_result(result: dict) -> None:
    rows = result.get("rows", [])
    if not rows:
        st.info("No rows returned.")
        return
    ui.render_html_table(rows)
    cites = result.get("citations", [])
    if cites:
        with st.expander(f"📎 {len(cites)} citation(s) — grounded in lakehouse"):
            ui.render_citations(cites)


def _toolcall_chip(name: str, args: dict) -> None:
    st.markdown(
        f'<div class="iq-toolcall">🛠️ <span class="name">{name}</span>({json.dumps(args)})</div>',
        unsafe_allow_html=True,
    )


def _route(text: str):
    """Cheap deterministic fallback when no LLM is configured."""
    t = text.lower()
    if "critical" in t or "alert" in t:
        building = next((b for b in ("Building A", "Building B", "Building C") if b.lower() in t), None)
        return "assets_by_alert_severity", {"severity": "Critical", "building": building, "hours": 24}
    if "checked in" in t or "stale" in t or "haven't" in t:
        dept = next((d for d in ("Finance", "Engineering", "Sales", "Marketing", "HR", "Operations", "Security", "IT") if d.lower() in t), "Finance")
        return "stale_assets_by_department", {"department": dept, "days": 7}
    if "blueprint" in t or "floor plan" in t:
        return "assets_on_blueprint", {"blueprint_name_like": "Floor"}
    if "unsupported" in t or "end-of-support" in t:
        return "unsupported_os_by_location", {}
    if "warranty" in t:
        return "warranty_expiring", {"days_ahead": 90}
    if "disk" in t or "drive" in t or "procurement" in t:
        return "disk_failure_pattern", {"days": 90}
    return "kpi_summary", {}


# Replay history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m.get("content"):
            st.markdown(m["content"])
        for r in m.get("tool_results", []):
            _toolcall_chip(r["call"], r["args"])
            _render_tool_result(r["result"])

# IMPORTANT: chat_input must be called on every rerun — never short-circuit it.
typed = st.chat_input("Ask about your IT estate…")
user_msg = st.session_state.pending or typed
st.session_state.pending = None

if not user_msg:
    st.stop()

# Render the user message immediately
st.session_state.messages.append({"role": "user", "content": user_msg})
with st.chat_message("user"):
    st.markdown(user_msg)

# ---------- Branch: deterministic fallback when no LLM configured ----------
if client is None:
    with st.chat_message("assistant"):
        st.warning("No Azure OpenAI configured — running in deterministic-routing mode. "
                   "Set AZURE_OPENAI_* in .env for the real agent loop.")
        tool_name, args = _route(user_msg)
        _toolcall_chip(tool_name, args)
        result = grounding.CALLABLES[tool_name](**args)
        _render_tool_result(result)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Called `{tool_name}`.",
            "tool_results": [{"call": tool_name, "args": args, "result": result}],
        })
    st.stop()

# ---------- Branch: real agent loop with tool calling ----------
chat_history = [{"role": "system", "content": SYSTEM}]
for m in st.session_state.messages:
    if m.get("role") in ("user", "assistant") and m.get("content"):
        chat_history.append({"role": m["role"], "content": m["content"]})

tool_results: list[dict] = []

with st.chat_message("assistant"):
    try:
        with st.spinner("Reasoning…"):
            response = client.chat.completions.create(
                model=MODEL,
                messages=chat_history,
                tools=grounding.TOOLS,
                tool_choice="auto",
            )
        msg = response.choices[0].message

        max_iterations = 4
        while msg.tool_calls and max_iterations > 0:
            max_iterations -= 1
            chat_history.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in msg.tool_calls
                ],
            })
            for call in msg.tool_calls:
                name = call.function.name
                args = json.loads(call.function.arguments or "{}")
                _toolcall_chip(name, args)
                if name not in grounding.CALLABLES:
                    err = {"error": f"unknown tool {name}"}
                    chat_history.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(err)})
                    continue
                result = grounding.CALLABLES[name](**args)
                _render_tool_result(result)
                tool_results.append({"call": name, "args": args, "result": result})
                chat_history.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str)[:6000],
                })
            with st.spinner("Synthesizing…"):
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=chat_history,
                    tools=grounding.TOOLS,
                    tool_choice="auto",
                )
            msg = response.choices[0].message

        answer = msg.content or "(no answer)"
        st.markdown(answer)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "tool_results": tool_results,
        })
    except Exception as e:
        st.error(f"LLM call failed: {type(e).__name__}: {e}")
        with st.expander("Traceback"):
            st.code(traceback.format_exc())
