import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import html

import user360_data as u360

# ============================================================
# 🎨 DESIGN TOKENS — duplicated from app.py / product_usage.py on
# purpose. user_360.py must not `import` from app.py (top-level
# st.set_page_config() would break/duplicate on import). Keeping a
# local copy means this tab can't accidentally affect any other tab.
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

HOVER_LABEL = dict(
    bgcolor="rgba(15,23,42,0.88)",
    bordercolor="rgba(37,99,235,0.6)",
    font=dict(family="Manrope", size=12, color="#F8FAFC"),
)

PLATFORM_COLORS = {
    "Instagram": "#2563EB", "Facebook": "#93C5FD", "LinkedIn": "#0A66C2",
    "WhatsApp": "#F9A8D4", "Twitter": "#10B981", "Email": "#F59E0B",
}

STATUS_BADGE = {
    "Premium - Active": ("#DCFCE7", "#166534"),
    "Premium - Expired": ("#FEE2E2", "#991B1B"),
    "Basic - Trial - Active": ("#DBEAFE", "#1E40AF"),
    "Basic - Trial - Expired": ("#FEE2E2", "#991B1B"),
    "Basic - Standard": ("#F1F5F9", "#475569"),
}


def insight_box(content_html, title="Insight"):
    return f"""
    <div style="
        background:#EFF6FF; border:1px solid #BFDBFE; border-left:3px solid #2563EB;
        border-radius:10px; padding:14px 18px; margin-top:12px; margin-bottom:8px;
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


def style_bar_chart(fig, height=320, orientation="h"):
    is_h = orientation == "h"
    for trace in fig.data:
        trace.update(
            marker_line_width=0, marker_cornerradius=4,
            texttemplate=f"%{{x:,.0f}}" if is_h else f"%{{y:,.0f}}",
            textposition="outside", textfont=dict(size=11, color="#374151"), cliponaxis=False,
        )
    fig.update_layout(
        height=height, bargap=0.35, **CHART_BG, font=FONT,
        margin=dict(l=16, r=70, t=10, b=40), showlegend=False,
        hoverlabel=HOVER_LABEL, hovermode="y" if is_h else "x",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=not is_h, title_font=AXIS_FONT, tickfont=TICK_FONT)
    fig.update_yaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
    return fig


def _fmt_date(value, fmt="%d %b %Y"):
    if not value:
        return "\u2014"
    try:
        return pd.to_datetime(value).strftime(fmt)
    except Exception:
        return "\u2014"


def _fmt_currency(value):
    try:
        return f"\u20b9{float(value):,.0f}"
    except (TypeError, ValueError):
        return "\u20b90"


def _safe_text(value, fallback="\u2014"):
    """Escapes HTML-special characters and strips embedded newlines from user-controlled
    profile data (names, company, email, etc.) before it's interpolated into an HTML string.
    Without this, a stray '<', '>', '&', or embedded newline in someone's raw data can break
    the markdown/HTML render for that specific record — the rest of the field renders fine,
    but everything after the bad character can leak out as literal text instead of rendering."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return fallback
    text = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    return html.escape(text) or fallback


def _status_badge_html(status):
    bg, fg = STATUS_BADGE.get(status, ("#F1F5F9", "#475569"))
    return (
        f'<span style="background:{bg};color:{fg};font-size:12px;font-weight:700;'
        f'padding:4px 12px;border-radius:6px;">{status}</span>'
    )


@st.cache_data(ttl=1800, show_spinner="Loading users…")
def _cached_search_list():
    """Cached for 30 minutes so every keystroke doesn't re-fetch/re-process all ~7,057
    users. Also precomputes the lowercase columns once here, instead of redoing that
    string work on every single search call."""
    df = u360.get_user_search_list()
    if df is None or df.empty:
        return df
    df["_id_str"] = df["user_id"].astype(str)
    df["_mobile_str"] = df["mobile_number"].fillna("").astype(str).str.lower()
    df["_label_str"] = df["search_label"].astype(str).str.lower()
    return df


def _search_users(searchterm):
    """Callback for st_searchbox — ranks exact user_id match, then exact mobile match, then
    id-starts-with, then mobile-contains, then label substring (name/company/email)."""
    if not searchterm:
        return []

    search_df = _cached_search_list()
    if search_df is None or search_df.empty:
        return []

    q = searchterm.strip().lower()
    ids_as_str = search_df["_id_str"]
    mobiles_as_str = search_df["_mobile_str"]

    exact_id = search_df[ids_as_str == q]
    matched_ids = set(exact_id["user_id"])

    exact_mobile = search_df[(mobiles_as_str == q) & (q != "") & (~search_df["user_id"].isin(matched_ids))]
    matched_ids |= set(exact_mobile["user_id"])

    startswith_id = search_df[ids_as_str.str.startswith(q) & (~search_df["user_id"].isin(matched_ids))] if q.isdigit() else search_df.iloc[0:0]
    matched_ids |= set(startswith_id["user_id"])

    mobile_contains = (
        search_df[mobiles_as_str.str.contains(q, regex=False) & (~search_df["user_id"].isin(matched_ids))]
        if q.isdigit() and len(q) >= 4 else search_df.iloc[0:0]
    )
    matched_ids |= set(mobile_contains["user_id"])

    label_match = search_df[
        search_df["_label_str"].str.contains(q, regex=False) & (~search_df["user_id"].isin(matched_ids))
    ]

    ranked = pd.concat([exact_id, exact_mobile, startswith_id, mobile_contains, label_match]).head(20)
    return [(row["search_label"], row["user_id"]) for _, row in ranked.iterrows()]


def show_user_360():
    st.markdown("<div class='section-header'>User 360</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SEARCH SELECTOR
    # st_searchbox reran the *entire* app on every debounced keystroke,
    # which is expensive on a file this size and felt like it was
    # "searching twice". A single-submit form only reruns once per
    # actual search, then a lightweight selectbox picks the exact user.
    # --------------------------------------------------------
    with st.form("user360_search_form", clear_on_submit=False):
        search_col, btn_col = st.columns([5, 1])
        query = search_col.text_input(
            "Search user",
            placeholder="Search by user ID, name, company, email, or mobile number",
            label_visibility="collapsed",
            key="user360_search_query",
        )
        submitted = btn_col.form_submit_button("Search", use_container_width=True)

    if submitted:
        st.session_state["user360_search_results"] = _search_users(query)
        st.session_state["user360_selected_user"] = None

    results = st.session_state.get("user360_search_results", [])

    if results:
        options = ["— Select a user —"] + [label for label, _ in results]
        choice = st.selectbox("Matching users", options, key="user360_result_picker", label_visibility="collapsed")
        if choice != "— Select a user —":
            st.session_state["user360_selected_user"] = next((uid for label, uid in results if label == choice), None)
    elif submitted:
        st.warning("No matching users found.")

    user_id = st.session_state.get("user360_selected_user")

    if not user_id:
        st.info("Search for a user above to view their full profile, revenue, activity, campaigns, and support history.")
        return

    user_id = int(user_id)

    # --------------------------------------------------------
    # PROFILE HEADER
    # --------------------------------------------------------
    profile = u360.get_user_profile(user_id) or {}
    membership = u360.get_user_membership_status(user_id) or {}

    user_name = profile.get("user_name") or f"User {user_id}"
    initials = "".join([p[0] for p in user_name.split()[:2]]).upper() or "U"
    safe_user_name = _safe_text(user_name, fallback=f"User {user_id}")

    status = membership.get("membership_status", "Basic - Standard")
    billed_plan_name = membership.get("billed_plan_name")
    plan_pill_html = (
        f'<span style="background:#F1F5F9;color:#475569;font-size:12px;font-weight:600;'
        f'padding:4px 12px;border-radius:6px;">{_safe_text(billed_plan_name)}</span>'
        if billed_plan_name else ""
    )
    date_pill_html = ""
    if status in ("Premium - Active", "Basic - Trial - Active"):
        renewal_date = _fmt_date(membership.get("billing_period_end_date"))
        date_pill_html = (
            f'<span style="background:#EFF6FF;color:#1E40AF;font-size:12px;font-weight:600;'
            f'padding:4px 12px;border-radius:6px;">Renews {renewal_date}</span>'
        )
    elif status in ("Premium - Expired", "Basic - Trial - Expired"):
        expired_date = _fmt_date(membership.get("billing_period_end_date"))
        date_pill_html = (
            f'<span style="background:#FEF2F2;color:#991B1B;font-size:12px;font-weight:600;'
            f'padding:4px 12px;border-radius:6px;">Expired {expired_date}</span>'
        )

    # Joined into ONE single-line string on purpose — if plan_pill_html/date_pill_html are
    # empty (e.g. a Basic-Standard user with no plan and no renewal date) and each sits on
    # its own line inside the multi-line f-string below, that line collapses to nothing but
    # the Python source's leading whitespace. Markdown treats a whitespace-only line in the
    # middle of an HTML block as a paragraph break, and everything after it — still carrying
    # that same source indentation — then gets parsed as an indented code block instead of
    # HTML. Joining everything into one variable with no embedded newlines avoids that entirely.
    pills_row_html = plan_pill_html + date_pill_html + _status_badge_html(status)

    st.markdown(f"""
    <div class="chart-card" style="padding:1.1rem 1.3rem;">
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
            <div style="width:48px;height:48px;border-radius:50%;background:#EFF6FF;display:flex;
                        align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#2563EB;flex-shrink:0;">{html.escape(initials)}</div>
            <div style="flex:1;min-width:200px;">
                <div style="font-weight:700;font-size:16px;color:#0F172A;">{safe_user_name}</div>
                <div style="font-size:13px;color:#64748B;">{_safe_text(profile.get('company_name'))} &bull; {_safe_text(profile.get('email_address'))}</div>
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">{pills_row_html}</div>
        </div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:14px;padding-top:12px;border-top:1px solid #F1F5F9;font-size:12.5px;color:#475569;">
            <div><b>Mobile:</b> {_safe_text(profile.get('mobile_number'))}</div>
            <div><b>User type:</b> {_safe_text(profile.get('user_type'))}</div>
            <div><b>SSO partner:</b> {_safe_text(profile.get('sso_partner_name'))}</div>
            <div><b>ARN:</b> {_safe_text(profile.get('arn_number'))}</div>
            <div><b>Registered:</b> {_fmt_date(profile.get('registered_at'))}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # KPI STRIP
    # --------------------------------------------------------
    revenue = u360.get_user_lifetime_revenue(user_id) or {}
    tenure = u360.get_user_tenure_activity(user_id) or {}
    issues = u360.get_user_open_issues_count(user_id) or {}
    scheduled_posts = u360.get_user_scheduled_posts_count(user_id)

    r1 = st.columns(4)
    r1[0].metric("Lifetime Revenue", _fmt_currency(revenue.get("lifetime_revenue", 0)))
    r1[1].metric("Total Invoices", f"{revenue.get('total_invoices', 0):,}")
    r1[2].metric("Tenure", f"{tenure.get('tenure_days', 0) or 0:,} days" if tenure.get("tenure_days") is not None else "\u2014")
    r1[3].metric("Scheduled Posts", f"{scheduled_posts:,}")

    r2 = st.columns(4)
    r2[0].metric("Last Login", _fmt_date(tenure.get("last_login")))
    r2[1].metric("Last Activity", _fmt_date(tenure.get("last_activity")), help="Excludes Post Planner activity.")
    r2[2].metric("Open Issues", f"{issues.get('open_issues', 0):,}")
    r2[3].metric("High Priority Open", f"{issues.get('open_high_priority', 0):,}")

    period_label = st.radio(
        "Totals period", ["All Time", "Last 30 Days"], horizontal=True, label_visibility="collapsed",
        key="user360_totals_period",
    )
    period = "30d" if period_label == "Last 30 Days" else "all_time"
    totals = u360.get_user_activity_login_totals(user_id, period=period) or {}

    r3 = st.columns(4)
    r3[0].metric(f"Total Activities ({period_label})", f"{totals.get('total_activities', 0):,}")
    r3[1].metric("Excl. Post Planner", f"{totals.get('total_activities_excl_post_planner', 0):,}")
    r3[2].metric(f"Total Logins ({period_label})", f"{totals.get('total_logins', 0):,}")
    r3[3].empty()

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SUB-TABS
    # --------------------------------------------------------
    revenue_tab, activity_tab, campaigns_tab, issues_tab = st.tabs(
        ["Revenue", "Activity", "Campaigns", "Issues"]
    )

    with revenue_tab:
        _render_revenue_tab(user_id, revenue)

    with activity_tab:
        _render_activity_tab(user_id)

    with campaigns_tab:
        _render_campaigns_tab(user_id)

    with issues_tab:
        _render_issues_tab(user_id)


# ================================================================
# REVENUE TAB
# ================================================================
def _render_revenue_tab(user_id, revenue):
    c1, c2 = st.columns(2)
    c1.metric("Lifetime Revenue", _fmt_currency(revenue.get("lifetime_revenue", 0)))
    c2.metric("Avg Invoice Amount", _fmt_currency(revenue.get("avg_invoice_amount", 0)))
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Revenue Trend", "Monthly revenue from this user's invoices.")
    df_trend = u360.get_user_revenue_trend(user_id)
    if df_trend is not None and not df_trend.empty:
        df_trend = df_trend.copy()
        df_trend["month"] = pd.to_datetime(df_trend["month"])
        fig = go.Figure(go.Scatter(
            x=df_trend["month"], y=df_trend["revenue"], mode="lines+markers",
            line=dict(color=BLUE, width=2.5, shape="spline"),
            fill="tozeroy", fillcolor=BLUE_LIGHT,
            hovertemplate="<b>%{x|%b %Y}</b><br>Revenue: \u20b9%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(height=280, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40),
                           hoverlabel=HOVER_LABEL, yaxis_title="Revenue")
        fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No revenue history for this user.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Invoice History", "Every invoice billed to this user, most recent first.")
    df_inv = u360.get_user_invoice_history(user_id)
    if df_inv is not None and not df_inv.empty:
        display_df = df_inv.rename(columns={
            "billed_plan_name": "Plan", "billing_period_start_date": "Start",
            "billing_period_end_date": "End", "amount_paid": "Amount",
            "billed_coupon_code": "Coupon", "razorpay_payment_id": "Payment ID",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No invoices for this user.")
    chart_card_close()


# ================================================================
# ACTIVITY TAB
# ================================================================
def _render_activity_tab(user_id):
    planner_label = st.radio(
        "Post Planner", ["With Post Planner", "Without Post Planner"], horizontal=True,
        label_visibility="collapsed", key="user360_activity_planner_toggle",
    )
    include_post_planner = planner_label == "With Post Planner"
    st.caption("Applies to Daily Activity Trend, Content Usage, and Premium vs Basic Content below. Feature Usage, Event Usage, and Login History are unaffected.")
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Daily Activity Trend", "Last 90 days.")
    df_daily = u360.get_user_daily_activity_trend(user_id, include_post_planner=include_post_planner)
    if df_daily is not None and not df_daily.empty:
        df_daily = df_daily.copy()
        df_daily["date"] = pd.to_datetime(df_daily["date"])
        fig = go.Figure(go.Scatter(
            x=df_daily["date"], y=df_daily["activities"], mode="lines",
            line=dict(color=GREEN, width=2.5, shape="spline"), fill="tozeroy", fillcolor="rgba(16,185,129,0.08)",
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Activities: <b>%{y}</b><extra></extra>",
        ))
        fig.update_layout(height=260, **CHART_BG, font=FONT, margin=dict(l=40, r=20, t=10, b=40), hoverlabel=HOVER_LABEL)
        fig.update_xaxes(showgrid=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, title_font=AXIS_FONT, tickfont=TICK_FONT)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No activity in the last 90 days.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        chart_card_open("Feature Usage", "This user's product feature adoption.")
        df_feat = u360.get_user_feature_usage(user_id)
        if df_feat is not None and not df_feat.empty:
            df_feat_sorted = df_feat.sort_values("events", ascending=True)
            fig = px.bar(df_feat_sorted, x="events", y="feature_type", orientation="h")
            fig.update_traces(marker_color=BLUE)
            fig = style_bar_chart(fig, height=260)
            fig.update_layout(xaxis_title="Events", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No feature usage data.")
        chart_card_close()

    with right:
        chart_card_open("Content Usage", "This user's content format interactions.")
        df_content = u360.get_user_content_usage(user_id, include_post_planner=include_post_planner)
        if df_content is not None and not df_content.empty:
            df_content_sorted = df_content.sort_values("interactions", ascending=True)
            fig = px.bar(df_content_sorted, x="interactions", y="content_type", orientation="h")
            fig.update_traces(marker_color=GREEN)
            fig = style_bar_chart(fig, height=260)
            fig.update_layout(xaxis_title="Interactions", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No content usage data.")
        chart_card_close()

    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Premium vs Basic Content", "Split of this user's content interactions by tier.")
    df_split = u360.get_user_content_premium_split(user_id, include_post_planner=include_post_planner)
    if df_split is not None and not df_split.empty:
        total = df_split["interactions"].sum()
        premium_row = df_split[df_split["content_tier"] == "Premium"]
        basic_row = df_split[df_split["content_tier"] == "Basic"]
        premium_n = int(premium_row["interactions"].iloc[0]) if not premium_row.empty else 0
        basic_n = int(basic_row["interactions"].iloc[0]) if not basic_row.empty else 0
        premium_pct = round(premium_n / total * 100, 1) if total else 0.0
        basic_pct = round(basic_n / total * 100, 1) if total else 0.0

        c1, c2 = st.columns(2)
        c1.metric("Premium Content Interactions", f"{premium_n:,}", f"{premium_pct}% of total", delta_color="off")
        c2.metric("Basic Content Interactions", f"{basic_n:,}", f"{basic_pct}% of total", delta_color="off")
    else:
        st.info("No content-tier data for this user.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Event Usage", "Distribution of this user's actions on Content features.")
    df_event = u360.get_user_event_usage(user_id)
    if df_event is not None and not df_event.empty:
        df_event_sorted = df_event.sort_values("events", ascending=True)
        fig = px.bar(df_event_sorted, x="events", y="event_type", orientation="h")
        fig.update_traces(marker_color=BLUE)
        fig = style_bar_chart(fig, height=240)
        fig.update_layout(xaxis_title="Events", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No event usage data.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Login History", "Most recent logins.")
    df_logins = u360.get_user_login_history(user_id, limit=20)
    if df_logins is not None and not df_logins.empty:
        display_df = df_logins.rename(columns={"logged_in_at": "Logged in at"})
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No login history for this user.")
    chart_card_close()


# ================================================================
# CAMPAIGNS TAB
# ================================================================
def _render_campaigns_tab(user_id):
    camp = u360.get_user_campaign_performance(user_id) or {}
    total_rows = camp.get("total_scheduled_rows", 0) or 0
    posted = camp.get("posted", 0) or 0
    pending = camp.get("pending", 0) or 0
    scheduled = camp.get("scheduled", 0) or 0
    failed = camp.get("failed", 0) or 0

    c1, c2 = st.columns(2)
    c1.metric("Total Scheduled Posts", f"{camp.get('total_scheduled_posts', 0):,}",
              help="Distinct scheduled_id, plus each null-scheduled_id row counted individually.")
    c2.metric("Posted", f"{posted:,}", f"{round(posted / total_rows * 100, 1) if total_rows else 0}% of total", delta_color="off")
    c3, c4 = st.columns(2)
    c3.metric("Pending", f"{pending:,}", f"{round(pending / total_rows * 100, 1) if total_rows else 0}% of total", delta_color="off")
    c4.metric("Scheduled", f"{scheduled:,}", f"{round(scheduled / total_rows * 100, 1) if total_rows else 0}% of total", delta_color="off")
    c5, c6 = st.columns(2)
    c5.metric("Failed", f"{failed:,}", f"{round(failed / total_rows * 100, 1) if total_rows else 0}% of total", delta_color="off")
    c6.metric("Publishing Success", f"{camp.get('publishing_success_rate', 0)}%")
    c7, c8 = st.columns(2)
    c7.metric("Automation Rate", f"{camp.get('automation_rate', 0)}%")
    c8.empty()
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Platform Distribution", "This user's scheduled posts by platform.")
    df_platform = u360.get_user_platform_status_breakdown(user_id)
    if df_platform is not None and not df_platform.empty:
        by_platform = df_platform.groupby("platform_name")["posts"].sum().reset_index().sort_values("posts", ascending=True)
        colors = [PLATFORM_COLORS.get(p, BLUE) for p in by_platform["platform_name"]]
        fig = go.Figure(go.Bar(x=by_platform["posts"], y=by_platform["platform_name"], orientation="h", marker_color=colors))
        fig = style_bar_chart(fig, height=240)
        fig.update_layout(xaxis_title="Posts", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        with st.expander("Status breakdown by platform"):
            pivot = df_platform.pivot_table(index="posting_status", columns="platform_name", values="posts", fill_value=0, aggfunc="sum")
            st.dataframe(pivot, use_container_width=True)
    else:
        st.info("No scheduled posts for this user.")
    chart_card_close()
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Scheduled Posts", "This user's most recent scheduled posts.")
    df_posts = u360.get_user_scheduled_posts_list(user_id, limit=20)
    if df_posts is not None and not df_posts.empty:
        display_df = df_posts.rename(columns={
            "scheduled_id": "Scheduled ID", "platform_name": "Platform", "posting_status": "Status",
            "is_manual_post": "Manual", "scheduled_for": "Scheduled At", "posted_on_time": "Posted On",
            "content_title": "Content", "content_type_name": "Content Type",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No scheduled posts for this user.")
    chart_card_close()


# ================================================================
# ISSUES TAB
# ================================================================
def _render_issues_tab(user_id):
    summary = u360.get_user_issues_summary(user_id) or {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Issues", f"{summary.get('total_issues', 0):,}")
    c2.metric("Closed", f"{summary.get('closed_issues', 0):,}")
    c3.metric("Open", f"{summary.get('open_issues', 0):,}")
    c4, c5 = st.columns(2)
    c4.metric("High Priority", f"{summary.get('high_priority_issues', 0):,}")
    avg_res = summary.get("avg_resolution_days")
    c5.metric("Avg Resolution Time", f"{avg_res} days" if avg_res is not None else "\u2014")
    st.markdown("<br>", unsafe_allow_html=True)

    chart_card_open("Support Tickets", "This user's most recent tickets. Select one below to view its activity timeline.")
    df_tickets = u360.get_user_ticket_list(user_id, limit=20)
    if df_tickets is not None and not df_tickets.empty:
        display_df = df_tickets.rename(columns={
            "ticket_id": "Ticket ID", "title": "Title", "issue_type": "Type", "priority": "Priority",
            "status": "Status", "source_channel": "Channel", "created_at": "Created",
            "first_response_at": "First Response", "resolved_at": "Resolved", "closed_at": "Closed",
            "reopened_count": "Reopens",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        ticket_options = ["Select a ticket..."] + df_tickets["ticket_id"].tolist()
        selected_ticket = st.selectbox("View activity timeline for ticket", options=ticket_options,
                                        key="user360_ticket_select")

        if selected_ticket != "Select a ticket...":
            st.markdown(f"**Activity timeline &mdash; {_safe_text(selected_ticket)}**")
            df_timeline = u360.get_ticket_activity_timeline(selected_ticket)
            if df_timeline is not None and not df_timeline.empty:
                for _, row in df_timeline.iterrows():
                    status_change = ""
                    if row.get("old_status") and row.get("new_status"):
                        status_change = f" &mdash; {_safe_text(row['old_status'])} \u2192 {_safe_text(row['new_status'])}"
                    st.markdown(
                        insight_box(
                            f"<b>{_safe_text(row.get('activity_type'), 'Activity')}</b>{status_change}"
                            f"<br>{_safe_text(row.get('activity_summary') or row.get('notes'), '')}"
                            f"<br><span style='color:#94A3B8;font-size:11px;'>{_safe_text(row.get('created_by'), 'Unknown')} "
                            f"&bull; {_fmt_date(row.get('created_at'), '%d %b %Y, %H:%M')}</span>",
                            title="Log Entry",
                        ),
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No activity found.")
    else:
        st.info("No support tickets for this user.")
    chart_card_close()