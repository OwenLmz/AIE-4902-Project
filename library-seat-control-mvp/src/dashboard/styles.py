from __future__ import annotations

KNOWN_STATUSES = {
    "free",
    "occupied",
    "suspected",
    "unavailable",
}

STUDENT_STATUS_LABELS = {
    "free": "空闲",
    "occupied": "使用中",
    "suspected": "疑似占座（待确认）",
    "unavailable": "不可用",
}

ADMIN_STATUS_LABELS = {
    "free": "空闲",
    "occupied": "使用中",
    "suspected": "疑似占座",
    "unavailable": "不可用",
}

UNKNOWN_STATUS_LABEL = "未知状态"

STATUS_COLORS = {
    "free": "#2e7d32",
    "occupied": "#1565c0",
    "suspected": "#c62828",
    "unavailable": "#757575",
    "UNKNOWN": "#616161",
}

CROWDING_LEVEL_LABELS = {
    "low": "低",
    "medium": "中等",
    "high": "拥挤",
    "full": "接近满载",
}

CROWDING_LEVEL_COLORS = {
    "low": "#2e7d32",
    "medium": "#f9a825",
    "high": "#ef6c00",
    "full": "#c62828",
}


def status_label(status: str | None, audience: str = "student") -> str:
    labels = ADMIN_STATUS_LABELS if audience == "admin" else STUDENT_STATUS_LABELS
    return labels.get(normalize_status(status)[0], UNKNOWN_STATUS_LABEL)


def normalize_status(status: object) -> tuple[str, str | None]:
    raw = str(status or "").strip()
    normalized = raw.lower()
    legacy_map = {
        "free": "free",
        "occupied": "occupied",
        "possibly_occupied": "occupied",
        "suspicious": "suspected",
        "suspected": "suspected",
        "unavailable": "unavailable",
    }
    mapped = legacy_map.get(normalized)
    if mapped in KNOWN_STATUSES:
        return mapped, None
    return normalized or "unknown", "unknown_status"


def crowding_level_from_ratio(ratio: float) -> str:
    if ratio < 0.50:
        return "low"
    if ratio < 0.75:
        return "medium"
    if ratio < 0.90:
        return "high"
    return "full"
