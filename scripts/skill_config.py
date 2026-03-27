#!/usr/bin/env python3
"""销售系统技能配置读写工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

根目录 = Path(__file__).resolve().parents[1]
配置文件路径 = 根目录 / "config.json"
默认线上地址 = "https://invite.limob.cn"
默认开发地址 = "http://127.0.0.1:8000"


def 加载技能配置() -> dict[str, Any]:
    配置: dict[str, Any] = {
        "development_mode": False,
        "long_term_token": "",
        "timeout_seconds": 20,
    }

    if 配置文件路径.exists():
        已加载配置 = json.loads(配置文件路径.read_text(encoding="utf-8"))
        if isinstance(已加载配置, dict):
            配置.update(已加载配置)

    配置["resolved_base_url"] = _解析基础地址(配置)
    return 配置


def 保存技能配置(配置: dict[str, Any]) -> None:
    可序列化配置 = {
        "development_mode": bool(配置.get("development_mode", False)),
        "long_term_token": str(配置.get("long_term_token") or ""),
        "timeout_seconds": 配置.get("timeout_seconds", 20),
    }
    配置文件路径.write_text(
        json.dumps(可序列化配置, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def 写入长效令牌(long_term_token: str) -> None:
    配置 = 加载技能配置()
    配置["long_term_token"] = str(long_term_token or "")
    保存技能配置(配置)


def _解析基础地址(配置: dict[str, Any]) -> str:
    if 配置.get("development_mode"):
        return 默认开发地址.rstrip("/")
    return 默认线上地址.rstrip("/")
