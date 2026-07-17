import pandas as pd
from dashboard_data import supabase

# ============================================================
# 👤 USER 360 — DATA LAYER
# Thin wrappers over the user360_* Supabase views (see
# user360_views.sql). Each view computes its metric for every
# user at once; these functions just filter by whichever user_id
# was picked in the search dropdown via .eq("user_id", ...).
# ============================================================


def _single(view_name, user_id, default=None):
    """For views where every user_id is guaranteed exactly one row (built off a LEFT JOIN from users)."""
    result = supabase.table(view_name).select("*").eq("user_id", user_id).execute()
    rows = result.data
    return rows[0] if rows else default


def _single_or_default(view_name, user_id, defaults):
    """For views built off a plain GROUP BY — a user with zero matching rows won't appear at all."""
    result = supabase.table(view_name).select("*").eq("user_id", user_id).execute()
    rows = result.data
    if rows:
        return rows[0]
    return {**defaults, "user_id": user_id}


def _many(view_name, user_id, order_col=None, desc=True, limit=None):
    query = supabase.table(view_name).select("*").eq("user_id", user_id)
    if order_col:
        query = query.order(order_col, desc=desc)
    if limit:
        query = query.limit(limit)
    return pd.DataFrame(query.execute().data)


# ------------------------------------------------------------
# Search / Profile
# ------------------------------------------------------------
def get_user_search_list():
    """Paginated fetch — this list can exceed Supabase's default 1000-row response cap.
    Only pulls the 3 columns actually used by the search/ranking logic, to keep the
    payload (and therefore the fetch time) as small as possible."""
    all_rows, start, page_size = [], 0, 1000
    while True:
        result = (
            supabase.table("user360_search_list")
            .select("user_id, mobile_number, search_label")
            .range(start, start + page_size - 1)
            .execute()
        )
        rows = result.data
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size
    return pd.DataFrame(all_rows)


def get_user_profile(user_id):
    return _single("user360_profile", user_id, default={})


# ------------------------------------------------------------
# Overview KPIs
# ------------------------------------------------------------
def get_user_membership_status(user_id):
    return _single("user360_membership_status", user_id, default={"membership_status": "Basic - Standard"})


def get_user_lifetime_revenue(user_id):
    return _single_or_default(
        "user360_lifetime_revenue", user_id,
        {"lifetime_revenue": 0, "total_invoices": 0, "avg_invoice_amount": 0},
    )


def get_user_tenure_activity(user_id):
    return _single("user360_tenure_activity", user_id, default={})


def get_user_open_issues_count(user_id):
    return _single_or_default(
        "user360_open_issues", user_id,
        {"open_issues": 0, "open_high_priority": 0},
    )


def get_user_scheduled_posts_count(user_id):
    row = _single_or_default("user360_scheduled_posts_count", user_id, {"scheduled_posts": 0})
    return row.get("scheduled_posts", 0)


def get_user_activity_login_totals(user_id, period="all_time"):
    view_name = "user360_totals_30d" if period == "30d" else "user360_totals_all_time"
    return _single(view_name, user_id, default={
        "total_activities": 0, "total_activities_excl_post_planner": 0, "total_logins": 0,
    })


# ------------------------------------------------------------
# Activity tab
# ------------------------------------------------------------
def get_user_feature_usage(user_id):
    return _many("user360_feature_usage", user_id, order_col="events")


def get_user_content_usage(user_id, include_post_planner=True):
    view_name = "user360_content_usage_with_planner" if include_post_planner else "user360_content_usage_without_planner"
    return _many(view_name, user_id, order_col="interactions")


def get_user_event_usage(user_id):
    return _many("user360_event_usage", user_id, order_col="events")


def get_user_content_premium_split(user_id, include_post_planner=True):
    view_name = "user360_content_premium_split_with_planner" if include_post_planner else "user360_content_premium_split_without_planner"
    return _many(view_name, user_id)


def get_user_daily_activity_trend(user_id, include_post_planner=True):
    view_name = "user360_daily_activity_trend_with_planner" if include_post_planner else "user360_daily_activity_trend_without_planner"
    return _many(view_name, user_id, order_col="date", desc=False)


def get_user_login_history(user_id, limit=20):
    return _many("user360_login_history", user_id, order_col="logged_in_at", limit=limit)


# ------------------------------------------------------------
# Campaigns tab
# ------------------------------------------------------------
def get_user_campaign_performance(user_id):
    return _single_or_default(
        "user360_campaign_performance", user_id,
        {
            "total_scheduled_posts": 0, "total_scheduled_rows": 0, "posted": 0,
            "failed": 0, "pending": 0, "scheduled": 0, "publishing_success_rate": 0.0, "automation_rate": 0.0,
        },
    )


def get_user_platform_status_breakdown(user_id):
    return _many("user360_platform_status_breakdown", user_id)


def get_user_scheduled_posts_list(user_id, limit=20):
    return _many("user360_scheduled_posts_list", user_id, order_col="scheduled_for", limit=limit)


# ------------------------------------------------------------
# Issues tab
# ------------------------------------------------------------
def get_user_issues_summary(user_id):
    return _single_or_default(
        "user360_issues_summary", user_id,
        {
            "total_issues": 0, "closed_issues": 0, "open_issues": 0,
            "high_priority_issues": 0, "avg_resolution_days": 0,
        },
    )


def get_user_ticket_list(user_id, limit=20):
    return _many("user360_ticket_list", user_id, order_col="created_at", limit=limit)


def get_ticket_activity_timeline(ticket_id):
    """Filtered by ticket_id, not user_id — call after the person clicks a ticket in the Query 17 table."""
    result = (
        supabase.table("user360_ticket_activity_log")
        .select("*")
        .eq("ticket_id", ticket_id)
        .order("created_at", desc=True)
        .execute()
    )
    return pd.DataFrame(result.data)


# ------------------------------------------------------------
# Revenue tab
# ------------------------------------------------------------
def get_user_invoice_history(user_id):
    return _many("user360_invoice_history", user_id, order_col="billing_period_start_date")


def get_user_revenue_trend(user_id):
    return _many("user360_revenue_trend", user_id, order_col="month", desc=False)