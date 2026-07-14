import streamlit as st
import dashboard_data as dd

# ============================================================
# 🛠️ ADMIN PANEL — Manage Users & Role Access
# Rendered only when the logged-in user's role is Admin.
# Two sections:
#   1. Manage Users        -> add / change role / remove app_users rows
#   2. Manage Role Access   -> per-role checkboxes for each dashboard section
# ============================================================

ALL_SECTIONS = [
    ("Revenue", "revenue"),
    ("Subscriptions", "subscriptions"),
    ("Engineering", "engineering"),
    ("Product Usage", "product_usage"),
    ("Content Analytics", "content_analytics"),
    ("Customer Support", "customer_support"),
    ("User 360", "user_360"),
]


def render_admin_panel():
    st.markdown("### ⚙️ Admin Settings")
    tab_users, tab_roles = st.tabs(["Manage Users", "Manage Role Access"])

    # --------------------------------------------------------
    # TAB — Manage Users
    # --------------------------------------------------------
    with tab_users:
        st.markdown("#### Current Users")
        df_users = dd.get_all_app_users()
        if df_users is not None and not df_users.empty:
            st.dataframe(df_users, use_container_width=True, hide_index=True)
        else:
            st.info("No users found in app_users yet.")

        st.markdown("#### Add or Update a User")
        roles = dd.get_distinct_roles() or ["Admin"]

        with st.form("add_update_user_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1.5])
            new_email = c1.text_input("Email")
            new_role = c2.selectbox("Role", roles)
            new_name = c3.text_input("Name (optional)")
            submitted = st.form_submit_button("Save User")

            if submitted:
                if not new_email:
                    st.error("Email is required.")
                else:
                    dd.upsert_app_user(new_email.strip().lower(), new_role, new_name.strip())
                    st.success(f"Saved {new_email} as {new_role}.")
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("#### Remove a User")
        if df_users is not None and not df_users.empty:
            emails = df_users["email"].tolist()
            d1, d2 = st.columns([3, 1])
            remove_email = d1.selectbox("Select user to remove", emails, key="remove_user_select")
            if d2.button("Remove", type="secondary"):
                dd.delete_app_user(remove_email)
                st.success(f"Removed {remove_email}.")
                st.cache_data.clear()
                st.rerun()

    # --------------------------------------------------------
    # TAB — Manage Role Access
    # --------------------------------------------------------
    with tab_roles:
        st.markdown("#### Section Access by Role")
        st.caption("Toggle which dashboard tabs each role can see. Changes apply immediately.")

        roles = dd.get_distinct_roles() or ["Admin"]
        df_perms = dd.get_all_role_permissions()

        selected_role = st.selectbox("Role", roles, key="role_perm_select")

        current = {}
        if df_perms is not None and not df_perms.empty:
            role_rows = df_perms[df_perms["role"] == selected_role]
            current = dict(zip(role_rows["section"], role_rows["has_access"]))

        with st.form(f"role_perm_form_{selected_role}"):
            new_values = {}
            cols = st.columns(2)
            for i, (label, section_key) in enumerate(ALL_SECTIONS):
                col = cols[i % 2]
                new_values[section_key] = col.checkbox(
                    label, value=bool(current.get(section_key, False)), key=f"perm_{selected_role}_{section_key}"
                )
            save_perms = st.form_submit_button("Save Role Access")

            if save_perms:
                for _, section_key in ALL_SECTIONS:
                    dd.update_role_permission(selected_role, section_key, new_values[section_key])
                st.success(f"Updated access for {selected_role}.")
                st.cache_data.clear()
                st.rerun()

        st.markdown("---")
        with st.expander("Add a brand-new role"):
            with st.form("new_role_form", clear_on_submit=True):
                new_role_name = st.text_input("New role name")
                add_role_submit = st.form_submit_button("Create Role")
                if add_role_submit:
                    if not new_role_name:
                        st.error("Role name is required.")
                    else:
                        # seed the new role with no access; admin can check boxes above afterward
                        for _, section_key in ALL_SECTIONS:
                            dd.update_role_permission(new_role_name.strip(), section_key, False)
                        st.success(f"Created role '{new_role_name}'. Select it above to set its access.")
                        st.cache_data.clear()
                        st.rerun()
