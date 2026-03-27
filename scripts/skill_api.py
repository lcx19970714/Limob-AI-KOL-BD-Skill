#!/usr/bin/env python3
"""Thin backend client for the sales system."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from skill_config import load_skill_config


class 销售系统接口客户端:
    def __init__(self) -> None:
        self.config = load_skill_config()
        self.base_url = self.config["resolved_base_url"]
        self.timeout = float(self.config.get("timeout_seconds", 20))
        self.long_term_token = str(self.config.get("long_term_token") or "")

    def _构建请求头(self) -> dict[str, str]:
        请求头 = {"Content-Type": "application/json"}
        if self.long_term_token:
            请求头["Authorization"] = f"Bearer {self.long_term_token}"
        return 请求头

    def _发送请求(self, 路径: str, *, 请求体: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.long_term_token:
            raise RuntimeError("未配置 long_term_token，请先让用户提供长效令牌并写入 config.json")

        请求地址 = f"{self.base_url}{路径}"
        请求数据 = None
        if 请求体 is not None:
            请求体数据 = {key: value for key, value in 请求体.items() if value is not None}
            请求数据 = json.dumps(请求体数据, ensure_ascii=False).encode("utf-8")

        请求对象 = urllib.request.Request(
            url=请求地址,
            data=请求数据,
            headers=self._构建请求头(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(请求对象, timeout=self.timeout) as 响应:
                解析结果 = json.loads(响应.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            响应文本 = exc.read().decode("utf-8", errors="ignore")
            try:
                解析结果 = json.loads(响应文本)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"后端请求失败: HTTP {exc.code}") from error

        if 解析结果.get("status") != 100:
            raise RuntimeError(解析结果.get("message") or "后端请求失败")
        return 解析结果.get("data", {})

    def 创建合作机会(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities", 请求体=请求体)

    def 更新合作机会(self, 机会编号: str, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/update", 请求体={"机会编号": 机会编号, **请求体})

    def 新增跟进记录(self, 机会编号: str, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/touch", 请求体={"机会编号": 机会编号, **请求体})

    def 查询合作机会列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/query", 请求体=请求体)

    def 查询合作机会详情(self, 机会编号: str) -> dict[str, Any]:
        return self._发送请求("/sales-system/opportunities/detail", 请求体={"机会编号": 机会编号})

    def 查询客户列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/customers/query", 请求体=请求体)

    def 查询联系人列表(self, 请求体: dict[str, Any]) -> dict[str, Any]:
        return self._发送请求("/sales-system/contacts/query", 请求体=请求体)

    def 查询销售汇总(self, *, 今日: str | None = None) -> dict[str, Any]:
        return self._发送请求("/sales-system/summary", 请求体={"今日": 今日})
