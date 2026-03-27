#!/usr/bin/env python3
"""SQLite data layer for sales automation and dashboard."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "sales.sqlite3"

阶段配置 = [
    {"代码": "lead-inbox", "名称": "线索入库", "目标": "24 小时内完成分级和下一步"},
    {"代码": "expo-touch", "名称": "展会首触达", "目标": "先加微信，再约演示"},
    {"代码": "first-chat", "名称": "入站首聊", "目标": "30 分钟内确认痛点方向"},
    {"代码": "qualification", "名称": "资格判断", "目标": "明确场景、拍板人、时间表"},
    {"代码": "discovery", "名称": "需求沟通", "目标": "把需求翻成可试用方案"},
    {"代码": "demo", "名称": "产品演示", "目标": "证明系统真的能执行"},
    {"代码": "trial", "名称": "试用启动", "目标": "限定场景并写清 KPI"},
    {"代码": "trial-follow-up", "名称": "试用跟进", "目标": "每次只讲一个结果和下一步"},
    {"代码": "quote", "名称": "报价", "目标": "把价值翻成可购买方案"},
    {"代码": "contract", "名称": "合同打款", "目标": "确认签约与付款节点"},
    {"代码": "handoff", "名称": "成交交接", "目标": "把背景和承诺完整同步实施"},
    {"代码": "closed-won", "名称": "已成交", "目标": "沉淀成交经验和交付信息"},
    {"代码": "closed-lost", "名称": "已丢单", "目标": "记录原因并用于复盘"},
]

阶段映射 = {item["代码"]: item for item in 阶段配置}
活跃阶段 = {item["代码"] for item in 阶段配置 if item["代码"] not in {"closed-won", "closed-lost"}}


def 当前时间() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def 文本值(值: object | None, 默认值: str = "") -> str:
    if 值 is None:
        return 默认值
    return str(值)


def 阶段名称(阶段代码: str | None) -> str:
    if not 阶段代码:
        return ""
    return 阶段映射.get(阶段代码, {}).get("名称", 阶段代码)


def 连接数据库(数据库路径: str | Path | None = None) -> sqlite3.Connection:
    路径 = Path(数据库路径 or DEFAULT_DB_PATH)
    路径.parent.mkdir(parents=True, exist_ok=True)
    连接 = sqlite3.connect(路径)
    连接.row_factory = sqlite3.Row
    连接.execute("PRAGMA foreign_keys = ON")
    初始化数据库(连接)
    return 连接


def 初始化数据库(连接: sqlite3.Connection) -> None:
    连接.executescript(
        """
        CREATE TABLE IF NOT EXISTS 销售机会 (
            线索编号 TEXT PRIMARY KEY,
            客户名称 TEXT NOT NULL,
            联系人 TEXT NOT NULL DEFAULT '',
            联系角色 TEXT NOT NULL DEFAULT '',
            线索来源 TEXT NOT NULL,
            产品类目 TEXT NOT NULL DEFAULT '',
            团队规模 INTEGER,
            当前合作方式 TEXT NOT NULL DEFAULT '',
            月建联量 INTEGER,
            决策人 TEXT NOT NULL DEFAULT '未确认',
            是否决策人 INTEGER,
            当前阶段 TEXT NOT NULL,
            优先级 TEXT NOT NULL,
            核心痛点 TEXT NOT NULL DEFAULT '',
            上次沟通摘要 TEXT NOT NULL DEFAULT '',
            客户想法 TEXT NOT NULL DEFAULT '',
            预计推进天数 INTEGER,
            内部负责人 TEXT NOT NULL DEFAULT '',
            下一步动作 TEXT NOT NULL,
            下一步日期 TEXT NOT NULL,
            是否已试用 INTEGER,
            试用状态 TEXT NOT NULL DEFAULT '未试用',
            试用开始日期 TEXT NOT NULL DEFAULT '',
            试用结束日期 TEXT NOT NULL DEFAULT '',
            报价版本 TEXT NOT NULL DEFAULT '',
            采购主体 TEXT NOT NULL DEFAULT '',
            最近联系时间 TEXT NOT NULL,
            备注 TEXT NOT NULL DEFAULT '',
            创建时间 TEXT NOT NULL,
            更新时间 TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS 成功指标 (
            指标编号 INTEGER PRIMARY KEY AUTOINCREMENT,
            线索编号 TEXT NOT NULL,
            指标名称 TEXT NOT NULL,
            FOREIGN KEY (线索编号) REFERENCES 销售机会(线索编号) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS 跟进记录 (
            记录编号 INTEGER PRIMARY KEY AUTOINCREMENT,
            线索编号 TEXT NOT NULL,
            记录时间 TEXT NOT NULL,
            沟通方式 TEXT NOT NULL DEFAULT '',
            预约时间 TEXT NOT NULL DEFAULT '',
            记录内容 TEXT NOT NULL,
            跟进结果 TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (线索编号) REFERENCES 销售机会(线索编号) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_销售机会_阶段 ON 销售机会(当前阶段);
        CREATE INDEX IF NOT EXISTS idx_销售机会_优先级 ON 销售机会(优先级);
        CREATE INDEX IF NOT EXISTS idx_销售机会_下一步日期 ON 销售机会(下一步日期);
        CREATE INDEX IF NOT EXISTS idx_跟进记录_线索编号 ON 跟进记录(线索编号);
        CREATE INDEX IF NOT EXISTS idx_成功指标_线索编号 ON 成功指标(线索编号);
        """
    )
    _迁移销售机会到单一下一步字段(连接)
    _确保字段存在(
        连接,
        "销售机会",
        [
            "上次沟通摘要 TEXT NOT NULL DEFAULT ''",
            "客户想法 TEXT NOT NULL DEFAULT ''",
            "是否已试用 INTEGER",
            "试用状态 TEXT NOT NULL DEFAULT '未试用'",
            "试用开始日期 TEXT NOT NULL DEFAULT ''",
            "试用结束日期 TEXT NOT NULL DEFAULT ''",
        ],
    )
    _确保字段存在(
        连接,
        "跟进记录",
        [
            "沟通方式 TEXT NOT NULL DEFAULT ''",
            "预约时间 TEXT NOT NULL DEFAULT ''",
        ],
    )
    连接.commit()


def _确保字段存在(连接: sqlite3.Connection, 表名: str, 字段定义列表: list[str]) -> None:
    已有字段 = {
        row["name"]
        for row in 连接.execute(f"PRAGMA table_info({表名})").fetchall()
    }
    for 字段定义 in 字段定义列表:
        字段名 = 字段定义.split()[0]
        if 字段名 in 已有字段:
            continue
        try:
            连接.execute(f"ALTER TABLE {表名} ADD COLUMN {字段定义}")
        except sqlite3.OperationalError as error:
            if "duplicate column name" not in str(error):
                raise


def _迁移销售机会到单一下一步字段(连接: sqlite3.Connection) -> None:
    字段列表 = [row["name"] for row in 连接.execute("PRAGMA table_info(销售机会)").fetchall()]
    if not {"下次沟通日期", "下次沟通目的"} & set(字段列表):
        return

    连接.executescript(
        """
        DROP INDEX IF EXISTS idx_销售机会_阶段;
        DROP INDEX IF EXISTS idx_销售机会_优先级;
        DROP INDEX IF EXISTS idx_销售机会_下一步日期;

        ALTER TABLE 销售机会 RENAME TO 销售机会_旧;

        CREATE TABLE 销售机会 (
            线索编号 TEXT PRIMARY KEY,
            客户名称 TEXT NOT NULL,
            联系人 TEXT NOT NULL DEFAULT '',
            联系角色 TEXT NOT NULL DEFAULT '',
            线索来源 TEXT NOT NULL,
            产品类目 TEXT NOT NULL DEFAULT '',
            团队规模 INTEGER,
            当前合作方式 TEXT NOT NULL DEFAULT '',
            月建联量 INTEGER,
            决策人 TEXT NOT NULL DEFAULT '未确认',
            是否决策人 INTEGER,
            当前阶段 TEXT NOT NULL,
            优先级 TEXT NOT NULL,
            核心痛点 TEXT NOT NULL DEFAULT '',
            上次沟通摘要 TEXT NOT NULL DEFAULT '',
            客户想法 TEXT NOT NULL DEFAULT '',
            预计推进天数 INTEGER,
            内部负责人 TEXT NOT NULL DEFAULT '',
            下一步动作 TEXT NOT NULL,
            下一步日期 TEXT NOT NULL,
            是否已试用 INTEGER,
            试用状态 TEXT NOT NULL DEFAULT '未试用',
            试用开始日期 TEXT NOT NULL DEFAULT '',
            试用结束日期 TEXT NOT NULL DEFAULT '',
            报价版本 TEXT NOT NULL DEFAULT '',
            采购主体 TEXT NOT NULL DEFAULT '',
            最近联系时间 TEXT NOT NULL,
            备注 TEXT NOT NULL DEFAULT '',
            创建时间 TEXT NOT NULL,
            更新时间 TEXT NOT NULL
        );

        INSERT INTO 销售机会 (
            线索编号, 客户名称, 联系人, 联系角色, 线索来源, 产品类目, 团队规模,
            当前合作方式, 月建联量, 决策人, 是否决策人, 当前阶段, 优先级,
            核心痛点, 上次沟通摘要, 客户想法, 预计推进天数, 内部负责人,
            下一步动作, 下一步日期, 是否已试用, 试用状态, 试用开始日期, 试用结束日期,
            报价版本, 采购主体, 最近联系时间, 备注, 创建时间, 更新时间
        )
        SELECT
            线索编号,
            客户名称,
            联系人,
            联系角色,
            线索来源,
            产品类目,
            团队规模,
            当前合作方式,
            月建联量,
            决策人,
            是否决策人,
            当前阶段,
            优先级,
            核心痛点,
            上次沟通摘要,
            客户想法,
            预计推进天数,
            内部负责人,
            CASE
                WHEN NULLIF(下一步动作, '') IS NOT NULL THEN 下一步动作
                WHEN NULLIF(下次沟通目的, '') IS NOT NULL THEN 下次沟通目的
                ELSE ''
            END,
            CASE
                WHEN NULLIF(下一步日期, '') IS NOT NULL THEN 下一步日期
                WHEN NULLIF(下次沟通日期, '') IS NOT NULL THEN 下次沟通日期
                ELSE ''
            END,
            是否已试用,
            试用状态,
            试用开始日期,
            试用结束日期,
            报价版本,
            采购主体,
            最近联系时间,
            备注,
            创建时间,
            更新时间
        FROM 销售机会_旧;

        DROP TABLE 销售机会_旧;

        CREATE INDEX IF NOT EXISTS idx_销售机会_阶段 ON 销售机会(当前阶段);
        CREATE INDEX IF NOT EXISTS idx_销售机会_优先级 ON 销售机会(优先级);
        CREATE INDEX IF NOT EXISTS idx_销售机会_下一步日期 ON 销售机会(下一步日期);
        """
    )


def 校验阶段(阶段代码: str | None) -> str | None:
    if 阶段代码 is None:
        return None
    if 阶段代码 not in 阶段映射:
        可选值 = "、".join(item["代码"] for item in 阶段配置)
        raise ValueError(f"阶段无效：{阶段代码}。可选值：{可选值}")
    return 阶段代码


def 校验优先级(优先级: str | None) -> str | None:
    if 优先级 is None:
        return None
    if 优先级 not in {"A", "B", "C"}:
        raise ValueError("优先级必须是 A、B 或 C")
    return 优先级


def 校验日期(日期值: str | None) -> str | None:
    if 日期值 in {None, ""}:
        return 日期值
    datetime.strptime(日期值, "%Y-%m-%d")
    return 日期值


def 解析布尔值(值: str | int | bool | None) -> int | None:
    if 值 is None or 值 == "":
        return None
    if isinstance(值, bool):
        return 1 if 值 else 0
    if isinstance(值, int):
        return 1 if 值 else 0
    标准值 = str(值).strip().lower()
    if 标准值 in {"1", "true", "yes", "y"}:
        return 1
    if 标准值 in {"0", "false", "no", "n"}:
        return 0
    raise ValueError(f"布尔值无效：{值}")


def 解析成功指标(原始值: str | list[str] | None) -> list[str]:
    if 原始值 is None:
        return []
    if isinstance(原始值, list):
        return [item.strip() for item in 原始值 if str(item).strip()]
    return [item.strip() for item in str(原始值).split(",") if item.strip()]


def 解析空日期(日期值: str | None) -> str:
    if 日期值 in {None, ""}:
        return ""
    return 校验日期(日期值) or ""


def 推断优先级(记录: dict) -> str:
    当前阶段 = 记录.get("当前阶段")
    决策人 = 记录.get("决策人")
    是否决策人 = 记录.get("是否决策人")
    预计推进天数 = 记录.get("预计推进天数")
    核心痛点 = 记录.get("核心痛点")
    是否已试用 = 记录.get("是否已试用")
    试用状态 = 记录.get("试用状态")
    已确认决策链 = 决策人 and 决策人 not in {"unknown", "未确认", "self"}

    if 当前阶段 in {"demo", "trial", "trial-follow-up", "quote", "contract", "handoff"}:
        return "A"
    if 是否决策人 == 1 or 决策人 in {"self", "当前联系人"}:
        if 预计推进天数 is not None and int(预计推进天数) <= 30:
            return "A"
        return "B"
    if 已确认决策链:
        if 预计推进天数 is not None and int(预计推进天数) <= 30:
            return "A"
        return "B"
    if 是否已试用 == 1 or 试用状态 in {"试用中", "试用完成"}:
        return "B"
    if 核心痛点 or 当前阶段 in {"qualification", "discovery", "first-chat"}:
        return "B"
    return "C"


def 生成线索编号(连接: sqlite3.Connection) -> str:
    结果 = 连接.execute(
        "SELECT 线索编号 FROM 销售机会 ORDER BY 线索编号 DESC LIMIT 1"
    ).fetchone()
    if not 结果:
        return "LEAD-0001"
    当前编号 = 结果["线索编号"]
    序号 = int(当前编号.split("-")[-1]) + 1
    return f"LEAD-{序号:04d}"


def _更新成功指标(连接: sqlite3.Connection, 线索编号: str, 指标列表: list[str]) -> None:
    连接.execute("DELETE FROM 成功指标 WHERE 线索编号 = ?", (线索编号,))
    for 指标 in 指标列表:
        连接.execute(
            "INSERT INTO 成功指标 (线索编号, 指标名称) VALUES (?, ?)",
            (线索编号, 指标),
        )


def 新增机会(连接: sqlite3.Connection, 数据: dict) -> dict:
    当前 = 当前时间()
    线索编号 = 生成线索编号(连接)
    是否决策人 = 解析布尔值(数据.get("是否决策人"))
    是否已试用 = 解析布尔值(数据.get("是否已试用"))
    决策人 = 文本值(数据.get("决策人"))
    记录 = {
        "线索编号": 线索编号,
        "客户名称": 数据["客户名称"],
        "联系人": 文本值(数据.get("联系人")),
        "联系角色": 文本值(数据.get("联系角色")),
        "线索来源": 数据["线索来源"],
        "产品类目": 文本值(数据.get("产品类目")),
        "团队规模": 数据.get("团队规模"),
        "当前合作方式": 文本值(数据.get("当前合作方式")),
        "月建联量": 数据.get("月建联量"),
        "决策人": 决策人 or ("当前联系人" if 是否决策人 == 1 else "未确认"),
        "是否决策人": 是否决策人,
        "当前阶段": 校验阶段(数据["当前阶段"]),
        "优先级": 校验优先级(数据.get("优先级")),
        "核心痛点": 文本值(数据.get("核心痛点")),
        "上次沟通摘要": 文本值(数据.get("上次沟通摘要")),
        "客户想法": 文本值(数据.get("客户想法")),
        "预计推进天数": 数据.get("预计推进天数"),
        "内部负责人": 文本值(数据.get("内部负责人")),
        "下一步动作": 数据["下一步动作"],
        "下一步日期": 校验日期(数据["下一步日期"]),
        "是否已试用": 是否已试用,
        "试用状态": 文本值(数据.get("试用状态"), "未试用") or "未试用",
        "试用开始日期": 解析空日期(数据.get("试用开始日期")),
        "试用结束日期": 解析空日期(数据.get("试用结束日期")),
        "报价版本": 文本值(数据.get("报价版本")),
        "采购主体": 文本值(数据.get("采购主体")),
        "最近联系时间": 当前,
        "备注": 文本值(数据.get("备注")),
        "创建时间": 当前,
        "更新时间": 当前,
    }
    if not 记录["优先级"]:
        记录["优先级"] = 推断优先级(记录)

    连接.execute(
        """
        INSERT INTO 销售机会 (
            线索编号, 客户名称, 联系人, 联系角色, 线索来源, 产品类目, 团队规模,
            当前合作方式, 月建联量, 决策人, 是否决策人, 当前阶段, 优先级,
            核心痛点, 上次沟通摘要, 客户想法, 预计推进天数, 内部负责人,
            下一步动作, 下一步日期, 是否已试用,
            试用状态, 试用开始日期, 试用结束日期, 报价版本, 采购主体,
            最近联系时间, 备注, 创建时间, 更新时间
        ) VALUES (
            :线索编号, :客户名称, :联系人, :联系角色, :线索来源, :产品类目, :团队规模,
            :当前合作方式, :月建联量, :决策人, :是否决策人, :当前阶段, :优先级,
            :核心痛点, :上次沟通摘要, :客户想法, :预计推进天数, :内部负责人,
            :下一步动作, :下一步日期, :是否已试用,
            :试用状态, :试用开始日期, :试用结束日期, :报价版本, :采购主体,
            :最近联系时间, :备注, :创建时间, :更新时间
        )
        """,
        记录,
    )
    _更新成功指标(连接, 线索编号, 解析成功指标(数据.get("成功指标")))
    连接.commit()
    return 查询机会详情(连接, 线索编号)


def 更新机会(连接: sqlite3.Connection, 线索编号: str, 更新数据: dict, 自动推断优先级: bool = False) -> dict:
    现有 = 查询机会详情(连接, 线索编号)
    if not 现有:
        raise ValueError(f"未找到线索编号：{线索编号}")

    字段映射 = {
        "客户名称": "客户名称",
        "联系人": "联系人",
        "联系角色": "联系角色",
        "线索来源": "线索来源",
        "产品类目": "产品类目",
        "团队规模": "团队规模",
        "当前合作方式": "当前合作方式",
        "月建联量": "月建联量",
        "决策人": "决策人",
        "是否决策人": "是否决策人",
        "当前阶段": "当前阶段",
        "优先级": "优先级",
        "核心痛点": "核心痛点",
        "上次沟通摘要": "上次沟通摘要",
        "客户想法": "客户想法",
        "预计推进天数": "预计推进天数",
        "内部负责人": "内部负责人",
        "下一步动作": "下一步动作",
        "下一步日期": "下一步日期",
        "是否已试用": "是否已试用",
        "试用状态": "试用状态",
        "试用开始日期": "试用开始日期",
        "试用结束日期": "试用结束日期",
        "报价版本": "报价版本",
        "采购主体": "采购主体",
        "备注": "备注",
    }

    参数 = {}
    变更片段 = []
    for 外部字段, 数据库字段 in 字段映射.items():
        if 外部字段 not in 更新数据 or 更新数据[外部字段] is None:
            continue
        值 = 更新数据[外部字段]
        if 外部字段 == "当前阶段":
            值 = 校验阶段(值)
        elif 外部字段 == "优先级":
            值 = 校验优先级(值)
        elif 外部字段 in {"下一步日期", "试用开始日期", "试用结束日期"}:
            值 = 解析空日期(值)
        elif 外部字段 == "是否决策人":
            值 = 解析布尔值(值)
        elif 外部字段 == "是否已试用":
            值 = 解析布尔值(值)
        参数[数据库字段] = 值
        变更片段.append(f"{数据库字段} = :{数据库字段}")

    if "成功指标" in 更新数据:
        _更新成功指标(连接, 线索编号, 解析成功指标(更新数据.get("成功指标")))

    if not 变更片段 and "成功指标" in 更新数据:
        连接.commit()
        return 查询机会详情(连接, 线索编号)

    if not 变更片段:
        return 查询机会详情(连接, 线索编号)

    if 自动推断优先级 and "优先级" not in 参数:
        预览 = {**现有, **参数}
        参数["优先级"] = 推断优先级(预览)
        变更片段.append("优先级 = :优先级")

    参数["更新时间"] = 当前时间()
    参数["最近联系时间"] = 参数["更新时间"]
    参数["线索编号"] = 线索编号
    变更片段.append("更新时间 = :更新时间")
    变更片段.append("最近联系时间 = :最近联系时间")

    连接.execute(
        f"UPDATE 销售机会 SET {', '.join(变更片段)} WHERE 线索编号 = :线索编号",
        参数,
    )
    连接.commit()
    return 查询机会详情(连接, 线索编号)


def 记录跟进(
    连接: sqlite3.Connection,
    线索编号: str,
    记录内容: str,
    跟进结果: str = "",
    沟通方式: str = "",
    预约时间: str = "",
    当前阶段: str | None = None,
    优先级: str | None = None,
    下一步动作: str | None = None,
    下一步日期: str | None = None,
    上次沟通摘要: str | None = None,
    客户想法: str | None = None,
) -> dict:
    if not 查询机会详情(连接, 线索编号):
        raise ValueError(f"未找到线索编号：{线索编号}")

    时间 = 当前时间()
    连接.execute(
        """
        INSERT INTO 跟进记录 (线索编号, 记录时间, 沟通方式, 预约时间, 记录内容, 跟进结果)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (线索编号, 时间, 沟通方式 or "", 预约时间 or "", 记录内容, 跟进结果 or ""),
    )

    更新片段 = ["最近联系时间 = :最近联系时间", "更新时间 = :更新时间"]
    参数 = {"最近联系时间": 时间, "更新时间": 时间, "线索编号": 线索编号}

    if 当前阶段 is not None:
        参数["当前阶段"] = 校验阶段(当前阶段)
        更新片段.append("当前阶段 = :当前阶段")
    if 优先级 is not None:
        参数["优先级"] = 校验优先级(优先级)
        更新片段.append("优先级 = :优先级")
    if 下一步动作 is not None:
        参数["下一步动作"] = 下一步动作
        更新片段.append("下一步动作 = :下一步动作")
    if 下一步日期 is not None:
        参数["下一步日期"] = 校验日期(下一步日期)
        更新片段.append("下一步日期 = :下一步日期")
    if 上次沟通摘要 is not None:
        参数["上次沟通摘要"] = 上次沟通摘要
        更新片段.append("上次沟通摘要 = :上次沟通摘要")
    if 客户想法 is not None:
        参数["客户想法"] = 客户想法
        更新片段.append("客户想法 = :客户想法")
    if 跟进结果:
        当前备注 = 连接.execute(
            "SELECT 备注 FROM 销售机会 WHERE 线索编号 = ?",
            (线索编号,),
        ).fetchone()["备注"]
        参数["备注"] = f"{当前备注}\n[{时间}] {跟进结果}".strip()
        更新片段.append("备注 = :备注")

    连接.execute(
        f"UPDATE 销售机会 SET {', '.join(更新片段)} WHERE 线索编号 = :线索编号",
        参数,
    )
    连接.commit()
    return 查询机会详情(连接, 线索编号)


def _读取成功指标(连接: sqlite3.Connection, 线索编号: str) -> list[str]:
    结果 = 连接.execute(
        "SELECT 指标名称 FROM 成功指标 WHERE 线索编号 = ? ORDER BY 指标编号",
        (线索编号,),
    ).fetchall()
    return [row["指标名称"] for row in 结果]


def _读取跟进记录(连接: sqlite3.Connection, 线索编号: str) -> list[dict]:
    结果 = 连接.execute(
        """
        SELECT 记录时间, 沟通方式, 预约时间, 记录内容, 跟进结果
        FROM 跟进记录
        WHERE 线索编号 = ?
        ORDER BY 记录编号
        """,
        (线索编号,),
    ).fetchall()
    return [dict(row) for row in 结果]


def 查询机会详情(连接: sqlite3.Connection, 线索编号: str) -> dict | None:
    结果 = 连接.execute(
        "SELECT * FROM 销售机会 WHERE 线索编号 = ?",
        (线索编号,),
    ).fetchone()
    if not 结果:
        return None
    记录 = dict(结果)
    记录["成功指标"] = _读取成功指标(连接, 线索编号)
    记录["跟进记录"] = _读取跟进记录(连接, 线索编号)
    return 格式化展示记录(记录)


def 查询机会列表(
    连接: sqlite3.Connection,
    当前阶段: str | None = None,
    优先级: str | None = None,
    内部负责人: str | None = None,
    到期日期: str | None = None,
    截止日期: str | None = None,
    仅活跃: bool = False,
) -> list[dict]:
    条件 = []
    参数: list = []

    if 当前阶段:
        条件.append("当前阶段 = ?")
        参数.append(校验阶段(当前阶段))
    if 优先级:
        条件.append("优先级 = ?")
        参数.append(校验优先级(优先级))
    if 内部负责人:
        条件.append("内部负责人 = ?")
        参数.append(内部负责人)
    if 到期日期:
        条件.append("下一步日期 = ?")
        参数.append(校验日期(到期日期))
    if 截止日期:
        条件.append("下一步日期 <= ?")
        参数.append(校验日期(截止日期))
    if 仅活跃:
        占位符 = ", ".join("?" for _ in 活跃阶段)
        条件.append(f"当前阶段 IN ({占位符})")
        参数.extend(sorted(活跃阶段))

    查询语句 = "SELECT * FROM 销售机会"
    if 条件:
        查询语句 += " WHERE " + " AND ".join(条件)
    查询语句 += " ORDER BY 下一步日期 ASC, 更新时间 DESC"

    结果 = 连接.execute(查询语句, 参数).fetchall()
    列表 = []
    for row in 结果:
        记录 = dict(row)
        记录["成功指标"] = _读取成功指标(连接, 记录["线索编号"])
        列表.append(格式化展示记录(记录))
    return 列表


def 查询汇总(连接: sqlite3.Connection, 今日日期: str | None = None) -> dict:
    今日 = 今日日期 or datetime.now().strftime("%Y-%m-%d")
    活跃记录 = 查询机会列表(连接, 仅活跃=True)
    阶段计数 = Counter(记录["当前阶段"] for 记录 in 活跃记录)
    优先级计数 = Counter(记录["优先级"] for 记录 in 活跃记录)
    今日到期 = [记录 for 记录 in 活跃记录 if 记录.get("下一步日期") == 今日]
    已逾期 = [记录 for 记录 in 活跃记录 if 记录.get("下一步日期") and 记录["下一步日期"] < 今日]

    return {
        "活跃机会数": len(活跃记录),
        "阶段分布": {阶段名称(key): value for key, value in 阶段计数.items()},
        "优先级分布": dict(优先级计数),
        "今日到期数": len(今日到期),
        "已逾期数": len(已逾期),
    }


def 生成看板数据(
    连接: sqlite3.Connection,
    当前阶段: str | None = None,
    优先级: str | None = None,
) -> dict:
    今天 = datetime.now().strftime("%Y-%m-%d")
    客户列表 = 查询机会列表(连接, 当前阶段=当前阶段, 优先级=优先级, 仅活跃=False)
    活跃列表 = [记录 for 记录 in 客户列表 if 记录["当前阶段"] in 活跃阶段]
    今日到期 = [记录 for 记录 in 活跃列表 if 记录["下一步日期"] == 今天]
    已逾期 = [记录 for 记录 in 活跃列表 if 记录["下一步日期"] and 记录["下一步日期"] < 今天]
    A类 = [记录 for 记录 in 活跃列表 if 记录["优先级"] == "A"]
    试用推进 = [记录 for 记录 in 活跃列表 if 记录["当前阶段"] in {"trial", "trial-follow-up"}]
    报价合同 = [记录 for 记录 in 活跃列表 if 记录["当前阶段"] in {"quote", "contract"}]
    阶段分布 = []

    for 配置 in 阶段配置:
        if 配置["代码"] in {"closed-won", "closed-lost"}:
            continue
        阶段客户 = [记录 for 记录 in 活跃列表 if 记录["当前阶段"] == 配置["代码"]]
        阶段分布.append(
            {
                "阶段代码": 配置["代码"],
                "阶段名称": 配置["名称"],
                "阶段目标": 配置["目标"],
                "数量": len(阶段客户),
                "代表客户": 阶段客户[0]["客户名称"] if 阶段客户 else "",
            }
        )

    焦点机会 = {
        "A类": next((记录 for 记录 in 客户列表 if 记录["优先级"] == "A"), None),
        "B类": next((记录 for 记录 in 客户列表 if 记录["优先级"] == "B"), None),
        "C类": next((记录 for 记录 in 客户列表 if 记录["优先级"] == "C"), None),
    }

    堵点阶段 = max(阶段分布, key=lambda item: item["数量"], default=None)
    洞察 = [
        {
            "标题": "当前最大堵点",
            "内容": f"当前客户最集中的阶段是“{堵点阶段['阶段名称']}”，说明这个环节最值得优先拆 SOP。"
            if 堵点阶段 and 堵点阶段["数量"] > 0
            else "当前数据库里还没有足够数据来判断堵点。先录入一批真实线索更合适。",
        },
        {
            "标题": "今天建议先推进的机会",
            "列表": [记录["客户名称"] for 记录 in A类[:3]] or ["暂无 A 类机会，建议先补齐资格判断字段。"],
        },
        {
            "标题": "风险提醒",
            "列表": [f"{记录['客户名称']} 已逾期，建议优先跟进。" for 记录 in 已逾期[:3]] or ["当前没有逾期客户。"],
        },
    ]

    return {
        "生成时间": 当前时间(),
        "统计": {
            "活跃机会数": len(活跃列表),
            "今日到期数": len(今日到期),
            "已逾期数": len(已逾期),
            "A类机会数": len(A类),
            "试用推进数": len(试用推进),
            "报价合同数": len(报价合同),
        },
        "今日行动": _去重机会(已逾期 + 今日到期 + A类)[:5],
        "焦点机会": 焦点机会,
        "阶段分布": 阶段分布,
        "客户列表": 客户列表,
        "销售洞察": 洞察,
        "筛选项": {
            "阶段": [{"代码": item["代码"], "名称": item["名称"]} for item in 阶段配置 if item["代码"] not in {"closed-won", "closed-lost"}],
            "优先级": ["A", "B", "C"],
        },
    }


def _去重机会(机会列表: list[dict]) -> list[dict]:
    已见: set[str] = set()
    结果 = []
    for 记录 in 机会列表:
        编号 = 记录["线索编号"]
        if 编号 in 已见:
            continue
        已见.add(编号)
        结果.append(记录)
    return 结果


def 机会转简表(记录: dict) -> str:
    return (
        f"{记录['线索编号']} | 客户: {记录['客户名称']} | 联系人: {记录.get('联系人', '')} | "
        f"阶段: {阶段名称(记录.get('当前阶段'))} | 优先级: {记录.get('优先级', '')} | "
        f"下一步: {记录.get('下一步动作', '')} | 日期: {记录.get('下一步日期', '')} | "
        f"负责人: {记录.get('内部负责人', '')}"
    )


def 机会转JSON(记录: dict) -> str:
    return json.dumps(记录, ensure_ascii=False, indent=2)


def 格式化展示记录(记录: dict) -> dict:
    数据 = dict(记录)
    if 数据.get("决策人") == "unknown":
        数据["决策人"] = "未确认"
    elif 数据.get("决策人") == "self":
        数据["决策人"] = "当前联系人"
    数据["当前阶段名称"] = 阶段名称(数据.get("当前阶段"))
    return 数据
