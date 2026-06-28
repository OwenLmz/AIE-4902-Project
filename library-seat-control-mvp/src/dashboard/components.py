from __future__ import annotations

import html
from datetime import datetime, timedelta
from typing import Any

import streamlit as st
import streamlit.components.v1 as st_components

from src.dashboard.i18n import crowd_level_text, current_language, status_text, t
from src.dashboard.styles import status_label
from src.dashboard.seat_layout import build_svg_seat_layout, group_seats_by_layout

READ_ERROR_CODES = {"missing_file", "invalid_json"}
SEAT_EMPTY_CODES = {"empty_seats", "missing_field", "duplicate_seat_id"}
CROWD_EMPTY_CODES = {"missing_file", "invalid_json", "missing_field", "invalid_current_people"}
AREA_STATUS_NO_CAPACITY = "暂无可用容量"
ANOMALY_STATUSES = {"POSSIBLY_OCCUPIED", "SUSPICIOUS"}
RECOMMENDED_AREA_LABEL = "推荐去"
CONSIDER_AREA_LABEL = "可考虑"
AVOID_AREA_LABEL = "不建议"
STUDENT_SECTION_TABS = ["总览", "区域推荐", "座位地图", "人流趋势"]
ADMIN_SECTION_TABS = ["管理概览", "异常座位", "异常定位"]
CROWD_TREND_RANGE_OPTIONS = ["近3小时", "今日", "近3天"]


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --library-green: #24745a;
            --library-green-dark: #16513f;
            --library-green-soft: #e8f4ee;
            --library-bg: #f3f6f4;
            --library-sidebar: #111827;
            --library-sidebar-muted: #9ca3af;
            --library-border: #dfe7e2;
        }
        .stApp {
            background: var(--library-bg);
        }
        .main .block-container {
            max-width: 1320px;
            padding-top: 0.9rem;
            padding-bottom: 2rem;
        }
        [data-testid="stSidebar"] {
            display: none;
        }
        .app-header {
            display: flex;
            align-items: flex-start;
            justify-content: flex-start;
            gap: 16px;
            margin-bottom: 6px;
        }
        .app-header h1 {
            margin: 0;
            font-size: 26px;
            line-height: 1.18;
            color: #101828;
            letter-spacing: 0;
            max-width: 320px;
        }
        .app-header p {
            margin: 3px 0 0;
            color: #667085;
            font-size: 14px;
        }
        .status-strip {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 2px;
            max-width: 620px;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            padding: 6px 10px;
            border-radius: 999px;
            background: var(--library-green-soft);
            color: var(--library-green-dark);
            font-size: 12px;
            line-height: 1.2;
            white-space: nowrap;
            border: 1px solid #cce4d7;
        }
        label:has(input[type="checkbox"][aria-checked="true"]) > div:first-child {
            background: var(--library-green) !important;
        }
        label:has(input[type="checkbox"][aria-checked="true"]) > div:first-child > div {
            background: #ffffff !important;
        }
        label:has(input[type="checkbox"][aria-checked="false"]) > div:first-child {
            background: #c7cdd5 !important;
        }
        .metric-card {
            min-height: 104px;
            padding: 16px 18px;
            border: 1px solid var(--library-border);
            border-left: 4px solid var(--library-green);
            border-radius: 8px;
            background: #ffffff;
            box-shadow: 0 8px 22px rgba(17, 24, 39, 0.05);
        }
        .metric-card.warning {
            border-left-color: #f79009;
            background: #fffbeb;
        }
        .metric-card.critical {
            border-left-color: #d92d20;
            background: #fef3f2;
        }
        .metric-label {
            color: #667085;
            font-size: 13px;
            line-height: 1.4;
            margin-bottom: 8px;
        }
        .metric-value {
            color: #0f172a;
            font-size: 24px;
            line-height: 1.22;
            font-weight: 700;
            word-break: normal;
            overflow-wrap: anywhere;
        }
        .metric-help {
            margin-top: 8px;
            color: #667085;
            font-size: 12px;
            line-height: 1.35;
        }
        .section-note {
            color: #667085;
            font-size: 13px;
            margin: -4px 0 12px;
        }
        .workspace-frame {
            margin-top: 10px;
        }
        div[data-testid="stColumn"]:has([role="radiogroup"][aria-label="功能导航"]) {
            background: linear-gradient(180deg, #111827 0%, #152033 100%) !important;
            border: 1px solid #263241 !important;
            border-radius: 14px !important;
            padding: 18px 16px !important;
            min-height: 500px;
            box-shadow: 0 18px 34px rgba(15, 23, 42, 0.18) !important;
        }
        div[data-testid="stColumn"]:has([role="radiogroup"][aria-label="功能导航"]) [data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        div[data-testid="stColumn"]:has([role="radiogroup"][aria-label="功能导航"]) * {
            color: #e5e7eb;
        }
        div[data-testid="stColumn"]:has(.module-heading) {
            background: #ffffff !important;
            border: 1px solid var(--library-border) !important;
            border-radius: 14px !important;
            padding: 16px 20px !important;
            min-height: 500px;
            box-shadow: 0 10px 24px rgba(17, 24, 39, 0.06) !important;
        }
        div[data-testid="stColumn"]:has(.module-heading) [data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        .side-panel {
            padding: 16px;
            border: 1px solid #e4e7ec;
            border-radius: 12px;
            background: var(--library-sidebar);
            min-height: 500px;
        }
        .side-panel-title {
            color: #f9fafb;
            font-size: 16px;
            font-weight: 800;
            line-height: 1.35;
            margin-bottom: 4px;
        }
        .side-panel-subtitle {
            color: var(--library-sidebar-muted);
            font-size: 13px;
            line-height: 1.45;
            margin-bottom: 14px;
        }
        .mode-badge {
            display: inline-flex;
            align-items: center;
            margin-bottom: 12px;
            padding: 5px 10px;
            border-radius: 999px;
            background: rgba(36, 116, 90, 0.18);
            border: 1px solid rgba(125, 211, 172, 0.35);
            color: #d1fae5;
            font-size: 12px;
            font-weight: 700;
        }
        .content-panel {
            padding: 18px;
            border: 1px solid #eaecf0;
            border-radius: 12px;
            background: #ffffff;
            min-height: 500px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        div[role="radiogroup"] {
            gap: 8px;
        }
        div[role="radiogroup"] label {
            padding: 10px 12px;
            border: 1px solid #e4e7ec;
            border-radius: 10px;
            background: #ffffff;
            margin-bottom: 8px;
        }
        div[role="radiogroup"] label:has(input:checked) {
            border-color: #9fd5bd;
            background: var(--library-green-soft);
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.06);
        }
        div[role="radiogroup"]:not([aria-label="功能导航"]) label > div:first-child {
            display: none !important;
        }
        div[role="radiogroup"]:not([aria-label="功能导航"]) label > input {
            opacity: 0 !important;
            position: absolute !important;
            pointer-events: none !important;
        }
        div[role="radiogroup"]:not([aria-label="功能导航"]) label {
            min-height: 42px;
            align-items: center;
            justify-content: center;
            color: #344054 !important;
        }
        div[role="radiogroup"]:not([aria-label="功能导航"]) label p {
            color: #344054 !important;
            font-weight: 700;
        }
        div[role="radiogroup"][aria-label="Language"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 6px !important;
            align-items: center !important;
        }
        div[role="radiogroup"][aria-label="Language"] label {
            min-width: 44px !important;
            min-height: 38px !important;
            margin-bottom: 0 !important;
            padding: 8px 10px !important;
            white-space: nowrap !important;
        }
        div[role="radiogroup"][aria-label="Language"] label p {
            white-space: nowrap !important;
        }
        div[role="radiogroup"]:not([aria-label="功能导航"]) label:has(input:checked) {
            border-color: #7dd3ac !important;
            background: var(--library-green-soft) !important;
            box-shadow: 0 6px 16px rgba(36, 116, 90, 0.12) !important;
        }
        div[role="radiogroup"]:not([aria-label="功能导航"]) label:has(input:checked) p {
            color: var(--library-green-dark) !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] {
            gap: 10px !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] label {
            display: flex;
            min-height: 46px;
            align-items: center;
            border-color: #263241 !important;
            background: #17212f !important;
            color: #d1d5db !important;
            padding: 12px 14px !important;
            border-radius: 12px !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] label > div:first-child {
            display: none !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] label > input {
            opacity: 0 !important;
            position: absolute !important;
            pointer-events: none !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] label p {
            color: #d1d5db !important;
            font-weight: 700;
        }
        div[role="radiogroup"][aria-label="功能导航"] label:hover {
            border-color: #3d4b60 !important;
            background: #202c3d !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] label:has(input:checked) {
            border-color: #7dd3ac !important;
            background: linear-gradient(135deg, #24745a 0%, #1f5d49 100%) !important;
            box-shadow: inset 4px 0 0 #a7f3d0, 0 10px 20px rgba(0, 0, 0, 0.20) !important;
        }
        div[role="radiogroup"][aria-label="功能导航"] label:has(input:checked) p {
            color: #ffffff !important;
        }
        .module-heading {
            margin: 2px 0 12px;
        }
        .module-heading h2 {
            margin: 0;
            color: #101828;
            font-size: 22px;
            line-height: 1.25;
            letter-spacing: 0;
        }
        .module-heading p {
            margin: 5px 0 0;
            color: #667085;
            font-size: 14px;
            line-height: 1.5;
        }
        .decision-callout {
            margin: 14px 0 4px;
            padding: 14px 16px;
            border: 1px solid #cce4d7;
            border-radius: 10px;
            background: #f0faf5;
            color: #16513f;
            font-size: 14px;
            line-height: 1.65;
        }
        .decision-callout strong {
            color: #052e16;
        }
        div[data-testid="stTabs"] > div > div > div[data-baseweb="tab-list"] {
            gap: 10px !important;
            padding: 8px !important;
            margin: 12px 0 18px !important;
            border: 1px solid #e4e7ec !important;
            border-radius: 12px !important;
            background: #f8fafc !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
        }
        button[data-testid="stTab"] {
            min-height: 42px !important;
            padding: 9px 18px !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            background: transparent !important;
            color: #475467 !important;
            font-weight: 700 !important;
            transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
        }
        button[data-testid="stTab"] p {
            font-size: 14px !important;
            font-weight: 700 !important;
            margin: 0 !important;
        }
        button[data-testid="stTab"][aria-selected="true"] {
            background: #ffffff !important;
            border-color: #b8c4d8 !important;
            color: #101828 !important;
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.08) !important;
        }
        button[data-testid="stTab"][aria-selected="true"] p {
            color: #101828 !important;
        }
        div[data-baseweb="tab-highlight"],
        div[data-baseweb="tab-border"] {
            display: none !important;
        }
        .recommendation-card {
            padding: 18px 20px;
            border: 1px solid #9fd5bd;
            border-left: 5px solid var(--library-green);
            border-radius: 10px;
            background: linear-gradient(135deg, #e8f4ee 0%, #f7fcfa 100%);
            color: var(--library-green-dark);
            margin-bottom: 10px;
            line-height: 1.6;
        }
        .recommendation-card .recommendation-title {
            display: block;
            margin-bottom: 4px;
            font-size: 17px;
            font-weight: 800;
            color: #052e16;
        }
        .recommendation-card strong {
            color: #052e16;
        }
        .area-card {
            min-height: 118px;
            padding: 14px 16px;
            border: 1px solid var(--library-border);
            border-radius: 8px;
            background: #ffffff;
            box-shadow: 0 8px 22px rgba(17, 24, 39, 0.05);
            margin-bottom: 12px;
        }
        .area-card.recommended {
            border-color: #9fd5bd;
            background: var(--library-green-soft);
        }
        .area-card.consider {
            border-color: #fedf89;
            background: #fffbeb;
        }
        .area-card.avoid {
            background: #f8fafc;
            color: #475467;
        }
        .area-card-title {
            color: #101828;
            font-size: 16px;
            font-weight: 700;
            line-height: 1.35;
            margin-bottom: 8px;
        }
        .area-card-meta {
            color: #475467;
            font-size: 13px;
            line-height: 1.55;
        }
        .area-card-label {
            display: inline-flex;
            margin-bottom: 8px;
            padding: 3px 8px;
            border-radius: 999px;
            background: #ffffff;
            color: var(--library-green-dark);
            font-size: 12px;
            font-weight: 700;
        }
        .detail-card {
            padding: 14px 16px;
            border: 1px solid var(--library-border);
            border-radius: 8px;
            background: #ffffff;
            box-shadow: 0 8px 22px rgba(17, 24, 39, 0.05);
            margin-bottom: 12px;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 9px 16px;
        }
        .detail-item {
            min-width: 0;
        }
        .detail-label {
            color: #667085;
            font-size: 12px;
            line-height: 1.3;
            margin-bottom: 2px;
        }
        .detail-value {
            color: #101828;
            font-size: 14px;
            line-height: 1.4;
            font-weight: 600;
            word-break: break-word;
        }
        .next-step-card {
            margin-top: 12px;
            padding: 12px 14px;
            border: 1px solid #d6ece0;
            border-radius: 10px;
            background: #f8fffb;
            color: #16513f;
            font-size: 13px;
            line-height: 1.55;
        }
        .anomaly-card-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
        }
        .anomaly-card {
            padding: 14px 16px;
            border: 1px solid #fecaca;
            border-left: 5px solid #d92d20;
            border-radius: 10px;
            background: #fff7f7;
            box-shadow: 0 8px 20px rgba(127, 29, 29, 0.05);
        }
        .anomaly-card-title {
            color: #7f1d1d;
            font-size: 18px;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .anomaly-card-meta {
            color: #344054;
            font-size: 13px;
            line-height: 1.55;
        }
        .cinema-seat-map {
            border: 1px solid #eaecf0;
            border-radius: 8px;
            padding: 20px;
            background:
                linear-gradient(#f8fafc 1px, transparent 1px),
                linear-gradient(90deg, #f8fafc 1px, transparent 1px),
                #ffffff;
            background-size: 28px 28px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .cinema-screen {
            text-align: center;
            color: #667085;
            font-size: 12px;
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 2px solid #d0d5dd;
        }
        .seat-row {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        .seat-chip {
            min-width: 48px;
            height: 38px;
            padding: 0 6px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid transparent;
            box-sizing: border-box;
            position: relative;
            line-height: 1;
        }
        .seat-free {
            background: #d1fadf;
            color: #027a48;
            border-color: #a6f4c5;
        }
        .seat-free-strong {
            background: #12b76a;
            color: #ffffff;
            border-color: #039855;
        }
        .seat-occupied {
            background: #d1e9ff;
            color: #175cd3;
            border-color: #84caff;
        }
        .seat-occupied-muted {
            background: #e0e7f2;
            color: #475467;
            border-color: #cbd5e1;
        }
        .seat-suspected {
            background: #fedf89;
            color: #93370d;
            border-color: #fdb022;
        }
        .seat-suspected-strong {
            background: #d92d20;
            color: #ffffff;
            border-color: #b42318;
        }
        .seat-unavailable {
            background: #f2f4f7;
            color: #667085;
            border-color: #d0d5dd;
        }
        .seat-selected {
            outline: 3px solid #101828;
            outline-offset: 2px;
        }
        .seat-recommended {
            box-shadow: 0 0 0 3px rgba(18, 183, 106, 0.24);
        }
        .seat-recommended::after {
            content: "★";
            position: absolute;
            top: -10px;
            right: -6px;
            font-size: 12px;
            color: #f79009;
        }
        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            align-items: center;
            margin-top: 12px;
            font-size: 13px;
            color: #475467;
        }
        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }
        .legend-dot.free {
            background: #12b76a;
        }
        .legend-dot.occupied {
            background: #84caff;
        }
        .legend-dot.suspected {
            background: #f79009;
        }
        .legend-dot.selected {
            border: 2px solid #101828;
            background: #ffffff;
            box-sizing: border-box;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _is_read_error(code: str | None) -> bool:
    return code in READ_ERROR_CODES


def format_datetime(value: Any, empty_text: str = "暂无数据") -> str:
    if not value:
        return empty_text
    parsed = _parse_timestamp(value)
    if parsed:
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    return str(value).replace("T", " ")


def _format_timestamp(value: Any, empty_text: str) -> str:
    return format_datetime(value, empty_text)


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_bool(value: Any) -> str:
    if value is True:
        return t("seat.yes")
    if value is False:
        return t("seat.no")
    return t("empty.no_data")


def _format_minutes(value: Any) -> str:
    if value is None:
        return t("empty.no_data")
    return f"{value} {t('unit.minutes')}"


def _seat_count(value: Any) -> str:
    return f"{value} {t('unit.seats')}"


def _people_count(value: Any) -> str:
    return f"{value} {t('unit.people')}"


def _metric_card(label: str, value: Any, help_text: str | None = None, tone: str | None = None) -> str:
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    help_html = f"<div class='metric-help'>{html.escape(help_text)}</div>" if help_text else ""
    tone_class = f" {html.escape(tone)}" if tone in {"warning", "critical"} else ""
    return (
        f"<div class='metric-card{tone_class}'>"
        f"<div class='metric-label'>{safe_label}</div>"
        f"<div class='metric-value'>{safe_value}</div>"
        f"{help_html}"
        "</div>"
    )


def _module_heading(title: str, description: str) -> None:
    st.markdown(
        "<div class='module-heading'>"
        f"<h2>{html.escape(title)}</h2>"
        f"<p>{html.escape(description)}</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def _detail_card(items: list[tuple[str, Any]]) -> str:
    rendered = []
    for label, value in items:
        rendered.append(
            "<div class='detail-item'>"
            f"<div class='detail-label'>{html.escape(str(label))}</div>"
            f"<div class='detail-value'>{html.escape(str(value or '暂无数据'))}</div>"
            "</div>"
        )
    return "<div class='detail-card'><div class='detail-grid'>" + "".join(rendered) + "</div></div>"


def _decision_callout(title: str, body: str) -> str:
    return (
        "<div class='decision-callout'>"
        f"<strong>{html.escape(title)}</strong><br>"
        f"{html.escape(body)}"
        "</div>"
    )


def _seat_data_available(data: dict[str, Any]) -> bool:
    return bool(data.get("seats")) and data.get("errors", {}).get("seat") not in READ_ERROR_CODES


def _crowd_data_available(data: dict[str, Any]) -> bool:
    error = data.get("errors", {}).get("crowd")
    return error not in CROWD_EMPTY_CODES


def render_data_status(data: dict[str, Any], auto_refresh_enabled: bool) -> None:
    errors = data.get("errors", {})
    if _is_read_error(errors.get("seat")) or _is_read_error(errors.get("crowd")):
        st.error(t("empty.read_failed"))


def render_student_summary(data: dict[str, Any]) -> None:
    seats = data.get("seats", [])
    crowd = data.get("crowd", {})
    errors = data.get("errors", {})

    current_people = crowd.get("current_people")
    capacity = crowd.get("capacity")
    crowd_level = crowd.get("crowd_level")
    forecast_30m = crowd.get("forecast_30m")

    if errors.get("crowd") == "invalid_capacity":
        people_capacity_text = t("summary.forecast_unavailable")
        crowd_level_label = t("summary.forecast_unavailable")
    elif not _crowd_data_available(data) or current_people is None:
        people_capacity_text = t("empty.no_crowd_data")
        crowd_level_label = t("empty.no_crowd_data")
    elif capacity is None:
        people_capacity_text = t("summary.forecast_unavailable")
        crowd_level_label = t("summary.forecast_unavailable")
    else:
        people_capacity_text = f"{current_people} / {capacity} {t('unit.people')}"
        crowd_level_label = crowd_level_text(crowd_level)

    free_count: int | None = None
    if not _seat_data_available(data) or errors.get("seat") in SEAT_EMPTY_CODES:
        free_seats_text = t("empty.no_seat_data")
    else:
        free_count = sum(1 for seat in seats if seat.get("status") == "FREE")
        free_seats_text = _seat_count(free_count)

    forecast_text = t("summary.forecast_unavailable") if forecast_30m is None else str(forecast_30m)

    st.subheader(t("summary.title"))
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(_metric_card(t("summary.people_capacity"), people_capacity_text, t("summary.people_help")), unsafe_allow_html=True)
    m2.markdown(_metric_card(t("summary.free_seats"), free_seats_text, t("summary.free_help")), unsafe_allow_html=True)
    m3.markdown(_metric_card(t("summary.crowd_level"), crowd_level_label), unsafe_allow_html=True)
    m4.markdown(_metric_card(t("summary.trend"), forecast_text, t("summary.forecast_help") if forecast_30m is None else None), unsafe_allow_html=True)

    if isinstance(free_count, int) and current_people is not None and capacity is not None:
        if free_count <= 0:
            action_text = t("summary.no_free_action")
        elif free_count <= 3:
            action_text = t("summary.low_free_action")
        else:
            action_text = t("summary.free_action")
        if current_language() == "en":
            trend_text = "Future trend is unavailable." if forecast_30m is None else f"Future trend: {forecast_30m}."
            decision_body = (
                f"Current crowd: {current_people}/{capacity} {t('unit.people')}; "
                f"level: {crowd_level_label}; free seats: {free_count}. {action_text} {trend_text}"
            )
        else:
            trend_text = "未来趋势暂不可用。" if forecast_30m is None else f"未来趋势：{forecast_30m}。"
            decision_body = f"馆内人数 {current_people}/{capacity} 人，拥挤等级为{crowd_level_label}，全馆空闲 {free_count} 座。{action_text}{trend_text}"
        st.markdown(
            _decision_callout(
                t("summary.decision"),
                decision_body,
            ),
            unsafe_allow_html=True,
        )
        next_step_text = (
            "下一步：先看区域推荐，再打开座位地图选择具体座位。"
            if current_language() == "zh"
            else "Next: check area advice, then open the seat map to choose a specific seat."
        )
        st.markdown(f"<div class='next-step-card'>{html.escape(next_step_text)}</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            _decision_callout(
                t("summary.decision"),
                "当前数据不足，建议先确认座位状态和人流数据是否已生成。"
                if current_language() == "zh"
                else "Insufficient data. Please confirm seat and crowd data are available.",
            ),
            unsafe_allow_html=True,
        )


def _area_status_label(available_ratio: float | None) -> str:
    if available_ratio is None:
        return AREA_STATUS_NO_CAPACITY
    if available_ratio >= 0.50:
        return "空闲较多"
    if available_ratio >= 0.20:
        return "座位紧张"
    if available_ratio > 0:
        return "接近满座"
    return "暂无空位"


def _area_recommendation_label(row: dict[str, Any]) -> str:
    anomaly_count = row["temporarily_unavailable_seats"] + row["suspicious_seats"]
    available_ratio = row.get("available_ratio")
    free_seats = row["free_seats"]
    if available_ratio is None or free_seats <= 0:
        return AVOID_AREA_LABEL
    if available_ratio >= 0.50 and anomaly_count == 0:
        return RECOMMENDED_AREA_LABEL
    if available_ratio >= 0.20:
        return CONSIDER_AREA_LABEL
    return AVOID_AREA_LABEL


def _area_sort_key(row: dict[str, Any]) -> tuple[int, float, int, int, str, str]:
    available_ratio = row.get("available_ratio")
    ratio_value = available_ratio if isinstance(available_ratio, (int, float)) else -1.0
    return (
        -row["free_seats"],
        -ratio_value,
        row["suspicious_seats"],
        row["temporarily_unavailable_seats"],
        row["floor"],
        row["zone"],
    )


def _free_seat_for_area(seats: list[dict[str, Any]], area: dict[str, Any]) -> str | None:
    floor = str(area.get("floor", ""))
    zone = str(area.get("zone", ""))
    matching = [
        seat for seat in seats
        if str(seat.get("floor", "")) == floor
        and str(seat.get("zone", "")) == zone
        and seat.get("status") == "FREE"
        and seat.get("seat_id")
    ]
    free_seats = sorted(matching, key=lambda seat: str(seat.get("seat_id", "")))
    if not free_seats:
        return None
    return str(free_seats[0].get("seat_id"))


def _recommended_seat_for_seats(seats: list[dict[str, Any]]) -> str | None:
    free_seats = sorted(
        (seat for seat in seats if seat.get("status") == "FREE" and seat.get("seat_id")),
        key=lambda seat: str(seat.get("seat_id", "")),
    )
    if not free_seats:
        return None
    return str(free_seats[0].get("seat_id"))


def _area_card_class(label: str) -> str:
    if label == RECOMMENDED_AREA_LABEL:
        return "recommended"
    if label == CONSIDER_AREA_LABEL:
        return "consider"
    return "avoid"


def _area_card(row: dict[str, Any], rank: int) -> str:
    lang = current_language()
    floor = row.get("floor") or ("未标注" if lang == "zh" else "Unlabeled")
    zone = row.get("zone") or ("未标注" if lang == "zh" else "Unlabeled")
    label = row.get("recommendation_label") or AVOID_AREA_LABEL
    css_class = _area_card_class(str(label))
    label_text = {
        RECOMMENDED_AREA_LABEL: t("area.recommend"),
        CONSIDER_AREA_LABEL: t("area.consider"),
        AVOID_AREA_LABEL: t("area.avoid"),
    }.get(str(label), str(label))
    risk_text = (
        f"异常座位 {row['anomaly_seats']} 座" if lang == "zh" else f"{row['anomaly_seats']} abnormal seats"
        if row.get("anomaly_seats", 0) > 0
        else ("暂无异常座位" if lang == "zh" else "No abnormal seats")
    )
    title_text = (
        f"{rank}. {floor} 楼 {zone} 区"
        if lang == "zh"
        else f"{rank}. Floor {floor} / Zone {zone}"
    )
    meta_text = (
        f"空闲 {row['free_seats']} 座<br>"
        f"可用比例 {html.escape(str(row['available_ratio_label']))}<br>"
        f"{html.escape(risk_text)}"
        if lang == "zh"
        else f"Free {row['free_seats']} seats<br>"
        f"Availability {html.escape(str(row['available_ratio_label']))}<br>"
        f"{html.escape(risk_text)}"
    )
    return (
        f"<div class='area-card {css_class}'>"
        f"<div class='area-card-label'>{html.escape(label_text)}</div>"
        f"<div class='area-card-title'>{html.escape(title_text)}</div>"
        f"<div class='area-card-meta'>{meta_text}</div>"
        "</div>"
    )


def build_area_summary(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for seat in seats:
        if not isinstance(seat, dict):
            continue
        key = (str(seat.get("floor", "")), str(seat.get("zone", "")))
        row = groups.setdefault(
            key,
            {
                "floor": key[0],
                "zone": key[1],
                "total_seats": 0,
                "free_seats": 0,
                "occupied_seats": 0,
                "temporarily_unavailable_seats": 0,
                "suspicious_seats": 0,
                "unavailable_seats": 0,
            },
        )
        row["total_seats"] += 1
        status = str(seat.get("status") or "").upper()
        if status == "FREE":
            row["free_seats"] += 1
        elif status == "OCCUPIED":
            row["occupied_seats"] += 1
        elif status == "POSSIBLY_OCCUPIED":
            row["temporarily_unavailable_seats"] += 1
        elif status == "SUSPICIOUS":
            row["suspicious_seats"] += 1
        elif status == "UNAVAILABLE":
            row["unavailable_seats"] += 1

    summary: list[dict[str, Any]] = []
    for row in groups.values():
        usable_capacity = row["total_seats"] - row["unavailable_seats"]
        available_ratio = None
        if usable_capacity > 0:
            available_ratio = row["free_seats"] / usable_capacity
        row["available_ratio"] = available_ratio
        row["available_ratio_label"] = (
            AREA_STATUS_NO_CAPACITY if available_ratio is None else f"{available_ratio:.0%}"
        )
        row["area_status_label"] = _area_status_label(available_ratio)
        row["anomaly_seats"] = row["temporarily_unavailable_seats"] + row["suspicious_seats"]
        row["recommendation_label"] = _area_recommendation_label(row)
        summary.append(row)

    return sorted(summary, key=_area_sort_key)


def render_area_overview(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    st.subheader(t("area.title"))
    summary = build_area_summary(seats)
    if not summary:
        st.info(t("area.no_data"))
        return []

    best_area = next((row for row in summary if row["recommendation_label"] != AVOID_AREA_LABEL), None)
    if best_area:
        lang = current_language()
        floor = best_area["floor"] or ("未标注" if lang == "zh" else "Unlabeled")
        zone = best_area["zone"] or ("未标注" if lang == "zh" else "Unlabeled")
        free_area_count = sum(1 for row in summary if row.get("free_seats", 0) > 0)
        suggested_seat = _free_seat_for_area(seats, best_area)
        if lang == "en":
            area_name = f"Floor {floor} / Zone {zone}"
            reason = (
                f"Only this area currently has free seats, so {area_name} is recommended."
                if free_area_count == 1
                else f"{area_name} has relatively more free seats, so it is recommended first."
            )
            risk = (
                f"This area has {best_area['anomaly_seats']} suspicious or temporarily unavailable seats."
                if best_area["anomaly_seats"] > 0
                else "No suspicious seat risk is currently shown in this area."
            )
            next_step = f"Choose {suggested_seat} first." if suggested_seat else "Open the seat map before choosing."
            title = f"{t('area.current_advice')}: check {area_name} first"
        else:
            area_name = f"{floor} 楼 {zone} 区"
            reason = (
                f"当前仅该区域存在空闲座位，因此推荐 {area_name}"
                if free_area_count == 1
                else f"{area_name}空闲座位相对更多，因此优先推荐"
            )
            risk = (
                f"该区域存在 {best_area['anomaly_seats']} 个疑似占座或暂不可用座位"
                if best_area["anomaly_seats"] > 0
                else "该区域暂无疑似占座风险"
            )
            next_step = f"建议优先选择 {suggested_seat}" if suggested_seat else "建议查看座位地图后再选择"
            title = f"{t('area.current_advice')}：优先查看 {area_name}"
        st.markdown(
            "<div class='recommendation-card'>"
            f"<span class='recommendation-title'>{html.escape(title)}</span>"
            f"{html.escape(t('area.free'))}: {_seat_count(best_area['free_seats'])} · "
            f"{html.escape(t('area.ratio'))}: {html.escape(best_area['available_ratio_label'])}<br>"
            f"{html.escape(t('area.reason'))}: {html.escape(reason)}<br>"
            f"{html.escape(t('area.risk'))}: {html.escape(risk)}<br>"
            f"{html.escape(t('area.next'))}: {html.escape(next_step)}"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info(t("area.no_recommendation"))
    st.markdown(
        f"<div class='section-note'>{html.escape(t('area.note'))}</div>",
        unsafe_allow_html=True,
    )

    rows_to_show = summary[:3]
    columns = st.columns(len(rows_to_show))
    for index, row in enumerate(rows_to_show):
        columns[index].markdown(_area_card(row, index + 1), unsafe_allow_html=True)
    return summary


def render_floor_zone_filters(
    seats: list[dict[str, Any]],
    preferred_area: dict[str, Any] | None = None,
    key_prefix: str = "student",
) -> list[dict[str, Any]]:
    st.subheader(t("map.title"))
    if not seats:
        st.info(t("empty.no_seat_data"))
        return []

    known_floors = sorted({str(seat.get("floor", "")) for seat in seats if seat.get("floor", "") != ""})
    floor_candidates = sorted(set(known_floors) | {"1", "2", "3", "4"}, key=lambda value: int(value) if value.isdigit() else 999)
    preferred_floor = str(preferred_area.get("floor", "")) if preferred_area else ""
    floor_values = floor_candidates
    floor_index = floor_values.index(preferred_floor) if preferred_floor in floor_values else (
        floor_values.index(known_floors[0]) if known_floors and known_floors[0] in floor_values else 0
    )
    def floor_label(floor: str) -> str:
        if current_language() == "en":
            return f"Floor {floor}" if floor in known_floors else f"Floor {floor} · no data"
        return f"{floor} 楼" if floor in known_floors else f"{floor} 楼 暂无数据"

    selected_floor_label = st.radio(
        t("map.floor"),
        floor_values,
        index=floor_index,
        horizontal=True,
        key=f"{key_prefix}_floor_filter",
        format_func=floor_label,
    )
    selected_floor = selected_floor_label

    floor_filtered = [seat for seat in seats if str(seat.get("floor", "")) == selected_floor]
    if not floor_filtered:
        st.info(t("empty.no_seat_data"))
        return []

    zones = sorted({str(seat.get("zone", "")) for seat in floor_filtered if seat.get("zone", "") != ""})
    if not zones:
        st.info(t("area.no_data"))
        return []
    preferred_zone = str(preferred_area.get("zone", "")) if preferred_area else ""
    zone_index = zones.index(preferred_zone) if preferred_zone in zones else 0
    selected_zone_label = st.radio(
        t("map.zone"),
        zones,
        index=zone_index,
        horizontal=True,
        key=f"{key_prefix}_zone_filter",
        format_func=lambda zone: f"{zone} 区" if current_language() == "zh" else f"Zone {zone}",
    )
    selected_zone = selected_zone_label

    return [seat for seat in floor_filtered if str(seat.get("zone", "")) == selected_zone]


def render_student_seat_preview(seats: list[dict[str, Any]]) -> None:
    if not seats:
        st.info(t("empty.no_seat_data"))
        return

    rows = [
        {
            t("seat.id"): seat.get("seat_id", ""),
            t("seat.floor"): seat.get("floor", ""),
            t("seat.zone"): seat.get("zone", ""),
            t("seat.status"): status_text(seat.get("status"), audience="student"),
            t("seat.updated"): seat.get("updated_at") or "",
        }
        for seat in seats
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def _layout_label(group: dict[str, Any]) -> str:
    lang = current_language()
    floor = group.get("floor") or ("未标注楼层" if lang == "zh" else "Unlabeled floor")
    zone = group.get("zone") or ("未标注区域" if lang == "zh" else "Unlabeled zone")
    camera_id = group.get("camera_id") or ("未标注摄像头" if lang == "zh" else "Unlabeled camera")
    return f"{floor} 楼 / {zone} 区 / {camera_id}" if lang == "zh" else f"Floor {floor} / Zone {zone} / {camera_id}"


def render_student_seat_layout(seats: list[dict[str, Any]]) -> None:
    if not seats:
        st.info(t("empty.no_layout_data"))
        return

    groups = group_seats_by_layout(seats)
    valid_groups = {
        key: group for key, group in groups.items()
        if group.get("seats")
    }
    if not valid_groups:
        st.info(t("empty.no_layout_data"))
        return

    group_keys = sorted(valid_groups)
    selected_group_key = group_keys[0]
    if len(group_keys) > 1:
        selected_group_key = st.selectbox(
            t("map.group"),
            group_keys,
            format_func=lambda key: _layout_label(valid_groups[key]),
            key="student_camera_layout_filter",
        )

    selected_group = valid_groups[selected_group_key]
    group_seats = selected_group.get("seats", [])
    if not group_seats:
        st.info(t("empty.no_layout_data"))
        return

    recommended_seat_id = _recommended_seat_for_seats(group_seats)
    seat_options = [
        str(seat.get("seat_id", ""))
        for seat in sorted(
            group_seats,
            key=lambda seat: (seat.get("status") != "FREE", str(seat.get("seat_id", ""))),
        )
        if seat.get("seat_id")
    ]
    default_seat = recommended_seat_id if recommended_seat_id in seat_options else (seat_options[0] if seat_options else "")
    default_index = seat_options.index(default_seat) if default_seat in seat_options else 0
    left_col, right_col = st.columns([3.3, 0.95], gap="large")
    with right_col:
        selected_seat_id = st.selectbox(
            t("map.seat"),
            seat_options,
            index=default_index,
            key=f"student_selected_seat_{selected_group_key}",
        )
    lang = current_language()
    floor_value = selected_group.get("floor") or ("未标注" if lang == "zh" else "Unlabeled")
    zone_value = selected_group.get("zone") or ("未标注" if lang == "zh" else "Unlabeled")
    svg = build_svg_seat_layout(
        group_seats,
        selected_seat_id=selected_seat_id,
        recommended_seat_id=recommended_seat_id,
        floor_label=f"{floor_value} 楼" if lang == "zh" else f"Floor {floor_value}",
        area_label=f"{zone_value} 区" if lang == "zh" else f"Zone {zone_value}",
        language=lang,
    )
    with left_col:
        st_components.html(svg, height=350, scrolling=False)

    selected_seat = next(
        (seat for seat in group_seats if str(seat.get("seat_id", "")) == selected_seat_id),
        None,
    )
    if selected_seat:
        with right_col:
            title = t("map.current_or_recommended")
            if recommended_seat_id and selected_seat_id == recommended_seat_id:
                title = t("map.recommended")
            st.markdown(f"**{title}**")
            st.markdown(
                _detail_card([
                    (t("seat.id"), selected_seat.get("seat_id")),
                    (t("seat.floor"), f"{selected_seat.get('floor') or t('empty.no_data')} 楼" if lang == "zh" else f"Floor {selected_seat.get('floor') or t('empty.no_data')}"),
                    (t("seat.zone"), f"{selected_seat.get('zone') or t('empty.no_data')} 区" if lang == "zh" else f"Zone {selected_seat.get('zone') or t('empty.no_data')}"),
                    (t("seat.camera"), selected_seat.get("camera_id")),
                    (t("seat.status"), status_text(selected_seat.get("status"), audience="student")),
                    (t("seat.updated"), format_datetime(selected_seat.get("updated_at"), t("empty.no_seat_data"))),
                ]),
                unsafe_allow_html=True,
            )
            if recommended_seat_id:
                st.caption(
                    f"当前推荐座位：{recommended_seat_id}。建议优先选择该空闲座位。"
                    if lang == "zh"
                    else f"Recommended seat: {recommended_seat_id}. Choose this free seat first."
                )

    warnings = selected_group.get("warnings") or []
    if warnings:
        st.warning(t("map.warning_invalid_polygon"))


def build_crowd_trend_frame(crowd: dict[str, Any]) -> dict[str, Any]:
    history = crowd.get("history")
    if not isinstance(history, list) or not history:
        return {
            "rows": [],
            "time_range": None,
            "has_capacity_line": False,
            "forecast_available": crowd.get("forecast_30m") is not None,
            "empty_reason": "empty_history",
        }

    capacity = crowd.get("capacity")
    has_capacity_line = isinstance(capacity, (int, float)) and capacity > 0
    rows: list[dict[str, Any]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        recorded_at = item.get("recorded_at")
        total = item.get("total_in_library")
        if recorded_at is None or total is None:
            continue
        row = {
            "时间": str(recorded_at),
            "历史馆内人数": total,
        }
        if has_capacity_line:
            row["容量参考线"] = capacity
        rows.append(row)

    if not rows:
        return {
            "rows": [],
            "time_range": None,
            "has_capacity_line": has_capacity_line,
            "forecast_available": crowd.get("forecast_30m") is not None,
            "empty_reason": "empty_history",
        }

    return {
        "rows": rows,
        "time_range": f"{format_datetime(rows[0]['时间'])} 至 {format_datetime(rows[-1]['时间'])}",
        "has_capacity_line": has_capacity_line,
        "forecast_available": crowd.get("forecast_30m") is not None,
        "empty_reason": None,
    }


def _parse_history_time(item: dict[str, Any]) -> datetime | None:
    return _parse_timestamp(item.get("recorded_at"))


def filter_crowd_history_by_range(history: Any, range_label: str) -> list[dict[str, Any]]:
    if not isinstance(history, list):
        return []

    parsed_rows: list[tuple[datetime, dict[str, Any]]] = []
    for item in history:
        if not isinstance(item, dict) or item.get("total_in_library") is None:
            continue
        recorded_at = _parse_history_time(item)
        if not recorded_at:
            continue
        parsed_rows.append((recorded_at, item))

    if not parsed_rows:
        return []

    latest_time = max(recorded_at for recorded_at, _ in parsed_rows)
    selected_range = range_label if range_label in CROWD_TREND_RANGE_OPTIONS else CROWD_TREND_RANGE_OPTIONS[0]
    if selected_range == "今日":
        start_time = latest_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif selected_range == "近3天":
        start_time = latest_time - timedelta(days=3)
    else:
        start_time = latest_time - timedelta(hours=3)

    return [
        dict(item)
        for recorded_at, item in sorted(parsed_rows, key=lambda row: row[0])
        if start_time <= recorded_at <= latest_time
    ]


def build_crowd_trend_frame_for_range(crowd: dict[str, Any], range_label: str) -> dict[str, Any]:
    selected_range = range_label if range_label in CROWD_TREND_RANGE_OPTIONS else CROWD_TREND_RANGE_OPTIONS[0]
    filtered_history = filter_crowd_history_by_range(crowd.get("history"), selected_range)
    if len(filtered_history) < 2:
        capacity = crowd.get("capacity")
        return {
            "rows": [],
            "time_range": None,
            "has_capacity_line": isinstance(capacity, (int, float)) and capacity > 0,
            "forecast_available": crowd.get("forecast_30m") is not None,
            "empty_reason": "insufficient_range_data",
            "selected_range": selected_range,
        }

    ranged_crowd = dict(crowd)
    ranged_crowd["history"] = filtered_history
    trend = build_crowd_trend_frame(ranged_crowd)
    trend["selected_range"] = selected_range
    return trend


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_time_label(value: Any) -> str:
    parsed = _parse_timestamp(value)
    if parsed:
        return parsed.strftime("%H:%M")
    text = str(value or "")
    if "T" in text:
        text = text.split("T", 1)[1]
    elif " " in text:
        text = text.rsplit(" ", 1)[-1]
    return text[:5] if len(text) >= 5 else text


def _format_duration_between(start: Any, end: Any) -> str:
    start_dt = _parse_timestamp(start)
    end_dt = _parse_timestamp(end)
    if not start_dt or not end_dt:
        return "这段时间"
    hours = abs((end_dt - start_dt).total_seconds()) / 3600
    if hours < 1:
        minutes = max(1, round(hours * 60))
        return f"过去 {minutes} 分钟"
    if hours.is_integer():
        return f"过去 {int(hours)} 小时"
    return f"过去 {hours:.1f} 小时"


def _format_plain_duration_between(start: datetime, end: datetime) -> str:
    hours = abs((end - start).total_seconds()) / 3600
    if hours < 1:
        minutes = max(1, round(hours * 60))
        return f"{minutes} 分钟"
    if hours.is_integer():
        return f"{int(hours)} 小时"
    return f"{hours:.1f} 小时"


def build_crowd_range_coverage_note(crowd: dict[str, Any]) -> str | None:
    history = crowd.get("history")
    if not isinstance(history, list) or len(history) < 2:
        return None

    parsed_times = [_parse_history_time(row) for row in history if isinstance(row, dict)]
    parsed_times = [value for value in parsed_times if value is not None]
    if len(parsed_times) < 2:
        return None

    signatures = {
        tuple(row.get("recorded_at") for row in filter_crowd_history_by_range(history, label))
        for label in CROWD_TREND_RANGE_OPTIONS
    }
    if len(signatures) != 1:
        return None

    duration = _format_plain_duration_between(min(parsed_times), max(parsed_times))
    return f"当前 mock 历史数据仅覆盖 {duration}，三个时间范围会显示相同折线。"


def _format_time_range_label(trend: dict[str, Any]) -> str | None:
    rows = trend.get("rows") or []
    if not rows:
        return None
    return f"{_format_time_label(rows[0].get('时间'))} 至 {_format_time_label(rows[-1].get('时间'))}"


def _row_time_value(row: dict[str, Any]) -> datetime | None:
    return _parse_timestamp(row.get("时间"))


def _crowd_axis_ticks(
    rows: list[dict[str, Any]],
    x_at_time: Any,
    fallback_x_at: Any,
    tick_count: int = 5,
) -> list[tuple[float, str]]:
    parsed_times = [_row_time_value(row) for row in rows]
    parsed_times = [value for value in parsed_times if value is not None]
    if len(parsed_times) >= 2:
        start = min(parsed_times)
        end = max(parsed_times)
        span_seconds = (end - start).total_seconds()
        if span_seconds > 0:
            ticks = []
            for index in range(tick_count):
                ratio = index / (tick_count - 1) if tick_count > 1 else 0
                tick_time = start + timedelta(seconds=span_seconds * ratio)
                ticks.append((x_at_time(tick_time), tick_time.strftime("%H:%M")))
            return ticks

    if len(rows) == 1:
        return [(fallback_x_at(0), _format_time_label(rows[0].get("时间")))]
    return [
        (fallback_x_at(index), _format_time_label(row.get("时间")))
        for index, row in enumerate(rows)
    ]


def _build_static_crowd_trend_chart(trend: dict[str, Any]) -> str:
    rows = trend.get("rows") or []
    width = 900
    height = 210
    padding_left = 52
    padding_right = 24
    padding_top = 18
    padding_bottom = 42
    plot_width = width - padding_left - padding_right
    plot_height = height - padding_top - padding_bottom

    people_values = [_to_float(row.get("历史馆内人数")) for row in rows]
    people_values = [value for value in people_values if value is not None]
    if not rows or not people_values:
        return "<div class='section-note'>暂无人流历史数据</div>"

    capacity_values = [
        _to_float(row.get("容量参考线"))
        for row in rows
        if _to_float(row.get("容量参考线")) is not None
    ]
    max_value = max(people_values + capacity_values + [1])
    min_value = 0
    y_span = max(max_value - min_value, 1)

    row_times = [_row_time_value(row) for row in rows]
    valid_times = [value for value in row_times if value is not None]
    time_start = min(valid_times) if valid_times else None
    time_end = max(valid_times) if valid_times else None
    time_span = (
        (time_end - time_start).total_seconds()
        if time_start is not None and time_end is not None
        else 0
    )

    def fallback_x_at(index: int) -> float:
        if len(rows) == 1:
            return padding_left + plot_width / 2
        return padding_left + (plot_width * index / (len(rows) - 1))

    def x_at_time(value: datetime) -> float:
        if time_start is None or time_span <= 0:
            return fallback_x_at(0)
        offset = (value - time_start).total_seconds()
        return padding_left + (plot_width * offset / time_span)

    def x_for_row(index: int, row: dict[str, Any]) -> float:
        row_time = _row_time_value(row)
        if row_time is not None and time_span > 0:
            return x_at_time(row_time)
        return fallback_x_at(index)

    def y_at(value: float) -> float:
        return padding_top + plot_height - ((value - min_value) / y_span * plot_height)

    people_points: list[tuple[float, float, dict[str, Any], float]] = []
    for index, row in enumerate(rows):
        people = _to_float(row.get("历史馆内人数"))
        if people is None:
            continue
        people_points.append((x_for_row(index, row), y_at(people), row, people))

    point_attr = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in people_points)
    baseline_y = padding_top + plot_height
    area_points = ""
    if people_points:
        first_x = people_points[0][0]
        last_x = people_points[-1][0]
        area_points = (
            f"{first_x:.1f},{baseline_y:.1f} "
            + point_attr
            + f" {last_x:.1f},{baseline_y:.1f}"
        )

    grid_lines = []
    y_labels = []
    for step in range(5):
        value = min_value + y_span * step / 4
        y = y_at(value)
        grid_lines.append(
            f"<line x1='{padding_left}' y1='{y:.1f}' x2='{width - padding_right}' y2='{y:.1f}' "
            "stroke='#e4e7ec' stroke-width='1' />"
        )
        y_labels.append(
            f"<text x='{padding_left - 10}' y='{y + 4:.1f}' text-anchor='end' "
            "font-size='12' fill='#667085'>"
            f"{int(round(value))}</text>"
        )

    axis_ticks = _crowd_axis_ticks(rows, x_at_time, fallback_x_at)
    x_grid_lines = []
    x_labels = []
    for x, label in axis_ticks:
        x_grid_lines.append(
            f"<line class='crowd-x-grid' x1='{x:.1f}' y1='{padding_top}' x2='{x:.1f}' y2='{baseline_y}' "
            "stroke='#eef2f6' stroke-width='1' />"
        )
        anchor = "middle"
        if x <= padding_left + 2:
            anchor = "start"
        elif x >= width - padding_right - 2:
            anchor = "end"
        x_labels.append(
            f"<text class='crowd-x-label' x='{x:.1f}' y='{height - 18}' text-anchor='{anchor}' "
            "font-size='12' fill='#667085'>"
            f"{html.escape(label)}</text>"
        )

    capacity_line = ""
    if trend.get("has_capacity_line") and capacity_values:
        capacity = capacity_values[0]
        y = y_at(capacity)
        capacity_line = (
            f"<line x1='{padding_left}' y1='{y:.1f}' x2='{width - padding_right}' y2='{y:.1f}' "
            "stroke='#93c5fd' stroke-width='2' stroke-dasharray='6 5'>"
            f"<title>容量参考线：{int(capacity)} 人</title>"
            "</line>"
            f"<text x='{width - padding_right}' y='{max(y - 8, padding_top + 10):.1f}' text-anchor='end' "
            "font-size='12' fill='#2563eb'>容量</text>"
        )

    circles = []
    for x, y, row, people in people_points:
        time_label = format_datetime(row.get("时间"))
        people_unit = t("unit.people")
        circles.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4.5' fill='#1677e8' stroke='#ffffff' stroke-width='2'>"
            f"<title>{html.escape(time_label)}: {int(people)} {html.escape(people_unit)}</title>"
            "</circle>"
        )

    hover_regions = []
    hit_width = max(36, plot_width / max(len(people_points), 1))
    tooltip_width = 112
    tooltip_height = 34
    for x, y, row, people in people_points:
        time_label = _format_time_label(row.get("时间"))
        tooltip_text = f"{time_label} · {int(people)} {t('unit.people')}"
        tooltip_x = min(max(x - tooltip_width / 2, padding_left), width - padding_right - tooltip_width)
        tooltip_y = max(y - 46, padding_top + 2)
        hover_regions.append(
            "<g class='crowd-hover-region'>"
            f"<rect x='{x - hit_width / 2:.1f}' y='{padding_top}' width='{hit_width:.1f}' height='{plot_height}' "
            "fill='transparent' />"
            "<g class='crowd-tooltip'>"
            f"<line x1='{x:.1f}' y1='{padding_top}' x2='{x:.1f}' y2='{padding_top + plot_height}' "
            "stroke='#98a2b3' stroke-width='1' stroke-dasharray='4 4' />"
            f"<rect x='{tooltip_x:.1f}' y='{tooltip_y:.1f}' width='{tooltip_width}' height='{tooltip_height}' rx='8' "
            "fill='#101828' opacity='0.94' />"
            f"<text x='{tooltip_x + tooltip_width / 2:.1f}' y='{tooltip_y + 22:.1f}' text-anchor='middle' "
            f"font-size='12' fill='#ffffff'>{html.escape(tooltip_text)}</text>"
            "</g>"
            "</g>"
        )

    return (
        "<div style='width:100%; overflow:visible;'>"
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='图书馆人流趋势' "
        "style='width:100%; height:210px; display:block; touch-action:pan-y;'>"
        "<style>"
        ".crowd-tooltip{display:none;pointer-events:none;}"
        ".crowd-hover-region:hover .crowd-tooltip{display:block;}"
        "</style>"
        "<rect x='0' y='0' width='100%' height='100%' fill='#ffffff' />"
        + "".join(x_grid_lines)
        + "".join(grid_lines)
        + "".join(y_labels)
        + capacity_line
        + (
            f"<polygon class='crowd-area-fill' points='{area_points}' fill='#1677e8' opacity='0.10' />"
            if area_points
            else ""
        )
        + f"<polyline points='{point_attr}' fill='none' stroke='#1677e8' stroke-width='3' "
        "stroke-linecap='round' stroke-linejoin='round' />"
        + "".join(circles)
        + "".join(hover_regions)
        + "".join(x_labels)
        + "</svg>"
        "</div>"
    )


def _crowd_decision_summary(crowd: dict[str, Any], trend: dict[str, Any]) -> str:
    return build_crowd_trend_summary(crowd, trend)


def _crowd_direction(rows: list[dict[str, Any]], selected_range: str) -> str | None:
    values = [_to_float(row.get("历史馆内人数")) for row in rows]
    values = [value for value in values if value is not None]
    if len(values) < 2:
        return None

    if selected_range == "近3小时":
        delta = values[-1] - values[0]
        stable_threshold = max(1, values[0] * 0.03)
        if abs(delta) <= stable_threshold:
            return "稳定"
        return "上升" if delta > 0 else "下降"

    deltas = [values[index + 1] - values[index] for index in range(len(values) - 1)]
    has_up = any(delta > 0 for delta in deltas)
    has_down = any(delta < 0 for delta in deltas)
    if has_up and has_down:
        return "波动"
    if values[-1] > values[0]:
        return "上升"
    if values[-1] < values[0]:
        return "下降"
    return "波动"


def build_crowd_trend_summary(crowd: dict[str, Any], trend: dict[str, Any]) -> str:
    current_people = _to_float(crowd.get("current_people"))
    capacity = _to_float(crowd.get("capacity"))
    lang = current_language()
    level = crowd_level_text(crowd.get("crowd_level"))
    rows = trend.get("rows") or []
    selected_range = str(trend.get("selected_range") or CROWD_TREND_RANGE_OPTIONS[0])
    direction = _crowd_direction(rows, selected_range)
    if not direction:
        return "当前数据量不足，暂无法判断趋势。" if lang == "zh" else "Not enough data to determine the trend."

    if current_people is None and rows:
        current_people = _to_float(rows[-1].get("历史馆内人数"))

    if current_people is not None and capacity and capacity > 0:
        current_text = f"{int(current_people)} / {int(capacity)} {t('unit.people')}"
    elif current_people is not None:
        current_text = _people_count(int(current_people))
    else:
        return "当前数据量不足，暂无法判断趋势。" if lang == "zh" else "Not enough data to determine the trend."

    if lang == "en":
        direction_text = {
            "上升": "increasing",
            "下降": "decreasing",
            "稳定": "stable",
            "波动": "fluctuating",
        }.get(direction, direction)
        if selected_range == "今日":
            return f"Today, the library crowd is generally {direction_text}. Current level: {current_text}."
        if selected_range == "近3天":
            return f"Over the last 3 days, the library crowd is {direction_text}. Current level: {current_text}."
        return f"Over the last 3 hours, the library crowd is {direction_text}. Current level: {current_text}, {level}."

    if selected_range == "今日":
        return f"今日馆内人数整体{direction}，当前为 {current_text}。"
    if selected_range == "近3天":
        return f"近3天内馆内人数呈现{direction}趋势，当前为 {current_text}。"
    return f"近3小时内馆内人数整体{direction}，当前为 {current_text}，{level}。"


def _crowd_capacity_strip(crowd: dict[str, Any], trend: dict[str, Any]) -> str:
    current_people = _to_float(crowd.get("current_people"))
    capacity = _to_float(crowd.get("capacity"))
    rows = trend.get("rows") or []
    if current_people is None and rows:
        current_people = _to_float(rows[-1].get("历史馆内人数"))
    if current_people is not None and capacity and capacity > 0:
        ratio = current_people / capacity
        ratio_text = f"{ratio:.0%}"
        current_text = _people_count(int(current_people))
        capacity_text = _people_count(int(capacity))
    else:
        ratio_text = t("empty.no_data")
        current_text = _people_count(int(current_people)) if current_people is not None else t("empty.no_data")
        capacity_text = t("empty.no_data")
    return (
        "<div class='decision-callout' style='margin-bottom:10px;'>"
        f"<strong>{html.escape(t('trend.current_people'))}: </strong>{html.escape(current_text)}"
        f"&nbsp;&nbsp; <strong>{html.escape(t('trend.capacity'))}: </strong>{html.escape(capacity_text)}"
        f"&nbsp;&nbsp; <strong>{html.escape(t('trend.ratio'))}: </strong>{html.escape(ratio_text)}"
        "</div>"
    )


def render_crowd_trend(crowd: dict[str, Any]) -> None:
    st.subheader(t("trend.title"))
    selected_range = st.radio(
        t("trend.range"),
        CROWD_TREND_RANGE_OPTIONS,
        index=0,
        horizontal=True,
        key="crowd_trend_range",
        format_func=lambda label: {
            "近3小时": t("trend.3h"),
            "今日": t("trend.today"),
            "近3天": t("trend.3d"),
        }.get(label, label),
    )
    trend = build_crowd_trend_frame_for_range(crowd, selected_range)

    if not trend["rows"]:
        st.info(t("trend.insufficient"))
    else:
        st.markdown(
            _decision_callout(t("trend.conclusion"), build_crowd_trend_summary(crowd, trend)),
            unsafe_allow_html=True,
        )
        st.markdown(_crowd_capacity_strip(crowd, trend), unsafe_allow_html=True)
        st.markdown(_build_static_crowd_trend_chart(trend), unsafe_allow_html=True)
        trend_notes: list[str] = []
        time_range_label = _format_time_range_label(trend)
        if time_range_label:
            trend_notes.append(f"{t('trend.data_range')}: {time_range_label}")
        coverage_note = build_crowd_range_coverage_note(crowd)
        if coverage_note:
            trend_notes.append(coverage_note)
        if not trend["forecast_available"]:
            trend_notes.append(t("trend.no_forecast"))
        if trend_notes:
            st.caption(" · ".join(trend_notes))

    if not trend["has_capacity_line"]:
        st.caption(t("trend.no_capacity"))


def _preferred_area_for_seats(seats: list[dict[str, Any]]) -> dict[str, Any] | None:
    area_summary = build_area_summary(seats)
    return next(
        (row for row in area_summary if row.get("recommendation_label") != AVOID_AREA_LABEL),
        area_summary[0] if area_summary else None,
    )


def _nav_description(label: str) -> str:
    descriptions = {
        "总览": t("nav.overview_desc"),
        "区域推荐": t("nav.area_desc"),
        "座位地图": t("nav.map_desc"),
        "人流趋势": t("nav.trend_desc"),
        "管理概览": t("nav.admin_overview_desc"),
        "异常座位": t("nav.anomaly_list_desc"),
        "异常定位": t("nav.anomaly_location_desc"),
    }
    return descriptions.get(label, "")


def _section_display_label(label: str) -> str:
    labels = {
        "总览": t("nav.overview"),
        "区域推荐": t("nav.area"),
        "座位地图": t("nav.map"),
        "人流趋势": t("nav.trend"),
        "管理概览": t("nav.admin_overview"),
        "异常座位": t("nav.anomaly_list"),
        "异常定位": t("nav.anomaly_location"),
    }
    return labels.get(label, label)


def _render_left_navigation(labels: list[str], admin_mode: bool) -> str:
    role_title = t("app.admin_mode") if admin_mode else t("app.student_mode")
    role_desc = t("nav.admin_desc") if admin_mode else t("nav.student_desc")
    st.markdown(
        f"<span class='mode-badge'>{html.escape(role_title)}</span>"
        f"<div class='side-panel-title'>{html.escape(t('nav.entry'))}</div>"
        f"<div class='side-panel-subtitle'>{html.escape(role_desc)}</div>",
        unsafe_allow_html=True,
    )
    session_key = "admin_nav" if admin_mode else "student_nav"
    current = st.session_state.get(session_key, labels[0])
    index = labels.index(current) if current in labels else 0
    selected = st.radio(
        "功能导航",
        labels,
        index=index,
        key=session_key,
        label_visibility="collapsed",
        format_func=_section_display_label,
    )
    st.caption(_nav_description(selected))
    return selected


def render_student_section(data: dict[str, Any], selected_section: str, auto_refresh_enabled: bool) -> None:
    render_data_status(data, auto_refresh_enabled)
    if selected_section == "总览":
        render_student_summary(data)
        return

    if not _seat_data_available(data):
        if selected_section == "区域推荐":
            st.info(t("empty.no_seat_data"))
        elif selected_section == "座位地图":
            st.info(t("empty.no_seat_data"))
        elif selected_section == "人流趋势":
            render_crowd_trend(data.get("crowd", {}))
        return

    seats = data.get("seats", [])
    preferred_area = _preferred_area_for_seats(seats)
    if selected_section == "区域推荐":
        render_area_overview(seats)
    elif selected_section == "座位地图":
        filtered_seats = render_floor_zone_filters(seats, preferred_area=preferred_area, key_prefix="student_seat")
        render_student_seat_layout(filtered_seats)
    elif selected_section == "人流趋势":
        render_crowd_trend(data.get("crowd", {}))


def render_student_view(data: dict[str, Any], auto_refresh_enabled: bool) -> None:
    render_student_section(data, STUDENT_SECTION_TABS[0], auto_refresh_enabled)


def build_admin_summary(seats: list[dict[str, Any]]) -> dict[str, Any]:
    if not seats:
        return {
            "possibly_occupied_count": 0,
            "suspicious_count": 0,
            "occupancy_rate": None,
            "occupancy_rate_label": "暂无数据",
            "busiest_anomaly_area": None,
            "busiest_anomaly_area_label": "暂无异常区域",
        }

    total_seats = len(seats)
    occupied_count = sum(1 for seat in seats if seat.get("status") == "OCCUPIED")
    unavailable_count = sum(1 for seat in seats if seat.get("status") == "UNAVAILABLE")
    possibly_count = sum(1 for seat in seats if seat.get("status") == "POSSIBLY_OCCUPIED")
    suspicious_count = sum(1 for seat in seats if seat.get("status") == "SUSPICIOUS")
    usable_capacity = total_seats - unavailable_count
    occupancy_rate = None
    if usable_capacity > 0:
        occupancy_rate = occupied_count / usable_capacity

    anomaly_areas: dict[tuple[str, str], int] = {}
    for seat in seats:
        if seat.get("status") in ANOMALY_STATUSES:
            key = (str(seat.get("floor", "")), str(seat.get("zone", "")))
            anomaly_areas[key] = anomaly_areas.get(key, 0) + 1

    busiest_area = None
    busiest_label = "暂无异常区域"
    if anomaly_areas:
        floor_zone, count = sorted(
            anomaly_areas.items(),
            key=lambda item: (-item[1], item[0][0], item[0][1]),
        )[0]
        busiest_area = {"floor": floor_zone[0], "zone": floor_zone[1], "anomaly_count": count}
        floor = floor_zone[0] or "未标注"
        zone = floor_zone[1] or "未标注"
        busiest_label = f"{floor} 楼 / {zone} 区，{count} 座异常"

    return {
        "possibly_occupied_count": possibly_count,
        "suspicious_count": suspicious_count,
        "occupancy_rate": occupancy_rate,
        "occupancy_rate_label": "暂无数据" if occupancy_rate is None else f"{occupancy_rate:.0%}",
        "busiest_anomaly_area": busiest_area,
        "busiest_anomaly_area_label": busiest_label,
    }


def _anomaly_sort_key(row: dict[str, Any]) -> tuple[int, int, float]:
    status_priority = 0 if row.get("status") == "SUSPICIOUS" else 1
    minutes = row.get("unattended_minutes")
    minutes_value = minutes if isinstance(minutes, int) else 0
    parsed = _parse_timestamp(row.get("updated_at"))
    timestamp = parsed.timestamp() if parsed else 0.0
    return status_priority, -minutes_value, -timestamp


def build_anomaly_rows(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for seat in seats:
        if seat.get("status") not in ANOMALY_STATUSES:
            continue
        rows.append({
            "seat_id": seat.get("seat_id", ""),
            "floor": seat.get("floor", ""),
            "zone": seat.get("zone", ""),
            "camera_id": seat.get("camera_id") or "",
            "status": seat.get("status"),
            "status_label": status_text(seat.get("status"), audience="admin"),
            "has_person": seat.get("has_person"),
            "has_object": seat.get("has_object"),
            "unattended_minutes": seat.get("unattended_minutes"),
            "updated_at": seat.get("updated_at"),
            "polygon": seat.get("polygon"),
        })
    return sorted(rows, key=_anomaly_sort_key)


def build_anomaly_display_rows(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unlabeled = "未标注" if current_language() == "zh" else "Unlabeled"
    return [
        {
            "seat_id": row["seat_id"],
            "floor": row["floor"] or unlabeled,
            "zone": row["zone"] or unlabeled,
            "status": row["status_label"],
            "unattended_minutes": _format_minutes(row["unattended_minutes"]),
            "updated_at": format_datetime(row["updated_at"]),
        }
        for row in build_anomaly_rows(seats)
    ]


def _localized_anomaly_display_rows(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    columns = {
        "seat_id": t("seat.id"),
        "floor": t("seat.floor"),
        "zone": t("seat.zone"),
        "status": t("seat.status"),
        "unattended_minutes": t("seat.unattended"),
        "updated_at": t("seat.updated"),
    }
    return [
        {columns[key]: value for key, value in row.items()}
        for row in build_anomaly_display_rows(seats)
    ]


def _same_layout_group(seats: list[dict[str, Any]], selected: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        seat for seat in seats
        if str(seat.get("floor", "")) == str(selected.get("floor", ""))
        and str(seat.get("zone", "")) == str(selected.get("zone", ""))
        and str(seat.get("camera_id") or "") == str(selected.get("camera_id") or "")
    ]


def render_admin_summary(seats: list[dict[str, Any]]) -> None:
    st.subheader(t("admin.title"))
    summary = build_admin_summary(seats)
    area_label = summary["busiest_anomaly_area_label"]
    if current_language() == "en":
        area = summary.get("busiest_anomaly_area")
        area_label = (
            f"Floor {area.get('floor') or 'Unlabeled'} / Zone {area.get('zone') or 'Unlabeled'}, {area.get('anomaly_count')} anomalies"
            if area
            else "No abnormal area"
        )
    occupancy_label = summary["occupancy_rate_label"]
    if current_language() == "en" and occupancy_label == "暂无数据":
        occupancy_label = t("empty.no_data")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(_metric_card(t("admin.possible"), _seat_count(summary["possibly_occupied_count"])), unsafe_allow_html=True)
    suspicious_tone = "critical" if summary["suspicious_count"] else None
    c2.markdown(_metric_card(t("admin.suspicious"), _seat_count(summary["suspicious_count"]), t("admin.priority"), suspicious_tone), unsafe_allow_html=True)
    c3.markdown(_metric_card(t("admin.occupancy_rate"), occupancy_label), unsafe_allow_html=True)
    area_tone = "warning" if summary["busiest_anomaly_area"] else None
    c4.markdown(_metric_card(t("admin.busiest_area"), area_label, t("admin.patrol_focus"), area_tone), unsafe_allow_html=True)


def render_anomaly_table(seats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = build_anomaly_rows(seats)
    if not rows:
        st.info(t("admin.no_anomalies"))
        return []

    cards = []
    for row in rows:
        location = (
            f"{row.get('floor') or '未标注'} 楼 / {row.get('zone') or '未标注'} 区"
            if current_language() == "zh"
            else f"Floor {row.get('floor') or 'Unlabeled'} / Zone {row.get('zone') or 'Unlabeled'}"
        )
        cards.append(
            "<div class='anomaly-card'>"
            f"<div class='anomaly-card-title'>{html.escape(str(row.get('seat_id') or ''))}</div>"
            "<div class='anomaly-card-meta'>"
            f"{html.escape(t('seat.status'))}: {html.escape(str(row.get('status_label') or ''))}<br>"
            f"{html.escape(t('seat.floor'))}/{html.escape(t('seat.zone'))}: {html.escape(location)}<br>"
            f"{html.escape(t('seat.unattended'))}: {html.escape(_format_minutes(row.get('unattended_minutes')))}<br>"
            f"{html.escape(t('seat.updated'))}: {html.escape(format_datetime(row.get('updated_at')))}"
            "</div>"
            "</div>"
        )
    st.markdown("<div class='anomaly-card-list'>" + "".join(cards) + "</div>", unsafe_allow_html=True)
    return rows


def render_anomaly_detail(selected_seat: dict[str, Any] | None) -> None:
    if not selected_seat:
        st.info(t("admin.choose_seat"))
        return

    st.markdown(
        _detail_card([
            (t("seat.id"), selected_seat.get("seat_id")),
            (t("seat.floor"), selected_seat.get("floor")),
            (t("seat.zone"), selected_seat.get("zone")),
            (t("seat.camera"), selected_seat.get("camera_id")),
            (t("seat.status"), status_text(selected_seat.get("status"), audience="admin")),
            (t("seat.has_person"), _format_bool(selected_seat.get("has_person"))),
            (t("seat.has_object"), _format_bool(selected_seat.get("has_object"))),
            (t("seat.unattended"), _format_minutes(selected_seat.get("unattended_minutes"))),
            (t("seat.updated"), format_datetime(selected_seat.get("updated_at"))),
        ]),
        unsafe_allow_html=True,
    )


def render_anomaly_location(seats: list[dict[str, Any]], selected_seat: dict[str, Any] | None) -> None:
    if not selected_seat:
        st.info(t("admin.no_anomalies"))
        return

    lang = current_language()
    floor = selected_seat.get("floor") or ("未标注" if lang == "zh" else "Unlabeled")
    zone = selected_seat.get("zone") or ("未标注" if lang == "zh" else "Unlabeled")
    camera_id = selected_seat.get("camera_id") or ("未标注摄像头" if lang == "zh" else "Unlabeled camera")
    scope = f"{floor} 楼 / {zone} 区 / {camera_id}" if lang == "zh" else f"Floor {floor} / Zone {zone} / {camera_id}"
    st.caption(("定位范围：" if lang == "zh" else "Location scope: ") + scope)

    if not selected_seat.get("polygon"):
        st.info(t("admin.no_polygon"))
        return

    group_seats = _same_layout_group(seats, selected_seat)
    if not group_seats:
        st.info(t("empty.no_layout_data"))
        return

    svg = build_svg_seat_layout(
        group_seats,
        selected_seat_id=str(selected_seat.get("seat_id", "")),
        mode="admin",
        floor_label=f"{floor} 楼" if lang == "zh" else f"Floor {floor}",
        area_label=f"{zone} 区" if lang == "zh" else f"Zone {zone}",
        language=lang,
    )
    if t("empty.no_layout_data", "zh") in svg or t("empty.no_layout_data", "en") in svg:
        st.info(t("empty.no_layout_data"))
        return
    st_components.html(svg, height=260, scrolling=False)


def render_admin_section(data: dict[str, Any], selected_section: str, auto_refresh_enabled: bool) -> None:
    errors = data.get("errors", {})
    if _is_read_error(errors.get("seat")):
        st.error(t("empty.read_failed"))

    if not _seat_data_available(data):
        st.info(t("empty.no_seat_data"))
        return

    seats = data.get("seats", [])
    if selected_section == "管理概览":
        render_admin_summary(seats)
    elif selected_section == "异常座位":
        anomaly_rows = build_anomaly_rows(seats)

        if not anomaly_rows:
            st.info(t("admin.no_anomalies"))
        else:
            render_anomaly_table(seats)
    elif selected_section == "异常定位":
        anomaly_rows = build_anomaly_rows(seats)

        if not anomaly_rows:
            st.info(t("admin.no_anomalies"))
            return

        selector_col, map_col, detail_col = st.columns([1, 1.8, 1.1])
        with selector_col:
            st.markdown(f"**{t('admin.select_anomaly')}**")
            options = [str(row.get("seat_id", "")) for row in anomaly_rows]
            selected_seat_id = st.selectbox(t("admin.select_anomaly"), options, key="admin_selected_anomaly_seat")
        selected_seat = next(
            (row for row in anomaly_rows if str(row.get("seat_id", "")) == selected_seat_id),
            None,
        )
        with map_col:
            st.markdown(f"**{t('admin.location')}**")
            render_anomaly_location(seats, selected_seat)
        with detail_col:
            st.markdown(f"**{t('admin.detail')}**")
            render_anomaly_detail(selected_seat)


def render_admin_view(data: dict[str, Any], auto_refresh_enabled: bool) -> None:
    render_admin_section(data, ADMIN_SECTION_TABS[0], auto_refresh_enabled)


def render_role_workspace(data: dict[str, Any], admin_mode: bool, auto_refresh_enabled: bool) -> None:
    labels = ADMIN_SECTION_TABS if admin_mode else STUDENT_SECTION_TABS
    left_col, right_col = st.columns([0.24, 0.76], gap="large")
    with left_col:
        with st.container(border=True):
            selected_section = _render_left_navigation(labels, admin_mode)
    with right_col:
        with st.container(border=True):
            if admin_mode:
                render_admin_section(data, selected_section, auto_refresh_enabled)
            else:
                render_student_section(data, selected_section, auto_refresh_enabled)
