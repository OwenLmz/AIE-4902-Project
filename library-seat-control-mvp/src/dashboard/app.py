from __future__ import annotations

import html
import time

import streamlit as st

from src.dashboard import components
from src.dashboard.data_provider import load_dashboard_data
from src.dashboard.i18n import LANGUAGE_OPTIONS, current_language, language_from_label, t


def main() -> None:
    language = current_language()
    st.set_page_config(
        page_title=t("app.page_title", language),
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles = getattr(components, "inject_global_styles", None)
    if callable(inject_styles):
        inject_styles()

    dashboard_data = load_dashboard_data()
    header_left, header_right = st.columns([3.1, 1.4])
    with header_right:
        lang_col, mode_col, refresh_col = st.columns([1.05, 1.2, 1.2])
        with lang_col:
            selected_language_label = st.radio(
                "Language",
                list(LANGUAGE_OPTIONS.keys()),
                index=list(LANGUAGE_OPTIONS.values()).index(language),
                horizontal=True,
                key="ui_language_selector",
                label_visibility="collapsed",
            )
            selected_language = language_from_label(selected_language_label)
            if selected_language != language:
                st.session_state["ui_language"] = selected_language
                st.rerun()
        with mode_col:
            admin_mode = st.toggle(t("app.admin_mode"), value=False)
        with refresh_col:
            auto_refresh = st.toggle(t("app.auto_refresh"), value=False)
    with header_left:
        seat_updated_at = html.escape(components.format_datetime(dashboard_data.get("seat_updated_at"), t("empty.no_seat_data")))
        refresh_status = t("app.refresh_on") if auto_refresh else t("app.refresh_off")
        mode_status = t("app.admin_mode") if admin_mode else t("app.student_mode")
        st.markdown(
            "<div class='app-header'>"
            "<div>"
            f"<h1>{html.escape(t('app.title'))}</h1>"
            f"<p>{html.escape(t('app.subtitle'))}</p>"
            "</div>"
            "<div class='status-strip'>"
            f"<span class='status-pill'>{html.escape(t('app.mock_status'))}</span>"
            f"<span class='status-pill'>{html.escape(t('app.current'))}: {html.escape(mode_status)}</span>"
            f"<span class='status-pill'>{html.escape(t('app.seat_updated'))}: {seat_updated_at}</span>"
            f"<span class='status-pill'>{html.escape(t('app.refresh'))}: {html.escape(refresh_status)}</span>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    components.render_role_workspace(dashboard_data, admin_mode=admin_mode, auto_refresh_enabled=auto_refresh)

    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main()
