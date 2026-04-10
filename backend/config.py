"""
Runtime configuration loader.

Reads config/mcp.yaml once at import time and exposes typed accessors for
model, transcription, and pipeline settings. Agents pull model name +
temperature from here instead of hardcoding, so config/mcp.yaml is the
single source of truth.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "mcp.yaml"

_DEFAULTS: dict[str, Any] = {
    "model": {
        "primary": "gpt-4o",
        "fallback": "gpt-4o-mini",
        "temperature": 0.2,
    },
    "transcription": {
        "model": "whisper-1",
    },
}


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return _DEFAULTS
    try:
        with CONFIG_PATH.open(encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
    except yaml.YAMLError:
        return _DEFAULTS

    merged = {**_DEFAULTS}
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def get_primary_model() -> str:
    return _load()["model"].get("primary", "gpt-4o")


def get_fallback_model() -> str:
    return _load()["model"].get("fallback", "gpt-4o-mini")


def get_model_temperature() -> float:
    return float(_load()["model"].get("temperature", 0.2))


def get_transcription_model() -> str:
    return _load().get("transcription", {}).get("model", "whisper-1")
