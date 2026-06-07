"""
InventoryIQ — visual theme helpers.

Pastel sky-blue palette, dark + light variants.
Both modes share the same primary so the brand stays consistent across the toggle.
"""

from __future__ import annotations
import os
import streamlit as st
import pandas as pd
from html import escape


# ---------- palette ----------

DARK = {
    "bg":         "#0B1220",
    "panel":      "#111A2E",
    "panel_alt":  "#162038",
    "border":     "#22304F",
    "text":       "#E6ECF5",
    "muted":      "#94A3B8",
    "primary":    "#38BDF8",  # sky-400
    "primary_2":  "#60A5FA",  # blue-400
    "accent":     "#C4B5FD",  # violet-300 — pastel
    "good":       "#34D399",
    "warn":       "#FBBF24",
    "bad":        "#F87171",
    "table_head_bg": "#1B2747",
    "table_row_alt": "#0E1729",
    "glow_a":     "1A",
    "glow_b":     "10",
}

LIGHT = {
    "bg":         "#FAFCFF",
    "panel":      "#FFFFFF",
    "panel_alt":  "#F0F9FF",  # sky-50 — pastel tint
    "border":     "#BAE6FD",  # sky-200 — soft pastel border
    "text":       "#0F172A",
    "muted":      "#64748B",
    "primary":    "#38BDF8",  # sky-400 — same as dark, shared brand
    "primary_2":  "#0EA5E9",  # sky-500
    "accent":     "#C4B5FD",  # violet-300
    "good":       "#10B981",
    "warn":       "#F59E0B",
    "bad":        "#EF4444",
    "table_head_bg": "#E0F2FE",  # sky-100 — pastel header
    "table_row_alt": "#F0F9FF",  # sky-50 — pastel zebra
    "glow_a":     "0E",
    "glow_b":     "08",
}


def palette() -> dict:
    return DARK if st.session_state.get("theme", "dark") == "dark" else LIGHT


def is_dark() -> bool:
    return st.session_state.get("theme", "dark") == "dark"


# ---------- CSS ----------

def inject_css() -> None:
    p = palette()
    user_bubble_bg = p['panel_alt']

    css = f"""
    <style>
      /* ---------- CSS variable override — wins against Streamlit defaults ---------- */
      :root, .stApp, [data-testid="stAppViewContainer"] {{
        --background-color: {p['bg']} !important;
        --secondary-background-color: {p['panel']} !important;
        --text-color: {p['text']} !important;
        --primary-color: {p['primary']} !important;
        --font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
      }}

      /* ---------- Global canvas ---------- */
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background:
          radial-gradient(800px 500px at 10% -10%, {p['primary']}{p['glow_a']}, transparent 60%),
          radial-gradient(700px 400px at 110% 10%, {p['accent']}{p['glow_b']}, transparent 55%),
          {p['bg']} !important;
        color: {p['text']} !important;
      }}
      [data-testid="stHeader"] {{ background: transparent !important; }}

      /* ---------- Sidebar ---------- */
      [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background: {p['panel']} !important;
        border-right: 1px solid {p['border']} !important;
      }}
      [data-testid="stSidebar"] * {{ color: {p['text']}; }}
      [data-testid="stSidebar"] h3 {{
        font-size: 11px !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {p['muted']} !important;
        margin: 1rem 0 0.5rem 0 !important;
      }}

      /* ---------- Hero / brand header ---------- */
      .iq-hero {{
        display: flex; align-items: center; gap: 14px;
        padding: 14px 18px; margin: 0 0 18px 0;
        background: {p['panel']};
        border: 1px solid {p['border']};
        border-radius: 14px;
      }}
      .iq-hero .logo {{
        width: 40px; height: 40px; border-radius: 10px;
        display: grid; place-items: center;
        background: linear-gradient(135deg, {p['primary']}, {p['accent']});
        color: white; font-size: 20px; font-weight: 700;
        flex-shrink: 0;
      }}
      .iq-hero .title {{ font-size: 18px; font-weight: 700; letter-spacing: -0.01em; color: {p['text']}; }}
      .iq-hero .subtitle {{ font-size: 13px; color: {p['muted']}; margin-top: 2px; }}

      /* ---------- Status pills ---------- */
      .iq-pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px 0; }}
      .iq-pill {{
        display: inline-flex; align-items: center; gap: 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12px;
        padding: 5px 10px; border-radius: 999px;
        background: {p['panel']}; border: 1px solid {p['border']}; color: {p['text']};
      }}
      .iq-pill .dot {{ width: 7px; height: 7px; border-radius: 50%; background: {p['good']}; }}
      .iq-pill.warn .dot {{ background: {p['warn']}; }}
      .iq-pill .k {{ color: {p['muted']}; }}
      .iq-pill .v {{ color: {p['text']}; font-weight: 600; }}

      /* ---------- Chat bubbles ---------- */
      [data-testid="stChatMessage"] {{
        background: {p['panel']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
      }}
      [data-testid="stChatMessage"] p,
      [data-testid="stChatMessage"] li,
      [data-testid="stChatMessage"] strong,
      [data-testid="stChatMessage"] span {{ color: {p['text']} !important; }}
      [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
        background: {user_bubble_bg} !important;
      }}

      /* ---------- Buttons ---------- */
      .stButton > button {{
        background: {p['panel']} !important;
        color: {p['text']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 10px !important;
        text-align: left;
        font-weight: 500;
        font-size: 13px !important;
        transition: all 120ms ease;
        box-shadow: none !important;
      }}
      .stButton > button:hover {{
        border-color: {p['primary']} !important;
        background: {p['primary']}11 !important;
        color: {p['text']} !important;
      }}
      .stButton > button:focus {{
        box-shadow: 0 0 0 3px {p['primary']}33 !important;
      }}

      /* ---------- Bottom chat-input strip ---------- */
      [data-testid="stBottomBlockContainer"],
      [data-testid="stBottom"],
      [data-testid="stBottom"] > div {{
        background: {p['bg']} !important;
        border-top: 1px solid {p['border']} !important;
      }}
      [data-testid="stChatInput"] {{ background: transparent !important; }}
      [data-testid="stChatInput"] > div,
      [data-testid="stChatInput"] > div > div {{
        background: {p['panel']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 12px !important;
      }}
      [data-testid="stChatInput"] textarea {{
        background: {p['panel']} !important;
        color: {p['text']} !important;
        border: none !important;
        font-size: 14px !important;
        caret-color: {p['primary']};
      }}
      [data-testid="stChatInput"] textarea::placeholder {{ color: {p['muted']} !important; }}
      [data-testid="stChatInput"] > div:focus-within {{
        border-color: {p['primary']} !important;
        box-shadow: 0 0 0 3px {p['primary']}22 !important;
      }}
      [data-testid="stChatInput"] button {{
        background: transparent !important;
        color: {p['muted']} !important;
      }}
      [data-testid="stChatInput"] button:hover {{ color: {p['primary']} !important; }}
      [data-testid="stChatInput"] svg {{ fill: currentColor !important; }}

      /* ---------- Custom HTML table ---------- */
      .iq-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid {p['border']};
        border-radius: 12px;
        overflow: hidden;
        font-size: 13px;
        margin: 6px 0 6px 0;
        background: {p['panel']};
      }}
      .iq-table thead th {{
        background: {p['table_head_bg']};
        color: {p['text']};
        font-weight: 600;
        text-align: left;
        padding: 9px 12px;
        border-bottom: 1px solid {p['border']};
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }}
      .iq-table tbody td {{
        padding: 8px 12px;
        border-bottom: 1px solid {p['border']};
        color: {p['text']};
        vertical-align: top;
      }}
      .iq-table tbody tr:nth-child(even) td {{ background: {p['table_row_alt']}; }}
      .iq-table tbody tr:last-child td {{ border-bottom: none; }}
      .iq-table tbody tr:hover td {{ background: {p['primary']}0E; }}

      .iq-table-wrap {{
        max-height: 360px;
        overflow: auto;
        border-radius: 12px;
      }}

      /* ---------- Captions ---------- */
      .stCaption, [data-testid="caption"], small {{
        color: {p['muted']} !important;
        font-size: 12px !important;
      }}

      /* ---------- Dividers ---------- */
      hr {{ border-color: {p['border']} !important; opacity: 0.6; }}

      /* ---------- Tool-call chip ---------- */
      .iq-toolcall {{
        display: inline-flex; align-items: center; gap: 6px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 11px;
        background: {p['accent']}22; color: {p['text']};
        border: 1px solid {p['accent']}66;
        padding: 3px 9px; border-radius: 6px;
        margin: 0 0 8px 0;
      }}
      .iq-toolcall .name {{ color: {p['primary_2']}; font-weight: 600; }}

      /* ---------- Info/warning/error blocks ---------- */
      [data-testid="stAlert"] {{
        background: {p['panel']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 10px !important;
      }}
      [data-testid="stAlert"] * {{ color: {p['text']} !important; }}

      /* ---------- Expander ---------- */
      [data-testid="stExpander"],
      [data-testid="stExpander"] > details,
      [data-testid="stExpander"] > div {{
        background: {p['panel']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 10px !important;
        overflow: hidden;
      }}
      /* SUMMARY HEADER background + text — override Streamlit's emotion-cache  */
      [data-testid="stExpander"] details > summary,
      [data-testid="stExpander"] summary,
      [data-testid="stExpanderToggleIcon"] {{
        background: {p['panel']} !important;
        color: {p['text']} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 10px 14px !important;
        border-radius: 10px 10px 0 0 !important;
      }}
      /* Force summary inner text + markdown to inherit palette */
      [data-testid="stExpander"] details > summary *,
      [data-testid="stExpander"] summary *,
      [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
      [data-testid="stExpander"] [data-testid="stMarkdownContainer"] *,
      [data-testid="stExpander"] [data-testid="stExpanderDetails"] *,
      [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] {{
        color: {p['text']} !important;
        opacity: 1 !important;
        background-color: transparent !important;
      }}
      [data-testid="stExpander"] details > summary:hover,
      [data-testid="stExpander"] summary:hover {{
        background: {p['primary']}0E !important;
      }}
      [data-testid="stExpander"] details[open] > summary {{
        border-bottom: 1px solid {p['border']} !important;
        border-radius: 10px 10px 0 0 !important;
      }}
      /* Body of the expander */
      [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
        background: {p['panel']} !important;
        padding: 6px 14px 12px 14px !important;
      }}
      /* Chevron icon color */
      [data-testid="stExpander"] svg {{
        fill: {p['muted']} !important;
        color: {p['muted']} !important;
      }}

      /* ---------- Hide default footer (NOT toolbar — that has the sidebar toggle) ---------- */
      footer {{ visibility: hidden; height: 0 !important; }}
      /* Keep the toolbar visible — Streamlit puts the sidebar collapse/expand button there.
         Just hide the Deploy + share buttons inside it without nuking the whole bar. */
      [data-testid="stToolbar"] [data-testid="stMainMenu"],
      [data-testid="stToolbar"] [data-testid="stDeployButton"] {{ display: none !important; }}

      /* Force-show sidebar collapse control */
      [data-testid="stSidebarCollapseButton"],
      [data-testid="stSidebarCollapsedControl"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
      }}

      /* ---------- Code blocks ---------- */
      pre, code {{
        background: {p['panel_alt']} !important;
        color: {p['text']} !important;
        border-radius: 6px;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------- components ----------

def render_hero(title: str = "InventoryIQ",
                subtitle: str = "IT asset & datacenter reasoning · grounded in Foundry IQ") -> None:
    st.markdown(
        f"""
        <div class="iq-hero">
          <div class="logo">🛰️</div>
          <div>
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_pills() -> None:
    backend = os.environ.get("GROUNDING", "duckdb")
    model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "deterministic")
    db_path = os.environ.get("DUCKDB_PATH", "inv.duckdb")
    db_name = os.path.basename(db_path)
    llm_ok = bool(os.environ.get("AZURE_OPENAI_API_KEY"))

    pills_html = f"""
    <div class="iq-pills">
      <div class="iq-pill">
        <span class="dot"></span>
        <span class="k">grounding</span><span class="v">{backend}</span>
      </div>
      <div class="iq-pill {'' if llm_ok else 'warn'}">
        <span class="dot"></span>
        <span class="k">model</span><span class="v">{model}</span>
      </div>
      <div class="iq-pill">
        <span class="dot"></span>
        <span class="k">db</span><span class="v">{db_name}</span>
      </div>
    </div>
    """
    st.markdown(pills_html, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    current = st.session_state.get("theme", "dark")
    label = "🌙 Dark" if current == "dark" else "☀️ Light"
    new = "light" if current == "dark" else "dark"
    if st.button(f"Theme: {label}", use_container_width=True, key="theme_toggle"):
        st.session_state.theme = new
        st.rerun()


def render_citations(citations: list[dict]) -> None:
    """Render citation rows as a compact themed table inside the expander."""
    if not citations:
        return
    p = palette()
    rows_html = "".join(
        f'<tr><td><span class="iq-cite-table">{escape(str(c.get("table","—")))}</span></td>'
        f'<td><code class="iq-cite-id">{escape(str(c.get("row_id","—")))}</code></td></tr>'
        for c in citations
    )
    css = f"""
    <style>
      .iq-cite {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-size: 12px; margin: 4px 0;
      }}
      .iq-cite td {{
        padding: 6px 10px;
        border-bottom: 1px solid {p['border']};
        color: {p['text']};
      }}
      .iq-cite tr:last-child td {{ border-bottom: none; }}
      .iq-cite-table {{
        display: inline-block;
        background: {p['primary']}1A; color: {p['primary_2']};
        padding: 2px 8px; border-radius: 999px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 11px; font-weight: 600;
      }}
      .iq-cite-id {{
        background: transparent !important;
        color: {p['muted']} !important;
        font-size: 11px;
        word-break: break-all;
      }}
    </style>
    <table class="iq-cite">
      <tbody>{rows_html}</tbody>
    </table>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_html_table(rows: list[dict], max_rows: int = 50) -> None:
    """Render result rows as a themed HTML table (replaces st.dataframe so theming inherits)."""
    if not rows:
        return
    df = pd.DataFrame(rows[:max_rows])

    # Format cells: stringify None as em-dash, truncate long strings
    def fmt(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return "—"
        s = str(v)
        if len(s) > 60:
            s = s[:57] + "…"
        return escape(s)

    cols = list(df.columns)
    head = "".join(f"<th>{escape(c)}</th>" for c in cols)
    body = "".join(
        "<tr>" + "".join(f"<td>{fmt(v)}</td>" for v in row) + "</tr>"
        for row in df.itertuples(index=False, name=None)
    )
    extra = ""
    if len(rows) > max_rows:
        extra = f'<div class="stCaption" style="margin-top:4px;">Showing first {max_rows} of {len(rows)} rows.</div>'

    html = f"""
    <div class="iq-table-wrap">
      <table class="iq-table">
        <thead><tr>{head}</tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    {extra}
    """
    st.markdown(html, unsafe_allow_html=True)
