import streamlit as st
import json
import html
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
from product_usage import show_product_usage
from user_360 import show_user_360
from content_usage import show_content_usage
from admin_panel import render_admin_panel
import dashboard_data as dd
from dashboard_data import *
import pandas as pd
from dashboard_data import (
    get_monthly_to_yearly_conversions,
    debug_conversion_counts
)
from dashboard_data import get_upcoming_renewals
from PIL import Image
from datetime import datetime, date, timedelta
from dashboard_data import (
    get_engineering_issues,
    get_engineering_kpis,
    get_engineering_activities
)

icon = Image.open("assests/icon.png")

st.set_page_config(
    page_title="TheFinPedia Executive Dashboard",
    page_icon=icon,
    layout="wide"
)

# ============================================================
# 🔐 AUTH GATE
# ============================================================
# ============================================================
# 🔐 AUTH GATE
# ============================================================
# ============================================================
# 🔐 AUTH GATE
# ============================================================
if not st.user.is_logged_in:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
    .stApp { background: #F7F8FA; }

    .login-card {
        background: white;
        border: 1px solid #EAECF0;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(16,24,40,0.08);
        padding: 40px 40px 8px 40px;
        text-align: center;
        margin-top: 12vh;
    }
    .login-badge {
        width: 52px; height: 52px;
        border-radius: 14px;
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 18px auto;
        font-size: 20px; font-weight: 800; color: white;
    }
    .login-title {
        font-size: 19px; font-weight: 800; color: #0F172A;
        letter-spacing: -0.3px; margin-bottom: 6px;
    }
    .login-subtitle {
        font-size: 13px; color: #64748B; font-weight: 500;
        margin-bottom: 24px; line-height: 1.5;
    }
    div[data-testid="stButton"] > button {
        width: 100%;
        background: white;
        color: #1F2937;
        border: 1px solid #D1D9E0;
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 700;
        font-size: 14px;
        box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #2563EB;
        color: #2563EB;
        box-shadow: 0 2px 8px rgba(37,99,235,0.12);
    }
    </style>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.1, 1])
    with center_col:
        st.markdown("""
        <div class="login-card">
            <div class="login-badge">FP</div>
            <div class="login-title">TheFinPedia Executive Dashboard</div>
            <div class="login-subtitle">Sign in with your work Google account to continue</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔐  Continue with Google"):
            st.login()

    st.stop()

user_email = st.user.email

@st.cache_data(ttl=300)
def _get_user_role(email):
    return dd.get_role_for_email(email)

@st.cache_data(ttl=300)
def _get_allowed_sections(role):
    return dd.get_permissions_for_role(role)

user_role = _get_user_role(user_email)

if not user_role:
    st.error(f"Access denied. {user_email} is not registered. Contact your admin.")
    if st.button("Log out"):
        st.logout()
    st.stop()

allowed_sections = _get_allowed_sections(user_role)

# ============================================================
# 🎨 STEP 1: UPGRADED CSS STYLE ENGINE
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif;
    font-size: 14px;
}

/* ── Page background ── */
.stApp { background: #F7F8FA; }

.block-container {
    padding: 3.5rem 2rem 3rem 2rem;
    max-width: 1560px;
}

/* ── Dashboard title ── */
.dash-title {
    font-size: 20px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.3px;
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.db-updated-pill {
    font-size: 11.5px;
    font-weight: 600;
    color: #0369A1;
    background: #EFF8FF;
    border: 1px solid #BAE3FD;
    border-radius: 999px;
    padding: 3px 11px;
    letter-spacing: 0;
    white-space: nowrap;
}
.dash-subtitle {
    font-size: 13px;
    color: #64748B;
    font-weight: 500;
    margin-bottom: 18px;
}

/* ── Section headers (used inside each tab) ── */
.section-header {
    font-size: 17px;
    font-weight: 700;
    color: #000000;
    letter-spacing: -0.2px;
    margin: 22px 0 14px 0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid #EAECF0;
    gap: 0;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Manrope', sans-serif;
    font-weight: 600;
    font-size: 15px;
    color: #6B7280;
    padding: 9px 18px;
    border-radius: 0;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #0F172A;
    border-bottom: 2px solid #2563EB;
    background: transparent;
}

/* ── Streamlit native metric cards ── */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #EAECF0;
    border-radius: 12px;
    padding: 18px 22px;
    min-height: 100px;
    box-shadow: 0 1px 3px rgba(16,24,40,0.05);
}
[data-testid="stMetricLabel"] > div {
    color: #6B7280;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: #0F172A;
    font-weight: 800;
    font-size: 28px;
    letter-spacing: -0.5px;
    margin-top: 4px;
}
[data-testid="stMetricDelta"] { font-size: 12px; font-weight: 600; margin-top: 3px; }
[data-testid="stMetricLabel"] svg { color: grey !important; fill: grey !important; opacity: 1 !important; }
[data-testid="stMetricLabel"] button { color: grey !important; }

/* ── Chart cards ── */
.chart-card {
    background: white;
    border: 1px solid #EAECF0;
    border-radius: 12px;
    padding: 20px 22px 16px 22px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(16,24,40,0.04);
    transition: box-shadow 0.18s ease, border-color 0.18s ease;
}
.chart-card:hover {
    box-shadow: 0 5px 16px rgba(16,24,40,0.08);
    border-color: #D1D9E0;
}
.figure-title {
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 3px;
}
.figure-caption {
    font-size: 12px !important;
    color: #9CA3AF;
    font-weight: 500;
    margin-bottom: 14px;
    line-height: 1.5;
}

/* ── Insight / alert cards (blue) ── */
.insight-card {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-left: 3px solid #2563EB;
    border-radius: 10px;
    padding: 11px 15px;
    margin-top: 10px;
    color: #1E3A5F;
    font-size: 12px;
    line-height: 1.65;
    font-weight: 500;
}

/* ── Health / Briefing cards ── */
.health-card {
    background: white;
    border: 1px solid #EAECF0;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 4px;
    box-shadow: 0 1px 3px rgba(16,24,40,0.04);
}
.health-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}
.health-card-title {
    font-size: 11px;
    font-weight: 700;
    color: #6B7280;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}
.score-badge {
    background: #0F172A;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
    text-align: center;
    line-height: 1.3;
}
.score-badge .score-value { font-size: 18px; font-weight: 800; display: block; }
.score-badge .score-label { font-size: 11px; font-weight: 500; opacity: 0.6; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Status pills ── */
.status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.status-pill {
    background: #F8FAFC;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.status-pill.watchlist { background: #FFFBEB; border-color: #FDE68A; }
.status-label { font-size: 11px; color: #6B7280; font-weight: 500; }
.status-value { font-size: 11px; font-weight: 700; color: #15803D; }
.status-pill.watchlist .status-value { color: #92400E; }

/* ── Briefing cards ── */
.briefing-card {
    background: white;
    border: 1px solid #EAECF0;
    border-radius: 12px;
    padding: 18px 20px;
    min-height: 160px;
    height: 100%;
    box-shadow: 0 1px 3px rgba(16,24,40,0.04);
}
.briefing-card.dark { background: #1F2430; border: none; }
.briefing-card-title {
    font-size: 10px;
    font-weight: 700;
    color: #9CA3AF;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.briefing-card.dark .briefing-card-title { color: #9CA3AF; }
.briefing-list { list-style: disc; padding-left: 16px; margin: 0; display: flex; flex-direction: column; gap: 9px; }
.briefing-list li { font-size: 12px; color: #374151; line-height: 1.6; }
.action-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.action-list li { font-size: 12px; color: #CBD5E1; font-weight: 500; line-height: 1.5; }
.action-num { color: #64748B; font-weight: 700; margin-right: 6px; }

/* ── Summary box ── */
.summary-box {
    background: #F8FAFC;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 16px 20px;
}
.summary-box-title { font-size: 10px; font-weight: 700; color: #9CA3AF; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
.summary-box-text { font-size: 12px; color: #4B5563; line-height: 1.75; }

/* ── Columns gap ── */
div[data-testid="stHorizontalBlock"] { gap: 14px; align-items: stretch; }

/* ── Section divider ── */
.section-divider { border: none; border-top: 1px solid #E5E7EB; margin: 20px 0; }

/* ── h2, h3 reset (prevent oversized headers from markdown) ── */
h1 { color: #0F172A; font-weight: 800 !important; font-size: 20px !important; margin-bottom: 3px !important; }
h2, h3 { color: #0F172A; font-weight: 700 !important; font-size: 15px !important; letter-spacing: -0.1px; margin-top: 0 !important; }

/* ── Radio buttons ── */
.stRadio label, .stRadio p { color: #0F172A !important; font-weight: 600 !important; }

/* ================================================================
   ENGINEERING TAB — KPI cards, hero banner, section icon headers
   ================================================================ */
.eng-metric-card {
    background: white;
    border: 1px solid #EAECF0;
    border-radius: 12px;
    padding: 16px 18px 14px 18px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(16,24,40,0.05);
    transition: transform 0.16s ease, box-shadow 0.16s ease;
    min-height: 100px;
}
.eng-metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(16,24,40,0.09);
    border-color: #D1D9E0;
}
.eng-indicator-strip {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 4px;
    border-radius: 12px 12px 0 0;
}
.eng-section-header {
    display: flex;
    align-items: center;
    gap: 9px;
    margin: 24px 0 12px 0;
}
.eng-section-header .eng-section-icon {
    width: 28px; height: 28px;
    border-radius: 8px;
    background: linear-gradient(135deg, #0f766e, #14b8a6);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0;
}
.eng-section-header .eng-section-text {
    font-size: 15px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.1px;
}
.eng-hero {
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 18px;
    color: black;
    box-shadow: 0 4px 16px rgba(15,23,42,0.15);
}
.eng-hero-title { font-size: 18px; font-weight: 800; letter-spacing: -0.3px; margin-bottom: 5px; }
.eng-hero-sub { font-size: 12px; color: #A7F3D0; font-weight: 500; opacity: 0.9; }

</style>
""", unsafe_allow_html=True)

# ============================================================
# 🎨 DESIGN TOKENS
# ============================================================
BLUE = "#2563EB"
BLUE_LIGHT = "rgba(37,99,235,0.07)"
GRID_COLOR = "#F1F5F9"
FONT = dict(family="Manrope", color="#1E293B", size=12)
AXIS_FONT = dict(family="Manrope", color="#0F172A", size=12)
TICK_FONT = dict(family="Manrope", color="#1E293B", size=11)
CHART_BG = dict(plot_bgcolor="white", paper_bgcolor="white")

HOVER_BG = "rgba(15,23,42,0.88)"
HOVER_FONT = "#F8FAFC"
HOVER_BORDER = "rgba(37,99,235,0.6)"

HOVER_LABEL = dict(
    bgcolor=HOVER_BG,
    bordercolor=HOVER_BORDER,
    font=dict(family="Manrope", size=12, color=HOVER_FONT),
)


# ============================================================
# 📊 CHART STYLE HELPERS
# ============================================================
def style_line_chart(fig, height=350, y_prefix="₹", y_suffix=""):
    for trace in fig.data:
        trace.update(
            mode="lines+markers",
            line=dict(color=BLUE, width=3, shape="spline"),
            marker=dict(
                size=8,
                color=BLUE,
                line=dict(color="white", width=2),
                symbol="circle",
            ),
            fill="tozeroy",
            fillcolor=BLUE_LIGHT,
            hovertemplate=(
                f"<b>%{{x}}</b><br>"
                f"{y_prefix}%{{y:,.0f}}{y_suffix}"
                f"<extra></extra>"
            ),
        )
    fig.update_layout(
        height=height,
        **CHART_BG,
        font=FONT,
        margin=dict(l=40, r=30, t=20, b=50),
        showlegend=False,
        hoverlabel=HOVER_LABEL,
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
    fig.update_yaxes(gridcolor=GRID_COLOR, title_font=AXIS_FONT, tickfont=TICK_FONT, zeroline=False)
    return fig


def style_bar_chart(fig, height=320, x_prefix="₹", orientation="h"):
    is_h = orientation == "h"
    for trace in fig.data:
        trace.update(
            marker_color=BLUE,
            marker_line_width=0,
            marker_cornerradius=4,
            texttemplate=f"{x_prefix}%{{x:,.0f}}" if is_h else f"{x_prefix}%{{y:,.0f}}",
            textposition="outside",
            textfont=dict(size=11, color="#374151"),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"{x_prefix}%{{x:,.0f}}"
                "<extra></extra>"
            ) if is_h else (
                "<b>%{x}</b><br>"
                f"{x_prefix}%{{y:,.0f}}"
                "<extra></extra>"
            ),
        )
    fig.update_layout(
        height=height,
        bargap=0.4,
        **CHART_BG,
        font=FONT,
        margin=dict(l=16, r=80, t=16, b=50),
        showlegend=False,
        hoverlabel=HOVER_LABEL,
        hovermode="y" if is_h else "x",
    )
    fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT, zeroline=False)
    fig.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
    return fig


# ============================================================
# 🧩 UI COMPONENT HELPERS
# ============================================================
def render_status_pill(label, status, positive=True):
    pill_class = "status-pill" if positive else "status-pill watchlist"
    arrow = "▲" if positive else "▼"
    return f"""
    <div class="{pill_class}">
        <span class="status-label">{label}</span>
        <span class="status-value">{arrow} {status}</span>
    </div>
    """


def render_health_card(score, status_items):
    pills_html = "".join(render_status_pill(**item) for item in status_items)
    return f"""
    <div class="health-card">
        <div class="health-card-header">
            <span class="health-card-title">Overall Health</span>
            <div class="score-badge">
                <span class="score-value">{score}/10</span>
                <span class="score-label">Score</span>
            </div>
        </div>
        <div class="status-grid">{pills_html}</div>
    </div>
    """


def render_list_card(title, items, dark=False):
    if dark:
        items_html = "".join(
            f'<li><span class="action-num">{i + 1}.</span>{item}</li>'
            for i, item in enumerate(items)
        )
        return f"""
        <div class="briefing-card dark">
            <div class="briefing-card-title">{title}</div>
            <ul class="action-list">{items_html}</ul>
        </div>
        """
    items_html = "".join(f"<li>{item}</li>" for item in items)
    return f"""
    <div class="briefing-card">
        <div class="briefing-card-title">{title}</div>
        <ul class="briefing-list">{items_html}</ul>
    </div>
    """


def render_summary_box(text, title="Generated Summary"):
    return f"""
    <div class="summary-box">
        <div class="summary-box-title">{title}</div>
        <div class="summary-box-text">{text}</div>
    </div>
    """


def insight_box(content_html, title="Insight"):
    return f"""
    <div style="
        background:#EFF6FF;
        border:1px solid #BFDBFE;
        border-left:3px solid #2563EB;
        border-radius:10px;
        padding:14px 18px;
        margin-top:12px;
        margin-bottom:8px;
    ">
        <div style="font-size:10px;font-weight:700;color:#2563EB;letter-spacing:0.08em;margin-bottom:8px;text-transform:uppercase;">{title}</div>
        <div style="font-size:13px;color:#1E3A5F;line-height:1.75;font-weight:500;">{content_html}</div>
    </div>
    """


# ============================================================
# 🔗 Helper: invisible scroll anchors
# ============================================================
def anchor(name):
    st.markdown(f'<div id="{name}" style="position:relative; top:-70px;"></div>', unsafe_allow_html=True)


# ============================================================
# 🧭 Left icon rail with hover flyout (white ribbon style)
# ============================================================
def render_nav_rail():
    components.html("""
    <style>
        * { box-sizing: border-box; margin:0; padding:0; }
        body { font-family: 'Manrope', sans-serif; overflow: visible; background: transparent; }

        .toc {
            width: 240px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .toc-section {
            border-radius: 8px;
            overflow: hidden;
        }

        .toc-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            cursor: pointer;
            border-radius: 8px;
            transition: background 0.12s ease;
            user-select: none;
        }

        .toc-header:hover {
            background: #F8FAFC;
        }

        .toc-section.open > .toc-header {
            background: #EFF6FF;
        }

        .toc-icon {
            font-size: 15px;
            flex-shrink: 0;
        }

        .toc-title {
            flex: 1;
            font-size: 13.5px;
            font-weight: 700;
            color: #1E293B;
        }

        .toc-section.open .toc-title {
            color: #2563EB;
        }

        .toc-chevron {
            font-size: 11px;
            color: #9CA3AF;
            transition: transform 0.15s ease;
            flex-shrink: 0;
        }

        .toc-section.open .toc-chevron {
            transform: rotate(180deg);
            color: #2563EB;
        }

        .toc-items {
            display: none;
            flex-direction: column;
            padding: 2px 0 6px 0;
        }

        .toc-section.open .toc-items {
            display: flex;
        }

        .toc-items a {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 7px 12px 7px 22px;
            font-size: 12.5px;
            font-weight: 600;
            color: #52525B;
            text-decoration: none;
            border-radius: 6px;
            margin: 0 4px;
            transition: background 0.12s ease, color 0.12s ease;
        }

        .toc-items a:hover {
            background: #EFF6FF;
            color: #2563EB;
        }

        .toc-dot {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #CBD5E1;
            flex-shrink: 0;
        }

        .toc-items a:hover .toc-dot {
            background: #2563EB;
        }
    </style>

    <div class="toc">

        <div class="toc-section open" data-toc-section>
            <div class="toc-header">
                <span class="toc-icon">💰</span>
                <span class="toc-title">Revenue</span>
                <span class="toc-chevron">▾</span>
            </div>
            <div class="toc-items">
                <a href="javascript:void(0)" data-tab="Revenue" data-target="revenue-overview"><span class="toc-dot"></span>Revenue Overview</a>
                <a href="javascript:void(0)" data-tab="Revenue" data-target="monthly-revenue-trend"><span class="toc-dot"></span>Monthly Revenue Trend</a>
                <a href="javascript:void(0)" data-tab="Revenue" data-target="revenue-by-plan"><span class="toc-dot"></span>Revenue by Plan</a>
                <a href="javascript:void(0)" data-tab="Revenue" data-target="revenue-by-partner"><span class="toc-dot"></span>Revenue by Partner</a>
                <a href="javascript:void(0)" data-tab="Revenue" data-target="monthly-yearly-conversions"><span class="toc-dot"></span>Monthly → Yearly Conversions</a>
            </div>
        </div>

        <div class="toc-section" data-toc-section>
            <div class="toc-header">
                <span class="toc-icon">👥</span>
                <span class="toc-title">Subscriptions</span>
                <span class="toc-chevron">▾</span>
            </div>
            <div class="toc-items">
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-overview"><span class="toc-dot"></span>Subscription Overview</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-tier-explorer"><span class="toc-dot"></span>Membership &amp; Tier Explorer</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-membership-distribution"><span class="toc-dot"></span>Membership Distribution</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-premium-by-partner"><span class="toc-dot"></span>Premium Users by Partner</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-user-growth-trend"><span class="toc-dot"></span>User Growth Trend</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-conversion-funnel"><span class="toc-dot"></span>Conversion Funnel</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-renewal-retention"><span class="toc-dot"></span>Renewal &amp; Retention</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-renewal-cohort-trend"><span class="toc-dot"></span>Renewal Cohort Trend</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-renewal-rate-by-plan"><span class="toc-dot"></span>Renewal Rate by Plan</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-renewal-rate-by-partner"><span class="toc-dot"></span>Renewal Rate by Partner</a>
                <a href="javascript:void(0)" data-tab="Subscriptions" data-target="subscription-non-renewal-insights"><span class="toc-dot"></span>Non-Renewal Insights</a>
            </div>
        </div>

        <div class="toc-section" data-toc-section>
            <div class="toc-header">
                <span class="toc-icon">🛠️</span>
                <span class="toc-title">Engineering</span>
                <span class="toc-chevron">▾</span>
            </div>
            <div class="toc-items">
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-overview"><span class="toc-dot"></span>Overview</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-release-defect-trend"><span class="toc-dot"></span>Release Defect Trend</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-severity-priority"><span class="toc-dot"></span>Severity / Priority Distribution</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-classification-filters"><span class="toc-dot"></span>Issue Classification Filters</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-classification-category"><span class="toc-dot"></span>Classification by Category</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-classification-technical-type"><span class="toc-dot"></span>Classification by Technical Type</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-module-wise-defect"><span class="toc-dot"></span>Module-wise Defect Distribution</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-feature-wise-issue-summary"><span class="toc-dot"></span>Feature-wise Issue Summary</a>
                <a href="javascript:void(0)" data-tab="Engineering" data-target="engineering-defect-lifecycle-registry"><span class="toc-dot"></span>Defect Lifecycle Registry</a>
            </div>
        </div>

        <div class="toc-section" data-toc-section>
            <div class="toc-header">
                <span class="toc-icon">📦</span>
                <span class="toc-title">Product Usage</span>
                <span class="toc-chevron">▾</span>
            </div>
            <div class="toc-items">
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-overview"><span class="toc-dot"></span>Overview</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-daily-trend"><span class="toc-dot"></span>Daily Activity Trend</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-feature-usage"><span class="toc-dot"></span>Feature Usage</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-content-usage"><span class="toc-dot"></span>Content Usage</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-premium-basic-content"><span class="toc-dot"></span>Premium vs Basic Content</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-campaign-performance"><span class="toc-dot"></span>Campaign Performance</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-platform-usage"><span class="toc-dot"></span>Platform Usage</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-event-usage"><span class="toc-dot"></span>Event Usage</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-top-active-users"><span class="toc-dot"></span>Top Active Users</a>
                <a href="javascript:void(0)" data-tab="Product Usage" data-target="product-usage-sso-partner"><span class="toc-dot"></span>Usage by SSO Partner</a>
            </div>
        </div>

    </div>

    <script>
        document.querySelectorAll('[data-toc-section]').forEach(function (section) {
            var header = section.querySelector('.toc-header');
            header.addEventListener('click', function () {
                var wasOpen = section.classList.contains('open');
                document.querySelectorAll('[data-toc-section]').forEach(function (s) {
                    s.classList.remove('open');
                });
                if (!wasOpen) {
                    section.classList.add('open');
                }
            });
        });

        // Find the Streamlit tab button whose visible label matches tabLabel.
        function findTabButton(tabLabel) {
            var buttons = window.parent.document.querySelectorAll('button[role="tab"], [role="tab"]');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === tabLabel) {
                    return buttons[i];
                }
            }
            return null;
        }

        // Poll until the target anchor is actually visible (offsetParent !== null
        // means it isn't hidden by a display:none ancestor — that's how Streamlit
        // hides inactive tab panels), then scroll to it. Needed because switching
        // tabs isn't necessarily synchronous.
        function scrollToAnchorWhenReady(targetId, attemptsLeft) {
            var targetEl = window.parent.document.getElementById(targetId);
            if (targetEl && targetEl.offsetParent !== null) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }
            if (attemptsLeft > 0) {
                setTimeout(function () {
                    scrollToAnchorWhenReady(targetId, attemptsLeft - 1);
                }, 50);
            }
        }

        // Scroll directly via the parent document instead of relying on
        // native target="_parent" href navigation, which can silently no-op
        // depending on how the browser treats fragment links inside a
        // components.html srcdoc iframe. If the target tab isn't currently
        // active, click its tab button first, then wait for the anchor to
        // become visible before scrolling.
        document.querySelectorAll('.toc-items a[data-target]').forEach(function (link) {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                var targetId = link.getAttribute('data-target');
                var tabLabel = link.getAttribute('data-tab');
                try {
                    var targetEl = window.parent.document.getElementById(targetId);
                    var alreadyVisible = targetEl && targetEl.offsetParent !== null;

                    if (!alreadyVisible && tabLabel) {
                        var tabButton = findTabButton(tabLabel);
                        if (tabButton) {
                            tabButton.click();
                        }
                    }
                    scrollToAnchorWhenReady(targetId, 40);
                } catch (err) {
                    console.warn('Nav scroll failed:', err);
                }
            });
        });
    </script>
    """, height=550, width=260, scrolling=False)


# ============================================================
# 📦 DATA LOAD
# ============================================================
kpis = get_executive_kpis()
renewal = get_renewal_metrics()

conversion_rate = round((kpis["premium_users"] / kpis["total_users"]) * 100, 2)
premium_share = round((kpis["premium_users"] / kpis["paying_users"]) * 100, 1)
non_premium_revenue_users = kpis["paying_users"] - kpis["premium_users"]

# ============================================================
# 🖥️ MAIN DASHBOARD
# ============================================================
@st.cache_data(ttl=3600)
def _get_last_db_update():
    return dd.get_last_database_update()

_last_update_raw = _get_last_db_update()
_last_update_display = "Unavailable"
if _last_update_raw:
    try:
        _last_update_display = datetime.strptime(str(_last_update_raw)[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        _last_update_display = str(_last_update_raw)

st.markdown("""
<style>
.st-key-refresh_btn_wrap button {
    border-radius: 50%;
    width: 30px;
    height: 30px;
    padding: 0;
    background: #FFF1E9;
    border: 1px solid #FEE0CC;
    color: #C2410C;
    line-height: 1;
}
.st-key-refresh_btn_wrap button:hover {
    background: #FFE4D1;
    border-color: #FDBA8C;
    color: #9A3412;
}
.st-key-refresh_btn_wrap button p {
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

title_col, pill_col, icon_col, _spacer_col, settings_col = st.columns(
    [2.6, 1.3, 0.3, 5.0, 0.9], gap="small", vertical_alignment="center"
)
with title_col:
    st.markdown('<div class="dash-title" style="margin-bottom:0;">TheFinPedia Executive Dashboard</div>', unsafe_allow_html=True)
with pill_col:
    st.markdown(f'<span class="db-updated-pill">Database updated on: {_last_update_display}</span>', unsafe_allow_html=True)
with icon_col:
    with st.container(key="refresh_btn_wrap"):
        if st.button("🔄", key="refresh_dashboard", help="Reload data from the database without losing your place"):
            st.cache_data.clear()
            st.rerun()

st.markdown('<div class="dash-subtitle" style="margin-top:2px;">Revenue, subscriptions and growth performance across plans and partners</div>', unsafe_allow_html=True)

if user_role == "Admin":
    with settings_col:
        if st.button("⚙️ Settings", key="open_admin_settings"):
            st.session_state["show_admin_panel"] = not st.session_state.get("show_admin_panel", False)

if user_role == "Admin" and st.session_state.get("show_admin_panel", False):
    with st.container(border=True):
        render_admin_panel()
    st.markdown("<br>", unsafe_allow_html=True)

ALL_TABS = ["Revenue", "Subscriptions", "Engineering", "Product Usage", "Content Analytics", "Customer Support", "User 360"]
allowed_sections_normalized = {s.strip().lower().replace(" ", "_") for s in allowed_sections}
visible_tabs = [t for t in ALL_TABS if t.lower().replace(" ", "_") in allowed_sections_normalized]

tab_objects = st.tabs(visible_tabs)
tab_map = dict(zip(visible_tabs, tab_objects))

revenue_tab = tab_map.get("Revenue")
subscription_tab = tab_map.get("Subscriptions")
engineering_tab = tab_map.get("Engineering")
product_usage_tab = tab_map.get("Product Usage")
content_analytics_tab = tab_map.get("Content Analytics")
customer_support_tab = tab_map.get("Customer Support")
user_360_tab = tab_map.get("User 360")

# ═══════════════════════════════════════════════════════
# TAB 1 — REVENUE
# ═══════════════════════════════════════════════════════
if revenue_tab:
    with revenue_tab:
        # ---- Sidebar nav rail ----
        with st.sidebar:
            render_nav_rail()

        def _resolve_revenue_period(period_label):
            """Converts a period label into (start_date, end_date) as date objects.
            Returns (None, None) for 'All Time' — meaning no date filtering at all."""
            today = date.today()
            if period_label == "This Month":
                start = today.replace(day=1)
                end = today
            elif period_label == "Last Month":
                first_of_this_month = today.replace(day=1)
                end = first_of_this_month - timedelta(days=1)
                start = end.replace(day=1)
            elif period_label == "This Year":
                start = today.replace(month=1, day=1)
                end = today
            else:  # "All Time"
                start, end = None, None
            return start, end

        anchor("revenue-overview")
        header_left, header_right = st.columns([3, 1])
        with header_left:
            st.markdown("<div class='section-header'>Revenue Overview</div>", unsafe_allow_html=True)
        with header_right:
            revenue_period_label = st.selectbox(
                "Period", ["This Month", "Last Month", "This Year", "All Time"],
                index=3, key="revenue_period_filter", label_visibility="collapsed",
            )
        revenue_period_start, revenue_period_end = _resolve_revenue_period(revenue_period_label)
        st.markdown("<br>", unsafe_allow_html=True)

        # ---- KPI Row ----
        c1, c2, c3 = st.columns(3)

        revenue_kpis = get_revenue_kpis(revenue_period_start, revenue_period_end)
        revenue_kpi_suffix = "" if revenue_period_label == "All Time" else f" — {revenue_period_label}"

        c1.metric(
            f"Total Revenue{revenue_kpi_suffix}",
            f"₹ {revenue_kpis['total_revenue']:,.0f}",
            help="Gross platform earnings accumulated across all paid subscriber categories, subscription renewals, plan upgrades, and individual top-ups." + ("" if revenue_period_label == "All Time" else f" Scoped to {revenue_period_label} (by billing_period_start_date).")
        )
        c2.metric(
            f"ARPU{revenue_kpi_suffix}",
            f"₹ {revenue_kpis['arpu']:,.0f}",
            help="Average Revenue Per User: Calculated as Total Revenue divided by your total count of active paying or contract-holding accounts." + ("" if revenue_period_label == "All Time" else f" Scoped to {revenue_period_label} (by billing_period_start_date).")
        )

        subscriber_kpis = get_subscriber_kpis(revenue_period_start, revenue_period_end)
        if revenue_period_label == "All Time":
            subscriber_main_label = "Total Subscribers"
            subscriber_main_value = subscriber_kpis["total_subscribers"]
            subscriber_tooltip = "All users who have ever paid for a Silver, Gold, Platinum, Diamond, or Trial plan — including expired subscriptions. Active reflects only those whose most recent plan is still within its billing period today."
        else:
            subscriber_main_label = "New Subscribers"
            subscriber_main_value = subscriber_kpis["new_subscribers"]
            subscriber_tooltip = f"Users whose first-ever Silver/Gold/Platinum/Diamond/Trial subscription started during {revenue_period_label}. Active reflects the current live snapshot, not scoped to this period."

        with c3:
            st.markdown(f"""
            <div style="background:white;border:1px solid #EAECF0;border-radius:12px;
                        padding:16px 20px;height:100%;display:flex;align-items:center;
                        justify-content:space-between;font-family:'Manrope',sans-serif;"
                 title="{subscriber_tooltip}">
                <div style="display:flex;flex-direction:column;gap:4px;">
                    <span style="font-size:12px;color:#6B7280;font-weight:600;letter-spacing:0.02em;">{subscriber_main_label}</span>
                    <span style="font-size:28px;font-weight:800;color:#0F172A;letter-spacing:-0.5px;">{subscriber_main_value:,}</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:4px;align-items:flex-end;padding-left:16px;
                            border-left:1px solid #EAECF0;">
                    <span style="font-size:11px;color:#6B7280;font-weight:600;letter-spacing:0.02em;">Active</span>
                    <span style="font-size:22px;font-weight:800;color:#2563EB;letter-spacing:-0.4px;">{subscriber_kpis['active_subscribers']:,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Revenue Breakdown Banner ----
        df_contrib = get_revenue_contribution(revenue_period_start, revenue_period_end)
        total_rev = df_contrib["revenue"].sum()
        df_contrib = df_contrib.sort_values("revenue", ascending=False)

        breakdown_items = ""
        for _, row in df_contrib.iterrows():
            pct = round((row["revenue"] / total_rev) * 100, 1) if total_rev else 0
            breakdown_items += f"""
            <div style="display:flex;flex-direction:column;gap:3px;padding:0 28px;border-left:1px solid #E5E7EB;flex:1;">
                <span style="font-size:10px;color:#9CA3AF;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;">{row['revenue_type']}</span>
                <span style="font-size:19px;font-weight:800;color:#0F172A;letter-spacing:-0.5px;">&#8377; {row['revenue']:,.0f}</span>
                <span style="font-size:11px;color:#2563EB;font-weight:700;">{pct}% of total</span>
            </div>"""

        breakdown_subtitle = "By subscription type" if revenue_period_label == "All Time" else f"By subscription type — {revenue_period_label}"
        st.components.v1.html(f"""
        <div style="font-family:'Manrope',sans-serif;background:white;border:1px solid #EAECF0;
                    border-radius:12px;padding:18px 24px;display:flex;align-items:center;gap:0;">
            <div style="display:flex;flex-direction:column;gap:3px;padding-right:28px;min-width:130px;flex-shrink:0;">
                <span style="font-size:10px;color:#9CA3AF;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;">Revenue Breakdown</span>
                <span style="font-size:12px;color:#6B7280;margin-top:2px;font-weight:500;">{breakdown_subtitle}</span>
            </div>
            {breakdown_items}
        </div>
        """, height=100)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Figure 1: Revenue Trend ----
        anchor("monthly-revenue-trend")
        st.markdown(f"""
        <div class="chart-card">
            <div class="figure-title">Daily Revenue Trend{'' if revenue_period_label == 'All Time' else f' — {revenue_period_label}'}</div>
        
        """, unsafe_allow_html=True)

        df = get_revenue_trend_daily(revenue_period_start, revenue_period_end)

        fig = px.line(df, x="date", y="revenue")
        fig.update_traces(
            mode="lines+markers",
            line=dict(color=BLUE, width=3.5, shape="spline"),
            marker=dict(size=6, color=BLUE, line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor=BLUE_LIGHT,
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b><br>"
                "Revenue: <b>₹%{y:,.0f}</b><br>"
                "<extra></extra>"
            ),
        )
        max_rev = df["revenue"].max() if not df.empty else 0
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Revenue (₹)",
            yaxis=dict(range=[0, max_rev * 1.18]),
            height=370,
            **CHART_BG,
            font=FONT,
            margin=dict(l=40, r=30, t=10, b=50),
            showlegend=False,
            hoverlabel=HOVER_LABEL,
            hovermode="x unified",
        )
        fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if len(df) >= 2:
            latest = df.iloc[-1]["revenue"]
            previous = df.iloc[-2]["revenue"]
            growth = round((latest - previous) / previous * 100, 1) if previous != 0 else 0

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


        def render_interactive_revenue_bar(pivot, div_id, segment_order, color_map, height=320,
                                           x_title="Revenue (₹)",
                                           users_pivot=None, active_pivot=None, inactive_pivot=None):
            """
            pivot: DataFrame indexed by category (one row per bar, e.g. plan_name
                   or sso_partner_name), with one column per segment (e.g.
                   billing_cycle or plan_name), values = revenue. Missing
                   category/segment combos should already be filled with 0.
            div_id: unique DOM id for this chart instance.
            segment_order: list of segment names, in the stacking/legend order
                           you want (bottom of stack -> top).
            color_map: dict of {segment_name: hex color}.

            Optional — same shape as `pivot` (category rows x segment columns),
            used to add extra hover lines. Pass all three, or leave all as None:
                users_pivot:    unique users per category/segment
                active_pivot:   active users per category/segment
                inactive_pivot: inactive users per category/segment
            """
            categories = [str(c) for c in pivot.index.tolist()]
            segments = [s for s in segment_order if s in pivot.columns]

            series = {seg: pivot[seg].astype(float).tolist() for seg in segments}
            totals = [sum(series[seg][i] for seg in segments) for i in range(len(categories))]

            has_users = users_pivot is not None
            has_active = active_pivot is not None and inactive_pivot is not None

            users_series, active_series, inactive_series = {}, {}, {}
            if has_users:
                for seg in segments:
                    users_series[seg] = (
                        users_pivot[seg].astype(int).tolist() if seg in users_pivot.columns
                        else [0] * len(categories)
                    )
            if has_active:
                for seg in segments:
                    active_series[seg] = (
                        active_pivot[seg].astype(int).tolist() if seg in active_pivot.columns
                        else [0] * len(categories)
                    )
                    inactive_series[seg] = (
                        inactive_pivot[seg].astype(int).tolist() if seg in inactive_pivot.columns
                        else [0] * len(categories)
                    )

            traces_js = []
            for seg in segments:
                color = color_map.get(seg, "#94A3B8")

                cd_build = f"""
                        var segVal = {json.dumps(series[seg])}[i];
                        var total = totalsArr[i];
                        var pct = total > 0 ? (segVal / total * 100).toFixed(1) : '0.0';
                        var cd = [segVal, total, pct];"""
                if has_users:
                    cd_build += f"""
                        cd.push({json.dumps(users_series[seg])}[i]);"""
                if has_active:
                    cd_build += f"""
                        cd.push({json.dumps(active_series[seg])}[i]);
                        cd.push({json.dumps(inactive_series[seg])}[i]);"""
                cd_build += """
                        return cd;"""

                hover_lines = [
                    "<b>%{y}</b>",
                    f"{seg}: <b>\u20b9%{{customdata[0]:,.0f}}</b> (%{{customdata[2]}}% of bar)",
                    "Bar Total: <b>\u20b9%{customdata[1]:,.0f}</b>",
                ]
                idx = 3
                if has_users:
                    hover_lines.append(f"{seg} Users: <b>%{{customdata[{idx}]}}</b>")
                    idx += 1
                if has_active:
                    hover_lines.append(
                        f"\U0001F7E2 Active: <b>%{{customdata[{idx}]}}</b>  |  "
                        f"\U0001F534 Inactive: <b>%{{customdata[{idx + 1}]}}</b>"
                    )
                    idx += 2
                hovertemplate = "<br>".join(hover_lines) + "<extra></extra>"

                traces_js.append(f"""
                {{
                    y: categories, x: {json.dumps(series[seg])}, name: {json.dumps(seg)},
                    type: 'bar', orientation: 'h', marker: {{ color: {json.dumps(color)} }},
                    customdata: categories.map(function(cat, i) {{{cd_build}
                    }}),
                    hovertemplate: {json.dumps(hovertemplate)}
                }}""")

            component_html = f"""
            <div id="{div_id}" style="width:100%; height:{height}px;"></div>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <script>
            (function() {{
                var categories = {json.dumps(categories)};
                var segmentValues = {json.dumps(series)};
                var segmentOrder = {json.dumps(segments)};
                var totalsArr = {json.dumps(totals)};

                var barTraces = [{','.join(traces_js)}];

                var traceTotal = {{
                    y: categories, x: totalsArr,
                    text: totalsArr.map(function(v) {{ return '\u20b9' + Math.round(v).toLocaleString('en-IN'); }}),
                    mode: 'text', textposition: 'middle right',
                    textfont: {{ size: 12, color: '#0F172A', family: 'Manrope' }},
                    showlegend: false, hoverinfo: 'skip', type: 'scatter'
                }};

                var layout = {{
                    height: {height},
                    barmode: 'stack',
                    margin: {{ l: 110, r: 150, t: 10, b: 40 }},
                    plot_bgcolor: 'white', paper_bgcolor: 'white',
                    font: {{ family: 'Manrope', color: '#1E293B', size: 12 }},
                    xaxis: {{ title: {json.dumps(x_title)}, gridcolor: '#E5E7EB', color: '#1E293B',
                              tickfont: {{ family: 'Manrope', size: 11 }},
                              range: [0, Math.max.apply(null, totalsArr) * 1.18] }},
                    yaxis: {{ color: '#1E293B', tickfont: {{ family: 'Manrope', size: 11 }} }},
                    legend: {{
                        orientation: 'v', yanchor: 'top', y: 1, xanchor: 'left', x: 1.0,
                        font: {{ size: 12, color: '#0F172A', family: 'Manrope' }}
                    }},
                    hoverlabel: {{
                        bgcolor: 'rgba(15,23,42,0.88)', bordercolor: 'rgba(37,99,235,0.6)',
                        font: {{ family: 'Manrope', size: 12, color: '#F8FAFC' }}
                    }}
                }};

                var config = {{ displayModeBar: false, responsive: true }};
                var gd = document.getElementById('{div_id}');

                // Fix: Plotly caches legend text-fitting boxes on its first layout
                // pass. A fixed setTimeout delay was a guess at when the iframe
                // would be settled to its real width — unreliable across
                // different zoom levels/environments. Instead, wait until the
                // container's width is actually unchanged across two animation
                // frames before ever calling Plotly.newPlot.
                function waitForStableWidth(el, cb, tries) {{
                    tries = tries || 0;
                    var w1 = el.offsetWidth;
                    requestAnimationFrame(function() {{
                        var w2 = el.offsetWidth;
                        if ((w1 === w2 && w1 > 0) || tries > 40) {{
                            cb();
                        }} else {{
                            waitForStableWidth(el, cb, tries + 1);
                        }}
                    }});
                }}

                waitForStableWidth(gd, function() {{
                    Plotly.newPlot(gd, barTraces.concat([traceTotal]), layout, config);

                    window.addEventListener('resize', function() {{ Plotly.Plots.resize(gd); }});

                    var visible = segmentOrder.map(function() {{ return true; }});

                    gd.on('plotly_legendclick', function(data) {{
                        var idx = data.curveNumber;
                        if (idx < segmentOrder.length) {{
                            visible[idx] = !visible[idx];
                            var newTotals = categories.map(function(_, i) {{
                                var sum = 0;
                                segmentOrder.forEach(function(seg, si) {{
                                    if (visible[si]) sum += segmentValues[seg][i];
                                }});
                                return sum;
                            }});
                            var newText = newTotals.map(function(v) {{ return '\u20b9' + Math.round(v).toLocaleString('en-IN'); }});
                            Plotly.restyle(gd, {{ x: [newTotals], text: [newText] }}, [segmentOrder.length]);
                        }}
                        return true;
                    }});
                }});
            }})();
            </script>
            """
            st.components.v1.html(component_html, height=height + 20, scrolling=False)

        
        # ---- Figure 2+3: Revenue by Plan & Partner ----
        c1, c2 = st.columns(2, gap="small")

        with c1:
            anchor("revenue-by-plan")
            st.markdown(f"""
                   <div class="chart-card">
                       <div class="figure-title">Revenue by Plan{'' if revenue_period_label == 'All Time' else f' — {revenue_period_label}'}</div>
                   """, unsafe_allow_html=True)

            df_plan_cycle = get_plan_revenue_by_cycle(revenue_period_start, revenue_period_end)
            if not df_plan_cycle.empty:
                unwanted_plans = ["Custom SSO 5.0", "Silver Duplicate 1", "Diamond Plan Duplicate", "Gold Plan Duplicate"]
                df_plan_clean = df_plan_cycle[~df_plan_cycle["plan_name"].isin(unwanted_plans)].copy()

                pivot_plan = (
                    df_plan_clean.groupby(["plan_name", "billing_cycle"])["revenue"].sum()
                    .unstack(fill_value=0)
                )
                plan_order_by_total = pivot_plan.sum(axis=1).sort_values(ascending=True).index.tolist()
                pivot_plan = pivot_plan.reindex(plan_order_by_total)

                pivot_plan_users = (
                    df_plan_clean.set_index(["plan_name", "billing_cycle"])["unique_users"]
                    .unstack(fill_value=0).reindex(plan_order_by_total)
                )
                pivot_plan_active = (
                    df_plan_clean.set_index(["plan_name", "billing_cycle"])["active_users"]
                    .unstack(fill_value=0).reindex(plan_order_by_total)
                )
                pivot_plan_inactive = (
                    df_plan_clean.set_index(["plan_name", "billing_cycle"])["inactive_users"]
                    .unstack(fill_value=0).reindex(plan_order_by_total)
                )

                render_interactive_revenue_bar(
                    pivot_plan,
                    div_id="revByPlan",
                    segment_order=["Annual", "Monthly"],
                    color_map={"Annual": "#00FF00", "Monthly": "#0000FF"},
                    height=320,
                    users_pivot=pivot_plan_users,
                    active_pivot=pivot_plan_active,
                    inactive_pivot=pivot_plan_inactive,
                )
            else:
                st.info("No plan revenue data available.")

            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            anchor("revenue-by-partner")
            with st.container():
                st.markdown(f"""
                   <div class="chart-card">
                       <div class="figure-title">Revenue by Partner{'' if revenue_period_label == 'All Time' else f' — {revenue_period_label}'}</div>
                   """, unsafe_allow_html=True)

                df_partner_plan = get_partner_revenue_by_plan(revenue_period_start, revenue_period_end)

                allowed_plans = ["Diamond Plan", "Platinum Plan", "Silver Plan",
                                 "Trial Plan", "Gold Plan", "Content Top up"]

                if not df_partner_plan.empty:
                    df_partner_plan = df_partner_plan[df_partner_plan["plan_name"].isin(allowed_plans)].copy()

                    excluded_partners = ["Custom SSO", "Testing SSO", "Test Partner", "Custom SSO 5.0"]
                    df_partner_plan = df_partner_plan[
                        ~df_partner_plan["sso_partner_name"].astype(str).str.contains(
                            "|".join(excluded_partners), case=False, na=False
                        )
                    ].copy()

                if not df_partner_plan.empty:
                    pivot_partner = (
                        df_partner_plan.groupby(["sso_partner_name", "plan_name"])["revenue"].sum()
                        .unstack(fill_value=0)
                    )
                    partner_order_by_total = pivot_partner.sum(axis=1).sort_values(ascending=True).index.tolist()
                    pivot_partner = pivot_partner.reindex(partner_order_by_total)

                    plan_color_map = {
                        "Trial Plan": "#D1D5DB",
                        "Silver Plan": "#9CA3AF",
                        "Gold Plan": "#F59E0B",
                        "Platinum Plan": "#2563EB",
                        "Diamond Plan": "#6366F1",
                        "Content Top up": "#10B981",
                    }

                    render_interactive_revenue_bar(
                        pivot_partner,
                        div_id="revByPartner",
                        segment_order=allowed_plans,
                        color_map=plan_color_map,
                        height=max(320, len(partner_order_by_total) * 70),
                    )
                else:
                    st.info("No partner revenue data available.")

                st.markdown("</div>", unsafe_allow_html=True)
        # ============================================================
        # Monthly → Yearly Plan Conversions
        # ============================================================
        debug_conversion_counts()

        anchor("monthly-yearly-conversions")
        st.markdown(f"""
        <div class="chart-card">
            <div class="figure-title">Monthly → Yearly Plan Conversions{'' if revenue_period_label == 'All Time' else f' — {revenue_period_label}'}</div>
        
        """, unsafe_allow_html=True)

        df_conv = get_monthly_to_yearly_conversions(revenue_period_start, revenue_period_end)

        if not df_conv.empty:
            total_users = len(df_conv)
            total_revenue = df_conv["amount_paid"].sum() if "amount_paid" in df_conv.columns else 0

            m1, m2 = st.columns(2)

            m1.metric("Upgraded Users", f"{total_users:,}")
            m2.metric("Conversion Revenue", f"₹ {total_revenue:,.0f}")

            st.markdown("<br>", unsafe_allow_html=True)

            # ---- Pattern breakdown banner ----
            if "pattern" in df_conv.columns:
                pattern_counts = df_conv["pattern"].value_counts().reset_index()
                pattern_counts.columns = ["pattern", "count"]
                pattern_counts = pattern_counts.sort_values("count", ascending=False)

                pattern_items = ""
                for _, row in pattern_counts.iterrows():
                    pattern_items += f"""
                    <div style="display:flex;flex-direction:column;gap:3px;padding:0 22px;border-left:1px solid #E5E7EB;flex:1;min-width:160px;">
                        <span style="font-size:10px;color:#9CA3AF;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;">{row['pattern']}</span>
                        <span style="font-size:19px;font-weight:800;color:#0F172A;letter-spacing:-0.5px;">{row['count']:,}</span>
                    
                    </div>"""

                st.components.v1.html(f"""
                <div style="font-family:'Manrope',sans-serif;background:white;border:1px solid #EAECF0;
                            border-radius:12px;padding:18px 24px;display:flex;align-items:center;gap:0;flex-wrap:wrap;">
                    <div style="display:flex;flex-direction:column;gap:3px;padding-right:22px;min-width:130px;flex-shrink:0;">
                        <span style="font-size:10px;color:#9CA3AF;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;">Conversion Patterns</span>
                        <span style="font-size:12px;color:#6B7280;margin-top:2px;font-weight:500;">By transition type</span>
                    </div>
                    {pattern_items}
                </div>
                """, height=100 + (20 if len(pattern_counts) > 4 else 0))

            st.markdown("<br>", unsafe_allow_html=True)

            styled_df = df_conv.copy()
            if "conversion_date" in styled_df.columns:
                styled_df["conversion_date"] = pd.to_datetime(styled_df["conversion_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")

            if "amount_paid" in styled_df.columns:
                styled_df["amount_paid"] = styled_df["amount_paid"].astype(int)

            light_table = styled_df.style.set_properties(**{
                'background-color': 'white',
                'color': '#1E293B',
                'border-color': '#F1F5F9',
                'font-family': 'Manrope, sans-serif'
            }).set_table_styles([
                {
                    'selector': 'th',
                    'props': [
                        ('background-color', '#F8FAFC'),
                        ('color', '#6B7280'),
                        ('font-weight', '700'),
                        ('text-transform', 'uppercase'),
                        ('letter-spacing', '0.04em'),
                        ('border-bottom', '1px solid #EAECF0')
                    ]
                },
                {
                    'selector': 'tr:hover',
                    'props': [('background-color', '#F1F5F9')]
                }
            ])

            st.dataframe(
                light_table,
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 2 — SUBSCRIPTIONS
# ═══════════════════════════════════════════════════════
if subscription_tab:
    with subscription_tab:
        def _resolve_subscription_period(period_label):
            """Converts a period label into (start_date, end_date) as date objects.
            Returns (None, None) for 'All Time' — meaning no date filtering at all."""
            today = date.today()
            if period_label == "This Month":
                start = today.replace(day=1)
                end = today
            elif period_label == "Last Month":
                first_of_this_month = today.replace(day=1)
                end = first_of_this_month - timedelta(days=1)
                start = end.replace(day=1)
            elif period_label == "This Year":
                start = today.replace(month=1, day=1)
                end = today
            else:  # "All Time"
                start, end = None, None
            return start, end

        anchor("subscription-overview")
        sub_header_left, sub_header_right = st.columns([3, 1])
        with sub_header_left:
            st.markdown("<div class='section-header'>Subscription Overview</div>", unsafe_allow_html=True)
        with sub_header_right:
            subscription_period_label = st.selectbox(
                "Period", ["This Month", "Last Month", "This Year", "All Time"],
                index=3, key="subscription_period_filter", label_visibility="collapsed",
            )
        subscription_period_start, subscription_period_end = _resolve_subscription_period(subscription_period_label)
        subscription_period_suffix = "" if subscription_period_label == "All Time" else f" — {subscription_period_label}"
        st.markdown("<br>", unsafe_allow_html=True)

        # ---- KPI Row ----
        c1, c2, c3, c4 = st.columns(4)

        sub_user_kpis = get_user_kpis(subscription_period_start, subscription_period_end)
        sub_renewal_kpis = get_renewal_kpis(subscription_period_start, subscription_period_end)

        c1_label = "Total Users" if subscription_period_label == "All Time" else "New Users"
        c1.metric(c1_label, f"{sub_user_kpis['total_users']:,}")

        c2.metric(
            f"Premium Conversion{subscription_period_suffix}",
            f"{sub_user_kpis['premium_conversion_rate']}%",
            help="Percentage of the selected user cohort who have EVER converted to a premium plan (Silver/Gold/Platinum/Diamond), at any point — not just within this window." if subscription_period_label != "All Time" else "Percentage of total users who have converted to a premium plan."
        )
        c3.metric(
            f"Renewal Rate{subscription_period_suffix}",
            f"{sub_renewal_kpis['renewal_rate']}%",
            help="Percentage of subscribers who returned for another billing cycle." + ("" if subscription_period_label == "All Time" else f" Scoped to invoices within {subscription_period_label}.")
        )

        renewed_split = get_renewed_users_by_cycle(subscription_period_start, subscription_period_end)

        with c4:
            st.markdown(f"""
                <div data-testid="stMetric" style="padding:16px 18px 14px 18px;">
                    <div style="color:#6B7280; font-size:11px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;">
                        Renewed Users{subscription_period_suffix}
                    </div>
                    <div style="color:#0F172A; font-weight:800; font-size:26px; letter-spacing:-0.5px; margin-top:4px;">
                        {sub_renewal_kpis['renewed_users']:,}
                    </div>
                    <div style="display:flex; gap:14px; margin-top:10px; padding-top:10px; border-top:1px solid #F1F5F9;">
                        <div style="flex:1;">
                            <span style="font-size:9px; font-weight:700; color:#3B82F6; text-transform:uppercase; letter-spacing:0.04em;">Monthly</span><br>
                            <span style="font-size:15px; font-weight:800; color:#0F172A;">{renewed_split['monthly_renewed']:,}</span>
                        </div>
                        <div style="width:1px; background:#E5E7EB;"></div>
                        <div style="flex:1; padding-left:4px;">
                            <span style="font-size:9px; font-weight:700; color:#1D4ED8; text-transform:uppercase; letter-spacing:0.04em;">Annual</span><br>
                            <span style="font-size:15px; font-weight:800; color:#0F172A;">{renewed_split['yearly_renewed']:,}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Tier Explorer ----
        anchor("subscription-tier-explorer")
        st.markdown(f"<div class='section-header'>Membership &amp; Subscription Tier Explorer{subscription_period_suffix}</div>",
                    unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #6B7280; font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>Active subscriber allocations, price points, and estimated billing cycle yields calculated directly from live database invoices.</p>",
            unsafe_allow_html=True)

        df_inv = dd._df("invoices")

        premium_plans_list = ["Silver Plan", "Gold Plan", "Platinum Plan", "Diamond Plan"]
        tier_explorer_plans = premium_plans_list + ["Trial Plan"]

        tiers_data = {p: {"m_users": 0, "y_users": 0} for p in tier_explorer_plans}

        if not df_inv.empty:
            df_inv = df_inv[df_inv["billed_plan_name"].isin(tier_explorer_plans)].copy()

            df_inv["billing_period_start_date"] = pd.to_datetime(df_inv["billing_period_start_date"])
            df_inv["billing_period_end_date"] = pd.to_datetime(df_inv["billing_period_end_date"])

            if subscription_period_start is not None:
                df_inv = df_inv[df_inv["billing_period_start_date"].dt.date >= subscription_period_start]
            if subscription_period_end is not None:
                df_inv = df_inv[df_inv["billing_period_start_date"].dt.date <= subscription_period_end]

            df_inv["cycle"] = np.where(
                (df_inv["billing_period_end_date"] - df_inv["billing_period_start_date"]).dt.days >= 300,
                "Annual", "Monthly"
            )

            df_inv = df_inv.sort_values("billing_period_start_date").drop_duplicates(
                subset=["user_id"],
                keep="last"
            )

            summary = df_inv.groupby(["billed_plan_name", "cycle"]).agg(
                unique_subs=("user_id", "nunique"),
                total_revenue=("amount_paid", "sum")
            ).reset_index()

            for _, row in summary.iterrows():
                plan = row["billed_plan_name"]
                if row["cycle"] == "Monthly":
                    tiers_data[plan]["m_users"] = int(row["unique_subs"])
                else:
                    tiers_data[plan]["y_users"] = int(row["unique_subs"])

            card_cols = st.columns(5, gap="medium")

            for idx, (tier_name, metrics) in enumerate(tiers_data.items()):
                with card_cols[idx]:
                    total_allocated = metrics["m_users"] + metrics["y_users"]

                    # Revenue split by cycle (NOT deduplicated — sum all payments)

            rev_by_cycle = df_inv.groupby(["billed_plan_name", "cycle"])["amount_paid"].sum().reset_index()
            rev_map = {}
            for _, row in rev_by_cycle.iterrows():
                plan = row["billed_plan_name"]
                if plan not in rev_map:
                    rev_map[plan] = {"m_rev": 0, "y_rev": 0}
                if row["cycle"] == "Monthly":
                    rev_map[plan]["m_rev"] = int(row["amount_paid"])
                else:
                    rev_map[plan]["y_rev"] = int(row["amount_paid"])

            card_cols = st.columns(5, gap="medium")

            for idx, (tier_name, metrics) in enumerate(tiers_data.items()):
                with card_cols[idx]:
                    total_allocated = metrics["m_users"] + metrics["y_users"]
                    m_rev = rev_map.get(tier_name, {}).get("m_rev", 0)
                    y_rev = rev_map.get(tier_name, {}).get("y_rev", 0)

                    html_card = f"""
                                    <div style="font-family:'Manrope',sans-serif; background:white; border:1px solid #EAECF0;
                                                border-radius:12px; padding:20px 18px;
                                                box-shadow:0px 1px 2px rgba(16,24,40,0.05);">
                                        <div style="font-size:10px; font-weight:700; color:#9CA3AF; text-transform:uppercase;
                                                    letter-spacing:0.06em; margin-bottom:4px;">{tier_name.upper()}</div>
                                        <div style="font-size:12px; color:#6B7280; font-weight:500; margin-bottom:14px;">
                                            Total: <b>{total_allocated:,}</b> unique users
                                        </div>
                                        <div style="display:flex; flex-direction:row; gap:16px;
                                                    border-top:1px solid #F1F5F9; padding-top:14px;">

                                            <div style="flex:1;">
                                                <div style="font-size:9px; font-weight:700; color:#3B82F6; text-transform:uppercase;
                                                            letter-spacing:0.04em; margin-bottom:6px;">MONTHLY</div>
                                                <div style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:3px;">
                                                    {metrics['m_users']:,}
                                                    <span style="font-size:9px; font-weight:500; color:#6B7280;">subs</span>
                                                </div>
                                                <div style="font-size:11px; font-weight:700; color:#2563EB;">
                                                    &#8377;{m_rev:,}
                                                </div>
                                            </div>

                                            <div style="width:1px; background:#E5E7EB; align-self:stretch;"></div>

                                            <div style="flex:1; padding-left:4px;">
                                                <div style="font-size:9px; font-weight:700; color:#1D4ED8; text-transform:uppercase;
                                                            letter-spacing:0.04em; margin-bottom:6px;">ANNUAL</div>
                                                <div style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:3px;">
                                                    {metrics['y_users']:,}
                                                    <span style="font-size:9px; font-weight:500; color:#6B7280;">subs</span>
                                                </div>
                                                <div style="font-size:11px; font-weight:700; color:#1D4ED8;">
                                                    &#8377;{y_rev:,}
                                                </div>
                                            </div>

                                        </div>
                                    </div>
                                    """
                    st.components.v1.html(html_card, height=215, scrolling=False)

        # ---- Membership Distribution + Premium by Partner ----
        c1, c2 = st.columns(2, gap="large")

        with c1:
            anchor("subscription-membership-distribution")
            st.markdown(f"""
            <div class="chart-card">
                <div class="figure-title">Membership Distribution</div>
            
            """, unsafe_allow_html=True)

            membership_rows = []
            for plan, metrics in tiers_data.items():
                users = metrics["m_users"] + metrics["y_users"]
                revenue = rev_map.get(plan, {}).get("m_rev", 0) + rev_map.get(plan, {}).get("y_rev", 0)
                membership_rows.append({
                    "plan_name": plan,
                    "users": users,
                    "monthly_subs": metrics["m_users"],
                    "annual_subs": metrics["y_users"],
                    "plan_revenue": revenue,
                })
            df_memb = pd.DataFrame(membership_rows)
            df_memb = df_memb[df_memb["users"] > 0]

            if not df_memb.empty:
                total_users = df_memb["users"].sum()
                df_memb["pct"] = (df_memb["users"] / total_users * 100).round(1)
                df_memb = df_memb.sort_values("users", ascending=True).reset_index(drop=True)

                colors = ["#2563EB" for _ in df_memb["plan_name"]]

                fig = px.bar(df_memb, x="users", y="plan_name", orientation="h")
                fig.update_traces(
                    marker_color=colors,
                    marker_line_width=0,
                    marker_cornerradius=4,
                    texttemplate="%{x:,} (%{customdata[0]:.1f}%)",
                    textposition="outside",
                    textfont=dict(size=11, color="#374151", family="Manrope"),
                    cliponaxis=False,
                    customdata=df_memb[["pct", "monthly_subs", "annual_subs", "plan_revenue"]].values,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Active Members: <b>%{x:,}</b><br>"
                        "Share: <b>%{customdata[0]:.1f}%</b><br>"
                        "Monthly Subs: <b>%{customdata[1]:,}</b><br>"
                        "Annual Subs: <b>%{customdata[2]:,}</b><br>"
                        "Total Revenue: <b>₹%{customdata[3]:,}</b>"
                        "<extra></extra>"
                    ),
                )
                fig.update_layout(
                    height=310,
                    bargap=0.4,
                    **CHART_BG,
                    font=FONT,
                    margin=dict(l=12, r=90, t=10, b=40),
                    showlegend=False,
                    hoverlabel=HOVER_LABEL,
                    hovermode="y",
                    xaxis_title="Active Members",
                    yaxis_title="",
                )
                fig.update_xaxes(
                    showgrid=False, zeroline=False,
                    showticklabels=False, title_font=AXIS_FONT
                )
                fig.update_yaxes(
                    showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No membership distribution data available.")

            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            anchor("subscription-premium-by-partner")
            st.markdown(f"""
            <div class="chart-card">
                <div class="figure-title">Premium Users by Partner</div>
            
            """, unsafe_allow_html=True)

            df_inv_premium_only = df_inv[df_inv["billed_plan_name"].isin(premium_plans_list)]
            df_users_for_partner = dd._df("users")
            merged_premium = df_inv_premium_only.merge(
                df_users_for_partner[["user_id", "sso_partner_name"]], on="user_id", how="left"
            )
            merged_premium["sso_partner_name"] = merged_premium["sso_partner_name"].astype(str).str.strip()
            partner_canonical = {
                "thefinpedia": "Thefinpedia",
                "ifanow": "IFANOW",
                "compoundexpress": "CompoundExpress",
                "investwell": "Investwell",
            }
            merged_premium["_norm"] = merged_premium["sso_partner_name"].str.lower()
            merged_premium = merged_premium[merged_premium["_norm"].isin(partner_canonical.keys())]
            merged_premium["sso_partner_name"] = merged_premium["_norm"].map(partner_canonical)

            df_p = (
                merged_premium.groupby("sso_partner_name")["user_id"]
                .nunique()
                .reset_index(name="premium_users")
            )
            df_p = df_p[df_p["premium_users"] > 0].sort_values("premium_users", ascending=True)

            # Own local partner-revenue pull, scoped to THIS tab's period filter —
            # not the Revenue tab's df_partner_plan, which uses a different period.
            df_partner_plan_local = dd.get_partner_revenue_by_plan(subscription_period_start, subscription_period_end)

            # Merge partner revenue and plan count from this tab's own partner plan data
            if not df_partner_plan_local.empty:
                partner_extra = df_partner_plan_local.groupby("sso_partner_name").agg(
                    total_revenue=("revenue", "sum"),
                    plan_count=("plan_name", "nunique")
                ).reset_index()
                df_p = df_p.merge(partner_extra, on="sso_partner_name", how="left")
            else:
                df_p["total_revenue"] = 0
                df_p["plan_count"] = 0

            df_p["total_revenue"] = df_p["total_revenue"].fillna(0).astype(int)
            df_p["plan_count"] = df_p["plan_count"].fillna(0).astype(int)
            df_p["pct"] = (df_p["premium_users"] / df_p["premium_users"].sum() * 100).round(1)
            df_p["arpu"] = (df_p["total_revenue"] / df_p["premium_users"].replace(0, 1)).round(0).astype(int)

            colors = [
                "#6366F1" if partner == "Thefinpedia" else "#D1D5DB"
                for partner in df_p["sso_partner_name"]
            ]

            fig = px.bar(df_p, x="premium_users", y="sso_partner_name", orientation="h")
            fig.update_traces(
                marker_color=colors,
                marker_line_width=0,
                text=[f"{users} ({pct:.1f}%)" for users, pct in zip(df_p["premium_users"], df_p["pct"])],
                texttemplate="%{text}",
                textposition="outside",
                textfont=dict(size=11, color="#374151"),
                cliponaxis=False,
                customdata=df_p[["pct", "total_revenue", "arpu", "plan_count"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Premium Users: <b>%{x:,.0f}</b><br>"
                    "Contribution: <b>%{customdata[0]:.1f}%</b><br>"
                    "Total Revenue: <b>₹%{customdata[1]:,}</b><br>"
                    "Revenue per User: <b>₹%{customdata[2]:,}</b><br>"
                    "Plans Active: <b>%{customdata[3]}</b>"
                    "<extra></extra>"
                ),
            )
            fig.update_layout(
                height=310,
                bargap=0.4,
                **CHART_BG,
                font=FONT,
                margin=dict(l=12, r=70, t=10, b=40),
                showlegend=False,
                hoverlabel=HOVER_LABEL,
                hovermode="y",
                xaxis_title="Premium Users",
                yaxis_title="",
            )
            fig.update_xaxes(
                showgrid=False, zeroline=False,
                showticklabels=False, title_font=AXIS_FONT, tickfont=TICK_FONT
            )
            fig.update_yaxes(
                showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        anchor("subscription-user-growth-trend")
        st.markdown("""
            <div class="chart-card">
                <div class="figure-title">User Growth Trend</div>
            
            """, unsafe_allow_html=True)

        # =========================================================
        # REPLACEMENT for the "User Growth Trend" block inside dashboard.py
        # =========================================================
        #
        # This replaces everything from `df_growth_daily = dd.get_customer_growth_daily()`
        # down through the `st.plotly_chart(fig, ...)` call for the growth trend chart
        # (i.e. the content INSIDE the existing "User Growth Trend" chart-card — the
        # card's opening `<div class="chart-card">...` and its final closing `</div>`
        # stay exactly where they already are in your file; only the content between
        # them changes).
        #
        # What changed:
        #   - "Total Users (End of Period)" metric is removed entirely.
        #   - "New Users (... view)" metric is kept, and moved into the same white
        #     card as the View-by radio + date pickers (instead of its own separate
        #     metric card below them).
        # =========================================================

        # =========================================================
        # User Growth Trend
        # =========================================================

        df_growth_daily = dd.get_customer_growth_daily()

        if df_growth_daily.empty:
            st.info("No user growth data available.")

        else:
            min_date = df_growth_daily["date"].min().date()
            max_date = df_growth_daily["date"].max().date()

            # -------------------------------------------------
            # Filters + Metric Card
            # -------------------------------------------------
            with st.container(border=True):

                st.markdown(
                    """
                    <div style="
                        font-size:11px;
                        font-weight:700;
                        color:#000000;
                        text-transform:uppercase;
                        letter-spacing:.06em;
                        margin-bottom:6px;
                    ">
                        VIEW BY
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col1, col2, col3 = st.columns([1, 1.5, 1.5])

                with col1:
                    granularity = st.radio(
                        "",
                        ["Monthly", "Weekly", "Daily"],
                        index=0,
                        horizontal=True,
                        key="growth_granularity",
                        label_visibility="collapsed",
                    )

                with col2:
                    start_date = st.date_input(
                        "Start date",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="growth_start_date",
                    )

                with col3:
                    end_date = st.date_input(
                        "End date",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="growth_end_date",
                    )

                if start_date > end_date:
                    st.warning("Start date must be before end date.")
                    st.stop()

                # -------------------------------------------------
                # Filter Data
                # -------------------------------------------------
                df_growth_filtered = (
                    df_growth_daily[
                        (df_growth_daily["date"].dt.date >= start_date)
                        & (df_growth_daily["date"].dt.date <= end_date)
                        ]
                    .copy()
                    .set_index("date")
                )

                # -------------------------------------------------
                # Aggregate
                # -------------------------------------------------
                if granularity == "Monthly":
                    df_plot = (
                        df_growth_filtered["customers"]
                        .resample("MS")
                        .last()
                        .reset_index()
                    )
                    x_title = "Month"
                    marker_size = 9
                    period_label = "vs prev month"

                elif granularity == "Weekly":
                    df_plot = (
                        df_growth_filtered["customers"]
                        .resample("W-MON")
                        .last()
                        .reset_index()
                    )
                    x_title = "Week Starting"
                    marker_size = 7
                    period_label = "vs prev week"

                else:
                    df_plot = (
                        df_growth_filtered["customers"]
                        .reset_index()
                    )
                    x_title = "Date"
                    marker_size = 5
                    period_label = "vs prev day"

                df_plot.columns = ["date", "customers"]
                df_plot = df_plot.dropna(subset=["customers"])

                if df_plot.empty:
                    st.info("No data available for selected range.")
                    st.stop()

                # -------------------------------------------------
                # Metrics
                # -------------------------------------------------
                df_plot["new_users"] = (
                    df_plot["customers"]
                    .diff()
                    .fillna(0)
                    .astype(int)
                )

                df_plot["pct_change"] = (
                    df_plot["customers"]
                    .pct_change()
                    .fillna(0)
                    .mul(100)
                    .round(1)
                )

                window_new = (
                    int(df_plot["customers"].iloc[-1] - df_plot["customers"].iloc[0])
                    if len(df_plot) > 1
                    else 0
                )

                st.divider()

                st.metric(
                    label=f"New Users ({granularity} View)",
                    value=f"{window_new:,}",
                )


            # -------------------------------------------------
            # Chart
            # -------------------------------------------------
            fig = px.line(
                df_plot,
                x="date",
                y="customers",
            )

            fig.update_traces(
                mode="lines+markers",
                line=dict(
                    color="#8B5CF6",
                    width=3.5,
                    shape="spline",
                ),
                marker=dict(
                    size=marker_size,
                    color="#8B5CF6",
                    line=dict(color="white", width=2),
                ),
                fill="tozeroy",
                fillcolor="rgba(139,92,246,0.07)",
                customdata=df_plot[["new_users", "pct_change"]].values,
                hovertemplate=(
                    "<b>%{x|%d %b %Y}</b><br>"
                    "Total Users: <b>%{y:,.0f}</b><br>"
                    "New Users: <b>+%{customdata[0]:,}</b><br>"
                    f"Growth ({period_label}): <b>%{{customdata[1]:+.1f}}%</b>"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                xaxis_title=x_title,
                yaxis_title="Registered Users",
                height=340,
                margin=dict(l=40, r=30, t=10, b=50),
                showlegend=False,
                hovermode="x unified",
                hoverlabel=HOVER_LABEL,
                font=FONT,
                **CHART_BG,
            )

            fig.update_xaxes(
                showgrid=False,
                title_font=AXIS_FONT,
                tickfont=TICK_FONT,
            )

            fig.update_yaxes(
                gridcolor=GRID_COLOR,
                zeroline=False,
                title_font=AXIS_FONT,
                tickfont=TICK_FONT,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        # ---- Conversion Funnel ----
        anchor("subscription-conversion-funnel")
        st.markdown(f"""
        <div class="chart-card">
            <div class="figure-title">Conversion Funnel Stages{subscription_period_suffix}</div>
        
        """, unsafe_allow_html=True)


        funnel = get_conversion_funnel(subscription_period_start, subscription_period_end)

        funnel = funnel.sort_values("users", ascending=False).reset_index(drop=True)

        total_max = funnel["users"].max()
        funnel["pct"] = (funnel["users"] / total_max * 100).round(1)
        funnel["dropoff"] = (100 - funnel["pct"]).round(1)

        # ---- Stage-to-stage lost users (vs. previous stage, not vs. total) ----
        funnel["prev_stage_users"] = funnel["users"].shift(1)
        funnel["lost"] = (funnel["prev_stage_users"] - funnel["users"]).fillna(0).astype(int)
        funnel["lost"] = funnel["lost"].clip(lower=0)  # safety net for genuine ties only now

        funnel["conv_opp"] = funnel["lost"].apply(
            lambda x: f"₹{x * int(kpis.get('arpu', 0)):,}"
        )
        funnel["stage_conv"] = [100.0] + [
            round(funnel["users"].iloc[i] / funnel["users"].iloc[i - 1] * 100, 1)
            for i in range(1, len(funnel))
        ]


        stage_colors = ["#1D4ED8", "#2563EB", "#3B82F6", "#93C5FD"]

        fig = go.Figure()

        for i, row in funnel.iterrows():
            fig.add_trace(go.Bar(
                x=[row["stage"]],
                y=[row["users"]],
                name=row["stage"],
                marker_color=stage_colors[i % len(stage_colors)],
                marker_line_width=0,
                marker_cornerradius=6,
                text=f"<b>{int(row['users']):,}</b><br>{row['pct']}%",
                textposition="outside",
                textfont=dict(size=11, color="#0F172A", family="Manrope"),
                cliponaxis=False,
                showlegend=False,
                width=0.5,
                customdata=[[
                    row["dropoff"],
                    int(row["lost"]),
                    row["conv_opp"],
                    row["stage_conv"],
                ]],
                hovertemplate=(
                    f"<b>{row['stage']}</b><br>"
                    f"Users: <b>{int(row['users']):,}</b> ({row['pct']}% of total)<br>"
                    "Overall drop-off vs. top of funnel: <b>%{customdata[0]}%</b><br>"
                    "Users lost vs. previous stage: <b>%{customdata[1]:,}</b><br>"
                    "Revenue opportunity (vs. previous stage): <b>%{customdata[2]}</b><br>"
                    "Conversion from prev stage: <b>%{customdata[3]}%</b>"
                    "<extra></extra>"
                ),
            ))

        fig.update_layout(
            height=380,
            **CHART_BG,
            font=FONT,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            hoverlabel=HOVER_LABEL,
            hovermode="x",
            yaxis=dict(
                type="log",
                title="Users (log scale)",
                title_font=dict(size=11, color="#6B7280", family="Manrope"),
                tickfont=dict(size=10, color="#6B7280", family="Manrope"),
                gridcolor="#F1F5F9",
                tickvals=[1, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000],
                ticktext=["1", "10", "25", "50", "100", "250", "500", "1K", "5K", "10K"],
                zeroline=False,
            ),
            xaxis=dict(
                title="",
                tickfont=dict(size=12, color="#0F172A", family="Manrope", weight="bold"),
                showgrid=False,
                zeroline=False,
            ),
            bargap=0.4,
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ---- Insight callout: biggest STAGE-TO-STAGE drop, not vs. total ----
        funnel_with_drop = funnel[funnel["lost"] > 0]  # excludes the first stage (always 0 lost)
        if not funnel_with_drop.empty:
            worst_drop = funnel_with_drop.loc[funnel_with_drop["lost"].idxmax()]

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


        # ---- Renewal & Retention ----


        anchor("subscription-renewal-retention")
        st.markdown("<div class='section-header'>Renewal and Retention</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        left, right = st.columns(2, gap="large")

        with left:
            anchor("subscription-renewal-cohort-trend")
            st.markdown(f"""
            <div class="chart-card">
                <div class="figure-title">Renewal Cohort Trend{subscription_period_suffix}</div>
            
            """, unsafe_allow_html=True)

            df_renewal_trend = dd.get_renewal_cohort_trend(subscription_period_start, subscription_period_end)

            if not df_renewal_trend.empty:
                df_renewal_trend = df_renewal_trend.sort_values("month").reset_index(drop=True)
                df_renewal_trend["mom_change"] = df_renewal_trend["renewed_subscribers"].diff().fillna(0).astype(int)
                df_renewal_trend["mom_pct"] = df_renewal_trend["renewed_subscribers"].pct_change().fillna(0).mul(100).round(
                    1)

                # ── Identify important nodes: peaks, troughs, first, last, big swings ──
                vals = df_renewal_trend["renewed_subscribers"].values
                important_idx = set()
                important_idx.add(0)
                important_idx.add(len(df_renewal_trend) - 1)
                for i in range(1, len(vals) - 1):
                    if vals[i] > vals[i - 1] and vals[i] > vals[i + 1]:
                        important_idx.add(i)
                    if vals[i] < vals[i - 1] and vals[i] < vals[i + 1]:
                        important_idx.add(i)
                    if abs(df_renewal_trend["mom_pct"].iloc[i]) > 30:
                        important_idx.add(i)

                df_key = df_renewal_trend.iloc[sorted(important_idx)].copy()
                df_other = df_renewal_trend.iloc[[i for i in range(len(df_renewal_trend)) if i not in important_idx]].copy()

                fig = go.Figure()

                # Base line
                fig.add_trace(go.Scatter(
                    x=df_renewal_trend["month"], y=df_renewal_trend["renewed_subscribers"],
                    mode="lines",
                    line=dict(color="#10B981", width=3, shape="spline"),
                    fill="tozeroy", fillcolor="rgba(16,185,129,0.07)",
                    showlegend=False, hoverinfo="skip",
                ))

                # Non-key points
                fig.add_trace(go.Scatter(
                    x=df_other["month"], y=df_other["renewed_subscribers"],
                    mode="markers",
                    marker=dict(size=5, color="white", line=dict(color="#10B981", width=1.5)),
                    showlegend=False,
                    customdata=df_other[["mom_change", "mom_pct"]].values,
                    hovertemplate=(
                        "<b>%{x|%b %Y}</b><br>"
                        "Renewals: <b>%{y}</b><br>"
                        "MoM Change: <b>%{customdata[0]:+,}</b> (%{customdata[1]:+.1f}%)"
                        "<extra></extra>"
                    ),
                ))

                # Key nodes
                key_colors = [
                    "#10B981" if row["mom_change"] >= 0 else "#EF4444"
                    for _, row in df_key.iterrows()
                ]
                key_text = [
                    f"+{row['mom_change']} ({row['mom_pct']:+.0f}%)" if row["mom_change"] >= 0
                    else f"{row['mom_change']} ({row['mom_pct']:+.0f}%)"
                    for _, row in df_key.iterrows()
                ]

                fig.add_trace(go.Scatter(
                    x=df_key["month"], y=df_key["renewed_subscribers"],
                    mode="markers+text",
                    marker=dict(size=11, color=key_colors, line=dict(color="white", width=2)),
                    text=key_text,
                    textposition=[
                        "top center" if row["mom_change"] >= 0 else "bottom center"
                        for _, row in df_key.iterrows()
                    ],
                    textfont=dict(
                        size=10, family="Manrope",
                        color=["#10B981" if c == "#10B981" else "#EF4444" for c in key_colors]
                    ),
                    showlegend=False,
                    customdata=df_key[["mom_change", "mom_pct"]].values,
                    hovertemplate=(
                        "<b>%{x|%b %Y}</b>  Key Event<br>"
                        "Renewals: <b>%{y}</b><br>"
                        "MoM Change: <b>%{customdata[0]:+,}</b> (%{customdata[1]:+.1f}%)"
                        "<extra></extra>"
                    ),
                ))

                fig.update_layout(
                    height=360,
                    **CHART_BG, font=FONT,
                    margin=dict(l=40, r=20, t=20, b=50),
                    hoverlabel=HOVER_LABEL,
                    hovermode="x unified",
                    showlegend=False,
                    xaxis=dict(title="Month", title_font=AXIS_FONT, tickfont=TICK_FONT, showgrid=False),
                    yaxis=dict(title="Renewed Subscribers", title_font=AXIS_FONT, tickfont=TICK_FONT,
                               gridcolor="#F1F5F9", zeroline=False),
                )

                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            anchor("subscription-renewal-rate-by-plan")
            st.markdown(f"""
            <div class="chart-card">
                <div class="figure-title">Renewal Rate by Plan{subscription_period_suffix}</div>
            
            """, unsafe_allow_html=True)
            df_plan_trend = dd.get_renewal_by_plan_period(subscription_period_start, subscription_period_end)

            color_map_plan = {
                "Silver Plan": "#9CA3AF", "Silver Tier": "#9CA3AF",
                "Gold Plan": "#F59E0B", "Gold Ultimate": "#F59E0B",
                "Platinum Plan": "#2563EB", "Platinum Executive": "#2563EB",
                "Diamond Plan": "#6366F1", "Diamond Elite": "#6366F1",
                "Trial Plan": "#D1D5DB",
            }

            if "month" in df_plan_trend.columns:
                fig_plan = go.Figure()
                for plan in df_plan_trend["plan_name"].unique():
                    df_sub = df_plan_trend[df_plan_trend["plan_name"] == plan]
                    fig_plan.add_trace(go.Scatter(
                        x=df_sub["month"],
                        y=df_sub["renewal_rate"],
                        name=plan,
                        mode="lines+markers",
                        line=dict(color=color_map_plan.get(plan, BLUE), width=2.5, shape="spline"),
                        marker=dict(size=7, line=dict(color="white", width=1.5)),
                        hovertemplate=(
                            f"<b>{plan}</b><br>"
                            "Month: <b>%{x}</b><br>"
                            "Renewal Rate: <b>%{y}%</b>"
                            "<extra></extra>"
                        ),
                    ))
                fig_plan.update_layout(
                    height=310,
                    **CHART_BG,
                    margin=dict(l=10, r=10, t=10, b=20),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1, font=dict(size=10, color="#0F172A"),
                    ),
                    font=dict(family="Manrope", color="#0F172A"),
                    hoverlabel=HOVER_LABEL,
                    hovermode="x unified",
                )
                fig_plan.update_yaxes(range=[30, 100], showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
                                      title_font=AXIS_FONT, tickfont=TICK_FONT)
                fig_plan.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
                st.plotly_chart(fig_plan, use_container_width=True, config={"displayModeBar": False})

            else:
                df_plan_trend = df_plan_trend[df_plan_trend["renewed_users"] > 0].sort_values("renewal_rate", ascending=True)

                if df_plan_trend.empty:
                    st.info("No renewals in this period.")
                else:
                    fig_plan = px.bar(df_plan_trend, x="renewal_rate", y="plan_name", orientation="h")

                    bar_colors = [color_map_plan.get(p, BLUE) for p in df_plan_trend["plan_name"]]

                    fig_plan.update_traces(
                        marker_color=bar_colors,
                        marker_line_width=0,
                        marker_cornerradius=4,

                        customdata=df_plan_trend[
                            [
                                "total_renewed_all_plans",
                                "renewed_users",
                                "monthly_renewed",
                                "annual_renewed",
                                "renewal_rate",
                            ]
                        ],

                        text=df_plan_trend["renewal_rate"].apply(lambda x: f"{x:.1f}%"),
                        textposition="outside",
                        textfont=dict(
                            size=11,
                            color="#374151",
                            family="Manrope",
                        ),

                        cliponaxis=False,

                        hovertemplate="""
                <b>%{y}</b>

                <br><br>
            
                Total Renewals (window)
                <b>%{customdata[0]:,}</b>
                <br>
                Renewed Users (this plan)
                <b>%{customdata[1]:,}</b>

                <br>

                Monthly
                <b>%{customdata[2]:,}</b>

                <br>

                Annual
                <b>%{customdata[3]:,}</b>

                <br><br>

                Share of Total Renewals
                <b>%{customdata[4]:.1f}%</b>

                <extra></extra>
                """
                    )

                    fig_plan.update_layout(
                        height=310,
                        bargap=0.4,
                        **CHART_BG,
                        font=FONT,
                        margin=dict(l=12, r=70, t=10, b=40),
                        showlegend=False,
                        hoverlabel=HOVER_LABEL,
                        hovermode="y",
                        xaxis_title="Renewal Rate (%)",
                        yaxis_title=""
                    )

                    fig_plan.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, title_font=AXIS_FONT)
                    fig_plan.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)

                    st.plotly_chart(fig_plan, use_container_width=True, config={"displayModeBar": False})

            st.markdown("</div>", unsafe_allow_html=True)

        # ---- Renewal Rate by Partner ----
        anchor("subscription-renewal-rate-by-partner")
        st.markdown(f"""
        <div class="chart-card">
            <div class="figure-title">Renewal Rate by Partner (Trend){subscription_period_suffix}</div>
        
        """, unsafe_allow_html=True)

        df_partner_trend = dd.get_renewal_by_partner_period(subscription_period_start, subscription_period_end)

        if "month" in df_partner_trend.columns:
            fig_partner = go.Figure()
            color_map_partner = {
                "HDFC Securities": "#10B981",
                "ICICI Direct": "#EF4444",
                "Zerodha Connect": "#F59E0B",
                "Groww Link": "#8B5CF6",
            }
            for partner in df_partner_trend["sso_partner_name"].unique():
                df_sub = df_partner_trend[df_partner_trend["sso_partner_name"] == partner]
                fig_partner.add_trace(go.Scatter(
                    x=df_sub["month"],
                    y=df_sub["renewal_rate"],
                    name=partner,
                    mode="lines+markers",
                    line=dict(color=color_map_partner.get(partner, BLUE), width=2.5, shape="spline"),
                    marker=dict(size=7, line=dict(color="white", width=1.5)),
                    hovertemplate=(
                        f"<b>{partner}</b><br>"
                        "Month: <b>%{x}</b><br>"
                        "Renewal Rate: <b>%{y}%</b>"
                        "<extra></extra>"
                    ),
                ))
            fig_partner.update_layout(
                height=320,
                **CHART_BG,
                margin=dict(l=10, r=10, t=10, b=20),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(size=10, color="#0F172A"),
                ),
                font=dict(family="Manrope", color="#0F172A"),
                hoverlabel=HOVER_LABEL,
                hovermode="x unified",
            )
            fig_partner.update_yaxes(range=[30, 100], showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
                                     title_font=AXIS_FONT, tickfont=TICK_FONT)
            fig_partner.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            st.plotly_chart(fig_partner, use_container_width=True, config={"displayModeBar": False})
        else:
            df_partner_trend = df_partner_trend[df_partner_trend["renewed_users"] > 0].sort_values("renewal_rate", ascending=True)

            if df_partner_trend.empty:
                st.info("No renewals in this period.")
            else:
                fig_partner = px.bar(df_partner_trend, x="renewal_rate", y="sso_partner_name", orientation="h")

                fig_partner.update_traces(
                    marker_color=BLUE,
                    marker_line_width=0,
                    marker_cornerradius=4,

                    customdata=df_partner_trend[
                        [
                            "total_renewed_all_partners",
                            "renewed_users",
                            "monthly_renewed",
                            "annual_renewed",
                            "renewal_rate",
                        ]
                    ],

                    text=df_partner_trend["renewal_rate"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                    textfont=dict(
                        size=11,
                        color="#374151",
                        family="Manrope",
                    ),

                    cliponaxis=False,

                    hovertemplate="""
            <b>%{y}</b>

            <br><br>

            Total Renewals (window)
            <b>%{customdata[0]:,}</b>

            <br>

            Renewed Users (this partner)
            <b>%{customdata[1]:,}</b>

            <br>

            Monthly
            <b>%{customdata[2]:,}</b>

            <br>

            Annual
            <b>%{customdata[3]:,}</b>

            <br><br>

            Share of Total Renewals
            <b>%{customdata[4]:.1f}%</b>

            <extra></extra>
            """
                )

                fig_partner.update_layout(
                    height=320,
                    bargap=0.4,
                    **CHART_BG,
                    font=FONT,
                    margin=dict(l=12, r=70, t=10, b=40),
                    showlegend=False,
                    hoverlabel=HOVER_LABEL,
                    hovermode="y",
                    xaxis_title="Renewal Rate (%)",
                    yaxis_title=""
                )

                fig_partner.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, title_font=AXIS_FONT)
                fig_partner.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)

                st.plotly_chart(fig_partner, use_container_width=True, config={"displayModeBar": False})

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        renewals = get_upcoming_renewals()

        next_1_day = renewals["next_1_day"]
        next_3_days = renewals["next_3_days"]
        next_7_days = renewals["next_7_days"]
        next_15_days = renewals["next_15_days"]

        st.markdown(
            "### <span style='color:#0F172A;'>Upcoming Renewals</span>",
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🔴 Next 1 Day",
            f"{next_1_day:,}",
            help=f"""
        Users:
        {', '.join(map(str, renewals['next_1_day_users'])) or 'None'}
        """
        )

        c2.metric(
            "🟠 Next 3 Days",
            f"{next_3_days:,}",
            help=f"""
        Users:
        {', '.join(map(str, renewals['next_3_days_users'])) or 'None'}
        """
        )

        c3.metric(
            "🟡 Next 7 Days",
            f"{next_7_days:,}",
            help=f"""
        Users:
        {', '.join(map(str, renewals['next_7_days_users'])) or 'None'}
        """
        )

        c4.metric(
            "🟢 Next 15 Days",
            f"{next_15_days:,}",
            help=f"""
        Users:
        {', '.join(map(str, renewals['next_15_days_users'])) or 'None'}
        """
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Non-Renewal Insights ----
        anchor("subscription-non-renewal-insights")
        st.markdown("""
        <div class="chart-card">
            <div class="figure-title">Non-Renewal Insights</div>
            <div class="figure-caption">Users whose latest invoice (Silver/Gold/Platinum/Diamond/Trial) has already expired with no newer invoice since.</div>
        """, unsafe_allow_html=True)

        df_renewal_status = get_renewal_status_by_plan()
        if df_renewal_status is not None and not df_renewal_status.empty:
            total_active_nr = int(df_renewal_status[df_renewal_status["renewal_status"] == "Active"]["user_count"].sum())
            total_non_renewal = int(df_renewal_status[df_renewal_status["renewal_status"] == "Non-Renewal"]["user_count"].sum())
            total_nr_base = total_active_nr + total_non_renewal
            non_renewal_rate = round(total_non_renewal / total_nr_base * 100, 1) if total_nr_base else 0.0

            nr1, nr2, nr3 = st.columns(3)
            nr1.metric("Active Subscribers", f"{total_active_nr:,}")
            nr2.metric("Non-Renewal Users", f"{total_non_renewal:,}")
            nr3.metric("Non-Renewal Rate", f"{non_renewal_rate}%")

            # Stacked bar: Active vs Non-Renewal per plan
            plan_order = (
                df_renewal_status.groupby("billed_plan_name")["user_count"].sum()
                .sort_values(ascending=True).index.tolist()
            )
            active_by_plan = df_renewal_status[df_renewal_status["renewal_status"] == "Active"].set_index("billed_plan_name").reindex(plan_order).fillna(0)
            nonrenewal_by_plan = df_renewal_status[df_renewal_status["renewal_status"] == "Non-Renewal"].set_index("billed_plan_name").reindex(plan_order).fillna(0)

            plan_hover_active, plan_hover_nonrenewal = [], []
            for plan in plan_order:
                a = int(active_by_plan.loc[plan, "user_count"])
                nr = int(nonrenewal_by_plan.loc[plan, "user_count"])
                plan_total = a + nr
                rate = round(nr / plan_total * 100, 1) if plan_total else 0.0
                plan_hover_active.append(f"<b>{plan}</b> — Active<br>Active: {a:,}<br>Non-Renewal: {nr:,}<br>Non-Renewal Rate: {rate}%")
                plan_hover_nonrenewal.append(f"<b>{plan}</b> — Non-Renewal<br>Active: {a:,}<br>Non-Renewal: {nr:,}<br>Non-Renewal Rate: {rate}%")

            fig_nr_plan = go.Figure()
            fig_nr_plan.add_trace(go.Bar(
                y=plan_order, x=active_by_plan["user_count"], name="Active", orientation="h",
                marker_color="#10B981", marker_line_width=0,
                hovertext=plan_hover_active, hoverinfo="text",
            ))
            fig_nr_plan.add_trace(go.Bar(
                y=plan_order, x=nonrenewal_by_plan["user_count"], name="Non-Renewal", orientation="h",
                marker_color="#EF4444", marker_line_width=0,
                hovertext=plan_hover_nonrenewal, hoverinfo="text",
            ))
            fig_nr_plan.update_layout(
                barmode="stack", height=280, **CHART_BG, font=FONT,
                margin=dict(l=12, r=30, t=10, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, color="#0F172A")),
                hoverlabel=HOVER_LABEL,
                xaxis_title="Users", yaxis_title="",
            )
            fig_nr_plan.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            fig_nr_plan.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            st.plotly_chart(fig_nr_plan, use_container_width=True, config={"displayModeBar": False})

            # Monthly trend of non-renewals
            df_nr_trend = get_non_renewal_trend()
            if df_nr_trend is not None and not df_nr_trend.empty:
                df_nr_trend = df_nr_trend.copy()
                df_nr_trend["month"] = pd.to_datetime(df_nr_trend["month"])
                fig_nr_trend = go.Figure(go.Scatter(
                    x=df_nr_trend["month"], y=df_nr_trend["non_renewal_count"], mode="lines+markers",
                    line=dict(color="#EF4444", width=2.5, shape="spline"),
                    hovertemplate="<b>%{x|%b %Y}</b><br>Non-Renewals: <b>%{y}</b><extra></extra>",
                ))
                fig_nr_trend.update_layout(
                    height=240, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40),
                    showlegend=False, hoverlabel=HOVER_LABEL,
                    xaxis_title="Month", yaxis_title="Non-Renewal Users",
                )
                fig_nr_trend.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
                fig_nr_trend.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
                st.plotly_chart(fig_nr_trend, use_container_width=True, config={"displayModeBar": False})

            top_plan_row = df_renewal_status[df_renewal_status["renewal_status"] == "Non-Renewal"].sort_values("user_count", ascending=False)
            if not top_plan_row.empty:
                top_plan_name = top_plan_row.iloc[0]["billed_plan_name"]
                top_plan_count = int(top_plan_row.iloc[0]["user_count"])
                st.markdown(
                    insight_box(
                        f"<b>{top_plan_name}</b> has the most non-renewal users (<b>{top_plan_count:,}</b>), out of "
                        f"<b>{total_non_renewal:,}</b> total non-renewals (<b>{non_renewal_rate}%</b> of all users on these plans).",
                        title="Non-Renewal Insight",
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.info("No non-renewal data available.")
        st.markdown("</div>", unsafe_allow_html=True)

df_partner = get_revenue_by_sso()

print("\n--- [DATABASE DEBUG] LIVE REVENUE BY SSO ---")
print(df_partner.to_string())
print("--------------------------------------------\n")

print(df_partner.to_string())

# ═══════════════════════════════════════════════════════
# 🛠️ TAB 3 — ENGINEERING
# ═══════════════════════════════════════════════════════
if engineering_tab:
    with engineering_tab:
        anchor("engineering-overview")
        st.markdown("""
        <div class="eng-hero">
            <div class="eng-hero-title"> Engineering Quality &amp; Release Analytics</div>
        """, unsafe_allow_html=True)

        if "engineering_issues" not in st.session_state:
            st.session_state["engineering_issues"] = get_engineering_issues()
        if "activities" not in st.session_state:
            st.session_state["activities"] = get_engineering_activities()

        df_issues = st.session_state["engineering_issues"]
        df_activities = st.session_state["activities"]

        # ---- 🔍 TEMP DEBUG: confirm real column names once, then remove this line ----


        # ---- Safely resolve the module/area column name ONCE for the whole Engineering tab ----
        MODULE_COL = next(
            (c for c in ["application_area", "module", "area", "feature_area", "component"]
             if c in df_issues.columns),
            None
        )

        eng_kpis = get_engineering_kpis(df_issues)

        k1, k2, k3, k4, k5, k6 = st.columns(6)

        with k1:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Total Issues</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{eng_kpis['total_issues']}</span>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Closed Issues</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{eng_kpis['closed_issues_count']}</span>

            </div>
            """, unsafe_allow_html=True)

        with k3:
            rejected_count = int((df_issues["status"].str.lower() == "rejected").sum())
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Rejected</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{rejected_count}</span>
            </div>
            """, unsafe_allow_html=True)

        with k4:
            open_count = int((df_issues["status"].str.lower() == "open").sum())
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Open</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{open_count}</span>
            </div>
            """, unsafe_allow_html=True)

        with k5:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Pending Backlog</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{eng_kpis['pending_backlog_count']}</span>

            </div>
            """, unsafe_allow_html=True)

        with k6:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Regression Rate</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{eng_kpis['regression_rate_percentage']}%</span>

            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        anchor("engineering-release-defect-trend")
        st.markdown("""
        <div class="chart-card">
            <div class="figure-title">Release Defect Trend (All Versions)</div>
            <div class="figure-caption">Issue volume across every release chronologically — each node represents one release.</div>
        """, unsafe_allow_html=True)

        df_release_all = dd.get_release_wise_defect_distribution()
        if df_release_all is not None and not df_release_all.empty:
            df_release_all = df_release_all.rename(columns={"total_issues": "Issues"})
            df_release_all = df_release_all.dropna(subset=["release_version"]).sort_values("release_version")
        else:
            df_release_all = df_issues.groupby("release_version").size().reset_index(name="Issues").sort_values(
                "release_version")

        fig_rel_line = px.line(df_release_all, x="release_version", y="Issues")
        fig_rel_line.update_traces(
            mode="lines+markers",
            line=dict(color="#1D4ED8", width=2.5, shape="linear"),
            marker=dict(size=7, color="#1D4ED8", line=dict(color="white", width=1.5)),
            fill="tozeroy",
            fillcolor="rgba(29,78,216,0.07)",
            hovertemplate="Release: <b>%{x}</b><br>Issues: <b>%{y}</b><extra></extra>"
        )
        fig_rel_line.update_layout(
            height=380, **CHART_BG, font=FONT,
            margin=dict(l=40, r=20, t=10, b=80),
            showlegend=False, hoverlabel=HOVER_LABEL,
            hovermode="x unified",
            xaxis_title="Release Version",
            yaxis_title="Total Issues"
        )
        fig_rel_line.update_xaxes(
            tickangle=-45,
            tickfont=dict(color="#1E293B", family="Manrope", size=10),
            title_font=dict(color="#1E293B"),
            showgrid=False
        )
        fig_rel_line.update_yaxes(
            tickfont=dict(color="#1E293B", family="Manrope", size=11),
            title_font=dict(color="#1E293B"),
            gridcolor=GRID_COLOR,
            zeroline=False
        )
        st.plotly_chart(fig_rel_line, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        anchor("engineering-severity-priority")
        st.markdown("""
          <div class="chart-card">
              <div class="figure-title">Severity / Priority Distribution</div>
              <div class="figure-caption">Each bar shows Total Issues split into Open, Reopen Events, and Closed segments. Click a legend item to toggle it — the total updates live.</div>
          """, unsafe_allow_html=True)

        severity_order = ["High", "Medium", "Low", "Very Low", "Unspecified"]

        df_sev = dd.get_severity_distribution()
        if df_sev is not None and not df_sev.empty:
            df_sev = df_sev.rename(columns={"issue_count": "Issues"})
        else:
            df_sev = df_issues.groupby("priority").size().reset_index(name="Issues")

        df_re_pri = dd.get_reopen_events_by_priority()
        if df_re_pri is not None and not df_re_pri.empty:
            df_re_pri = df_re_pri.rename(columns={"reopen_events": "Reopens"})
        else:
            df_re_pri = df_issues.groupby("priority")["reopened_count"].sum().reset_index(name="Reopens")

        df_open_pri = (df_issues[df_issues["status"].str.lower() == "open"]
                       .groupby("priority").size().reset_index(name="Open"))

        for df in [df_sev, df_re_pri, df_open_pri]:
            df["priority"] = df["priority"].fillna("Unspecified").replace("", "Unspecified")

        df_sev = df_sev.merge(df_re_pri[["priority", "Reopens"]], on="priority", how="left")
        df_sev = df_sev.merge(df_open_pri[["priority", "Open"]], on="priority", how="left")
        df_sev["Reopens"] = df_sev["Reopens"].fillna(0).astype(int)
        df_sev["Open"] = df_sev["Open"].fillna(0).astype(int)
        df_sev["Closed"] = (df_sev["Issues"] - df_sev["Open"] - df_sev["Reopens"]).clip(lower=0)

        df_sev["priority"] = pd.Categorical(df_sev["priority"], categories=severity_order, ordered=True)
        df_sev = df_sev.dropna(subset=["priority"]).sort_values("priority", ascending=False)

        categories = df_sev["priority"].astype(str).tolist()
        closed_vals = df_sev["Closed"].astype(int).tolist()
        open_vals = df_sev["Open"].astype(int).tolist()
        reopen_vals = df_sev["Reopens"].astype(int).tolist()
        total_vals = [c + o + r for c, o, r in zip(closed_vals, open_vals, reopen_vals)]

        chart_height = 280

        severity_component_html = f"""
          <div id="sevChart" style="width:100%; height:{chart_height}px;"></div>
          <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
          <script>
          (function() {{
              var categories = {json.dumps(categories)};
              var closedVals = {json.dumps(closed_vals)};
              var openVals = {json.dumps(open_vals)};
              var reopenVals = {json.dumps(reopen_vals)};

              var traceClosed = {{
                  y: categories, x: closedVals, name: 'Closed', type: 'bar', orientation: 'h',
                  marker: {{ color: '#1D4ED8' }},
                  hovertemplate: 'Priority: <b>%{{y}}</b><br>Closed: <b>%{{x}}</b><extra></extra>'
              }};
              var traceOpen = {{
                  y: categories, x: openVals, name: 'Open', type: 'bar', orientation: 'h',
                  marker: {{ color: '#F59E0B' }},
                  hovertemplate: 'Priority: <b>%{{y}}</b><br>Open: <b>%{{x}}</b><extra></extra>'
              }};
              var traceReopen = {{
                  y: categories, x: reopenVals, name: 'Reopen Events', type: 'bar', orientation: 'h',
                  marker: {{ color: '#EF4444' }},
                  hovertemplate: 'Priority: <b>%{{y}}</b><br>Reopen Events: <b>%{{x}}</b><extra></extra>'
              }};

              var initialTotals = categories.map(function(_, i) {{
                  return closedVals[i] + openVals[i] + reopenVals[i];
              }});

              var traceTotal = {{
                  y: categories, x: initialTotals, text: initialTotals.map(String),
                  mode: 'text', textposition: 'middle right',
                  textfont: {{ size: 11, color: '#0F172A', family: 'Manrope' }},
                  showlegend: false, hoverinfo: 'skip', type: 'scatter'
              }};

              var layout = {{
                  barmode: 'stack',
                  height: {chart_height},
                  margin: {{ l: 90, r: 130, t: 10, b: 30 }},
                  plot_bgcolor: 'white', paper_bgcolor: 'white',
                  font: {{ family: 'Manrope', color: '#1E293B', size: 12 }},
                  xaxis: {{ title: 'Issues Count', color: '#1E293B', tickfont: {{ family: 'Manrope', size: 11 }} }},
                  yaxis: {{ color: '#1E293B', tickfont: {{ family: 'Manrope', size: 11 }} }},
                  legend: {{
                      orientation: 'v', yanchor: 'top', y: 1, xanchor: 'left', x: 1.0,
                      font: {{ size: 11, color: '#0F172A', family: 'Manrope' }},
                      bgcolor: 'rgba(255,255,255,0.95)', bordercolor: '#E5E7EB', borderwidth: 1
                  }},
                  hoverlabel: {{
                      bgcolor: 'rgba(15,23,42,0.88)', bordercolor: 'rgba(37,99,235,0.6)',
                      font: {{ family: 'Manrope', size: 12, color: '#F8FAFC' }}
                  }}
              }};

              var config = {{ displayModeBar: false, responsive: true }};
              var gd = document.getElementById('sevChart');

              // Fix: Plotly caches the legend's text-fitting boxes on its first
              // layout pass. A fixed setTimeout delay was a guess at when the
              // iframe would be settled to its real width — unreliable across
              // different zoom levels/environments. Instead, wait until the
              // container's width is actually unchanged across two animation
              // frames before ever calling Plotly.newPlot.
              function waitForStableWidth(el, cb, tries) {{
                  tries = tries || 0;
                  var w1 = el.offsetWidth;
                  requestAnimationFrame(function() {{
                      var w2 = el.offsetWidth;
                      if ((w1 === w2 && w1 > 0) || tries > 40) {{
                          cb();
                      }} else {{
                          waitForStableWidth(el, cb, tries + 1);
                      }}
                  }});
              }}

              waitForStableWidth(gd, function() {{
                  Plotly.newPlot(gd, [traceClosed, traceOpen, traceReopen, traceTotal], layout, config);

                  window.addEventListener('resize', function() {{ Plotly.Plots.resize(gd); }});

                  // visible[0..2] track Closed/Open/Reopens; index 3 (traceTotal) is never toggled directly
                  var visible = [true, true, true];

                  gd.on('plotly_legendclick', function(data) {{
                      var idx = data.curveNumber;
                      if (idx < 3) {{
                          visible[idx] = !visible[idx];
                          var newTotals = categories.map(function(_, i) {{
                              var sum = 0;
                              if (visible[0]) sum += closedVals[i];
                              if (visible[1]) sum += openVals[i];
                              if (visible[2]) sum += reopenVals[i];
                              return sum;
                          }});
                          Plotly.restyle(gd, {{ x: [newTotals], text: [newTotals.map(String)] }}, [3]);
                      }}
                      return true; // let Plotly's default legend toggle (hide/show the bar segment) proceed
                  }});
              }});
          }})();
          </script>
          """

        st.components.v1.html(severity_component_html, height=chart_height + 20, scrolling=False)

        st.markdown("</div>", unsafe_allow_html=True)

        # ============================================================
        # 🎛️ Shared filters for Classification charts
        # ============================================================
        anchor("engineering-classification-filters")
        st.markdown("<div class='section-header' style='margin-top:26px;'>Issue Classification Filters</div>",
                    unsafe_allow_html=True)

        f1, f2, f3 = st.columns([1.4, 1.4, 1.4])

        with f1:
            if MODULE_COL:
                module_options = ["All Modules"] + sorted(df_issues[MODULE_COL].dropna().unique().tolist())
                selected_module = st.selectbox("Module", module_options, key="cls_module")
            else:
                st.selectbox("Module", ["Column not found"], key="cls_module", disabled=True)
                selected_module = "All Modules"
        with f2:
            if "release_version" in df_issues.columns:
                release_options = ["All Releases"] + sorted(df_issues["release_version"].dropna().unique().tolist())
                selected_release = st.selectbox("Release Version", release_options, key="cls_release")
            else:
                st.selectbox("Release Version", ["Column not found"], key="cls_release", disabled=True)
                selected_release = "All Releases"
                if "releases" in dd._ENG_VIEW_ERRORS:
                    st.caption(f"⚠️ engineering.releases: {dd._ENG_VIEW_ERRORS['releases']}")
        with f3:
            if "platform" in df_issues.columns:
                platform_options = ["All Platforms"] + sorted(df_issues["platform"].dropna().unique().tolist())
                selected_platform = st.selectbox("Platform", platform_options, key="cls_platform")
            else:
                st.selectbox("Platform", ["Column not found"], key="cls_platform", disabled=True)
                selected_platform = "All Platforms"

        # ---- Build filtered dataset: all statuses included, narrowed by Module/Release/Platform only ----
        df_cls_filtered = df_issues.copy()

        if MODULE_COL and selected_module != "All Modules":
            df_cls_filtered = df_cls_filtered[df_cls_filtered[MODULE_COL] == selected_module]

        if "release_version" in df_issues.columns and selected_release != "All Releases":
            df_cls_filtered = df_cls_filtered[df_cls_filtered["release_version"] == selected_release]

        if "platform" in df_issues.columns and selected_platform != "All Platforms":
            df_cls_filtered = df_cls_filtered[df_cls_filtered["platform"] == selected_platform]
        # ============================================================
        # 🧩 Helper: stacked status bars + severity-mix hover

        _severity_chart_counter = {"n": 0}  # ensures a unique DOM id per call, even across reruns


        def build_status_severity_chart(df_source, group_col, title_label):
            if df_source.empty:
                st.info(f"No issues match the current filters for {title_label}.")
                return

            work = df_source.copy()
            work["priority"] = work["priority"].fillna("Unspecified").replace("", "Unspecified")

            def classify_status(row):
                if row["reopened_count"] > 0:
                    return "Reopened"
                elif str(row["status"]).lower() == "closed":
                    return "Closed"
                elif str(row["status"]).lower() == "open":
                    return "Open"
                else:
                    return "Other"

            work["status_group"] = work.apply(classify_status, axis=1)

            pivot = work.groupby([group_col, "status_group"]).size().unstack(fill_value=0)
            for col in ["Open", "Closed", "Reopened"]:
                if col not in pivot.columns:
                    pivot[col] = 0
            pivot["Total"] = pivot[["Open", "Closed", "Reopened"]].sum(axis=1)
            pivot = pivot.sort_values("Total", ascending=True)

            # Severity mix text, computed SEPARATELY per status segment — this is the
            # fix: previously one severity_text dict was shared across Closed/Open/
            # Reopened hovers, so all three showed the category's overall mix instead
            # of the mix within that specific segment.
            severity_text = {"Closed": {}, "Open": {}, "Reopened": {}}
            for cat_val in pivot.index:
                for status_name in ["Closed", "Open", "Reopened"]:
                    sub = work[(work[group_col] == cat_val) & (work["status_group"] == status_name)]
                    sev_counts = sub["priority"].value_counts()
                    lines = [f"{sev}: {cnt}" for sev, cnt in sev_counts.items()]
                    severity_text[status_name][cat_val] = "<br>".join(lines) if lines else "No issues in this segment"

            categories = [str(c) for c in pivot.index.tolist()]
            closed_vals = pivot["Closed"].astype(int).tolist()
            open_vals = pivot["Open"].astype(int).tolist()
            reopen_vals = pivot["Reopened"].astype(int).tolist()

            severity_hover_closed = [severity_text["Closed"][c] for c in pivot.index]
            severity_hover_open = [severity_text["Open"][c] for c in pivot.index]
            severity_hover_reopened = [severity_text["Reopened"][c] for c in pivot.index]

            _severity_chart_counter["n"] += 1
            div_id = f"clsChart_{_severity_chart_counter['n']}"
            chart_height = max(260, len(pivot) * 45)

            component_html = f"""
            <div id="{div_id}" style="width:100%; height:{chart_height}px;"></div>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <script>
            (function() {{
                var categories = {json.dumps(categories)};
                var closedVals = {json.dumps(closed_vals)};
                var openVals = {json.dumps(open_vals)};
                var reopenVals = {json.dumps(reopen_vals)};
                var severityHoverClosed = {json.dumps(severity_hover_closed)};
                var severityHoverOpen = {json.dumps(severity_hover_open)};
                var severityHoverReopened = {json.dumps(severity_hover_reopened)};

                function makeHover(statusName) {{
                    var vals = statusName === 'Closed' ? closedVals : statusName === 'Open' ? openVals : reopenVals;
                    var sevHover = statusName === 'Closed' ? severityHoverClosed : statusName === 'Open' ? severityHoverOpen : severityHoverReopened;
                    return categories.map(function(cat, i) {{
                        return '<b>' + cat + '</b><br>' + statusName + ': <b>' + vals[i] +
                            '</b><br><br>Severity mix (' + statusName + ' only):<br>' + sevHover[i];
                    }});
                }}

                var traceClosed = {{
                    y: categories, x: closedVals, name: 'Closed', type: 'bar', orientation: 'h',
                    marker: {{ color: '#1D4ED8' }},
                    hovertext: makeHover('Closed'), hoverinfo: 'text'
                }};
                var traceOpen = {{
                    y: categories, x: openVals, name: 'Open', type: 'bar', orientation: 'h',
                    marker: {{ color: '#F59E0B' }},
                    hovertext: makeHover('Open'), hoverinfo: 'text'
                }};
                var traceReopen = {{
                    y: categories, x: reopenVals, name: 'Reopened', type: 'bar', orientation: 'h',
                    marker: {{ color: '#EF4444' }},
                    hovertext: makeHover('Reopened'), hoverinfo: 'text'
                }};

                var initialTotals = categories.map(function(_, i) {{
                    return closedVals[i] + openVals[i] + reopenVals[i];
                }});

                var traceTotal = {{
                    y: categories, x: initialTotals, text: initialTotals.map(String),
                    mode: 'text', textposition: 'middle right',
                    textfont: {{ size: 11, color: '#0F172A', family: 'Manrope' }},
                    showlegend: false, hoverinfo: 'skip', type: 'scatter'
                }};

                var layout = {{
                    barmode: 'stack',
                    height: {chart_height},
                    margin: {{ l: 100, r: 50, t: 36, b: 30 }},
                    plot_bgcolor: 'white', paper_bgcolor: 'white',
                    font: {{ family: 'Manrope', color: '#1E293B', size: 12 }},
                    xaxis: {{ title: 'Issues', color: '#1E293B', tickfont: {{ family: 'Manrope', size: 11 }} }},
                    yaxis: {{ color: '#1E293B', tickfont: {{ family: 'Manrope', size: 11 }} }},
                    legend: {{
                        orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1,
                        font: {{ size: 11, color: '#0F172A', family: 'Manrope' }}
                    }},
                    hoverlabel: {{
                        bgcolor: 'rgba(15,23,42,0.88)', bordercolor: 'rgba(37,99,235,0.6)',
                        font: {{ family: 'Manrope', size: 12, color: '#F8FAFC' }}
                    }}
                }};

                var config = {{ displayModeBar: false, responsive: true }};

                var gd = document.getElementById('{div_id}');

                // Fix: Plotly caches the legend's text-fitting boxes on its first
                // layout pass. Plotting immediately then calling resize() after a
                // fixed delay doesn't redo that legend text-fit calculation, so
                // it can stay truncated. Instead, wait until the container's
                // width is actually unchanged across two animation frames before
                // ever calling Plotly.newPlot.
                function waitForStableWidth(el, cb, tries) {{
                    tries = tries || 0;
                    var w1 = el.offsetWidth;
                    requestAnimationFrame(function() {{
                        var w2 = el.offsetWidth;
                        if ((w1 === w2 && w1 > 0) || tries > 40) {{
                            cb();
                        }} else {{
                            waitForStableWidth(el, cb, tries + 1);
                        }}
                    }});
                }}

                waitForStableWidth(gd, function() {{
                    Plotly.newPlot(gd, [traceClosed, traceOpen, traceReopen, traceTotal], layout, config);
                    window.addEventListener('resize', function() {{ Plotly.Plots.resize(gd); }});

                    var visible = [true, true, true];  // Closed, Open, Reopened

                    gd.on('plotly_legendclick', function(data) {{
                        var idx = data.curveNumber;
                        if (idx < 3) {{
                            visible[idx] = !visible[idx];
                            var newTotals = categories.map(function(_, i) {{
                                var sum = 0;
                                if (visible[0]) sum += closedVals[i];
                                if (visible[1]) sum += openVals[i];
                                if (visible[2]) sum += reopenVals[i];
                                return sum;
                            }});
                            Plotly.restyle(gd, {{ x: [newTotals], text: [newTotals.map(String)] }}, [3]);
                        }}
                        return true;
                    }});
                }});
            }})();
            </script>
            """

            st.components.v1.html(component_html, height=chart_height + 20, scrolling=False)

        # ============================================================
        # 📊 Classification charts (now filterable)
        # ============================================================
        c_cl1, c_cl2 = st.columns(2, gap="large")

        with c_cl1:
            anchor("engineering-classification-category")
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Classification by Category</div>
                <div class="figure-caption">Hover a segment for its severity mix. Filtered by status, module, and release above.</div>
            """, unsafe_allow_html=True)
            build_status_severity_chart(df_cls_filtered, "issue_category", "Category")
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cl2:
            anchor("engineering-classification-technical-type")
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Classification by Technical Type</div>
                <div class="figure-caption">Hover a segment for its severity mix. Filtered by status, module, and release above.</div>
            """, unsafe_allow_html=True)
            build_status_severity_chart(df_cls_filtered, "issue_type", "Technical Type")
            st.markdown("</div>", unsafe_allow_html=True)

        anchor("engineering-module-wise-defect")
        st.markdown("""
        <div class="chart-card">
            <div class="figure-title">Module-wise Defect Distribution</div>
            <div class="figure-caption">Total issues vs reopen events per module — hover any bar for full breakdown.</div>
        """, unsafe_allow_html=True)

        df_mod = dd.get_module_wise_defect_distribution()
        if df_mod is not None and not df_mod.empty:
            df_mod = df_mod.rename(columns={"issue_count": "Issues"})
            # Normalize whatever column dd.get_module_wise_defect_distribution() uses to "application_area"
            if "application_area" not in df_mod.columns and MODULE_COL and MODULE_COL in df_mod.columns:
                df_mod = df_mod.rename(columns={MODULE_COL: "application_area"})
        elif MODULE_COL:
            df_mod = df_issues.groupby(MODULE_COL).size().reset_index(name="Issues")
            df_mod = df_mod.rename(columns={MODULE_COL: "application_area"})
        else:
            df_mod = pd.DataFrame(columns=["application_area", "Issues"])

        df_re_mod = dd.get_reopen_events_by_module()
        if df_re_mod is not None and not df_re_mod.empty:
            df_re_mod = df_re_mod.rename(columns={"reopen_events": "Reopens"})
            if "application_area" not in df_re_mod.columns and MODULE_COL and MODULE_COL in df_re_mod.columns:
                df_re_mod = df_re_mod.rename(columns={MODULE_COL: "application_area"})
        elif MODULE_COL:
            df_re_mod = df_issues.groupby(MODULE_COL)["reopened_count"].sum().reset_index(name="Reopens")
            df_re_mod = df_re_mod.rename(columns={MODULE_COL: "application_area"})
        else:
            df_re_mod = pd.DataFrame(columns=["application_area", "Reopens"])

        if not df_mod.empty:
            df_mod = df_mod.merge(df_re_mod, on="application_area", how="left")
            df_mod["Reopens"] = df_mod["Reopens"].fillna(0).astype(int)
            df_mod = df_mod.sort_values("Issues", ascending=True)

            fig_mod = go.Figure()

            fig_mod.add_trace(go.Bar(
                y=df_mod["application_area"],
                x=df_mod["Issues"],
                name="Total Issues",
                orientation="h",
                marker=dict(color="#1D4ED8", line_width=0),
                text=df_mod["Issues"],
                textposition="outside",
                textfont=dict(size=11, color="#1E293B", family="Manrope"),
                cliponaxis=False,
                hovertemplate="Module: <b>%{y}</b><br>Total Issues: <b>%{x}</b><extra></extra>"
            ))

            fig_mod.add_trace(go.Bar(
                y=df_mod["application_area"],
                x=df_mod["Reopens"],
                name="Reopen Events",
                orientation="h",
                marker=dict(color="#F59E0B", line_width=0),
                text=df_mod["Reopens"],
                textposition="outside",
                textfont=dict(size=11, color="#1E293B", family="Manrope"),
                cliponaxis=False,
                hovertemplate="Module: <b>%{y}</b><br>Reopen Events: <b>%{x}</b><extra></extra>"
            ))

            fig_mod.update_layout(
                barmode="group",
                height=max(300, len(df_mod) * 50),
                **CHART_BG, font=FONT,
                margin=dict(l=12, r=80, t=10, b=30),
                bargap=0.25,
                bargroupgap=0.1,
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                    font=dict(size=11, color="#0F172A", family="Manrope")
                ),
                hoverlabel=HOVER_LABEL,
                xaxis_title="Count", yaxis_title=""
            )
            fig_mod.update_xaxes(
                color="#1E293B", tickfont=dict(color="#1E293B", family="Manrope", size=11),
                title_font=dict(color="#1E293B")
            )
            fig_mod.update_yaxes(
                color="#1E293B", tickfont=dict(color="#1E293B", family="Manrope", size=11),
                title_font=dict(color="#1E293B")
            )
            st.plotly_chart(fig_mod, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No module-level data available (module/area column not found in the issues dataset).")

        st.markdown("</div>", unsafe_allow_html=True)

        # ---- Issues Reopened Multiple Times ----
        df_rmt = dd.get_issues_reopened_multiple_times()
        if df_rmt is not None and not df_rmt.empty:
            rename_map = {"reopened_count": "reopen_events"}
            if "application_area" in df_rmt.columns:
                rename_map["application_area"] = "module"
            elif MODULE_COL and MODULE_COL in df_rmt.columns:
                rename_map[MODULE_COL] = "module"
            df_rmt = df_rmt.rename(columns=rename_map)
        elif MODULE_COL:
            df_rmt = (df_issues[df_issues["reopened_count"] > 1]
                      [["issue_id", MODULE_COL, "reopened_count"]]
                      .rename(columns={MODULE_COL: "module", "reopened_count": "reopen_events"}))
        else:
            df_rmt = pd.DataFrame(columns=["issue_id", "module", "reopen_events"])

        if not df_rmt.empty:
            df_rmt = df_rmt.sort_values("reopen_events", ascending=False)

            rows_html = ""
            for _, r in df_rmt.iterrows():
                desc = str(r.get('issue_description', '')).strip()
                desc = desc[:120] + "..." if len(desc) > 120 else desc
                rows_html += f"""
                <div style="display:flex; justify-content:space-between; align-items:flex-start;
                            padding:12px 0; border-bottom:1px solid #F1F5F9;">
                    <div style="flex:1; min-width:0; padding-right:20px;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                            <span style="font-family:Manrope,sans-serif; font-size:12px; font-weight:800;
                                         color:#0d9488;">{r['issue_id']}</span>
                            <span style="font-family:Manrope,sans-serif; font-size:12px; color:#64748B;">{r['module']}</span>
                        </div>
                        <span style="font-family:Manrope,sans-serif; font-size:11px; color:#94A3B8;
                                     line-height:1.5;">{desc}</span>
                    </div>
                    <span style="font-family:Manrope,sans-serif; font-size:12px; font-weight:800;
                                 color:#000000; white-space:nowrap;">{int(r['reopen_events'])} events</span>
                </div>"""
            card_height = max(300, len(df_rmt) * 44 + 80)

            st.components.v1.html(f"""
            <div style="background:white; border:1px solid #EAECF0; border-radius:12px;
                        padding:20px 22px; box-shadow:0 1px 3px rgba(16,24,40,0.04);
                        font-family:Manrope,sans-serif;">
                <div style="font-size:14px; font-weight:700; color:#0F172A; margin-bottom:3px;">
                    Issues Reopened Multiple Times
                </div>
                <div style="font-size:12px; color:#9CA3AF; font-weight:500; margin-bottom:14px;">
                    Defects flagged for repeated instability.
                </div>
                <div style="border-top:1px solid #F1F5F9;">
                    {rows_html}
                </div>
            </div>
            """, height=card_height, scrolling=False)
        else:
            st.info("No repeatedly-reopened issues found (or module/area column not available).")

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Feature-wise Issue Summary ----
        # ---- Feature-wise Issue Summary (own dedicated filters) ----

        FEATURE_COL = next(
            (c for c in ["feature", "feature_name", "feature_area"] if c in df_issues.columns),
            None
        )

        anchor("engineering-feature-wise-issue-summary")
        st.markdown("<div class='section-header' style='margin-top:26px;'>Feature-wise Issue Summary</div>",
                    unsafe_allow_html=True)

        if FEATURE_COL:
            feat_f1, feat_f2, feat_f3, feat_f4 = st.columns([1.4, 1.4, 1.4, 1.4])

            with feat_f1:
                feature_options = ["All Features"] + sorted(df_issues[FEATURE_COL].dropna().unique().tolist())
                selected_feature_only = st.selectbox("Feature", feature_options, key="feat_only_feature")

            with feat_f2:
                if MODULE_COL:
                    feat_module_options = ["All Modules"] + sorted(df_issues[MODULE_COL].dropna().unique().tolist())
                    selected_feature_module = st.selectbox("Module", feat_module_options, key="feat_only_module")
                else:
                    st.selectbox("Module", ["Column not found"], key="feat_only_module", disabled=True)
                    selected_feature_module = "All Modules"

            with feat_f3:
                if "release_version" in df_issues.columns:
                    feat_release_options = ["All Releases"] + sorted(
                        df_issues["release_version"].dropna().unique().tolist())
                    selected_feature_release = st.selectbox("Release Version", feat_release_options,
                                                            key="feat_only_release")
                else:
                    st.selectbox("Release Version", ["Column not found"], key="feat_only_release", disabled=True)
                    selected_feature_release = "All Releases"

            with feat_f4:
                if "platform" in df_issues.columns:
                    feat_platform_options = ["All Platforms"] + sorted(df_issues["platform"].dropna().unique().tolist())
                    selected_feature_platform = st.selectbox("Platform", feat_platform_options, key="feat_only_platform")
                else:
                    st.selectbox("Platform", ["Column not found"], key="feat_only_platform", disabled=True)
                    selected_feature_platform = "All Platforms"

            # ---- Build the independently-filtered dataset for this chart only ----
            df_feature_filtered = df_issues.copy()

            if selected_feature_only != "All Features":
                df_feature_filtered = df_feature_filtered[df_feature_filtered[FEATURE_COL] == selected_feature_only]

            if MODULE_COL and selected_feature_module != "All Modules":
                df_feature_filtered = df_feature_filtered[df_feature_filtered[MODULE_COL] == selected_feature_module]

            if "release_version" in df_issues.columns and selected_feature_release != "All Releases":
                df_feature_filtered = df_feature_filtered[
                    df_feature_filtered["release_version"] == selected_feature_release]

            if "platform" in df_issues.columns and selected_feature_platform != "All Platforms":
                df_feature_filtered = df_feature_filtered[df_feature_filtered["platform"] == selected_feature_platform]

            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Feature-wise Issue Summary</div>
                <div class="figure-caption">Hover a segment for its severity mix. Filtered independently by Feature, Module, Release, and Platform above.</div>
            """, unsafe_allow_html=True)

            build_status_severity_chart(df_feature_filtered, FEATURE_COL, "Feature")

            st.markdown("</div>", unsafe_allow_html=True)

        else:
            # Fallback: original static chart if no per-issue feature column exists
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Feature-wise Issue Summary</div>
            """, unsafe_allow_html=True)

            df_feature = dd.get_feature_issue_summary()
            if df_feature is not None and not df_feature.empty:
                df_feature = df_feature.sort_values("total_issues", ascending=True)

                fig_feature = px.bar(df_feature, x="total_issues", y="feature", orientation="h")
                fig_feature.update_traces(
                    marker_color="#1D4ED8", marker_line_width=0, marker_cornerradius=4,
                    texttemplate="%{x}", textposition="outside", cliponaxis=False,
                    hovertemplate="Feature: <b>%{y}</b><br>Total Issues: <b>%{x}</b><extra></extra>"
                )
                fig_feature.update_layout(
                    height=400, **CHART_BG, font=FONT, margin=dict(l=12, r=50, t=10, b=30),
                    showlegend=False, hoverlabel=HOVER_LABEL, xaxis_title="Total Issues", yaxis_title=""
                )
                fig_feature.update_xaxes(color="#1E293B", tickfont=dict(color="#1E293B", family="Manrope", size=11),
                                         title_font=dict(color="#1E293B"))
                fig_feature.update_yaxes(color="#1E293B", tickfont=dict(color="#1E293B", family="Manrope", size=11),
                                         title_font=dict(color="#1E293B"))
                st.plotly_chart(fig_feature, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No feature-wise issue data available (no feature column found in the issues dataset).")

            st.markdown("</div>", unsafe_allow_html=True)

        anchor("engineering-defect-lifecycle-registry")
        st.markdown("""
           <div class="chart-card">
               <div class="figure-title">Defect Lifecycle Registry Explorer (Live Issues)</div>
           """, unsafe_allow_html=True)

        df_filtered = df_issues[df_issues["status"].str.lower().isin(["open", "pending"])].copy()
        df_filtered = df_filtered.sort_values("reported_date", ascending=False)

        if df_filtered.empty:
            st.info("No live issues found.")
        else:
            col_th1, col_th2, col_th3, col_th4, col_th5, col_th6 = st.columns([1.5, 3, 1.8, 2, 2, 1.5])
            col_th1.markdown("<span style='font-weight:700; color:#0F172A; font-size:13px;'>Defect ID / Priority</span>",
                             unsafe_allow_html=True)
            col_th2.markdown(
                "<span style='font-weight:700; color:#0F172A; font-size:13px;'>Module & Bug Description</span>",
                unsafe_allow_html=True)
            col_th3.markdown("<span style='font-weight:700; color:#0F172A; font-size:13px;'>Category / Type</span>",
                             unsafe_allow_html=True)
            col_th4.markdown(
                "<span style='font-weight:700; color:#0F172A; font-size:13px;'>Status & UAT Verification</span>",
                unsafe_allow_html=True)
            col_th5.markdown(
                "<span style='font-weight:700; color:#0F172A; font-size:13px;'>Release &amp; Evidence</span>",
                unsafe_allow_html=True)
            col_th6.markdown("<span style='font-weight:700; color:#0F172A; font-size:13px;'>Date Reported</span>",
                             unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0 12px 0; border:none; border-top:1px solid #000000;'>",
                        unsafe_allow_html=True)

            limit_rows = 8
            for index, row in df_filtered.head(limit_rows).iterrows():
                with st.container():
                    c_r1, c_r2, c_r3, c_r4, c_r5, c_r6 = st.columns([1.5, 3, 1.8, 2, 2, 1.5])

                    p_color = "#EF4444" if row['priority'] == "High" else "#F59E0B" if row[
                                                                                           'priority'] == "Medium" else "#6B7280"

                    env_val = str(row.get("environment", "")).strip()
                    is_prod = env_val.lower() == "production"
                    env_badge = (
                        f"<span style='font-size:9px; font-weight:700; color:#DC2626; background:rgba(220,38,38,0.08); "
                        f"border-radius:4px; padding:1px 6px; margin-left:4px;'>🔴 PROD</span>"
                        if is_prod else
                        f"<span style='font-size:9px; font-weight:600; color:#6B7280; background:rgba(107,114,128,0.08); "
                        f"border-radius:4px; padding:1px 6px; margin-left:4px;'>{env_val or 'N/A'}</span>"
                    )

                    c_r1.markdown(f"""
                       <div style="font-family:'Manrope'; font-size:13px;">
                           <span style="font-weight:700; color:#2563EB;">{row['issue_id']}</span><br>
                           <span style="font-size:10px; font-weight:700; color:{p_color}; background:rgba(0,0,0,0.03);
                                        border-radius:4px; padding:2px 6px;">{row['priority']}</span>
                           {env_badge}
                       </div>
                       """, unsafe_allow_html=True)

                    c_r2.markdown(f"""
                       <div style="font-family:'Manrope'; font-size:13px;">
                           <span style="font-weight:700; color:#0F172A;">{row[MODULE_COL] if MODULE_COL and MODULE_COL in row else row.get('module', '')}</span><br>
                           <span style="font-size:11px; color:#4B5563; display:block; overflow:hidden;
                                        text-overflow:ellipsis; white-space:nowrap;">{row['issue_description']}</span>
                       </div>
                       """, unsafe_allow_html=True)

                    c_r3.markdown(f"""
                       <div style="font-family:'Manrope'; font-size:12px; color:#374151;">
                           <span style="font-weight:600;">{row['issue_category']}</span><br>
                           <span style="font-size:10px; color:#6B7280;">{row['issue_type']}</span>
                       </div>
                       """, unsafe_allow_html=True)

                    s_color = "#F59E0B" if str(row['status']).lower() == "pending" else "#EF4444"
                    v_text = "✔️ Verified" if row['uat_verified'] else "⏳ Pending"
                    v_color = "#047857" if row['uat_verified'] else "#6B7280"

                    reopened_raw = row.get("reopened_count", 0)
                    reopened_n = int(reopened_raw) if pd.notna(reopened_raw) else 0
                    reopen_flag = (
                        f"<br><span style='font-size:10px; font-weight:700; color:#DC2626;'>🔁 Reopened {reopened_n}x</span>"
                        if reopened_n > 0 else ""
                    )

                    c_r4.markdown(f"""
                       <div style="font-family:'Manrope'; font-size:12px;">
                           <span style="font-weight:700; color:{s_color};">• {row['status']}</span><br>
                           <span style="font-size:10px; font-weight:600; color:{v_color};">{v_text}</span>
                           {reopen_flag}
                       </div>
                       """, unsafe_allow_html=True)

                    fixed_in = row.get("fixed_in_release_id")
                    fixed_in_display = fixed_in if pd.notna(fixed_in) and str(fixed_in).strip() else "Unscheduled"

                    screenshot_url = row.get("screenshot_url")
                    has_screenshot = pd.notna(screenshot_url) and str(screenshot_url).strip()
                    screenshot_link = (
                        f"<a href='{screenshot_url}' target='_blank' style='font-size:10px; font-weight:700; "
                        f"color:#2563EB; text-decoration:none;'>📷 View screenshot</a>"
                        if has_screenshot else
                        "<span style='font-size:10px; color:#9CA3AF;'>No screenshot</span>"
                    )

                    c_r5.markdown(f"""
                       <div style="font-family:'Manrope'; font-size:11px; color:#374151;">
                           <span style="color:#6B7280;">Fix targeted:</span>
                           <span style="font-weight:700; color:{'#0F172A' if fixed_in_display != 'Unscheduled' else '#9CA3AF'};">{fixed_in_display}</span><br>
                           {screenshot_link}
                       </div>
                       """, unsafe_allow_html=True)

                    reported = pd.to_datetime(row.get('reported_date', '')).strftime('%d %b %Y') if pd.notna(
                        row.get('reported_date')) else 'N/A'
                    c_r6.markdown(f"""
                       <div style="font-family:'Manrope'; font-size:12px; color:#0F172A; font-weight:600;">
                           {reported}
                       </div>
                       """, unsafe_allow_html=True)

                    st.markdown("<hr style='margin:8px 0; border:none; border-top:1px solid #F1F5F9;'>",
                                unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB 4 — PRODUCT USAGE
# ═══════════════════════════════════════════════════════
if product_usage_tab:
    with product_usage_tab:
        show_product_usage()

# ═══════════════════════════════════════════════════════
# TAB — CONTENT ANALYTICS
# ═══════════════════════════════════════════════════════
if content_analytics_tab:
    with content_analytics_tab:
        show_content_usage()

# ═══════════════════════════════════════════════════════
# 🎧 TAB — CUSTOMER SUPPORT
# ═══════════════════════════════════════════════════════
if customer_support_tab:
    with customer_support_tab:
        st.markdown("""
        <div class="eng-hero" style="background: linear-gradient(135deg, #1E293B, #334155); color:white;">
            <div class="eng-hero-title" style="color:white;">🎧 Customer Support Overview</div>
            <div class="eng-hero-sub" style="color:#CBD5E1;">Ticket health, SLA compliance, and the live issue queue</div>
        </div>
        """, unsafe_allow_html=True)

        cs_kpis = get_customer_support_kpis() or {}

        # ---- KPI row 1 ----
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Total Tickets</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('total_tickets', 0)}</span>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Open</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('open_tickets', 0)}</span>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">SLA Breached</span>
                <span style="font-size:28px; font-weight:800; color:#DC2626; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('sla_breached', 0)}</span>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Reopen Rate</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('reopen_rate_pct', 0)}%</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- KPI row 2 ----
        k5, k6, k7, k8 = st.columns(4)
        with k5:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Investigating</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('investigating_tickets', 0)}</span>
            </div>
            """, unsafe_allow_html=True)
        with k6:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Resolved</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('resolved_tickets', 0)}</span>
            </div>
            """, unsafe_allow_html=True)
        with k7:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Avg First Response</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('avg_first_response_hours', 0)}h</span>
            </div>
            """, unsafe_allow_html=True)
        with k8:
            st.markdown(f"""
            <div class="eng-metric-card">
                <span style="font-size:11px; color:#6B7280; font-weight:700; text-transform:uppercase; letter-spacing:0.06em;">Avg Resolution Time</span>
                <span style="font-size:28px; font-weight:800; color:#0F172A; margin-top:6px; letter-spacing:-0.5px; display:block;">{cs_kpis.get('avg_resolution_hours', 0)}h</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Ticket Volume Trend ----
        st.markdown("""
        <div class="chart-card">
            <div class="figure-title">Ticket Volume Trend</div>
            <div class="figure-caption">Created vs. Resolved (team fixed it) vs. Closed (client confirmed) per day &mdash; showing the last 90 days by default, drag the chart to pan through the full history.</div>
        """, unsafe_allow_html=True)

        df_trend = get_daily_ticket_trend()
        if df_trend is not None and not df_trend.empty:
            df_trend = df_trend.copy()
            df_trend["date"] = pd.to_datetime(df_trend["date"])
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=df_trend["date"], y=df_trend["created"], name="Created",
                mode="lines+markers", line=dict(color="#2563EB", width=3, shape="spline"),
                marker=dict(size=6, color="#2563EB", line=dict(color="white", width=2)),
                fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
                hovertemplate="<b>%{x|%d %b}</b><br>Created: <b>%{y}</b><extra></extra>",
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_trend["date"], y=df_trend["resolved"], name="Resolved",
                mode="lines+markers", line=dict(color="#10B981", width=3, shape="spline"),
                marker=dict(size=6, color="#10B981", line=dict(color="white", width=2)),
                hovertemplate="<b>%{x|%d %b}</b><br>Resolved: <b>%{y}</b><extra></extra>",
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_trend["date"], y=df_trend["closed"], name="Closed",
                mode="lines+markers", line=dict(color="#8B5CF6", width=3, shape="spline"),
                marker=dict(size=6, color="#8B5CF6", line=dict(color="white", width=2)),
                hovertemplate="<b>%{x|%d %b}</b><br>Closed: <b>%{y}</b><extra></extra>",
            ))

            default_start = df_trend["date"].max() - pd.Timedelta(days=90)
            default_end = df_trend["date"].max()

            fig_trend.update_layout(
                height=320, **CHART_BG, font=FONT,
                margin=dict(l=40, r=20, t=10, b=40),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, color="#0F172A", family="Manrope")),
                hoverlabel=HOVER_LABEL, hovermode="x unified",
                xaxis_title="Date", yaxis_title="Tickets",
                dragmode="pan",
            )
            fig_trend.update_xaxes(
                showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT,
                range=[default_start, default_end],
            )
            fig_trend.update_yaxes(
                gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT,
                rangemode="tozero",
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})
        else:
            st.info("No ticket volume data available.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Priority / Status / Channel breakdowns (bar charts, not pie) ----
        def _cs_bar_breakdown(df, cat_col, val_col, color, height=260, extra_hover_lines=None):
            """
            extra_hover_lines: optional list of (column_name, label, format) tuples,
            appended to the hover tooltip below the base 'Tickets: N' line.
            format is a Python format spec applied via customdata, e.g. '.1f' or ',.0f'.
            """
            if df is None or df.empty:
                st.info("No data available.")
                return
            df_sorted = df.sort_values(val_col, ascending=True)
            fig = px.bar(df_sorted, x=val_col, y=cat_col, orientation="h")

            hover_template = "<b>%{y}</b><br>Tickets: <b>%{x}</b>"
            customdata = None
            if extra_hover_lines:
                customdata = df_sorted[[c for c, _, _ in extra_hover_lines]]
                for i, (_, label, fmt) in enumerate(extra_hover_lines):
                    hover_template += f"<br>{label}: <b>%{{customdata[{i}]:{fmt}}}</b>"
            hover_template += "<extra></extra>"

            fig.update_traces(
                marker_color=color, marker_line_width=0, marker_cornerradius=4,
                texttemplate="%{x}", textposition="outside", cliponaxis=False,
                customdata=customdata, hovertemplate=hover_template,
            )
            fig.update_layout(
                height=height, bargap=0.35, **CHART_BG, font=FONT,
                margin=dict(l=12, r=50, t=10, b=30),
                showlegend=False, hoverlabel=HOVER_LABEL, hovermode="y",
                xaxis_title="Tickets", yaxis_title="",
            )
            fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, title_font=AXIS_FONT)
            fig.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Priority</div>
                <div class="figure-caption">All tickets, by priority.</div>
            """, unsafe_allow_html=True)
            _cs_bar_breakdown(get_priority_breakdown(), "priority", "count", "#DC2626", extra_hover_lines=[
                ("open_count", "Open/Investigating", ",.0f"), ("closed_count", "Closed", ",.0f"),
            ])
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Status</div>
                <div class="figure-caption">Every distinct status in the data.</div>
            """, unsafe_allow_html=True)
            _cs_bar_breakdown(get_status_breakdown(), "status", "count", BLUE, extra_hover_lines=[
                ("avg_days_in_status", "Avg days in this status", ".1f"),
            ])
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Source Channel</div>
                <div class="figure-caption">Where tickets are coming in from.</div>
            """, unsafe_allow_html=True)
            _cs_bar_breakdown(get_channel_breakdown(), "source_channel", "count", "#8B5CF6", extra_hover_lines=[
                ("avg_resolution_hours", "Avg resolution time (resolved only)", ".1f"),
            ])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Issue Type / Resolution Type / Agent Workload ----
        c4, c5, c6 = st.columns(3)
        with c4:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Issue Type</div>
                <div class="figure-caption">What tickets are about.</div>
            """, unsafe_allow_html=True)
            _cs_bar_breakdown(get_issue_type_breakdown(), "issue_type", "count", "#F59E0B", extra_hover_lines=[
                ("open_count", "Open/Investigating", ",.0f"), ("closed_count", "Closed", ",.0f"),
                ("avg_resolution_hours", "Avg resolution time (resolved only)", ".1f"), ("premium_pct", "From Premium users", ".1f"),
            ])
            st.markdown("</div>", unsafe_allow_html=True)

        with c5:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Resolution Type</div>
                <div class="figure-caption">How resolved tickets were closed out.</div>
            """, unsafe_allow_html=True)
            _cs_bar_breakdown(get_resolution_type_breakdown(), "resolution_type", "count", "#10B981")
            st.markdown("</div>", unsafe_allow_html=True)

        with c6:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Agent Workload</div>
                <div class="figure-caption">Ticket volume per assignee, top 10.</div>
            """, unsafe_allow_html=True)
            df_agents = get_agent_workload()
            if df_agents is not None and not df_agents.empty:
                df_agents_sorted = df_agents.sort_values("total_tickets", ascending=True)
                agent_customdata = df_agents_sorted[["avg_resolution_hours", "sla_breach_rate_pct"]]
                fig_ag = go.Figure()
                fig_ag.add_trace(go.Bar(
                    x=df_agents_sorted["open_tickets"], y=df_agents_sorted["assigned_to"],
                    name="Open", orientation="h", marker_color="#F59E0B",
                    customdata=agent_customdata,
                    hovertemplate="<b>%{y}</b><br>Open: <b>%{x}</b><br>Avg resolution time (resolved only): <b>%{customdata[0]:.1f}h</b><br>SLA breach rate: <b>%{customdata[1]:.1f}%</b><extra></extra>",
                ))
                fig_ag.add_trace(go.Bar(
                    x=df_agents_sorted["investigating_tickets"], y=df_agents_sorted["assigned_to"],
                    name="Investigating", orientation="h", marker_color=BLUE,
                    customdata=agent_customdata,
                    hovertemplate="<b>%{y}</b><br>Investigating: <b>%{x}</b><br>Avg resolution time (resolved only): <b>%{customdata[0]:.1f}h</b><br>SLA breach rate: <b>%{customdata[1]:.1f}%</b><extra></extra>",
                ))
                fig_ag.add_trace(go.Bar(
                    x=df_agents_sorted["closed_tickets"], y=df_agents_sorted["assigned_to"],
                    name="Closed", orientation="h", marker_color="#10B981",
                    customdata=agent_customdata,
                    hovertemplate="<b>%{y}</b><br>Closed: <b>%{x}</b><br>Avg resolution time (resolved only): <b>%{customdata[0]:.1f}h</b><br>SLA breach rate: <b>%{customdata[1]:.1f}%</b><extra></extra>",
                ))
                fig_ag.update_layout(
                    height=260, barmode="stack", **CHART_BG, font=FONT,
                    margin=dict(l=12, r=20, t=10, b=30),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                font=dict(size=10, color="#0F172A", family="Manrope")),
                    hoverlabel=HOVER_LABEL, hovermode="closest",
                    xaxis_title="Tickets", yaxis_title="",
                )
                fig_ag.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
                fig_ag.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
                st.plotly_chart(fig_ag, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No agent assignment data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- VIP Ticket Load + Repeat-Reopened Tickets ----
        c7, c8 = st.columns(2)
        with c7:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">VIP Ticket Load</div>
                <div class="figure-caption">Premium vs Basic, based on each user's latest invoice.</div>
            """, unsafe_allow_html=True)
            vip = get_vip_ticket_load() or {}
            v1, v2 = st.columns(2)
            v1.metric("Premium", f"{vip.get('premium_tickets', 0):,}", f"{vip.get('premium_pct', 0)}% of total", delta_color="off",
                      help=f"Avg resolution time: {vip.get('premium_avg_resolution_hours', 0)}h")
            v2.metric("Basic", f"{vip.get('basic_tickets', 0):,}", f"{vip.get('basic_pct', 0)}% of total", delta_color="off",
                      help=f"Avg resolution time: {vip.get('basic_avg_resolution_hours', 0)}h")
            st.markdown("</div>", unsafe_allow_html=True)

        with c8:
            st.markdown("""
            <div class="chart-card">
                <div class="figure-title">Repeat-Reopened Tickets</div>
                <div class="figure-caption">Reopened more than once — worth a root-cause look.</div>
            """, unsafe_allow_html=True)
            df_repeat = get_repeat_reopened_tickets()
            if df_repeat is not None and not df_repeat.empty:
                for _, rr in df_repeat.head(6).iterrows():
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #F1F5F9;">
                        <span style="font-size:12px; color:#0F172A; font-weight:600;">{html.escape(str(rr.get('ticket_id', '')))} &middot; {html.escape(str(rr.get('title', '')))[:40]}</span>
                        <span style="font-size:12px; color:#DC2626; font-weight:700;">{rr.get('reopened_count', 0)} reopens</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No tickets have been reopened more than once.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Time-to-Resolution Distribution ----
        st.markdown("""
        <div class="chart-card">
            <div class="figure-title">Time-to-Resolution Distribution</div>
            <div class="figure-caption">Hours from ticket creation to resolution, across every resolved ticket — shows the typical case and the long tail, not just the average.</div>
        """, unsafe_allow_html=True)

        df_resolution, res_stats = get_resolution_time_distribution()

        if res_stats["count"] > 0:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Median", f"{res_stats['median_hours']:.1f}h",
                      help="Half of resolved tickets were closed faster than this.")
            m2.metric("P90", f"{res_stats['p90_hours']:.1f}h",
                      help="90% of resolved tickets were closed faster than this.")
            m3.metric("Mean", f"{res_stats['mean_hours']:.1f}h")
            m4.metric("Slowest", f"{res_stats['max_hours']:.1f}h")

            fig_box = go.Figure(go.Box(
                x=df_resolution["resolution_hours"],
                name="Resolution Time",
                marker_color=BLUE,
                boxpoints="outliers",
                hoveron="points",
                customdata=df_resolution[["ticket_id"]],
                hovertemplate="Ticket: <b>%{customdata[0]}</b><br>Hours: <b>%{x:.1f}</b><extra></extra>",
            ))
            fig_box.update_layout(
                height=220, **CHART_BG, font=FONT,
                margin=dict(l=40, r=20, t=20, b=40),
                showlegend=False, hoverlabel=HOVER_LABEL, hovermode="closest",
                xaxis_title="Hours to resolution", yaxis_title="",
            )
            fig_box.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            fig_box.update_yaxes(showgrid=False, showticklabels=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No resolved tickets with both created_at and resolved_at populated yet.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =====================================================
        # TICKET EXPLORER — filterable table + detail drill-down
        # =====================================================
        st.markdown("<div class='section-header'>Ticket Explorer</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#6B7280; font-size:13px; margin-top:-10px; margin-bottom:16px;'>Browse, filter, and drill into individual customer tickets.</p>",
            unsafe_allow_html=True
        )

        df_tickets = get_ticket_explorer()

        if df_tickets is None or df_tickets.empty:
            st.info("No customer issues found.")
        else:
            f1, f2, f3 = st.columns([1.2, 1.2, 2])
            with f1:
                status_options = ["All"] + sorted(df_tickets["status"].dropna().unique().tolist())
                issues_status_filter = st.selectbox("Status", status_options, key="cs_status_filter")
            with f2:
                priority_options = ["All"] + sorted(df_tickets["priority"].dropna().unique().tolist())
                issues_priority_filter = st.selectbox("Priority", priority_options, key="cs_priority_filter")
            with f3:
                issues_search = st.text_input("Search ticket ID, title, or description", key="cs_search")

            df_filtered = df_tickets.copy()
            if issues_status_filter != "All":
                df_filtered = df_filtered[df_filtered["status"] == issues_status_filter]
            if issues_priority_filter != "All":
                df_filtered = df_filtered[df_filtered["priority"] == issues_priority_filter]
            if issues_search:
                q = issues_search.lower()
                df_filtered = df_filtered[
                    df_filtered["ticket_id"].astype(str).str.lower().str.contains(q, na=False) |
                    df_filtered["title"].astype(str).str.lower().str.contains(q, na=False) |
                    df_filtered["description"].astype(str).str.lower().str.contains(q, na=False)
                ]

            df_filtered = df_filtered.sort_values("created_at", ascending=False)

            display_df = df_filtered[[
                "ticket_id", "title", "status", "priority", "source_channel",
                "company_name", "is_premium", "is_sla_breached", "created_at",
            ]].rename(columns={
                "ticket_id": "Ticket ID", "title": "Title", "status": "Status",
                "priority": "Priority", "source_channel": "Channel", "company_name": "Company",
                "is_premium": "Premium", "is_sla_breached": "SLA Breached", "created_at": "Created",
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=420)
            st.caption(f"Showing all {len(df_filtered):,} matching ticket(s) of {len(df_tickets):,} total.")

            # ---- Ticket detail drill-down ----
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='section-header'>Ticket Detail</div>", unsafe_allow_html=True)

            ticket_ids = df_filtered["ticket_id"].tolist()
            if ticket_ids:
                selected_ticket_id = st.selectbox("Select a ticket to inspect", ticket_ids, key="cs_detail_select")
                ticket_row = df_filtered[df_filtered["ticket_id"] == selected_ticket_id].iloc[0]

                d1, d2 = st.columns([1.5, 1], gap="large")

                with d1:
                    st.markdown(f"""
                    <div class="chart-card">
                        <div class="figure-title">{html.escape(str(ticket_row.get('title', '')))}</div>
                        <div class="figure-caption">{html.escape(str(ticket_row.get('ticket_id', '')))} &middot; {html.escape(str(ticket_row.get('status', '')))} &middot; {html.escape(str(ticket_row.get('priority', '')))}</div>
                        <div style="font-size:13px; color:#374151; line-height:1.6; background:#F8FAFC;
                                    border:1px solid #E5E7EB; border-radius:10px; padding:14px 16px; margin-bottom:14px;">
                            {html.escape(str(ticket_row.get('description', '') or ''))}
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<div style='font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;'>Activity Log</div>", unsafe_allow_html=True)
                    df_activity = get_ticket_activity_log(selected_ticket_id)
                    if df_activity is not None and not df_activity.empty:
                        for _, act in df_activity.iterrows():
                            created_str = pd.to_datetime(act.get('created_at')).strftime('%d %b %Y %H:%M') if pd.notna(act.get('created_at')) else ''
                            st.markdown(f"""
                            <div style="border-left:2px solid #E5E7EB; padding:6px 0 6px 12px; margin-bottom:8px;">
                                <span style="font-size:12px; font-weight:700; color:#0F172A;">{html.escape(str(act.get('activity_type', '') or ''))}</span>
                                <span style="font-size:11px; color:#9CA3AF; float:right;">{created_str}</span><br>
                                <span style="font-size:12px; color:#4B5563;">{html.escape(str(act.get('activity_summary', '') or act.get('notes', '') or ''))}</span><br>
                                <span style="font-size:11px; color:#6B7280;">by {html.escape(str(act.get('created_by', 'Unknown') or 'Unknown'))}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No activity logged yet for this ticket.")

                    st.markdown("</div>", unsafe_allow_html=True)

                with d2:
                    st.markdown("""
                    <div class="chart-card">
                        <div class="figure-title">Reporting User</div>
                    """, unsafe_allow_html=True)
                    premium_tag = ' <span style="color:#D97706; font-weight:700;">(Premium)</span>' if ticket_row.get('is_premium') else ''
                    st.markdown(f"""
                    <div style="font-size:13px; color:#0F172A; font-weight:700;">{html.escape(str(ticket_row.get('user_name', '') or ''))}</div>
                    <div style="font-size:12px; color:#6B7280; margin-bottom:10px;">{html.escape(str(ticket_row.get('company_name', '') or ''))}</div>
                    <div style="font-size:12px; color:#374151; line-height:1.8;">
                        Email: {html.escape(str(ticket_row.get('email_address', 'N/A') or 'N/A'))}<br>
                        Phone: {html.escape(str(ticket_row.get('mobile_number', 'N/A') or 'N/A'))}<br>
                        Plan: {html.escape(str(ticket_row.get('current_plan', 'N/A') or 'N/A'))}{premium_tag}
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("""
                    <div class="chart-card">
                        <div class="figure-title">Linked Engineering Issues</div>
                    """, unsafe_allow_html=True)
                    df_mapping = get_ticket_issue_mapping(selected_ticket_id)
                    if df_mapping is not None and not df_mapping.empty:
                        for _, m in df_mapping.iterrows():
                            st.markdown(f"""
                            <div style="font-size:12px; color:#374151; padding:6px 0; border-bottom:1px solid #F1F5F9;">
                                <span style="font-weight:700; color:#7C3AED;">{html.escape(str(m.get('issue_id', '') or ''))}</span> &mdash; {html.escape(str(m.get('relationship_type', '') or ''))}<br>
                                <span style="font-size:11px; color:#9CA3AF;">{html.escape(str(m.get('notes', '') or ''))}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No linked engineering issues.")
                    st.markdown("</div>", unsafe_allow_html=True)

if user_360_tab:
    with user_360_tab:
        show_user_360()