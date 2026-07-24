import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

import dashboard_data as dd

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


def _metric_with_breakdown(col, label, value_str, trend_str, monthly_df, value_col,
                            value_fmt=lambda v: f"{v:,.0f}", help_text=None):
    """Renders an st.metric, then a small popover trigger right below it showing
    the month-wise breakdown for that specific metric (trailing 12 months).
    monthly_df: DataFrame with a 'month' column plus value_col.
    value_fmt: formatter applied to each month's value for display."""
    with col:
        col.metric(label, value_str, trend_str, help=help_text)
        with st.popover("📊 Monthly breakdown", use_container_width=True):
            if monthly_df is None or monthly_df.empty or value_col not in monthly_df.columns:
                st.caption("No monthly data available.")
            else:
                display_df = monthly_df[["month", value_col]].copy()
                display_df["month"] = display_df["month"].dt.strftime("%b %Y")
                display_df[value_col] = display_df[value_col].apply(
                    lambda v: value_fmt(v) if pd.notna(v) else "—"
                )
                display_df = display_df.rename(columns={"month": "Month", value_col: label})
                st.dataframe(display_df, hide_index=True, use_container_width=True)


def anchor(name):
    """Duplicated from app.py's helper — invisible marker div for the nav rail's scroll-to
    links. Offset -70px so the section lands clear of the sticky header when scrolled to."""
    st.markdown(f'<div id="{name}" style="position:relative; top:-70px;"></div>', unsafe_allow_html=True)


def _resolve_period(period_label):
    """Converts a period label into (start_date, end_date) as date objects.
    Returns (None, None) for 'All Time' — meaning no date filtering at all.
    'This Year' = financial-year-to-date (Apr 1 of the current FY through
    today), per company convention, not the calendar year."""
    today = date.today()
    if period_label == "This Month":
        start = today.replace(day=1)
        end = today
    elif period_label == "Last Month":
        first_of_this_month = today.replace(day=1)
        end = first_of_this_month - timedelta(days=1)
        start = end.replace(day=1)
    elif period_label == "This Year":
        start, _ = dd.get_financial_year_bounds(today, years_back=0)
        end = today
    else:  # "All Time"
        start, end = None, None
    return start, end


COMPARISON_PERIOD_OPTIONS = ["This Month", "Last Month", "This Quarter", "Last Quarter", "This Year", "Last Year", "All Time"]


def _resolve_comparison_period(label):
    """Resolves any of the comparison-dropdown options into (start_date, end_date).
    'All Time' returns (None, None) — no date filtering. 'This Year' =
    financial-year-to-date and 'Last Year' = the full previous financial
    year (Apr 1 - Mar 31), per company convention, not the calendar year.
    Uses dd.get_financial_year_bounds() so this always agrees with Revenue
    and Subscriptions."""
    today = date.today()
    if label == "This Month":
        return today.replace(day=1), today
    elif label == "Last Month":
        end = today.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end
    elif label == "This Quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=q_start_month, day=1), today
    elif label == "Last Quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        this_q_start = today.replace(month=q_start_month, day=1)
        last_q_end = this_q_start - timedelta(days=1)
        last_q_start_month = ((last_q_end.month - 1) // 3) * 3 + 1
        return last_q_end.replace(month=last_q_start_month, day=1), last_q_end
    elif label == "This Year":
        fy_start, _ = dd.get_financial_year_bounds(today, years_back=0)
        return fy_start, today
    elif label == "Last Year":
        return dd.get_financial_year_bounds(today, years_back=1)
    else:  # "All Time"
        return None, None


def _resolve_previous_period(period_label):
    """Returns (prev_start, prev_end, comparison_label) for the 'previous equivalent
    period' used in period-over-period comparison — e.g. This Month compares against
    the full previous calendar month, This Year compares against the same
    financial-year-to-date range one FY earlier (apples-to-apples, not a full prior
    FY). Returns (None, None, None) for 'All Time', since there's no sensible
    'previous all-time' to compare against."""
    today = date.today()
    if period_label == "This Month":
        end = today.replace(day=1) - timedelta(days=1)
        start = end.replace(day=1)
        return start, end, "vs Last Month"
    elif period_label == "Last Month":
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        end = last_month_start - timedelta(days=1)
        start = end.replace(day=1)
        return start, end, "vs Month Before"
    elif period_label == "This Year":
        start, _ = dd.get_financial_year_bounds(today, years_back=1)
        try:
            end = today.replace(year=today.year - 1)
        except ValueError:
            # today is Feb 29 and last year wasn't a leap year
            end = today.replace(year=today.year - 1, day=28)
        return start, end, "vs Last Year (same period)"
    else:  # "All Time"
        return None, None, None


def show_product_usage():
    anchor("product-usage-overview")
    st.markdown("<div class='section-header'>Product Usage Overview</div>", unsafe_allow_html=True)

    top_left, top_right = st.columns([2, 2])
    with top_left:
        planner_label = st.radio(
            "Post Planner", ["With Post Planner", "Without Post Planner"], horizontal=True,
            label_visibility="collapsed", key="product_usage_planner_toggle",
        )
    with top_right:
        cmp_col_a, cmp_col_vs, cmp_col_b = st.columns([2, 0.4, 2])
        with cmp_col_a:
            period_a_label = st.selectbox(
                "Compare", COMPARISON_PERIOD_OPTIONS, index=COMPARISON_PERIOD_OPTIONS.index("All Time"),
                key="product_usage_period_a", label_visibility="collapsed",
            )
        with cmp_col_vs:
            st.markdown("<div style='text-align:center; padding-top:8px; color:#6B7280;'>vs</div>", unsafe_allow_html=True)
        with cmp_col_b:
            period_b_locked = period_a_label == "All Time"
            period_b_options = [opt for opt in COMPARISON_PERIOD_OPTIONS if opt != period_a_label]
            if st.session_state.get("product_usage_period_b") not in period_b_options:
                st.session_state["product_usage_period_b"] = period_b_options[0]
            period_b_label = st.selectbox(
                "vs", period_b_options,
                key="product_usage_period_b", label_visibility="collapsed",
                disabled=period_b_locked,
                help="Pick a period on the left other than All Time to unlock this." if period_b_locked else None,
            )
    period_a_start, period_a_end = _resolve_comparison_period(period_a_label)
    period_b_start, period_b_end = _resolve_comparison_period(period_b_label)

    # Charts below not yet migrated to full two-period comparison (Campaign Performance,
    # Platform Usage, Usage by SSO Partner) still read period_label/period_start/period_end
    # directly — alias them to Period A so those keep working exactly as before.
    period_label = period_a_label
    period_start, period_end = period_a_start, period_a_end

    include_post_planner = planner_label == "With Post Planner"
    st.caption("Post Planner toggle applies to everything below except Feature Usage (Post Planner always shown), and Campaign Performance / Platform Usage (unrelated \u2014 those come from scheduled posts, not activity). "
               "By default the left dropdown is All Time and the right one is locked \u2014 pick a specific period on the left to unlock a comparison. Total Users / New Users / Total Activities / Avg Actions per User and Feature Usage use both sides once unlocked. "
               "DAU/WAU/MAU/Premium Active/Basic Active, Daily Activity Trend, Feature Adoption Depth, Time to First Value, and Top Active Users are unaffected (they have their own fixed windows). "
               "Feature Adoption Depth measures lifetime feature usage, not a specific window, so it isn't part of the comparison either.")
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # KPI STRIP
    # --------------------------------------------------------
    kpis = dd.get_product_usage_kpis(include_post_planner=include_post_planner) or {}
    monthly_breakdown = dd.get_product_usage_monthly_breakdown(include_post_planner)

    mau = kpis.get("mau", 0) or 0
    premium_active = kpis.get("premium_active", 0) or 0
    basic_active = kpis.get("basic_active", 0) or 0
    premium_active_pct = round(premium_active / mau * 100, 1) if mau else 0.0
    basic_active_pct = round(basic_active / mau * 100, 1) if mau else 0.0

    r1 = st.columns(4)
    if period_a_label == "All Time":
        _metric_with_breakdown(
            r1[0], "Total Users", f"{kpis.get('total_users', 0):,}",
            _trend(kpis.get('total_users'), kpis.get('total_users_prev')),
            monthly_breakdown, "new_users",
            help_text="Cumulative registered users. Breakdown shows new signups per month."
        )
    else:
        period_kpis_a = dd.get_product_usage_period_kpis(period_a_start, period_a_end, include_post_planner) or {}
        period_kpis_b = dd.get_product_usage_period_kpis(period_b_start, period_b_end, include_post_planner) or {}
        _metric_with_breakdown(
            r1[0], "New Users", f"{period_kpis_a.get('new_users', 0):,}",
            _trend(period_kpis_a.get('new_users'), period_kpis_b.get('new_users'), f"vs {period_b_label}"),
            monthly_breakdown, "new_users",
            help_text=f"Users who registered during {period_a_label}. Compared vs {period_b_label}."
        )
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
    if period_a_label == "All Time":
        # NOTE: kpis['total_activities'] from get_product_usage_kpis() is actually
        # always a fixed last-30-days figure (same pattern as DAU/WAU/MAU) — NOT a
        # true all-time total. So "All Time" mode also calls the period function
        # with (None, None), which correctly returns true unfiltered lifetime totals.
        all_time_kpis = dd.get_product_usage_period_kpis(None, None, include_post_planner) or {}
        _metric_with_breakdown(
            r2[2], "Total Activities", f"{all_time_kpis.get('total_activities', 0):,}", None,
            monthly_breakdown, "total_activities",
            help_text="All activity events, all time (platform-wide)."
        )
        _metric_with_breakdown(
            r2[3], "Avg Actions/User", f"{all_time_kpis.get('avg_actions_per_user', 0) or 0:,}", None,
            monthly_breakdown, "avg_actions_per_user", value_fmt=lambda v: f"{v:,.2f}",
            help_text="All-time total activities divided by all-time new users."
        )
    else:
        _metric_with_breakdown(
            r2[2], "Total Activities", f"{period_kpis_a.get('total_activities', 0):,}",
            _trend(period_kpis_a.get('total_activities'), period_kpis_b.get('total_activities'), f"vs {period_b_label}"),
            monthly_breakdown, "total_activities",
            help_text=f"All activity events during {period_a_label} (platform-wide). Compared vs {period_b_label}."
        )
        _metric_with_breakdown(
            r2[3], "Avg Actions/User", f"{period_kpis_a.get('avg_actions_per_user', 0) or 0:,}",
            _trend(period_kpis_a.get('avg_actions_per_user'), period_kpis_b.get('avg_actions_per_user'), f"vs {period_b_label}"),
            monthly_breakdown, "avg_actions_per_user", value_fmt=lambda v: f"{v:,.2f}",
            help_text=f"Total activities during {period_a_label} divided by new users in that period. Compared vs {period_b_label}."
        )

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
            dragmode="pan",
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
        # Show the most recent 90 days by default (matches prior behavior),
        # but the full dataset is loaded — drag left/right (not scroll/pinch)
        # to pan through all of history.
        default_window_start = daily["date"].max() - pd.Timedelta(days=90)
        fig.update_xaxes(
            showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT,
            range=[max(daily["date"].min(), default_window_start), daily["date"].max()],
            fixedrange=False,
        )
        fig.update_yaxes(fixedrange=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

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
    # FEATURE USAGE
    # (was paired 2-up with "Content Usage" — that chart moved to Content
    # Analytics as the corrected "Content Type Distribution" chart, so
    # Feature Usage now takes the full row.)
    # --------------------------------------------------------
    anchor("product-usage-feature-usage")

    if period_a_label == "All Time":
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
        st.markdown("<br>", unsafe_allow_html=True)

    else:
        chart_card_open("Feature Usage", f"Top product features by adoption — {period_a_label} vs {period_b_label}.")

        df_feat_a = dd.get_feature_usage_period(period_a_start, period_a_end)
        df_feat_b = dd.get_feature_usage_period(period_b_start, period_b_end)

        if (df_feat_a is not None and not df_feat_a.empty) or (df_feat_b is not None and not df_feat_b.empty):
            df_a = df_feat_a[["feature_type", "events"]].rename(columns={"events": "a"}) if df_feat_a is not None and not df_feat_a.empty else pd.DataFrame(columns=["feature_type", "a"])
            df_b = df_feat_b[["feature_type", "events"]].rename(columns={"events": "b"}) if df_feat_b is not None and not df_feat_b.empty else pd.DataFrame(columns=["feature_type", "b"])

            df_compare = df_a.merge(df_b, on="feature_type", how="outer").fillna(0)
            df_compare["a"] = df_compare["a"].astype(int)
            df_compare["b"] = df_compare["b"].astype(int)
            df_compare = df_compare.sort_values("a", ascending=True)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=df_compare["feature_type"], x=df_compare["b"], orientation="h",
                name=period_b_label, marker_color="#B5D4F4",
            ))
            fig.add_trace(go.Bar(
                y=df_compare["feature_type"], x=df_compare["a"], orientation="h",
                name=period_a_label, marker_color=BLUE,
            ))
            fig.update_layout(
                barmode="group", height=280, xaxis_title="Total Events", yaxis_title="",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=12, r=20, t=40, b=40),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            with st.expander("Reconciliation table"):
                table_df = df_compare.sort_values("a", ascending=False).copy()
                table_df["change_pct"] = table_df.apply(
                    lambda r: "—" if r["b"] == 0 else f"{((r['a'] - r['b']) / r['b'] * 100):+.1f}%",
                    axis=1,
                )
                table_df = table_df.rename(columns={
                    "feature_type": "Feature", "a": period_a_label, "b": period_b_label, "change_pct": "Change",
                })
                st.dataframe(table_df, hide_index=True, use_container_width=True)

            if df_feat_a is not None and not df_feat_a.empty:
                top = df_feat_a.sort_values("events", ascending=False).iloc[0]
                st.markdown(
                    insight_box(
                        f"<b>{top['feature_type']}</b> is the most used feature in {period_a_label} with "
                        f"<b>{top['events']:,}</b> events from <b>{top['unique_users']:,}</b> users.",
                        title="Feature Insight",
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.info("No feature usage data available for either selected period.")
        chart_card_close()
        st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CAMPAIGN PERFORMANCE  +  PLATFORM USAGE
    # --------------------------------------------------------
    left, right = st.columns(2)

    with left:
        anchor("product-usage-campaign-performance")
        chart_card_open("Campaign Performance", "Overall scheduled-post publishing performance." if period_a_label == "All Time" else f"Scheduled-post publishing performance — {period_a_label} vs {period_b_label} (failure-rate trend below always stays all-time).")
        camp = dd.get_campaign_performance() or {}  # always fetched — failure_rate_* fields and the "Failure rate over time" section below are never period-filtered

        if period_a_label == "All Time":
            total_scheduled_posts_display = camp.get('total_scheduled_posts', 0)
            posted_display = camp.get('posted', 0) or 0
            failed_display = camp.get('failed', 0) or 0
            pending_display = camp.get('pending', 0) or 0
            scheduled_display = camp.get('scheduled', 0) or 0
            publishing_success_rate_display = camp.get('publishing_success_rate', 0) or 0
            automation_rate_display = camp.get('automation_rate', 0) or 0

            total_scheduled_posts_trend = _trend(camp.get('total_scheduled_posts_curr30d'), camp.get('total_scheduled_posts_prev30d'), "new vs last 30d")
            posted_trend = _trend(camp.get('posted_curr30d'), camp.get('posted_prev30d'), "vs last 30d")
            pending_trend = _trend(camp.get('pending_curr30d'), camp.get('pending_prev30d'), "vs last 30d")
            scheduled_trend = _trend(camp.get('scheduled_curr30d'), camp.get('scheduled_prev30d'), "vs last 30d")
            failed_trend = _trend_points(camp.get('failure_rate_alltime'), camp.get('failure_rate_excl_last_30d'), "vs before last 30d")
            success_trend = _trend_points(camp.get('publishing_success_rate_curr30d'), camp.get('publishing_success_rate_prev30d'), "vs last 30d")
            automation_trend = _trend_points(camp.get('automation_rate_curr30d'), camp.get('automation_rate_prev30d'), "vs last 30d")
            scope_help = f" Scoped to {period_a_label}."
        else:
            camp_a = dd.get_campaign_performance_period(period_a_start, period_a_end) or {}
            camp_b = dd.get_campaign_performance_period(period_b_start, period_b_end) or {}

            total_scheduled_posts_display = camp_a.get('total_scheduled_posts', 0)
            posted_display = camp_a.get('posted', 0) or 0
            failed_display = camp_a.get('failed', 0) or 0
            pending_display = camp_a.get('pending', 0) or 0
            scheduled_display = camp_a.get('scheduled', 0) or 0
            publishing_success_rate_display = camp_a.get('publishing_success_rate', 0) or 0
            automation_rate_display = camp_a.get('automation_rate', 0) or 0

            cmp_suffix = f"vs {period_b_label}"
            total_scheduled_posts_trend = _trend(camp_a.get('total_scheduled_posts'), camp_b.get('total_scheduled_posts'), cmp_suffix)
            posted_trend = _trend(camp_a.get('posted'), camp_b.get('posted'), cmp_suffix)
            pending_trend = _trend(camp_a.get('pending'), camp_b.get('pending'), cmp_suffix)
            scheduled_trend = _trend(camp_a.get('scheduled'), camp_b.get('scheduled'), cmp_suffix)
            failed_trend = _trend(camp_a.get('failed'), camp_b.get('failed'), cmp_suffix)
            success_trend = _trend_points(camp_a.get('publishing_success_rate'), camp_b.get('publishing_success_rate'), cmp_suffix)
            automation_trend = _trend_points(camp_a.get('automation_rate'), camp_b.get('automation_rate'), cmp_suffix)
            scope_help = f" Scoped to {period_a_label}, compared vs {period_b_label}."

        c1, c2 = st.columns(2)
        c1.metric("Total Scheduled Posts", f"{total_scheduled_posts_display:,}", total_scheduled_posts_trend,
                  help="Distinct scheduled_id — one piece of content, regardless of how many platforms it went to." + scope_help)

        total_rows = camp.get('total_scheduled_rows', 0) or 0
        posted = posted_display
        pending = pending_display
        scheduled = scheduled_display
        failed = failed_display
        posted_pct = round(posted / total_rows * 100, 1) if total_rows else 0.0
        pending_pct = round(pending / total_rows * 100, 1) if total_rows else 0.0
        scheduled_pct = round(scheduled / total_rows * 100, 1) if total_rows else 0.0
        failed_pct = round(failed / total_rows * 100, 1) if total_rows else 0.0

        c2.metric("Posted", f"{posted:,}", posted_trend,
                  help=f"{posted_pct}% of total row-level attempts." + scope_help)
        c3, c4 = st.columns(2)
        c3.metric("Pending", f"{pending:,}", pending_trend, delta_color="inverse",
                  help=f"{pending_pct}% of total.")
        c4.metric("Scheduled", f"{scheduled:,}", scheduled_trend,
                  help=f"{scheduled_pct}% of total.")
        c5, c6 = st.columns(2)
        c5.metric("Failed", f"{failed:,}", failed_trend, delta_color="inverse",
                  help=f"{failed_pct}% of total." + scope_help)
        c6.metric("Publishing Success", f"{publishing_success_rate_display}%", success_trend)
        c7, c8 = st.columns(2)
        c7.metric("Automation Rate", f"{automation_rate_display}%", automation_trend)
        c8.empty()

        with st.expander("Failure rate over time (always all-time \u2014 not affected by the period filter)"):
            fr1, fr2, fr3, fr4, fr5 = st.columns(5)
            fr1.metric("1-7 Days", f"{camp.get('failure_rate_1_7d', 0)}%")
            fr2.metric("1-15 Days", f"{camp.get('failure_rate_1_15d', 0)}%")
            fr3.metric("1-30 Days", f"{camp.get('failure_rate_1_30d', 0)}%")
            fr4.metric("1-60 Days", f"{camp.get('failure_rate_1_60d', 0)}%")
            fr5.metric("1-90 Days", f"{camp.get('failure_rate_1_90d', 0)}%")

        if period_a_label == "All Time":
            status_by_platform = dd.get_status_by_platform()
            if status_by_platform is not None and not status_by_platform.empty:
                with st.expander("Status breakdown by platform"):
                    pivot = (
                        status_by_platform.pivot(index="posting_status", columns="platform_name", values="count")
                        .fillna(0).astype(int)
                    )
                    st.dataframe(pivot, use_container_width=True)
        else:
            status_a = dd.get_status_by_platform_period(period_a_start, period_a_end)
            status_b = dd.get_status_by_platform_period(period_b_start, period_b_end)
            if (status_a is not None and not status_a.empty) or (status_b is not None and not status_b.empty):
                with st.expander(f"Status breakdown by platform — {period_a_label} vs {period_b_label}"):
                    sb_col_a, sb_col_b = st.columns(2)
                    with sb_col_a:
                        st.caption(period_a_label)
                        if status_a is not None and not status_a.empty:
                            pivot_a = status_a.pivot(index="posting_status", columns="platform_name", values="count").fillna(0).astype(int)
                            st.dataframe(pivot_a, use_container_width=True)
                        else:
                            st.caption("No data.")
                    with sb_col_b:
                        st.caption(period_b_label)
                        if status_b is not None and not status_b.empty:
                            pivot_b = status_b.pivot(index="posting_status", columns="platform_name", values="count").fillna(0).astype(int)
                            st.dataframe(pivot_b, use_container_width=True)
                        else:
                            st.caption("No data.")

        st.markdown(
            insight_box(
                f"<b>{posted_display:,}</b> posts have gone out successfully "
                f"(<b>{publishing_success_rate_display}%</b> success rate). "
                f"Automated publishing accounts for <b>{automation_rate_display}%</b> of all scheduled posts.",
                title="Campaign Insight",
            ),
            unsafe_allow_html=True,
        )
        chart_card_close()

    with right:
        anchor("product-usage-platform-usage")

        if period_a_label == "All Time":
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

        else:
            chart_card_open("Platform Usage", f"Scheduled post distribution across publishing platforms — {period_a_label} vs {period_b_label}.")
            df_plat_a = dd.get_platform_usage_period(period_a_start, period_a_end)
            df_plat_b = dd.get_platform_usage_period(period_b_start, period_b_end)

            if (df_plat_a is not None and not df_plat_a.empty) or (df_plat_b is not None and not df_plat_b.empty):
                dfa = df_plat_a[["platform_name", "posts"]].rename(columns={"posts": "a"}) if df_plat_a is not None and not df_plat_a.empty else pd.DataFrame(columns=["platform_name", "a"])
                dfb = df_plat_b[["platform_name", "posts"]].rename(columns={"posts": "b"}) if df_plat_b is not None and not df_plat_b.empty else pd.DataFrame(columns=["platform_name", "b"])

                df_pcompare = dfa.merge(dfb, on="platform_name", how="outer").fillna(0)
                df_pcompare["a"] = df_pcompare["a"].astype(int)
                df_pcompare["b"] = df_pcompare["b"].astype(int)
                df_pcompare = df_pcompare.sort_values("a", ascending=True)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=df_pcompare["platform_name"], x=df_pcompare["b"], orientation="h",
                    name=period_b_label, marker_color="#B5D4F4",
                ))
                fig.add_trace(go.Bar(
                    y=df_pcompare["platform_name"], x=df_pcompare["a"], orientation="h",
                    name=period_a_label, marker_color=BLUE,
                ))
                fig.update_layout(
                    barmode="group", height=320, xaxis_title="Posts", yaxis_title="",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=12, r=20, t=40, b=40),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                with st.expander("Reconciliation table"):
                    table_pdf = df_pcompare.sort_values("a", ascending=False).copy()
                    table_pdf["change_pct"] = table_pdf.apply(
                        lambda r: "—" if r["b"] == 0 else f"{((r['a'] - r['b']) / r['b'] * 100):+.1f}%",
                        axis=1,
                    )
                    table_pdf = table_pdf.rename(columns={
                        "platform_name": "Platform", "a": period_a_label, "b": period_b_label, "change_pct": "Change",
                    })
                    st.dataframe(table_pdf, hide_index=True, use_container_width=True)

                if df_plat_a is not None and not df_plat_a.empty:
                    top = df_plat_a.sort_values("posts", ascending=False).iloc[0]
                    st.markdown(
                        insight_box(
                            f"<b>{top['platform_name']}</b> is the most used platform in {period_a_label} with "
                            f"<b>{top['posts']:,}</b> posts and a <b>{top['success_rate']}%</b> publishing success rate.",
                            title="Platform Insight",
                        ),
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No platform usage data available for either selected period.")
            chart_card_close()

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # (Event Usage chart moved to Content Analytics, placed alongside
    # its "Engagement by Event Type Over Time" chart.)
    # --------------------------------------------------------

    # --------------------------------------------------------
    # TOP ACTIVE USERS  (All Time / Last 30 Days toggle)
    # --------------------------------------------------------
    anchor("product-usage-top-active-users")
    chart_card_open("Top Active Users", "Users ranked by overall platform activity.")
    top_users_period_label = st.radio(
        "Period", ["All Time", "Last 30 Days"], horizontal=True, label_visibility="collapsed",
        key="product_usage_top_users_period",
    )
    period = "30d" if top_users_period_label == "Last 30 Days" else "all_time"

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
                f"({top_users_period_label.lower()}) with <b>{top_user['activities']:,}</b> activities, "
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

    if period_a_label == "All Time":
        chart_card_open("Usage by SSO Partner", "Total users, active users, and engagement rate per acquisition partner.")
        df_sso = dd.get_sso_partner_usage_period(None, None, include_post_planner)
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

    else:
        chart_card_open("Usage by SSO Partner", f"Active users per acquisition partner — {period_a_label} vs {period_b_label} (Total Users stays all-time regardless of period).")
        df_sso_a = dd.get_sso_partner_usage_period(period_a_start, period_a_end, include_post_planner)
        df_sso_b = dd.get_sso_partner_usage_period(period_b_start, period_b_end, include_post_planner)

        if (df_sso_a is not None and not df_sso_a.empty) or (df_sso_b is not None and not df_sso_b.empty):
            dfa = df_sso_a[["sso_partner_name", "active_users"]].rename(columns={"active_users": "a"}) if df_sso_a is not None and not df_sso_a.empty else pd.DataFrame(columns=["sso_partner_name", "a"])
            dfb = df_sso_b[["sso_partner_name", "active_users"]].rename(columns={"active_users": "b"}) if df_sso_b is not None and not df_sso_b.empty else pd.DataFrame(columns=["sso_partner_name", "b"])

            df_scompare = dfa.merge(dfb, on="sso_partner_name", how="outer").fillna(0)
            df_scompare["a"] = df_scompare["a"].astype(int)
            df_scompare["b"] = df_scompare["b"].astype(int)
            df_scompare = df_scompare.sort_values("a", ascending=True)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=df_scompare["sso_partner_name"], x=df_scompare["b"], orientation="h",
                name=period_b_label, marker_color="#B5D4F4",
            ))
            fig.add_trace(go.Bar(
                y=df_scompare["sso_partner_name"], x=df_scompare["a"], orientation="h",
                name=period_a_label, marker_color=BLUE,
            ))
            fig.update_layout(
                barmode="group", height=260, xaxis_title="Active Users", yaxis_title="",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=12, r=20, t=40, b=40),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            with st.expander("Reconciliation table"):
                table_sdf = df_scompare.sort_values("a", ascending=False).copy()
                table_sdf["change_pct"] = table_sdf.apply(
                    lambda r: "—" if r["b"] == 0 else f"{((r['a'] - r['b']) / r['b'] * 100):+.1f}%",
                    axis=1,
                )
                table_sdf = table_sdf.rename(columns={
                    "sso_partner_name": "Partner", "a": period_a_label, "b": period_b_label, "change_pct": "Change",
                })
                st.dataframe(table_sdf, hide_index=True, use_container_width=True)

            if df_sso_a is not None and not df_sso_a.empty:
                top = df_sso_a.sort_values("active_users", ascending=False).iloc[0]
                st.markdown(
                    insight_box(
                        f"<b>{top['sso_partner_name']}</b> drives the most active usage in {period_a_label} with "
                        f"<b>{top['active_users']:,}</b> active users out of <b>{top['total_users']:,}</b> total "
                        f"(<b>{top['engagement_rate']}%</b> engagement rate).",
                        title="Partner Insight",
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.info("No SSO partner usage data available for either selected period.")
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

    # --------------------------------------------------------
    # FEATURE ADOPTION DEPTH
    # How many distinct features each user touches, not just how many people
    # use each feature. A user base clustered at "1 feature" has found exactly
    # one reason to open the app and no others — a stickiness risk even if
    # each feature individually looks well-used.
    # --------------------------------------------------------
    chart_card_open("Feature Adoption Depth", "How many distinct features each user has touched. Hover a bar for the specific feature combinations behind that count.")
    df_depth = dd.get_feature_adoption_depth()
    if df_depth is not None and not df_depth.empty:
        depth_totals = (
            df_depth.groupby("distinct_features_used")["user_count"].sum().reset_index()
            .sort_values("distinct_features_used")
        )

        combo_text_by_depth = {}
        for depth, grp in df_depth.groupby("distinct_features_used"):
            grp_sorted = grp.sort_values("user_count", ascending=False)
            lines = [f"{row['feature_combination']}: {row['user_count']:,}" for _, row in grp_sorted.iterrows()]
            combo_text_by_depth[depth] = "<br>".join(lines)

        depth_totals["hover_text"] = depth_totals["distinct_features_used"].map(
            lambda d: f"<b>{d} feature{'s' if d != 1 else ''}</b><br>Total Users: {int(depth_totals.loc[depth_totals['distinct_features_used'] == d, 'user_count'].iloc[0]):,}<br><br><b>Feature Combinations</b><br>{combo_text_by_depth.get(d, '')}"
        )

        fig = go.Figure(go.Bar(
            x=depth_totals["distinct_features_used"].astype(str), y=depth_totals["user_count"],
            marker_color=BLUE, marker_line_width=0,
            hovertext=depth_totals["hover_text"], hoverinfo="text",
        ))
        fig.update_layout(
            height=300, **CHART_BG, font=FONT,
            margin=dict(l=40, r=20, t=10, b=40),
            showlegend=False, hoverlabel=HOVER_LABEL,
            xaxis_title="Distinct Features Used", yaxis_title="Users",
        )
        fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        total_users_depth = depth_totals["user_count"].sum()
        single_feature_users = depth_totals[depth_totals["distinct_features_used"] == 1]["user_count"].sum()
        single_pct = round(single_feature_users / total_users_depth * 100, 1) if total_users_depth else 0.0
        top_single_combo = combo_text_by_depth.get(1, "").split("<br>")[0] if combo_text_by_depth.get(1) else "N/A"
        st.markdown(
            insight_box(
                f"<b>{single_pct}%</b> of users have only ever used a single feature — most commonly "
                f"<b>{top_single_combo}</b>. These users have found exactly one reason to open the app; "
                f"in-app prompts toward a second feature could meaningfully improve stickiness.",
                title="Adoption Insight",
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No feature adoption data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TIME TO FIRST VALUE
    # Days between signup and a user's first recorded activity of any kind —
    # a classic onboarding health metric. A long or fat-tailed distribution
    # here signals users are signing up but not immediately finding value.
    # --------------------------------------------------------
    chart_card_open("Time to First Value", "Days between signup and each user's first recorded activity.")
    df_ttfv = dd.get_time_to_first_value()
    if df_ttfv is not None and not df_ttfv.empty:
        df_ttfv_valid = df_ttfv.dropna(subset=["days_to_first_activity"]).copy()
        df_ttfv_valid = df_ttfv_valid[df_ttfv_valid["days_to_first_activity"] >= 0]
        never_activated = int(df_ttfv["days_to_first_activity"].isna().sum())

        if not df_ttfv_valid.empty:
            same_day = int((df_ttfv_valid["days_to_first_activity"] == 0).sum())
            within_week = int((df_ttfv_valid["days_to_first_activity"] <= 7).sum())
            total_valid = len(df_ttfv_valid)
            median_days = df_ttfv_valid["days_to_first_activity"].median()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Median Days to First Activity", f"{median_days:.0f}")
            m2.metric("Same-Day Activation", f"{round(same_day / total_valid * 100, 1)}%")
            m3.metric("Activated Within 7 Days", f"{round(within_week / total_valid * 100, 1)}%")
            m4.metric("Never Activated", f"{never_activated:,}")

            capped = df_ttfv_valid[df_ttfv_valid["days_to_first_activity"] <= 30]
            fig2 = go.Figure(go.Histogram(
                x=capped["days_to_first_activity"], marker_color=GREEN, marker_line_width=0,
                hovertemplate="Day: <b>%{x}</b><br>Users: <b>%{y}</b><extra></extra>",
            ))
            fig2.update_layout(
                height=280, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40),
                showlegend=False, hoverlabel=HOVER_LABEL,
                xaxis_title="Days to First Activity (capped at 30)", yaxis_title="Users", bargap=0.05,
            )
            fig2.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            fig2.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No users with a recorded first activity yet.")
    else:
        st.info("No time-to-first-value data available.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)