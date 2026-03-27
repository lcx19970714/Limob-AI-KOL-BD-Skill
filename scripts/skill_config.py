#!/usr/bin/env python3
"""Configuration loader for the sales system."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"
DEFAULT_REMOTE_BASE_URL = "https://invite.limob.cn"
DEFAULT_DEV_BASE_URL = "http://127.0.0.1:8000"


def load_skill_config() -> dict[str, Any]:
    config: dict[str, Any] = {
        "development_mode": False,
        "long_term_token": "",
        "timeout_seconds": 20,
    }

    if CONFIG_PATH.exists():
        loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            config.update(loaded)

    config["resolved_base_url"] = _resolve_base_url(config)
    return config


def save_skill_config(config: dict[str, Any]) -> None:
    serializable_config = {
        "development_mode": bool(config.get("development_mode", False)),
        "long_term_token": str(config.get("long_term_token") or ""),
        "timeout_seconds": config.get("timeout_seconds", 20),
    }
    CONFIG_PATH.write_text(
        json.dumps(serializable_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_long_term_token(long_term_token: str) -> None:
    config = load_skill_config()
    config["long_term_token"] = str(long_term_token or "")
    save_skill_config(config)


def _resolve_base_url(config: dict[str, Any]) -> str:
    if config.get("development_mode"):
        return DEFAULT_DEV_BASE_URL.rstrip("/")
    return DEFAULT_REMOTE_BASE_URL.rstrip("/")
