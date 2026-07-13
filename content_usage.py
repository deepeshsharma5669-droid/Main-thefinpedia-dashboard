import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from dashboard_data import supabase

# ============================================================
# 🎨 DESIGN TOKENS — duplicated from product_usage.py on purpose,
# same reasoning: this module must not import from app.py or
# product_usage.py, so it can never accidentally affect either
# if edited independently.
# ============================================================
BLUE = "#2563EB"
BLUE_LIGHT = "rgba(37,99,235,0.07)"
GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#8B5CF6"
SLATE = "#94A3B8"
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


def chart_card_open(title, caption):
    st.markdown(f"""
    <div class="chart-card">
        <div class="figure-title">{title}</div>
        <div class="figure-caption">{caption}</div>
    """, unsafe_allow_html=True)


def chart_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def style_bar_chart(fig, height=320, x_suffix="", orientation="h"):
    is_h = orientation == "h"
    for trace in fig.data:
        trace.update(
            marker_line_width=0,
            marker_cornerradius=4,
            texttemplate=f"%{{x:,.0f}}{x_suffix}" if is_h else f"%{{y:,.0f}}{x_suffix}",
            textposition="outside",
            textfont=dict(size=11, color="#374151"),
            cliponaxis=False,
        )
    fig.update_layout(
        height=height,
        bargap=0.35,
        **CHART_BG,
        font=FONT,
        margin=dict(l=12, r=50, t=10, b=30) if is_h else dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        hoverlabel=HOVER_LABEL,
        hovermode="y" if is_h else "x",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=not is_h, title_font=AXIS_FONT, tickfont=TICK_FONT)
    fig.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
    return fig


# ============================================================
# 📊 DATA LAYER — thin wrappers over the content_* Supabase views
# ============================================================

def _df(view_name):
    page_size = 1000
    start = 0
    all_rows = []
    while True:
        result = supabase.table(view_name).select("*").range(start, start + page_size - 1).execute()
        batch = result.data or []
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return pd.DataFrame(all_rows)


def get_content_kpis():
    """content_kpis view -> single row: total_content, unique_users, total_engagement,
    downloads, saves, likes, shares, cobrands, premium_engagement, free_engagement,
    avg_engagement_per_content, avg_engagement_per_user. Scoped to feature_type='Content'."""
    return supabase.table("content_kpis").select("*").single().execute().data


def get_content_daily_trend():
    """content_daily_trend view -> date, total_engagement, unique_users, unique_content,
    downloads, saves, likes, shares, cobrands, premium_engagement, free_engagement."""
    return _df("content_daily_trend")


def get_content_type_usage():
    """content_type_usage view -> content_type, total_content, unique_users, total_engagement,
    downloads, saves, likes, shares, cobrands, premium_engagement, free_engagement."""
    return _df("content_type_usage")


def get_content_engagement_distribution():
    """content_engagement_distribution view -> one row per content item: content_id,
    content_title, content_type, language_name, is_premium_content, downloads, saves,
    likes, shares, cobrands, total_engagement, unique_users."""
    return _df("content_engagement_distribution")


# ============================================================
# 📝 MAIN ENTRY POINT
# ============================================================

def show_content_usage():
    st.markdown("<div class='section-header'>Content Analytics</div>", unsafe_allow_html=True)
    st.caption("Scoped to feature_type = 'Content' only — Calculator and Post Planner activity are never counted here.")
    st.markdown("<br>", unsafe_allow_html=True)

    kpis = get_content_kpis() or {}

    # --------------------------------------------------------
    # KPI STRIP
    # --------------------------------------------------------
    r1 = st.columns(4)
    r1[0].metric("Total Content", f"{kpis.get('total_content', 0):,}",
                 help="Distinct content items with at least one Content-feature interaction.")
    r1[1].metric("Unique Users", f"{kpis.get('unique_users', 0):,}")
    r1[2].metric("Total Engagement", f"{kpis.get('total_engagement', 0):,}",
                 help="Every Content-feature event: Downloaded + Saved + Liked + Shared + Cobrand.")
    r1[3].metric("Avg Engagement/Content", f"{kpis.get('avg_engagement_per_content', 0):,.2f}")

    r2 = st.columns(4)
    r2[0].metric("Avg Engagement/User", f"{kpis.get('avg_engagement_per_user', 0):,.2f}")
    r2[1].metric("Downloads", f"{kpis.get('downloads', 0):,}")
    r2[2].metric("Saves", f"{kpis.get('saves', 0):,}")
    r2[3].metric("Likes", f"{kpis.get('likes', 0):,}")

    r3 = st.columns(4)
    r3[0].metric("Shares", f"{kpis.get('shares', 0):,}")
    r3[1].metric("Cobrands", f"{kpis.get('cobrands', 0):,}")
    total_pf = (kpis.get('premium_engagement', 0) or 0) + (kpis.get('free_engagement', 0) or 0)
    premium_pct = round(100 * (kpis.get('premium_engagement', 0) or 0) / total_pf, 1) if total_pf else 0.0
    r3[2].empty()
    r3[3].empty()

    st.markdown(
        insight_box(
            f"<b>{premium_pct}%</b> of all Content engagement is on Premium content "
            f"(matches Product Usage's Premium vs Basic Content split, shown there in detail).",
            title="Content Overview",
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # DAILY TREND
    # --------------------------------------------------------
    chart_card_open("Daily Engagement Trend", "Total engagement and unique active content users per day.")
    daily = get_content_daily_trend()
    if daily is not None and not daily.empty:
        daily = daily.copy()
        daily["date"] = pd.to_datetime(daily["date"])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily["date"], y=daily["total_engagement"], name="Engagement",
            marker_color=GREEN, marker_line_width=0, opacity=0.55,
            yaxis="y2",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Engagement: <b>%{y}</b><extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["date"], y=daily["unique_users"], name="Active Content Users",
            mode="lines", line=dict(color=BLUE, width=2.5, shape="spline"),
            yaxis="y1",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Active Users: <b>%{y}</b><extra></extra>",
        ))
        fig.update_layout(
            height=320, **CHART_BG, font=FONT,
            margin=dict(l=40, r=40, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11, color="#0F172A")),
            hoverlabel=HOVER_LABEL, hovermode="x unified",
            bargap=0.15,
            yaxis=dict(title=dict(text="Active Users", font=dict(color=BLUE)), tickfont=dict(color=BLUE),
                       gridcolor=GRID_COLOR, zeroline=False),
            yaxis2=dict(title=dict(text="Engagement", font=dict(color=GREEN)), tickfont=dict(color=GREEN),
                        overlaying="y", side="right", showgrid=False, zeroline=False),
        )
        fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No daily trend data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # ENGAGEMENT BY EVENT TYPE, OVER TIME
    # --------------------------------------------------------
    chart_card_open("Engagement by Event Type Over Time", "Downloads, Saves, Likes, Shares, and Cobrands per day.")
    if daily is not None and not daily.empty:
        fig2 = go.Figure()
        for col, label, color in [
            ("downloads", "Downloads", BLUE), ("saves", "Saves", GREEN),
            ("likes", "Likes", RED), ("shares", "Shares", PURPLE), ("cobrands", "Cobrand", AMBER),
        ]:
            fig2.add_trace(go.Scatter(
                x=daily["date"], y=daily[col], name=label, mode="lines",
                line=dict(color=color, width=2, shape="spline"),
                hovertemplate=f"<b>%{{x|%d %b %Y}}</b><br>{label}: <b>%{{y}}</b><extra></extra>",
            ))
        fig2.update_layout(
            height=300, **CHART_BG, font=FONT,
            margin=dict(l=40, r=20, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=10, color="#0F172A")),
            hoverlabel=HOVER_LABEL, hovermode="x unified",
            xaxis_title="Date", yaxis_title="Events",
        )
        fig2.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig2.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No event-type trend data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # PREMIUM VS FREE, OVER TIME
    # --------------------------------------------------------
    chart_card_open("Premium vs Free Engagement Over Time", "Stacked daily split of Content engagement by tier.")
    if daily is not None and not daily.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=daily["date"], y=daily["premium_engagement"], name="Premium",
            marker_color=AMBER, marker_line_width=0,
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Premium: <b>%{y}</b><extra></extra>",
        ))
        fig3.add_trace(go.Bar(
            x=daily["date"], y=daily["free_engagement"], name="Basic",
            marker_color=GREEN, marker_line_width=0,
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Basic: <b>%{y}</b><extra></extra>",
        ))
        fig3.update_layout(
            barmode="stack", height=280, **CHART_BG, font=FONT,
            margin=dict(l=40, r=20, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11, color="#0F172A")),
            hoverlabel=HOVER_LABEL, hovermode="x unified",
            xaxis_title="Date", yaxis_title="Engagement",
        )
        fig3.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig3.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No premium/free trend data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CONTENT LIBRARY SIZE BY TYPE
    # (genuinely new vs Product Usage's Content Usage chart —
    # that one shows engagement/interactions per type, this shows
    # how many DISTINCT content items exist per type, plus how
    # efficiently each type's library converts to engagement)
    # --------------------------------------------------------
    chart_card_open("Content Library Size by Type", "How many distinct content items exist per type, and how much engagement each piece drives on average.")
    df_type = get_content_type_usage()
    if df_type is not None and not df_type.empty:
        df_type = df_type.copy()
        df_type["avg_engagement_per_item"] = (df_type["total_engagement"] / df_type["total_content"].replace(0, np.nan)).round(1)
        df_type_sorted = df_type.sort_values("total_content", ascending=True)
        fig4 = px.bar(df_type_sorted, x="total_content", y="content_type", orientation="h")
        fig4.update_traces(
            marker_color=PURPLE,
            customdata=df_type_sorted[["total_engagement", "avg_engagement_per_item", "unique_users"]],
            hovertemplate=(
                "<b>%{y}</b><br>Content Items: %{x}<br>Total Engagement: %{customdata[0]:,}"
                "<br>Avg Engagement/Item: %{customdata[1]:,.1f}<br>Unique Users: %{customdata[2]:,}<extra></extra>"
            ),
        )
        fig4 = style_bar_chart(fig4, height=280)
        fig4.update_layout(xaxis_title="Distinct Content Items", yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No content type data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # LANGUAGE BREAKDOWN
    # --------------------------------------------------------
    chart_card_open("Engagement by Language", "Total engagement and content library size per language.")
    df_dist = get_content_engagement_distribution()
    if df_dist is not None and not df_dist.empty and "language_name" in df_dist.columns:
        df_lang = (
            df_dist.groupby("language_name")
            .agg(total_engagement=("total_engagement", "sum"), content_count=("content_id", "nunique"))
            .reset_index()
        )
        df_lang["avg_engagement_per_item"] = (df_lang["total_engagement"] / df_lang["content_count"].replace(0, np.nan)).round(1)
        df_lang_sorted = df_lang.sort_values("total_engagement", ascending=True)
        fig5 = px.bar(df_lang_sorted, x="total_engagement", y="language_name", orientation="h")
        fig5.update_traces(
            marker_color=BLUE,
            customdata=df_lang_sorted[["content_count", "avg_engagement_per_item"]],
            hovertemplate=(
                "<b>%{y}</b><br>Total Engagement: %{x:,}<br>Content Items: %{customdata[0]:,}"
                "<br>Avg Engagement/Item: %{customdata[1]:,.1f}<extra></extra>"
            ),
        )
        fig5 = style_bar_chart(fig5, height=260)
        fig5.update_layout(xaxis_title="Total Engagement", yaxis_title="")
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No language data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TOP / BOTTOM PERFORMING CONTENT
    # --------------------------------------------------------
    chart_card_open("Top & Bottom Performing Content", "Individual content items ranked by total engagement.")
    if df_dist is not None and not df_dist.empty:
        rank_choice = st.radio(
            "View", ["Top 10", "Bottom 10"], horizontal=True,
            label_visibility="collapsed", key="content_rank_toggle",
        )
        df_ranked = df_dist.sort_values("total_engagement", ascending=(rank_choice == "Bottom 10"))
        df_display = df_ranked.head(10)[[
            "content_title", "content_type", "language_name", "is_premium_content",
            "total_engagement", "unique_users", "downloads", "saves", "likes", "shares", "cobrands",
        ]].rename(columns={
            "content_title": "Title", "content_type": "Type", "language_name": "Language",
            "is_premium_content": "Premium", "total_engagement": "Total Engagement",
            "unique_users": "Unique Users", "downloads": "Downloads", "saves": "Saves",
            "likes": "Likes", "shares": "Shares", "cobrands": "Cobrand",
        })
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=380)
    else:
        st.info("No content-level data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # ADVANCED ANALYTICS — Histogram, Lorenz, Pareto, Zipf
    # --------------------------------------------------------
    st.markdown("<div class='section-header'>Advanced Analytics</div>", unsafe_allow_html=True)
    st.caption("Statistical view of how engagement is distributed across individual content items — not shown anywhere else in the dashboard.")
    st.markdown("<br>", unsafe_allow_html=True)

    if df_dist is None or df_dist.empty:
        st.info("No content-level data available for advanced analytics.")
        return

    values = df_dist["total_engagement"].sort_values(ascending=False).reset_index(drop=True)
    n = len(values)

    adv_tab1, adv_tab2, adv_tab3, adv_tab4 = st.tabs(["Histogram", "Lorenz Curve", "Pareto Analysis", "Rank (Zipf) Curve"])

    with adv_tab1:
        chart_card_open("Engagement Distribution", "How many content items fall into each engagement-count range.")
        fig_h = go.Figure(go.Histogram(
            x=values, marker_color=BLUE, marker_line_width=0,
            hovertemplate="Range: <b>%{x}</b><br>Content Items: <b>%{y}</b><extra></extra>",
        ))
        fig_h.update_layout(
            height=320, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40),
            showlegend=False, hoverlabel=HOVER_LABEL,
            xaxis_title="Total Engagement", yaxis_title="Content Items", bargap=0.05,
        )
        fig_h.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig_h.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})
        chart_card_close()

    with adv_tab2:
        chart_card_open("Lorenz Curve", "Cumulative share of engagement captured by the bottom X% of content, sorted ascending. The further this bends below the diagonal, the more concentrated engagement is among a few top performers.")
        sorted_asc = values.sort_values(ascending=True).reset_index(drop=True)
        cum_engagement = sorted_asc.cumsum() / sorted_asc.sum()
        cum_pct_content = np.arange(1, n + 1) / n
        fig_l = go.Figure()
        fig_l.add_trace(go.Scatter(
            x=cum_pct_content * 100, y=cum_engagement * 100, mode="lines",
            line=dict(color=BLUE, width=3), fill="tozeroy", fillcolor=BLUE_LIGHT,
            name="Actual", hovertemplate="Bottom %{x:.0f}% of content<br>= %{y:.1f}% of engagement<extra></extra>",
        ))
        fig_l.add_trace(go.Scatter(
            x=[0, 100], y=[0, 100], mode="lines", line=dict(color=SLATE, width=1.5, dash="dash"),
            name="Perfect Equality", hoverinfo="skip",
        ))
        fig_l.update_layout(
            height=380, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11, color="#0F172A")),
            hoverlabel=HOVER_LABEL,
            xaxis_title="Cumulative % of Content", yaxis_title="Cumulative % of Engagement",
        )
        fig_l.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT, range=[0, 100])
        fig_l.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT, range=[0, 100])
        st.plotly_chart(fig_l, use_container_width=True, config={"displayModeBar": False})

        # Manual trapezoidal integration instead of np.trapz/np.trapezoid —
        # avoids depending on either name, since np.trapz was removed in
        # NumPy 2.0 (renamed to np.trapezoid), and this way it works on
        # any NumPy version without checking which one is installed.
        area_under_curve = np.sum(
            (cum_engagement.values[1:] + cum_engagement.values[:-1]) / 2
            * np.diff(cum_pct_content)
        )
        gini = 1 - 2 * area_under_curve
        st.markdown(
            insight_box(
                f"Gini coefficient: <b>{gini:.2f}</b> (0 = perfectly even, 1 = fully concentrated in one item). "
                f"A higher number means engagement leans heavily on a small set of top performers.",
                title="Concentration Insight",
            ),
            unsafe_allow_html=True,
        )
        chart_card_close()

    with adv_tab3:
        chart_card_open("Pareto Analysis", "Content sorted by engagement (descending) with a cumulative % line — shows what share of your content drives most of the engagement.")
        cum_pct_engagement = values.cumsum() / values.sum() * 100
        rank_pct = np.arange(1, n + 1) / n * 100
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(
            x=rank_pct, y=values, name="Engagement", marker_color=BLUE, marker_line_width=0,
            hovertemplate="Rank: top %{x:.0f}%<br>Engagement: %{y}<extra></extra>",
        ))
        fig_p.add_trace(go.Scatter(
            x=rank_pct, y=cum_pct_engagement, name="Cumulative %", mode="lines",
            line=dict(color=RED, width=2.5), yaxis="y2",
            hovertemplate="Top %{x:.0f}% of content<br>= %{y:.1f}% of engagement<extra></extra>",
        ))
        eighty_idx = int(np.searchsorted(cum_pct_engagement.values, 80))
        eighty_pct_content = round((eighty_idx + 1) / n * 100, 1) if eighty_idx < n else 100.0
        fig_p.update_layout(
            height=380, **CHART_BG, font=FONT, margin=dict(l=40, r=40, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11, color="#0F172A")),
            hoverlabel=HOVER_LABEL, hovermode="x unified",
            xaxis_title="Content, ranked by engagement (top X%)",
            yaxis=dict(title="Engagement", gridcolor=GRID_COLOR, zeroline=False),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 100], showgrid=False),
        )
        fig_p.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            insight_box(
                f"The top <b>{eighty_pct_content}%</b> of content drives <b>80%</b> of all engagement.",
                title="Pareto Insight",
            ),
            unsafe_allow_html=True,
        )
        chart_card_close()

    with adv_tab4:
        chart_card_open("Rank (Zipf) Curve", "Log-log plot of engagement vs. rank — a straight line here suggests content popularity follows a power-law distribution, common in real-world engagement data.")
        ranks = np.arange(1, n + 1)
        fig_z = go.Figure(go.Scatter(
            x=ranks, y=values, mode="markers", marker=dict(color=BLUE, size=5, opacity=0.7),
            hovertemplate="Rank: %{x}<br>Engagement: %{y}<extra></extra>",
        ))
        fig_z.update_layout(
            height=380, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40),
            showlegend=False, hoverlabel=HOVER_LABEL,
            xaxis=dict(title="Rank", type="log", gridcolor=GRID_COLOR),
            yaxis=dict(title="Engagement", type="log", gridcolor=GRID_COLOR),
        )
        fig_z.update_xaxes(title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig_z.update_yaxes(title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig_z, use_container_width=True, config={"displayModeBar": False})
        chart_card_close()