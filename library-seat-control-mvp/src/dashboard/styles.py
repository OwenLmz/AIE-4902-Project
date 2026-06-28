from __future__ import annotations

KNOWN_STATUSES = {
    "FREE",
    "OCCUPIED",
    "POSSIBLY_OCCUPIED",
    "SUSPICIOUS",
    "UNAVAILABLE",
}

STUDENT_STATUS_LABELS = {
    "FREE": "空闲",
    "OCCUPIED": "使用中",
    "POSSIBLY_OCCUPIED": "暂不可用",
    "SUSPICIOUS": "疑似占座（待确认）",
    "UNAVAILABLE": "不可用",
}

ADMIN_STATUS_LABELS = {
    "FREE": "空闲",
    "OCCUPIED": "使用中",
    "POSSIBLY_OCCUPIED": "暂不可用",
    "SUSPICIOUS": "疑似占座",
    "UNAVAILABLE": "不可用",
}

UNKNOWN_STATUS_LABEL = "未知状态"

STATUS_COLORS = {
    "FREE": "#2e7d32",
    "OCCUPIED": "#1565c0",
    "POSSIBLY_OCCUPIED": "#ef6c00",
    "SUSPICIOUS": "#c62828",
    "UNAVAILABLE": "#757575",
    "UNKNOWN": "#616161",
}

CROWD_LEVEL_LABELS = {
    "LOW": "低",
    "MEDIUM": "中等",
    "HIGH": "拥挤",
    "FULL": "接近满载",
}

CROWD_LEVEL_COLORS = {
    "LOW": "#2e7d32",
    "MEDIUM": "#f9a825",
    "HIGH": "#ef6c00",
    "FULL": "#c62828",
}


def status_label(status: str | None, audience: str = "student") -> str:
    labels = ADMIN_STATUS_LABELS if audience == "admin" else STUDENT_STATUS_LABELS
    return labels.get(str(status or "").upper(), UNKNOWN_STATUS_LABEL)


def normalize_status(status: object) -> tuple[str, str | None]:
    normalized = str(status or "").strip().upper()
    if normalized in KNOWN_STATUSES:
        return normalized, None
    return normalized or "UNKNOWN", "unknown_status"


def crowd_level_from_ratio(ratio: float) -> str:
    if ratio < 0.50:
        return "LOW"
    if ratio < 0.75:
        return "MEDIUM"
    if ratio < 0.90:
        return "HIGH"
    return "FULL"

