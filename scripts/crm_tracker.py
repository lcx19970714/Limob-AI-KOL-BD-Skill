#!/usr/bin/env python3
"""SQLite-backed sales CRM command line tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sales_db import (
    DEFAULT_DB_PATH,
    机会转JSON,
    机会转简表,
    生成看板数据,
    连接数据库,
    查询机会列表,
    查询汇总,
    新增机会,
    更新机会,
    记录跟进,
)


def 添加通用字段(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--company")
    parser.add_argument("--contact-name")
    parser.add_argument("--role")
    parser.add_argument("--source")
    parser.add_argument("--category")
    parser.add_argument("--team-size", type=int)
    parser.add_argument("--current-collab-mode")
    parser.add_argument("--monthly-outreach", type=int)
    parser.add_argument("--decision-maker")
    parser.add_argument("--is-decision-maker")
    parser.add_argument("--stage")
    parser.add_argument("--grade")
    parser.add_argument("--pain-points")
    parser.add_argument("--last-summary")
    parser.add_argument("--customer-idea")
    parser.add_argument("--timeline-days", type=int)
    parser.add_argument("--success-metrics")
    parser.add_argument("--owner")
    parser.add_argument("--next-action")
    parser.add_argument("--next-action-date")
    parser.add_argument("--trialed")
    parser.add_argument("--trial-status")
    parser.add_argument("--trial-start-date")
    parser.add_argument("--trial-end-date")
    parser.add_argument("--quote-version")
    parser.add_argument("--buyer-entity")
    parser.add_argument("--notes")


def 设为必填(parser: argparse.ArgumentParser, 参数名列表: list[str]) -> None:
    必填集合 = set(参数名列表)
    for action in parser._actions:
        if any(option in 必填集合 for option in action.option_strings):
            action.required = True


def 构建解析器() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SQLite 版销售客户台账工具")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="新增一条销售机会")
    添加通用字段(add_parser)
    设为必填(add_parser, ["--company", "--source", "--stage", "--next-action", "--next-action-date"])

    update_parser = subparsers.add_parser("update", help="更新销售机会字段")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--auto-grade", action="store_true")
    添加通用字段(update_parser)

    touch_parser = subparsers.add_parser("touch", help="记录一次跟进")
    touch_parser.add_argument("--id", required=True)
    touch_parser.add_argument("--note", required=True)
    touch_parser.add_argument("--result")
    touch_parser.add_argument("--channel")
    touch_parser.add_argument("--meeting-at")
    touch_parser.add_argument("--stage")
    touch_parser.add_argument("--grade")
    touch_parser.add_argument("--next-action")
    touch_parser.add_argument("--next-action-date")
    touch_parser.add_argument("--last-summary")
    touch_parser.add_argument("--customer-idea")

    list_parser = subparsers.add_parser("list", help="查看客户列表")
    list_parser.add_argument("--stage")
    list_parser.add_argument("--grade")
    list_parser.add_argument("--owner")
    list_parser.add_argument("--due-on")
    list_parser.add_argument("--due-before")
    list_parser.add_argument("--active-only", action="store_true")
    list_parser.add_argument("--json", action="store_true")

    summary_parser = subparsers.add_parser("summary", help="查看汇总")
    summary_parser.add_argument("--today")
    summary_parser.add_argument("--json", action="store_true")

    dashboard_parser = subparsers.add_parser("dashboard-data", help="导出看板 API 数据")
    dashboard_parser.add_argument("--stage")
    dashboard_parser.add_argument("--grade")

    return parser


def 转换字段(args: argparse.Namespace) -> dict:
    return {
        "客户名称": args.company,
        "联系人": args.contact_name,
        "联系角色": args.role,
        "线索来源": args.source,
        "产品类目": args.category,
        "团队规模": args.team_size,
        "当前合作方式": args.current_collab_mode,
        "月建联量": args.monthly_outreach,
        "决策人": args.decision_maker,
        "是否决策人": args.is_decision_maker,
        "当前阶段": args.stage,
        "优先级": args.grade,
        "核心痛点": args.pain_points,
        "上次沟通摘要": args.last_summary,
        "客户想法": args.customer_idea,
        "预计推进天数": args.timeline_days,
        "成功指标": args.success_metrics,
        "内部负责人": args.owner,
        "下一步动作": args.next_action,
        "下一步日期": args.next_action_date,
        "是否已试用": args.trialed,
        "试用状态": args.trial_status,
        "试用开始日期": args.trial_start_date,
        "试用结束日期": args.trial_end_date,
        "报价版本": args.quote_version,
        "采购主体": args.buyer_entity,
        "备注": args.notes,
    }


def main() -> None:
    parser = 构建解析器()
    args = parser.parse_args()
    db_path = Path(args.db)

    with 连接数据库(db_path) as conn:
        if args.command == "add":
            记录 = 新增机会(conn, 转换字段(args))
            print(机会转JSON(记录))
            return

        if args.command == "update":
            记录 = 更新机会(conn, args.id, 转换字段(args), 自动推断优先级=args.auto_grade)
            print(机会转JSON(记录))
            return

        if args.command == "touch":
            记录 = 记录跟进(
                conn,
                args.id,
                记录内容=args.note,
                跟进结果=args.result or "",
                沟通方式=args.channel or "",
                预约时间=args.meeting_at or "",
                当前阶段=args.stage,
                优先级=args.grade,
                下一步动作=args.next_action,
                下一步日期=args.next_action_date,
                上次沟通摘要=args.last_summary,
                客户想法=args.customer_idea,
            )
            print(机会转JSON(记录))
            return

        if args.command == "list":
            记录列表 = 查询机会列表(
                conn,
                当前阶段=args.stage,
                优先级=args.grade,
                内部负责人=args.owner,
                到期日期=args.due_on,
                截止日期=args.due_before,
                仅活跃=args.active_only,
            )
            if args.json:
                print(json.dumps(记录列表, ensure_ascii=False, indent=2))
                return
            for 记录 in 记录列表:
                print(机会转简表(记录))
            print(f"合计 {len(记录列表)} 条")
            return

        if args.command == "summary":
            汇总 = 查询汇总(conn, 今日日期=args.today)
            if args.json:
                print(json.dumps(汇总, ensure_ascii=False, indent=2))
                return
            print(f"在跟进机会: {汇总['活跃机会数']}")
            print(f"阶段分布: {json.dumps(汇总['阶段分布'], ensure_ascii=False)}")
            print(f"优先级分布: {json.dumps(汇总['优先级分布'], ensure_ascii=False)}")
            print(f"今日到期: {汇总['今日到期数']}")
            print(f"已逾期: {汇总['已逾期数']}")
            return

        if args.command == "dashboard-data":
            数据 = 生成看板数据(conn, 当前阶段=args.stage, 优先级=args.grade)
            print(json.dumps(数据, ensure_ascii=False, indent=2))
            return

    raise ValueError(f"不支持的命令: {args.command}")


if __name__ == "__main__":
    main()
