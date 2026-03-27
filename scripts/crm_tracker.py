#!/usr/bin/env python3
"""销售系统命令行工具（完整 CRUD）。"""

from __future__ import annotations

import argparse
import json
from datetime import date
from getpass import getpass
from typing import Any

from skill_api import 销售系统接口客户端
from skill_config import write_long_term_token as 写入长效令牌
from 日期工具 import 标准化参数日期字段

机会字段列表 = [
    "客户名称",
    "联系人姓名",
    "联系角色",
    "线索来源",
    "产品类目",
    "团队规模",
    "当前合作方式",
    "月建联量",
    "决策关系说明",
    "是否决策人",
    "当前阶段",
    "优先级",
    "核心痛点",
    "上次沟通摘要",
    "客户想法",
    "预计推进天数",
    "内部负责人",
    "下一步动作",
    "下一步日期",
    "是否已试用",
    "试用状态",
    "试用开始日期",
    "试用结束日期",
    "报价版本",
    "采购主体",
    "备注",
]

客户字段列表 = ["客户名称", "产品类目", "团队规模", "当前合作方式", "月建联量", "采购主体"]
联系人字段列表 = ["客户编号", "联系人姓名", "联系角色", "是否决策人", "决策关系说明"]

机会列表查询字段 = [
    "搜索关键词",
    "当前阶段",
    "优先级",
    "内部负责人",
    "下一步日期",
    "下一步日期截止前",
    "仅看活跃",
    "排序字段",
    "排序方向",
    "页码",
    "每页数量",
]
客户列表查询字段 = ["搜索关键词", "产品类目", "排序字段", "排序方向", "页码", "每页数量"]
联系人列表查询字段 = ["搜索关键词", "客户编号", "联系角色", "是否决策人", "排序字段", "排序方向", "页码", "每页数量"]


def 添加机会字段(参数解析器: argparse.ArgumentParser) -> None:
    参数解析器.add_argument("--客户名称")
    参数解析器.add_argument("--联系人姓名")
    参数解析器.add_argument("--联系角色")
    参数解析器.add_argument("--线索来源")
    参数解析器.add_argument("--产品类目")
    参数解析器.add_argument("--团队规模", type=int)
    参数解析器.add_argument("--当前合作方式")
    参数解析器.add_argument("--月建联量", type=int)
    参数解析器.add_argument("--决策关系说明")
    参数解析器.add_argument("--是否决策人")
    参数解析器.add_argument("--当前阶段")
    参数解析器.add_argument("--优先级")
    参数解析器.add_argument("--核心痛点")
    参数解析器.add_argument("--上次沟通摘要")
    参数解析器.add_argument("--客户想法")
    参数解析器.add_argument("--预计推进天数", type=int)
    参数解析器.add_argument("--内部负责人")
    参数解析器.add_argument("--下一步动作")
    参数解析器.add_argument("--下一步日期", help="支持：2026-03-27 / 2026/03/27 / 20260327 / 今天 / tomorrow")
    参数解析器.add_argument("--是否已试用")
    参数解析器.add_argument("--试用状态")
    参数解析器.add_argument("--试用开始日期", help="支持多种日期格式")
    参数解析器.add_argument("--试用结束日期", help="支持多种日期格式")
    参数解析器.add_argument("--报价版本")
    参数解析器.add_argument("--采购主体")
    参数解析器.add_argument("--备注")


def 添加客户字段(参数解析器: argparse.ArgumentParser) -> None:
    参数解析器.add_argument("--客户名称")
    参数解析器.add_argument("--产品类目")
    参数解析器.add_argument("--团队规模", type=int)
    参数解析器.add_argument("--当前合作方式")
    参数解析器.add_argument("--月建联量", type=int)
    参数解析器.add_argument("--采购主体")


def 添加联系人字段(参数解析器: argparse.ArgumentParser) -> None:
    参数解析器.add_argument("--客户编号")
    参数解析器.add_argument("--联系人姓名")
    参数解析器.add_argument("--联系角色")
    参数解析器.add_argument("--是否决策人")
    参数解析器.add_argument("--决策关系说明")


def 构建参数解析器() -> argparse.ArgumentParser:
    参数解析器 = argparse.ArgumentParser(description="销售系统命令行工具")
    参数解析器.set_defaults(今日=None, 输出JSON=False)
    子命令解析器 = 参数解析器.add_subparsers(dest="命令", required=False)

    设置令牌解析器 = 子命令解析器.add_parser("设置令牌", help="写入 long_term_token 到 config.json")
    设置令牌解析器.add_argument("long_term_token", nargs="?", help="可选：长效令牌；不传则交互输入")

    机会新增解析器 = 子命令解析器.add_parser("机会新增", aliases=["新增"], help="新增合作机会")
    添加机会字段(机会新增解析器)
    for 必填参数 in ["--客户名称", "--线索来源", "--当前阶段", "--下一步动作", "--下一步日期"]:
        for 动作 in 机会新增解析器._actions:
            if 必填参数 in 动作.option_strings:
                动作.required = True

    机会更新解析器 = 子命令解析器.add_parser("机会更新", aliases=["更新"], help="更新合作机会")
    机会更新解析器.add_argument("--机会编号", required=True)
    机会更新解析器.add_argument("--自动评级", action="store_true")
    添加机会字段(机会更新解析器)

    机会删除解析器 = 子命令解析器.add_parser("机会删除", help="删除合作机会")
    机会删除解析器.add_argument("--机会编号", required=True)

    机会跟进解析器 = 子命令解析器.add_parser("机会跟进", aliases=["跟进"], help="记录合作机会跟进")
    机会跟进解析器.add_argument("--机会编号", required=True)
    机会跟进解析器.add_argument("--记录内容", required=True)
    机会跟进解析器.add_argument("--跟进结果")
    机会跟进解析器.add_argument("--沟通方式")
    机会跟进解析器.add_argument("--预约时间", help="支持：2026-03-27 15:30 / 2026/03/27 15:30 / 今天 15:30")
    机会跟进解析器.add_argument("--当前阶段")
    机会跟进解析器.add_argument("--优先级")
    机会跟进解析器.add_argument("--下一步动作")
    机会跟进解析器.add_argument("--下一步日期", help="支持多种日期格式")
    机会跟进解析器.add_argument("--上次沟通摘要")
    机会跟进解析器.add_argument("--客户想法")

    机会列表解析器 = 子命令解析器.add_parser("机会列表", aliases=["列表"], help="查看合作机会列表")
    机会列表解析器.add_argument("--搜索关键词")
    机会列表解析器.add_argument("--当前阶段")
    机会列表解析器.add_argument("--优先级")
    机会列表解析器.add_argument("--内部负责人")
    机会列表解析器.add_argument("--下一步日期", help="支持多种日期格式")
    机会列表解析器.add_argument("--下一步日期截止前", help="支持多种日期格式")
    机会列表解析器.add_argument("--仅看活跃", action="store_true")
    机会列表解析器.add_argument("--排序字段", default="下一步日期")
    机会列表解析器.add_argument("--排序方向", default="升序")
    机会列表解析器.add_argument("--页码", type=int, default=1)
    机会列表解析器.add_argument("--每页数量", type=int, default=20)
    机会列表解析器.add_argument("--输出JSON", action="store_true")

    机会详情解析器 = 子命令解析器.add_parser("机会详情", aliases=["详情"], help="查看合作机会详情")
    机会详情解析器.add_argument("--机会编号", required=True)

    客户新增解析器 = 子命令解析器.add_parser("客户新增", help="新增客户")
    添加客户字段(客户新增解析器)
    for 动作 in 客户新增解析器._actions:
        if "--客户名称" in 动作.option_strings:
            动作.required = True

    客户更新解析器 = 子命令解析器.add_parser("客户更新", help="更新客户")
    客户更新解析器.add_argument("--客户编号", required=True)
    添加客户字段(客户更新解析器)

    客户删除解析器 = 子命令解析器.add_parser("客户删除", help="删除客户")
    客户删除解析器.add_argument("--客户编号", required=True)

    客户详情解析器 = 子命令解析器.add_parser("客户详情", help="查看客户详情")
    客户详情解析器.add_argument("--客户编号", required=True)

    客户列表解析器 = 子命令解析器.add_parser("客户列表", help="查看客户列表")
    客户列表解析器.add_argument("--搜索关键词")
    客户列表解析器.add_argument("--产品类目")
    客户列表解析器.add_argument("--排序字段", default="更新时间")
    客户列表解析器.add_argument("--排序方向", default="降序")
    客户列表解析器.add_argument("--页码", type=int, default=1)
    客户列表解析器.add_argument("--每页数量", type=int, default=20)
    客户列表解析器.add_argument("--输出JSON", action="store_true")

    联系人新增解析器 = 子命令解析器.add_parser("联系人新增", help="新增联系人")
    添加联系人字段(联系人新增解析器)
    for 必填参数 in ["--客户编号", "--联系人姓名"]:
        for 动作 in 联系人新增解析器._actions:
            if 必填参数 in 动作.option_strings:
                动作.required = True

    联系人更新解析器 = 子命令解析器.add_parser("联系人更新", help="更新联系人")
    联系人更新解析器.add_argument("--联系人编号", required=True, type=int)
    添加联系人字段(联系人更新解析器)

    联系人删除解析器 = 子命令解析器.add_parser("联系人删除", help="删除联系人")
    联系人删除解析器.add_argument("--联系人编号", required=True, type=int)

    联系人详情解析器 = 子命令解析器.add_parser("联系人详情", help="查看联系人详情")
    联系人详情解析器.add_argument("--联系人编号", required=True, type=int)

    联系人列表解析器 = 子命令解析器.add_parser("联系人列表", help="查看联系人列表")
    联系人列表解析器.add_argument("--搜索关键词")
    联系人列表解析器.add_argument("--客户编号")
    联系人列表解析器.add_argument("--联系角色")
    联系人列表解析器.add_argument("--是否决策人")
    联系人列表解析器.add_argument("--排序字段", default="更新时间")
    联系人列表解析器.add_argument("--排序方向", default="降序")
    联系人列表解析器.add_argument("--页码", type=int, default=1)
    联系人列表解析器.add_argument("--每页数量", type=int, default=20)
    联系人列表解析器.add_argument("--输出JSON", action="store_true")

    汇总解析器 = 子命令解析器.add_parser("汇总", aliases=["工作台"], help="查看销售工作台汇总")
    汇总解析器.add_argument("--今日", help="支持多种日期格式；不传默认今天")
    汇总解析器.add_argument("--输出JSON", action="store_true")

    看板解析器 = 子命令解析器.add_parser("看板", help="查看销售看板")
    看板解析器.add_argument("--当前阶段")
    看板解析器.add_argument("--优先级")
    看板解析器.add_argument("--输出JSON", action="store_true")

    return 参数解析器


def 构建请求体(参数: argparse.Namespace, 字段列表: list[str]) -> dict[str, Any]:
    return {字段: getattr(参数, 字段, None) for 字段 in 字段列表}


def 生成机会简要行(记录: dict[str, Any]) -> str:
    return (
        f"{记录.get('机会编号', '')} | {记录.get('客户名称', '')} | "
        f"{记录.get('当前阶段名称') or 记录.get('当前阶段', '')} | "
        f"{记录.get('优先级', '')} | {记录.get('下一步动作', '')} | {记录.get('下一步日期', '')}"
    )


def 生成客户简要行(记录: dict[str, Any]) -> str:
    return (
        f"{记录.get('客户编号', '')} | {记录.get('客户名称', '')} | "
        f"{记录.get('产品类目', '')} | 联系人 {记录.get('联系人数量', 0)} | "
        f"活跃机会 {记录.get('活跃合作机会数量', 0)}"
    )


def 生成联系人简要行(记录: dict[str, Any]) -> str:
    决策标签 = "决策人" if str(记录.get("是否决策人", "")) == "1" else "普通联系人"
    return (
        f"{记录.get('联系人编号', '')} | {记录.get('联系人姓名', '')} | "
        f"{记录.get('客户名称', '')} | {记录.get('联系角色', '')} | {决策标签}"
    )


def 输出分页结果(查询结果: dict[str, Any], 行生成器) -> None:
    for 记录 in 查询结果.get("列表", []):
        print(行生成器(记录))
    print(
        f"第 {查询结果.get('页码', 1)} 页 / 共 {查询结果.get('总页数', 1)} 页 / "
        f"合计 {查询结果.get('总数', 0)} 条"
    )


def 获取并校验令牌(参数令牌: str | None) -> str:
    if 参数令牌 and 参数令牌.strip():
        return 参数令牌.strip()
    输入令牌 = getpass("请输入 long_term_token（输入过程不回显）：").strip()
    if not 输入令牌:
        raise ValueError("long_term_token 不能为空")
    return 输入令牌


def 执行汇总命令(客户端: 销售系统接口客户端, 参数: argparse.Namespace) -> None:
    今日参数 = getattr(参数, "今日", None) or date.today().isoformat()
    汇总数据 = 客户端.查询销售汇总(今日=今日参数)
    if getattr(参数, "输出JSON", False):
        print(json.dumps(汇总数据, ensure_ascii=False, indent=2))
        return
    print(f"统计日期: {今日参数}")
    print(f"在跟进合作机会: {汇总数据['活跃合作机会数']}")
    print(f"阶段分布: {json.dumps(汇总数据['阶段分布统计'], ensure_ascii=False)}")
    print(f"优先级分布: {json.dumps(汇总数据['优先级分布统计'], ensure_ascii=False)}")
    print(f"今日到期: {汇总数据['今日到期数']}")
    print(f"已逾期: {汇总数据['逾期数']}")


def 主程序() -> None:
    参数解析器 = 构建参数解析器()
    参数 = 参数解析器.parse_args()

    try:
        标准化参数日期字段(参数)
    except ValueError as 异常:
        raise SystemExit(str(异常)) from 异常

    if 参数.命令 == "设置令牌":
        try:
            令牌 = 获取并校验令牌(参数.long_term_token)
        except ValueError as 异常:
            raise SystemExit(str(异常)) from 异常
        写入长效令牌(令牌)
        print("long_term_token 已写入 config.json")
        return

    try:
        客户端 = 销售系统接口客户端()

        if 参数.命令 in {"机会新增", "新增"}:
            print(json.dumps(客户端.创建合作机会(构建请求体(参数, 机会字段列表)), ensure_ascii=False, indent=2))
            return

        if 参数.命令 in {"机会更新", "更新"}:
            请求体 = 构建请求体(参数, 机会字段列表)
            if 参数.自动评级:
                请求体["自动评级"] = True
            print(json.dumps(客户端.更新合作机会(参数.机会编号, 请求体), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "机会删除":
            print(json.dumps(客户端.删除合作机会(参数.机会编号), ensure_ascii=False, indent=2))
            return

        if 参数.命令 in {"机会跟进", "跟进"}:
            跟进字段 = ["记录内容", "跟进结果", "沟通方式", "预约时间", "当前阶段", "优先级", "下一步动作", "下一步日期", "上次沟通摘要", "客户想法"]
            print(json.dumps(客户端.新增跟进记录(参数.机会编号, 构建请求体(参数, 跟进字段)), ensure_ascii=False, indent=2))
            return

        if 参数.命令 in {"机会列表", "列表"}:
            查询结果 = 客户端.查询合作机会列表(构建请求体(参数, 机会列表查询字段))
            if 参数.输出JSON:
                print(json.dumps(查询结果, ensure_ascii=False, indent=2))
                return
            输出分页结果(查询结果, 生成机会简要行)
            return

        if 参数.命令 in {"机会详情", "详情"}:
            print(json.dumps(客户端.查询合作机会详情(参数.机会编号), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "客户新增":
            print(json.dumps(客户端.创建客户(构建请求体(参数, 客户字段列表)), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "客户更新":
            print(json.dumps(客户端.更新客户(参数.客户编号, 构建请求体(参数, 客户字段列表)), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "客户删除":
            print(json.dumps(客户端.删除客户(参数.客户编号), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "客户详情":
            print(json.dumps(客户端.查询客户详情(参数.客户编号), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "客户列表":
            查询结果 = 客户端.查询客户列表(构建请求体(参数, 客户列表查询字段))
            if 参数.输出JSON:
                print(json.dumps(查询结果, ensure_ascii=False, indent=2))
                return
            输出分页结果(查询结果, 生成客户简要行)
            return

        if 参数.命令 == "联系人新增":
            print(json.dumps(客户端.创建联系人(构建请求体(参数, 联系人字段列表)), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "联系人更新":
            print(json.dumps(客户端.更新联系人(参数.联系人编号, 构建请求体(参数, 联系人字段列表)), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "联系人删除":
            print(json.dumps(客户端.删除联系人(参数.联系人编号), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "联系人详情":
            print(json.dumps(客户端.查询联系人详情(参数.联系人编号), ensure_ascii=False, indent=2))
            return

        if 参数.命令 == "联系人列表":
            查询结果 = 客户端.查询联系人列表(构建请求体(参数, 联系人列表查询字段))
            if 参数.输出JSON:
                print(json.dumps(查询结果, ensure_ascii=False, indent=2))
                return
            输出分页结果(查询结果, 生成联系人简要行)
            return

        if 参数.命令 in {"汇总", "工作台", None}:
            执行汇总命令(客户端, 参数)
            return

        if 参数.命令 == "看板":
            看板数据 = 客户端.查询销售看板(当前阶段=getattr(参数, "当前阶段", None), 优先级=getattr(参数, "优先级", None))
            print(json.dumps(看板数据, ensure_ascii=False, indent=2))
            return
    except RuntimeError as 异常:
        raise SystemExit(str(异常)) from 异常

    raise SystemExit(f"不支持的命令：{参数.命令}")


if __name__ == "__main__":
    主程序()
