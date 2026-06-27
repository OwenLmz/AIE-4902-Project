from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


ENV_PATTERN = re.compile(r"^\$\{([^:}]+):?([^}]*)\}$")


class ConfigError(RuntimeError):
    pass


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_dotenv(root: Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(root / ".env")


def _expand_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if not isinstance(value, str):
        return value

    match = ENV_PATTERN.match(value)
    if not match:
        return value
    name, default = match.groups()
    return os.getenv(name, default)


def _resolve_paths(config: dict[str, Any], root: Path) -> dict[str, Any]:
    paths = config.setdefault("paths", {})
    for key in ("model", "images_dir", "outputs_dir"):
        raw = Path(paths[key])
        paths[key] = str(raw if raw.is_absolute() else root / raw)
    return config


def _coerce_numbers(config: dict[str, Any]) -> dict[str, Any]:
    mysql = config.get("mysql", {})
    redis = config.get("redis", {})
    runtime = config.get("runtime", {})
    mysql["port"] = int(mysql.get("port", 3306))
    redis["port"] = int(redis.get("port", 6379))
    redis["db"] = int(redis.get("db", 0))
    runtime["image_size"] = int(runtime.get("image_size", 640))
    runtime["sample_interval_min"] = int(runtime.get("sample_interval_min", 30))
    runtime["suspect_threshold_min"] = int(runtime.get("suspect_threshold_min", 20))
    runtime["redis_ttl_sec"] = int(runtime.get("redis_ttl_sec", 120))
    runtime["confidence"] = float(runtime.get("confidence", 0.25))
    config["mysql"] = mysql
    config["redis"] = redis
    config["runtime"] = runtime
    return config


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    root = project_root()
    _load_dotenv(root)

    path = Path(config_path) if config_path else root / "config.yaml"
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        import yaml
    except ImportError as exc:
        raise ConfigError("Missing dependency PyYAML. Run setup.ps1 or pip install -r requirements.txt.") from exc

    with path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    config = _expand_env(config)
    config = _resolve_paths(config, root)
    config = _coerce_numbers(config)
    config["project_root"] = str(root)
    return config

