#!/usr/bin/env python3
"""销售系统后端接口客户端。"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from skill_config import 加载技能配置


class 销售系统接口客户端:
    def __init__(self, long_term_token: str | None = None) -> None:
        配置 = 加载技能配置()
        self.base_url = str(配置["resolved_base_url"]).rstrip("/")
        self.timeout = float(配置.get("timeout_seconds", 20))
        self.long_term_token = str(long_term_token or 配置.get("long_term_token") or "")

    def _构建请求头(self) -> dict[str, str]:
        请求头 = {"Content-Type": "application/json"}
        if self.long_term_token:
            请求头["Authorization"] = f"Bearer {self.long_term_token}"
        return 请求头

    def _发送请求(
        self,
        路径: str,
        *,
        请求体: dict[str, Any] | None = None,
        方法: str = "POST",
    ) -> dict[str, Any]:
        if not self.long_term_token:
            raise RuntimeError("未配置 long_term_token，请先让用户提供长效令牌并写入 config.json")

        请求地址 = f"{self.base_url}{路径}"
        请求数据 = None
        if 请求体 is not None:
            请求数据 = json.dumps({k: v for k, v in 请求体.items() if v is not None}, ensure_ascii=False).encode("utf-8")

        请求对象 = urllib.request.Request(
            url=请求地址,
            data=请求数据,
            headers=self._构建请求头(),
            method=方法,
        )

        try:
            with urllib.request.urlopen(请求对象, timeout=self.timeout) as 响应:
                结果 = json.loads(响应.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            响应文本 = exc.read().decode("utf-8", errors="ignore")
            try:
                结果 = json.loads(响应文本)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"后端请求失败: HTTP {exc.code}，响应={响应文本[:300]}") from error

        if 结果.get("status") != 100:
            状态码 = 结果.get("status")
            消息 = str(结果.get("message") or "后端请求失败")
            详情 = 结果.get("data")
            if 详情 not in (None, "", [], {}):
                raise RuntimeError(f"{消息}（status={状态码}，data={json.dumps(详情, ensure_ascii=False)}）")
            raise RuntimeError(f"{消息}（status={状态码}）")
        return 结果.get("data", {})

    def 查询当前团队(self) -> dict[str, Any]:
        """验证长效令牌，并确认其绑定的团队仍存在。"""
        return self._发送请求("/user/current-team", 方法="GET")

    def 查询销售线索列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads/query", 请求体=请求体)

    def 创建销售线索(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads", 请求体=请求体)

    def 导入微信好友为销售线索(self, 微信好友表id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads/import-wechat-friend", 请求体={"微信好友表id": 微信好友表id})

    def 转化销售线索(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads/convert", 请求体=请求体)

    def 排除销售线索(self, 线索id: int, 排除原因: str | None = None) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads/exclude", 请求体={"线索id": 线索id, "排除原因": 排除原因})

    def 批量排除销售线索(self, 线索id列表: list[int], 排除原因: str | None = None) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads/batch-exclude", 请求体={"线索id列表": 线索id列表, "排除原因": 排除原因})

    def 删除销售线索(self, 线索id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/leads/delete", 请求体={"线索id": 线索id})

    def 创建合作机会(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities", 请求体=请求体)

    def 更新合作机会(self, 合作机会id: int, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/update", 请求体={"合作机会id": 合作机会id, **请求体})

    def 删除合作机会(self, 合作机会id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/delete", 请求体={"合作机会id": 合作机会id})

    def 新增跟进记录(self, 合作机会id: int, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/touch", 请求体={"合作机会id": 合作机会id, **请求体})

    def 查询合作机会列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/query", 请求体=请求体)

    def 查询合作机会详情(self, 合作机会id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/detail", 请求体={"合作机会id": 合作机会id})

    def 创建客户(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/customers", 请求体=请求体)

    def 更新客户(self, 客户id: int, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/customers/update", 请求体={"客户id": 客户id, **请求体})

    def 删除客户(self, 客户id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/customers/delete", 请求体={"客户id": 客户id})

    def 查询客户列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/customers/query", 请求体=请求体)

    def 查询客户详情(self, 客户id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/customers/detail", 请求体={"客户id": 客户id})

    def 创建联系人(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts", 请求体=请求体)

    def 记录销售联系人(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/record", 请求体=请求体)

    def 补充联系人联系方式(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/contact-method", 请求体=请求体)

    def 删除联系人联系方式(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/contact-method/delete", 请求体=请求体)

    def 更新联系人(self, 联系人id: int, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/update", 请求体={"联系人id": 联系人id, **请求体})

    def 删除联系人(self, 联系人id: int) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/delete", 请求体={"联系人id": 联系人id})

    def 查询联系人列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/query", 请求体=请求体)

    def 查询联系人详情(self, 联系人uuid: str) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/detail", 请求体={"联系人uuid": 联系人uuid})

    def 查询销售汇总(self, *, 今日: str | None = None) -> dict[str, Any]:
        return self._发送请求("/sales-system/summary", 请求体={"今日": 今日})

    def 查询销售看板(self, *, 当前阶段: str | None = None, 优先级: str | None = None) -> dict[str, Any]:
        return self._发送请求("/sales-system/dashboard", 请求体={"当前阶段": 当前阶段, "优先级": 优先级})



