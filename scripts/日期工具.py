#!/usr/bin/env python3
"""日期与日期时间标准化工具。"""

from __future__ import annotations

import re
from argparse import Namespace
from datetime import date, datetime, timedelta


def 标准化日期(日期文本: str | None) -> str | None:
    if 日期文本 is None:
        return None
    文本 = 日期文本.strip()
    if not 文本:
        return None

    今天 = date.today()
    相对日期映射 = {
        "今天": 0,
        "今日": 0,
        "today": 0,
        "明天": 1,
        "tomorrow": 1,
        "后天": 2,
        "昨天": -1,
        "yesterday": -1,
    }
    偏移量 = 相对日期映射.get(文本.lower(), 相对日期映射.get(文本))
    if 偏移量 is not None:
        return (今天 + timedelta(days=偏移量)).isoformat()

    for 格式 in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.strptime(文本, 格式).date().isoformat()
        except ValueError:
            pass

    月日匹配 = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})", 文本)
    if 月日匹配:
        月份, 日 = (int(值) for 值 in 月日匹配.groups())
        try:
            return date(今天.year, 月份, 日).isoformat()
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(文本).date().isoformat()
    except ValueError as 异常:
        raise ValueError(
            f"无法识别日期格式：{日期文本}。支持示例：2026-03-27 / 2026/03/27 / 20260327 / 今天 / tomorrow"
        ) from 异常


def 标准化日期时间(日期时间文本: str | None) -> str | None:
    if 日期时间文本 is None:
        return None
    文本 = 日期时间文本.strip()
    if not 文本:
        return None

    匹配结果 = re.fullmatch(r"(.+?)\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?", 文本)
    if 匹配结果:
        日期部分, 小时, 分钟, 秒钟 = 匹配结果.groups()
        规范日期 = 标准化日期(日期部分)
        秒数字符串 = 秒钟 or "00"
        return f"{规范日期} {int(小时):02d}:{int(分钟):02d}:{int(秒数字符串):02d}"

    for 格式 in (
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y.%m.%d %H:%M",
        "%Y%m%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y%m%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(文本, 格式).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(文本).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    try:
        return 标准化日期(文本)
    except ValueError as 异常:
        raise ValueError(
            f"无法识别日期时间格式：{日期时间文本}。支持示例：2026-03-27 15:30 / 2026/03/27 15:30 / 今天 15:30"
        ) from 异常


def 标准化参数日期字段(参数: Namespace) -> None:
    for 字段 in ["下一步日期", "下一步日期截止前", "试用开始日期", "试用结束日期", "今日"]:
        if hasattr(参数, 字段) and getattr(参数, 字段):
            setattr(参数, 字段, 标准化日期(getattr(参数, 字段)))

    if hasattr(参数, "预约时间") and 参数.预约时间:
        参数.预约时间 = 标准化日期时间(参数.预约时间)
