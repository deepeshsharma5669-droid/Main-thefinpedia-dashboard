import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import dashboard_data as dd
from content_usage import show_content_usage

# ============================================================
# 🎨 DESIGN TOKENS — duplicated from app.py on purpose.
# product_usage.py must not `import` from app.py (app.py runs
# st.set_page_config() and top-level Streamlit calls at import
# time, which would break/duplicate on import). Keeping a local
# copy here means this tab can't accidentally affect Revenue,
# Subscriptions, or Engineering if it's ever edited.
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

PLATFORM_COLORS = {
    "Instagram": "#2563EB",
    "Facebook": "#93C5FD",
    "LinkedIn": "#0A66C2",
    "WhatsApp": "#F9A8D4",
    "Twitter": "#10B981",
    "Email": "#F59E0B",
}


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
        margin=dict(l=16, r=70, t=10, b=40),
        showlegend=False,
        hoverlabel=HOVER_LABEL,
        hovermode="y" if is_h else "x",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=not is_h, title_font=AXIS_FONT, tickfont=TICK_FONT)
    fig.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
    return fig


def _trend(current, previous, suffix="vs last month", small_base_threshold=10):
    """Returns a signed relative-% delta string for st.metric (e.g. '+12.3% vs last month'), or
    None if previous is missing/zero. Use for count metrics (users, activities, posts).
    Streamlit auto-colors based on the +/- sign; pass delta_color='inverse' at the call site
    for metrics where a decrease is the good direction (e.g. Failed, Pending, Dormant).
    If the previous period's value is below small_base_threshold, a tiny denominator can produce
    a wild, meaningless percentage (e.g. 1 -> 39 reads as +3800%) — in that case this returns
    the raw count change instead (e.g. '+38 vs last month')."""
    if current is None or previous is None:
        return None
    if previous == 0:
        return None
    if previous < small_base_threshold:
        diff = current - previous
        return f"{diff:+,.0f} {suffix}"
    pct = round((current - previous) / previous * 100, 1)
    return f"{pct:+.1f}% {suffix}"


def _trend_points(current, previous, suffix="vs last month"):
    """Returns a signed percentage-POINT delta string (e.g. '+3.2 pts vs last month'), or None
    if either value is missing. Use for metrics that are ALREADY a percentage/rate (engagement
    rate, stickiness, publishing success, automation rate) — a relative-% of a % is confusing,
    so this shows the plain point difference instead."""
    if current is None or previous is None:
        return None
    diff = round(current - previous, 1)
    return f"{diff:+.1f} pts {suffix}"


def anchor(name):
    """Duplicated from app.py's helper — invisible marker div for the nav rail's scroll-to
    links. Offset -70px so the section lands clear of the sticky header when scrolled to."""
    st.markdown(f'<div id="{name}" style="position:relative; top:-70px;"></div>', unsafe_allow_html=True)


def show_product_usage():
    anchor("product-usage-overview")
    st.markdown("<div class='section-header'>Product Usage Overview</div>", unsafe_allow_html=True)

    planner_label = st.radio(
        "Post Planner", ["With Post Planner", "Without Post Planner"], horizontal=True,
        label_visibility="collapsed", key="product_usage_planner_toggle",
    )
    include_post_planner = planner_label == "With Post Planner"
    st.caption("Applies to everything below except Feature Usage (Post Planner always shown), and Campaign Performance / Platform Usage (unrelated \u2014 those come from scheduled posts, not activity).")
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # KPI STRIP
    # --------------------------------------------------------
    kpis = dd.get_product_usage_kpis(include_post_planner=include_post_planner) or {}

    mau = kpis.get("mau", 0) or 0
    premium_active = kpis.get("premium_active", 0) or 0
    basic_active = kpis.get("basic_active", 0) or 0
    premium_active_pct = round(premium_active / mau * 100, 1) if mau else 0.0
    basic_active_pct = round(basic_active / mau * 100, 1) if mau else 0.0

    r1 = st.columns(4)
    r1[0].metric("Total Users", f"{kpis.get('total_users', 0):,}",
                 _trend(kpis.get('total_users'), kpis.get('total_users_prev')))
    r1[1].metric("DAU", f"{kpis.get('dau', 0):,}",
                 _trend(kpis.get('dau'), kpis.get('dau_prev'), "vs 7 days ago"))
    r1[2].metric("WAU", f"{kpis.get('wau', 0):,}",
                 _trend(kpis.get('wau'), kpis.get('wau_prev'), "vs last week"))
    r1[3].metric("MAU", f"{mau:,}", _trend(mau, kpis.get('mau_prev')),
                 help="Users with at least one activity event in the last 30 days. This is also the Active User / Premium-Basic Active cohort.")

    r2 = st.columns(4)
    r2[0].metric("Premium Active", f"{premium_active:,}",
                 _trend(premium_active, kpis.get('premium_active_prev')),
                 help="MAU users with a current Silver/Gold/Platinum/Diamond plan invoice.")
    r2[1].metric("Basic Active", f"{basic_active:,}",
                 _trend(basic_active, kpis.get('basic_active_prev')))
    r2[2].metric("Total Activities", f"{kpis.get('total_activities', 0):,}",
                 _trend(kpis.get('total_activities'), kpis.get('total_activities_prev')),
                 help="All activity events in the last 30 days (platform-wide, not just MAU).")
    r2[3].metric("Avg Actions/User", f"{kpis.get('avg_actions_per_user', 0):,}",
                 _trend(kpis.get('avg_actions_per_user'), kpis.get('avg_actions_per_user_prev')))

    engagement_trend = _trend_points(kpis.get('engagement_rate'), kpis.get('engagement_rate_prev'))
    stickiness_trend = _trend_points(kpis.get('stickiness'), kpis.get('stickiness_prev'), "vs 7 days ago")
    st.markdown(
        insight_box(
            f"{kpis.get('engagement_rate', 0)}% engagement rate"
            f"{' (' + engagement_trend + ')' if engagement_trend else ''} &nbsp;·&nbsp; "
            f"{kpis.get('stickiness', 0)}% stickiness (DAU/MAU)"
            f"{' (' + stickiness_trend + ')' if stickiness_trend else ''} &nbsp;·&nbsp; "
            f"{premium_active_pct}% Premium Active Users &nbsp;·&nbsp; "
            f"{basic_active_pct}% Basic Active Users",
            title="Product Overview",
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # DAILY ACTIVITY TREND
    # --------------------------------------------------------
    anchor("product-usage-daily-trend")
    chart_card_open("Daily Activity Trend", "Daily active users and overall platform activities (excludes Post Planner).")

    daily = dd.get_daily_activity_trend(include_post_planner=include_post_planner)
    if daily is not None and not daily.empty:
        daily = daily.copy()
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.sort_values("date")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily["date"], y=daily["activities"],
            name="Activities",
            marker_color=GREEN, marker_line_width=0, opacity=0.55,
            yaxis="y2",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Activities: <b>%{y}</b><extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=daily["date"], y=daily["active_users"],
            name="Daily Active Users", mode="lines",
            line=dict(color=BLUE, width=2.5, shape="spline"),
            yaxis="y1",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Active Users: <b>%{y}</b><extra></extra>",
        ))
        fig.update_layout(
            height=320,
            **CHART_BG,
            font=FONT,
            margin=dict(l=40, r=40, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11, color="#0F172A")),
            hoverlabel=HOVER_LABEL,
            hovermode="x unified",
            bargap=0.15,
            yaxis=dict(
                title=dict(text="Active Users", font=dict(color=BLUE)),
                tickfont=dict(color=BLUE),
                gridcolor=GRID_COLOR, zeroline=False,
            ),
            yaxis2=dict(
                title=dict(text="Activities", font=dict(color=GREEN)),
                tickfont=dict(color=GREEN),
                overlaying="y", side="right",
                showgrid=False, zeroline=False,
            ),
        )
        fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        peak = daily.loc[daily["activities"].idxmax()]
        st.markdown(
            insight_box(
                f"Peak activity occurred on <b>{peak['date'].strftime('%d %b %Y')}</b> with "
                f"<b>{int(peak['active_users'])}</b> active users generating "
                f"<b>{int(peak['activities'])}</b> activities.",
                title="Trend Insight",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No activity data available for this period.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # FEATURE USAGE  +  CONTENT USAGE
    # --------------------------------------------------------
    left, right = st.columns(2)

    with left:
        anchor("product-usage-feature-usage")
        chart_card_open("Feature Usage", "Top product features by adoption.")
        df_feat = dd.get_feature_usage()
        if df_feat is not None and not df_feat.empty:
            df_feat_sorted = df_feat.sort_values("events", ascending=True)

            df_event_for_content = dd.get_event_usage()
            content_breakdown_lines = ""
            if df_event_for_content is not None and not df_event_for_content.empty:
                df_event_sorted_desc = df_event_for_content.sort_values("events", ascending=False)
                content_breakdown_lines = "<br>".join(
                    f"{row['event_type']}: {row['events']:,}" for _, row in df_event_sorted_desc.iterrows()
                )

            hover_texts = []
            for _, row in df_feat_sorted.iterrows():
                base = f"<b>{row['feature_type']}</b><br>Events: {row['events']:,}<br>Unique Users: {row['unique_users']:,}"
                if row["feature_type"] == "Content" and content_breakdown_lines:
                    base += f"<br><br>By event type:<br>{content_breakdown_lines}"
                hover_texts.append(base)

            fig = px.bar(df_feat_sorted, x="events", y="feature_type", orientation="h")
            fig.update_traces(
                marker_color=BLUE,
                text=hover_texts,
                hovertemplate="%{text}<extra></extra>",
            )
            fig = style_bar_chart(fig, height=280)
            fig.update_layout(xaxis_title="Total Events", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            top = df_feat.sort_values("events", ascending=False).iloc[0]
            st.markdown(
                insight_box(
                    f"<b>{top['feature_type']}</b> is the most used feature with "
                    f"<b>{top['events']:,}</b> events from <b>{top['unique_users']:,}</b> users.",
                    title="Feature Insight",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.info("No feature usage data available.")
        chart_card_close()

    with right:
        anchor("product-usage-content-usage")
        chart_card_open("Content Usage", "Top content formats by interaction, split by Premium vs Basic.")
        df_content = dd.get_content_usage(include_post_planner=include_post_planner)
        if df_content is not None and not df_content.empty:
            df_content_sorted = df_content.sort_values("interactions", ascending=True)

            df_content_events = dd.get_content_event_breakdown()
            event_lines_by_content = {}
            if df_content_events is not None and not df_content_events.empty:
                for content_type_val, group in df_content_events.groupby("content_type"):
                    group_sorted = group.sort_values("events", ascending=False)
                    event_lines_by_content[content_type_val] = "<br>".join(
                        f"{row['event_type']}: {row['events']:,}" for _, row in group_sorted.iterrows()
                    )

            hover_texts = []
            for _, row in df_content_sorted.iterrows():
                base = (
                    f"<b>{row['content_type']}</b><br>Interactions: {row['interactions']:,}<br>Unique Users: {row['unique_users']:,}"
                    f"<br>Premium: {row['premium_engagement']:,}<br>Basic: {row['free_engagement']:,}"
                )
                breakdown = event_lines_by_content.get(row["content_type"])
                if breakdown:
                    base += f"<br><br>By event type:<br>{breakdown}"
                hover_texts.append(base)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_content_sorted["premium_engagement"], y=df_content_sorted["content_type"],
                name="Premium", orientation="h", marker_color=AMBER,
                text=hover_texts, hovertemplate="%{text}<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                x=df_content_sorted["free_engagement"], y=df_content_sorted["content_type"],
                name="Basic", orientation="h", marker_color=GREEN,
                text=hover_texts, hovertemplate="%{text}<extra></extra>",
            ))
            fig.update_layout(
                barmode="stack", height=280, **CHART_BG, font=FONT,
                margin=dict(l=12, r=20, t=10, b=30),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, color="#0F172A")),
                hoverlabel=HOVER_LABEL, hovermode="closest",
                xaxis_title="Interactions", yaxis_title="",
            )
            fig.update_xaxes(showgrid=False, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            fig.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            top = df_content.sort_values("interactions", ascending=False).iloc[0]
            st.markdown(
                insight_box(
                    f"<b>{top['content_type']}</b> generated <b>{top['interactions']:,}</b> "
                    f"interactions from <b>{top['unique_users']:,}</b> unique users.",
                    title="Content Insight",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.info("No content usage data available.")
        chart_card_close()

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CONTENT PREMIUM / BASIC SPLIT
    # --------------------------------------------------------
    anchor("product-usage-premium-basic-content")
    chart_card_open("Premium vs Basic Content", "Split of content interactions by content tier (excludes Post Planner activity).")
    df_split = dd.get_content_premium_split(include_post_planner=include_post_planner)
    if df_split is not None and not df_split.empty:
        total_interactions = df_split["interactions"].sum()
        premium_row = df_split[df_split["content_tier"] == "Premium"]
        basic_row = df_split[df_split["content_tier"] == "Basic"]
        premium_n = int(premium_row["interactions"].iloc[0]) if not premium_row.empty else 0
        basic_n = int(basic_row["interactions"].iloc[0]) if not basic_row.empty else 0
        premium_pct = round(premium_n / total_interactions * 100, 1) if total_interactions else 0.0
        basic_pct = round(basic_n / total_interactions * 100, 1) if total_interactions else 0.0

        c1, c2 = st.columns(2)
        c1.metric("Premium Content Interactions", f"{premium_n:,}", f"{premium_pct}% of total", delta_color="off")
        c2.metric("Basic Content Interactions", f"{basic_n:,}", f"{basic_pct}% of total", delta_color="off")
    else:
        st.info("No content-tier data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CAMPAIGN PERFORMANCE  +  PLATFORM USAGE
    # --------------------------------------------------------
    left, right = st.columns(2)

    with left:
        anchor("product-usage-campaign-performance")
        chart_card_open("Campaign Performance", "Overall scheduled-post publishing performance.")
        camp = dd.get_campaign_performance() or {}

        c1, c2 = st.columns(2)
        c1.metric("Total Scheduled Posts", f"{camp.get('total_scheduled_posts', 0):,}",
                  _trend(camp.get('total_scheduled_posts_curr30d'), camp.get('total_scheduled_posts_prev30d'), "new vs last 30d"),
                  help="Distinct scheduled_id — one piece of content, regardless of how many platforms it went to. Trend = new posts scheduled in the last 30 days vs the 30 days before that.")

        total_rows = camp.get('total_scheduled_rows', 0) or 0
        posted = camp.get('posted', 0) or 0
        pending = camp.get('pending', 0) or 0
        scheduled = camp.get('scheduled', 0) or 0
        failed = camp.get('failed', 0) or 0
        posted_pct = round(posted / total_rows * 100, 1) if total_rows else 0.0
        pending_pct = round(pending / total_rows * 100, 1) if total_rows else 0.0
        scheduled_pct = round(scheduled / total_rows * 100, 1) if total_rows else 0.0
        failed_pct = round(failed / total_rows * 100, 1) if total_rows else 0.0

        posted_trend = _trend(camp.get('posted_curr30d'), camp.get('posted_prev30d'), "vs last 30d")
        pending_trend = _trend(camp.get('pending_curr30d'), camp.get('pending_prev30d'), "vs last 30d")
        scheduled_trend = _trend(camp.get('scheduled_curr30d'), camp.get('scheduled_prev30d'), "vs last 30d")
        failed_trend = _trend_points(camp.get('failure_rate_alltime'), camp.get('failure_rate_excl_last_30d'), "vs before last 30d")
        success_trend = _trend_points(camp.get('publishing_success_rate_curr30d'), camp.get('publishing_success_rate_prev30d'), "vs last 30d")
        automation_trend = _trend_points(camp.get('automation_rate_curr30d'), camp.get('automation_rate_prev30d'), "vs last 30d")

        c2.metric("Posted", f"{posted:,}", posted_trend,
                  help=f"{posted_pct}% of total row-level attempts. Trend compares scheduled_for in the last 30 days vs the 30 days before that.")
        c3, c4 = st.columns(2)
        c3.metric("Pending", f"{pending:,}", pending_trend, delta_color="inverse",
                  help=f"{pending_pct}% of total.")
        c4.metric("Scheduled", f"{scheduled:,}", scheduled_trend,
                  help=f"{scheduled_pct}% of total.")
        c5, c6 = st.columns(2)
        c5.metric("Failed", f"{failed:,}", failed_trend, delta_color="inverse",
                  help=f"{failed_pct}% of total. Trend = overall failure rate (all data) minus the failure rate excluding the last 30 days \u2014 shows how much the last 30 days shifted the all-time rate.")
        c6.metric("Publishing Success", f"{camp.get('publishing_success_rate', 0)}%", success_trend)
        c7, c8 = st.columns(2)
        c7.metric("Automation Rate", f"{camp.get('automation_rate', 0)}%", automation_trend)
        c8.empty()

        with st.expander("Failure rate over time"):
            fr1, fr2, fr3, fr4, fr5 = st.columns(5)
            fr1.metric("1-7 Days", f"{camp.get('failure_rate_1_7d', 0)}%")
            fr2.metric("1-15 Days", f"{camp.get('failure_rate_1_15d', 0)}%")
            fr3.metric("1-30 Days", f"{camp.get('failure_rate_1_30d', 0)}%")
            fr4.metric("1-60 Days", f"{camp.get('failure_rate_1_60d', 0)}%")
            fr5.metric("1-90 Days", f"{camp.get('failure_rate_1_90d', 0)}%")

        status_by_platform = dd.get_status_by_platform()
        if status_by_platform is not None and not status_by_platform.empty:
            with st.expander("Status breakdown by platform"):
                pivot = (
                    status_by_platform.pivot(index="posting_status", columns="platform_name", values="count")
                    .fillna(0).astype(int)
                )
                st.dataframe(pivot, use_container_width=True)

        st.markdown(
            insight_box(
                f"<b>{camp.get('posted', 0):,}</b> posts have gone out successfully "
                f"(<b>{camp.get('publishing_success_rate', 0)}%</b> success rate). "
                f"Automated publishing accounts for <b>{camp.get('automation_rate', 0)}%</b> of all scheduled posts.",
                title="Campaign Insight",
            ),
            unsafe_allow_html=True,
        )
        chart_card_close()

    with right:
        anchor("product-usage-platform-usage")
        chart_card_open("Platform Usage", "Scheduled post distribution across publishing platforms.")
        df_platform = dd.get_platform_usage()
        if df_platform is not None and not df_platform.empty:
            df_platform_sorted = df_platform.sort_values("posts", ascending=True)
            colors = [PLATFORM_COLORS.get(p, BLUE) for p in df_platform_sorted["platform_name"]]
            fig = go.Figure(go.Bar(
                x=df_platform_sorted["posts"],
                y=df_platform_sorted["platform_name"],
                orientation="h",
                marker_color=colors,
                customdata=df_platform_sorted[["share_pct", "success_rate", "distinct_users"]],
                hovertemplate=(
                    "<b>%{y}</b><br>Posts: %{x}<br>Share: %{customdata[0]}%"
                    "<br>Success Rate: %{customdata[1]}%<br>Unique Users: %{customdata[2]:,}<extra></extra>"
                ),
            ))
            fig = style_bar_chart(fig, height=320)
            fig.update_layout(xaxis_title="Posts", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            top = df_platform.sort_values("posts", ascending=False).iloc[0]
            st.markdown(
                insight_box(
                    f"<b>{top['platform_name']}</b> is the most used platform with "
                    f"<b>{top['posts']:,}</b> posts and a <b>{top['success_rate']}%</b> publishing success rate.",
                    title="Platform Insight",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.info("No platform usage data available.")
        chart_card_close()

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # EVENT USAGE
    # --------------------------------------------------------
    anchor("product-usage-event-usage")
    chart_card_open("Event Usage", "Distribution of user actions on Content features.")
    df_event = dd.get_event_usage()
    if df_event is not None and not df_event.empty:
        df_event_sorted = df_event.sort_values("events", ascending=True)
        fig = px.bar(df_event_sorted, x="events", y="event_type", orientation="h")
        fig.update_traces(
            marker_color=BLUE,
            customdata=df_event_sorted[["unique_users"]],
            hovertemplate="<b>%{y}</b><br>Events: %{x:,}<br>Unique Users: %{customdata[0]:,}<extra></extra>",
        )
        fig = style_bar_chart(fig, height=280)
        fig.update_layout(xaxis_title="Total Events", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        top = df_event.sort_values("events", ascending=False).iloc[0]
        st.markdown(
            insight_box(
                f"<b>{top['event_type']}</b> is the most common user action with "
                f"<b>{top['events']:,}</b> events generated by <b>{top['unique_users']:,}</b> unique users.",
                title="Event Insight",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No event usage data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TOP ACTIVE USERS  (All Time / Last 30 Days toggle)
    # --------------------------------------------------------
    anchor("product-usage-top-active-users")
    chart_card_open("Top Active Users", "Users ranked by overall platform activity.")
    period_label = st.radio(
        "Period", ["All Time", "Last 30 Days"], horizontal=True, label_visibility="collapsed",
        key="product_usage_top_users_period",
    )
    period = "30d" if period_label == "Last 30 Days" else "all_time"

    df_top = dd.get_top_active_users(period=period, include_post_planner=include_post_planner)
    if df_top is not None and not df_top.empty:
        display_df = df_top.rename(columns={
            "user_id": "User ID",
            "user_name": "User",
            "company_name": "Company",
            "sso_partner_name": "SSO Partner",
            "activities": "Activities",
            "logins": "Logins",
            "scheduled_posts": "Scheduled Posts",
            "activity_score": "Activity Score",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        top_user = df_top.iloc[0]
        st.markdown(
            insight_box(
                f"<b>{top_user['user_name'] or 'User ' + str(top_user['user_id'])}</b> from "
                f"<b>{top_user['company_name'] or 'N/A'}</b> is the platform's most active user "
                f"({period_label.lower()}) with <b>{top_user['activities']:,}</b> activities, "
                f"<b>{top_user['logins']:,}</b> logins and <b>{top_user['scheduled_posts']:,}</b> scheduled posts.",
                title="Power User Insight",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No user activity data available for this period.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # USAGE BY SSO PARTNER
    # --------------------------------------------------------
    anchor("product-usage-sso-partner")
    chart_card_open("Usage by SSO Partner", "Total users, active users, and engagement rate per acquisition partner.")
    df_sso = dd.get_sso_partner_usage(include_post_planner=include_post_planner)
    if df_sso is not None and not df_sso.empty:
        df_sso_sorted = df_sso.sort_values("active_users", ascending=True)
        fig = go.Figure(go.Bar(
            x=df_sso_sorted["active_users"],
            y=df_sso_sorted["sso_partner_name"],
            orientation="h",
            marker_color=BLUE,
            customdata=df_sso_sorted[["total_users", "engagement_rate"]],
            hovertemplate=(
                "<b>%{y}</b><br>Active Users: %{x}<br>Total Users: %{customdata[0]}"
                "<br>Engagement Rate: %{customdata[1]}%<extra></extra>"
            ),
        ))
        fig = style_bar_chart(fig, height=260)
        fig.update_layout(xaxis_title="Active Users", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        top = df_sso.sort_values("active_users", ascending=False).iloc[0]
        st.markdown(
            insight_box(
                f"<b>{top['sso_partner_name']}</b> drives the most active usage with "
                f"<b>{top['active_users']:,}</b> active users out of <b>{top['total_users']:,}</b> total "
                f"(<b>{top['engagement_rate']}%</b> engagement rate).",
                title="Partner Insight",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No SSO partner usage data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # RETENTION  +  NEW VS RETURNING
    # Both hidden for now (per request, since they're linked) but
    # the code is kept intact — flip SHOW_RETENTION to True to bring
    # both back.
    # --------------------------------------------------------
    SHOW_RETENTION = False

    if SHOW_RETENTION:
        left, right = st.columns(2)

        with left:
            chart_card_open("Retention", "Active users over the last 30 vs 60 days, and users who've gone dormant.")
            retention = dd.get_retention_metrics(include_post_planner=include_post_planner) or {}
            active_30d = retention.get("active_30d_users", 0) or 0
            active_60d = retention.get("active_60d_users", 0) or 0
            dormant = retention.get("dormant_users", 0) or 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Active (30d)", f"{active_30d:,}")
            c2.metric("Active (60d)", f"{active_60d:,}")
            c3.metric("Dormant", f"{dormant:,}",
                      help="Active sometime in the last 60 days, but not in the last 30.")

            dormant_pct = round(dormant / active_60d * 100, 1) if active_60d else 0.0
            st.markdown(
                insight_box(
                    f"<b>{dormant:,}</b> users (<b>{dormant_pct}%</b> of the 60-day active base) have gone quiet "
                    f"in the last 30 days — worth a re-engagement push.",
                    title="Retention Insight",
                ),
                unsafe_allow_html=True,
            )
            chart_card_close()

        with right:
            chart_card_open("New vs Returning Active Users", "Of users active in the last 30 days, how many are new signups vs returning users.")
            nvr = dd.get_new_vs_returning_users(include_post_planner=include_post_planner) or {}
            new_users = nvr.get("new_active_users", 0) or 0
            returning_users = nvr.get("returning_active_users", 0) or 0
            unknown_users = nvr.get("unknown_registration_date", 0) or 0
            total_nvr = new_users + returning_users + unknown_users

            fig = go.Figure(go.Bar(
                x=[new_users, returning_users],
                y=["New", "Returning"],
                orientation="h",
                marker_color=[AMBER, BLUE],
            ))
            fig = style_bar_chart(fig, height=160)
            fig.update_layout(xaxis_title="Active Users", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            new_pct = round(new_users / total_nvr * 100, 1) if total_nvr else 0.0
            insight_text = (
                f"<b>{new_pct}%</b> of active users this month registered within the last 30 days — "
                f"the rest (<b>{returning_users:,}</b>) are returning users from before that."
            )
            if unknown_users:
                insight_text += f" <b>{unknown_users}</b> user(s) have no registration date on file."
            st.markdown(insight_box(insight_text, title="Growth Insight"), unsafe_allow_html=True)
            chart_card_close()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 Content Analytics", expanded=False):
        show_content_usage()