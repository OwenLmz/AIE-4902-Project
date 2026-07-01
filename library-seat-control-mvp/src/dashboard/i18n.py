from __future__ import annotations

from typing import Any

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

LANGUAGE_OPTIONS = {"中": "zh", "EN": "en"}
LANGUAGE_LABELS = {"zh": "中", "en": "EN"}
DEFAULT_LANGUAGE = "zh"


TRANSLATIONS: dict[str, dict[str, str]] = {
    "app.page_title": {"zh": "图书馆智能位控 MVP", "en": "Library Seat Control MVP"},
    "app.title": {"zh": "图书馆智能位控系统", "en": "Library Smart Seat Control"},
    "app.subtitle": {"zh": "Library Decision System", "en": "Library Decision System"},
    "app.admin_mode": {"zh": "管理员模式", "en": "Admin"},
    "app.student_mode": {"zh": "学生模式", "en": "Student"},
    "app.auto_refresh": {"zh": "自动刷新", "en": "Auto refresh"},
    "app.refresh_on": {"zh": "开启 · 每 5 秒", "en": "On · every 5s"},
    "app.refresh_off": {"zh": "关闭", "en": "Off"},
    "app.mock_status": {"zh": "模拟数据 · 原型验证中", "en": "Mock data · prototype only"},
    "app.current": {"zh": "当前", "en": "Mode"},
    "app.seat_updated": {"zh": "座位更新", "en": "Seat updated"},
    "app.refresh": {"zh": "自动刷新", "en": "Auto refresh"},
    "empty.no_data": {"zh": "暂无数据", "en": "No data"},
    "empty.no_seat_data": {"zh": "暂无座位数据", "en": "No seat data"},
    "empty.no_crowd_data": {"zh": "暂无人流数据", "en": "No crowd data"},
    "empty.no_layout_data": {"zh": "暂无座位布局数据", "en": "No seat layout data"},
    "empty.read_failed": {"zh": "数据读取失败", "en": "Failed to load data"},
    "unit.people": {"zh": "人", "en": "people"},
    "unit.seats": {"zh": "座", "en": "seats"},
    "unit.minutes": {"zh": "分钟", "en": "min"},
    "nav.entry": {"zh": "功能入口", "en": "Navigation"},
    "nav.student_desc": {"zh": "面向学生完成空间决策和选座", "en": "For students to choose area and seat"},
    "nav.admin_desc": {"zh": "面向馆员查看异常和定位座位", "en": "For staff to inspect and locate anomalies"},
    "nav.overview": {"zh": "总览", "en": "Overview"},
    "nav.area": {"zh": "区域推荐", "en": "Area Advice"},
    "nav.map": {"zh": "座位地图", "en": "Seat Map"},
    "nav.trend": {"zh": "人流趋势", "en": "Crowd Trend"},
    "nav.admin_overview": {"zh": "管理概览", "en": "Admin Overview"},
    "nav.anomaly_list": {"zh": "异常座位", "en": "Anomalies"},
    "nav.anomaly_location": {"zh": "异常定位", "en": "Locate"},
    "nav.overview_desc": {"zh": "判断现在是否适合去图书馆", "en": "Decide whether to go now"},
    "nav.area_desc": {"zh": "查看哪一层、哪个区域更适合前往", "en": "Find the best floor and zone"},
    "nav.map_desc": {"zh": "切换楼层和区域，选择具体座位", "en": "Choose a specific seat"},
    "nav.trend_desc": {"zh": "查看历史人数变化和预测状态", "en": "Review historical crowd changes"},
    "nav.admin_overview_desc": {"zh": "快速了解异常规模和使用率", "en": "Review anomaly scale and occupancy"},
    "nav.anomaly_list_desc": {"zh": "查看异常座位及持续时间", "en": "Review abnormal seats and duration"},
    "nav.anomaly_location_desc": {"zh": "定位异常座位所在区域", "en": "Locate the abnormal seat"},
    "summary.title": {"zh": "当前概览", "en": "Current Overview"},
    "summary.people_capacity": {"zh": "馆内人数 / 容量", "en": "People / Capacity"},
    "summary.people_help": {"zh": "来自闸机模拟数据", "en": "From mock gate data"},
    "summary.free_seats": {"zh": "全馆空闲座位", "en": "Free Seats"},
    "summary.free_help": {"zh": "仅统计空闲座位", "en": "Free seats only"},
    "summary.crowding_level": {"zh": "当前拥挤等级", "en": "Crowding Level"},
    "summary.trend": {"zh": "趋势判断", "en": "Trend"},
    "summary.forecast_unavailable": {"zh": "预测数据暂不可用", "en": "Prediction unavailable"},
    "summary.forecast_help": {"zh": "预测模型暂未启用", "en": "Forecast model not enabled"},
    "summary.decision": {"zh": "当前判断", "en": "Decision"},
    "summary.no_free_action": {"zh": "当前暂无空闲座位，建议暂缓前往或等待数据刷新。", "en": "No free seats now. Consider waiting or refreshing later."},
    "summary.low_free_action": {"zh": "当前空闲座位很少，建议先查看区域推荐和座位地图后再出发。", "en": "Only a few seats are free. Check area advice and the seat map first."},
    "summary.free_action": {"zh": "当前仍有空闲座位，可以继续查看推荐区域并选择具体座位。", "en": "Free seats are available. Continue to area advice and choose a seat."},
    "area.title": {"zh": "推荐结论", "en": "Recommendation"},
    "area.no_data": {"zh": "暂无区域数据", "en": "No area data"},
    "area.no_recommendation": {"zh": "暂无足够数据生成区域推荐", "en": "Not enough data for area advice"},
    "area.current_advice": {"zh": "当前建议", "en": "Current advice"},
    "area.free": {"zh": "当前区域空闲", "en": "Free seats"},
    "area.ratio": {"zh": "可用率", "en": "Availability"},
    "area.reason": {"zh": "推荐原因", "en": "Reason"},
    "area.risk": {"zh": "风险提示", "en": "Risk"},
    "area.next": {"zh": "下一步建议", "en": "Next step"},
    "area.note": {"zh": "说明：馆内人数来自闸机模拟数据；座位状态来自座位识别模拟数据。当前区域指标仅统计对应楼层和区域。", "en": "Note: crowd data comes from mock gate flow, and seat status comes from mock recognition data. Area metrics only count the selected floor and zone."},
    "area.recommend": {"zh": "推荐去", "en": "Recommended"},
    "area.consider": {"zh": "可考虑", "en": "Consider"},
    "area.avoid": {"zh": "不建议", "en": "Not advised"},
    "map.title": {"zh": "座位选择", "en": "Seat Selection"},
    "map.floor": {"zh": "选择楼层", "en": "Floor"},
    "map.zone": {"zh": "选择区域", "en": "Zone"},
    "map.group": {"zh": "选择摄像头视角", "en": "Camera view"},
    "map.seat": {"zh": "选择座位（空闲座位优先）", "en": "Choose seat (free seats first)"},
    "map.current_or_recommended": {"zh": "推荐 / 选中座位", "en": "Recommended / Selected Seat"},
    "map.selected": {"zh": "选中座位", "en": "Selected Seat"},
    "map.recommended": {"zh": "推荐座位", "en": "Recommended Seat"},
    "map.warning_invalid_layout": {"zh": "部分座位 ROI / 布局坐标不可用，已跳过对应座位。", "en": "Some seat ROI/layout coordinates are invalid and were skipped."},
    "seat.id": {"zh": "座位编号", "en": "Seat ID"},
    "seat.location": {"zh": "位置", "en": "Location"},
    "seat.floor": {"zh": "楼层", "en": "Floor"},
    "seat.zone": {"zh": "区域", "en": "Zone"},
    "seat.camera": {"zh": "摄像头视角", "en": "Camera View"},
    "seat.status": {"zh": "当前状态", "en": "Status"},
    "seat.updated": {"zh": "最后更新", "en": "Last Updated"},
    "seat.has_person": {"zh": "是否检测到人", "en": "Person Detected"},
    "seat.has_object": {"zh": "是否检测到物品", "en": "Object Detected"},
    "seat.unattended": {"zh": "无人有物持续时间", "en": "Unattended Duration"},
    "seat.yes": {"zh": "是", "en": "Yes"},
    "seat.no": {"zh": "否", "en": "No"},
    "trend.title": {"zh": "图书馆人流趋势", "en": "Library Crowd Trend"},
    "trend.range": {"zh": "时间范围", "en": "Time Range"},
    "trend.3h": {"zh": "近3小时", "en": "Last 3 Hours"},
    "trend.today": {"zh": "今日", "en": "Today"},
    "trend.3d": {"zh": "近3天", "en": "Last 3 Days"},
    "trend.insufficient": {"zh": "该时间范围内暂无足够数据", "en": "Not enough data in this range"},
    "trend.conclusion": {"zh": "趋势结论", "en": "Trend Summary"},
    "trend.data_range": {"zh": "数据范围", "en": "Data range"},
    "trend.no_capacity": {"zh": "容量数据缺失，暂不显示容量参考线", "en": "Capacity is missing, so the capacity line is hidden."},
    "trend.no_forecast": {"zh": "未来 30 分钟预测数据暂不可用，当前仅展示历史人流变化。", "en": "30-minute forecast is unavailable; only historical crowd changes are shown."},
    "trend.total_in_library": {"zh": "当前人数", "en": "Current"},
    "trend.capacity": {"zh": "容量", "en": "Capacity"},
    "trend.ratio": {"zh": "占比", "en": "Ratio"},
    "trend.no_history": {"zh": "暂无人流历史数据", "en": "No crowd history data"},
    "admin.title": {"zh": "管理概览", "en": "Admin Overview"},
    "admin.possible": {"zh": "暂不可用", "en": "Temporarily Unavailable"},
    "admin.suspicious": {"zh": "疑似占座", "en": "Suspicious"},
    "admin.occupancy_rate": {"zh": "实际座位使用率", "en": "Actual Occupancy"},
    "admin.busiest_area": {"zh": "异常最多区域", "en": "Top Anomaly Area"},
    "admin.priority": {"zh": "优先巡查", "en": "Priority check"},
    "admin.patrol_focus": {"zh": "用于定位巡查重点", "en": "Patrol focus"},
    "admin.no_anomalies": {"zh": "当前暂无疑似占座座位", "en": "No suspicious seats now"},
    "admin.select_anomaly": {"zh": "选择异常座位", "en": "Select Anomaly Seat"},
    "admin.location": {"zh": "异常定位", "en": "Anomaly Location"},
    "admin.detail": {"zh": "异常详情", "en": "Anomaly Details"},
    "admin.same_view": {"zh": "当前只显示同一楼层、区域和摄像头视角下的座位，不混合不同坐标系。", "en": "Only seats in the same floor, zone, and camera view are shown."},
    "admin.no_layout_coordinates": {"zh": "该座位暂无 ROI / 布局坐标，无法在座位图中定位", "en": "This seat has no ROI/layout coordinates and cannot be located on the map."},
    "admin.choose_seat": {"zh": "请选择异常座位", "en": "Please select an abnormal seat"},
}


STATUS_LABELS = {
    "zh": {
        "free": "空闲",
        "occupied": "使用中",
        "suspected": "疑似占座",
        "unavailable": "不可用",
        "unknown": "未知状态",
    },
    "en": {
        "free": "Free",
        "occupied": "Occupied",
        "suspected": "Suspicious",
        "unavailable": "Unavailable",
        "unknown": "Unknown",
    },
}


STUDENT_STATUS_LABELS = {
    "zh": {
        "suspected": "疑似占座（待确认）",
    },
    "en": {
        "suspected": "Suspicious (pending check)",
    },
}


CROWDING_LEVEL_LABELS = {
    "zh": {
        "LOW": "低",
        "MEDIUM": "中等",
        "HIGH": "拥挤",
        "FULL": "接近满载",
    },
    "en": {
        "LOW": "Low",
        "MEDIUM": "Medium",
        "HIGH": "Crowded",
        "FULL": "Near full",
    },
}


def current_language() -> str:
    if get_script_run_ctx(suppress_warning=True) is None:
        return DEFAULT_LANGUAGE
    try:
        value = st.session_state.get("ui_language", DEFAULT_LANGUAGE)
    except Exception:
        value = DEFAULT_LANGUAGE
    return value if value in LANGUAGE_LABELS else DEFAULT_LANGUAGE


def language_from_label(label: str) -> str:
    return LANGUAGE_OPTIONS.get(label, DEFAULT_LANGUAGE)


def language_label(language: str | None = None) -> str:
    return LANGUAGE_LABELS.get(language or current_language(), LANGUAGE_LABELS[DEFAULT_LANGUAGE])


def t(key: str, language: str | None = None, **kwargs: Any) -> str:
    lang = language or current_language()
    text = TRANSLATIONS.get(key, {}).get(lang)
    if text is None:
        text = TRANSLATIONS.get(key, {}).get(DEFAULT_LANGUAGE, key)
    return text.format(**kwargs) if kwargs else text


def status_text(status: object, audience: str = "student", language: str | None = None) -> str:
    lang = language or current_language()
    normalized = str(status or "").strip().lower() or "unknown"
    normalized = {
        "suspicious": "suspected",
        "possibly_occupied": "occupied",
    }.get(normalized, normalized)
    labels = dict(STATUS_LABELS.get(lang, STATUS_LABELS[DEFAULT_LANGUAGE]))
    if audience == "student":
        labels.update(STUDENT_STATUS_LABELS.get(lang, {}))
    return labels.get(normalized, labels["unknown"])


def crowding_level_text(level: object, language: str | None = None) -> str:
    lang = language or current_language()
    return CROWDING_LEVEL_LABELS.get(lang, CROWDING_LEVEL_LABELS[DEFAULT_LANGUAGE]).get(str(level or "").upper(), t("empty.no_crowd_data", lang))
