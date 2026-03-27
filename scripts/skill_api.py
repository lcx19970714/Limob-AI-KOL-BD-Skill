#!/usr/bin/env python3
"""Thin backend client for the sales system."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from skill_config import load_skill_config, save_skill_config


class 销售系统接口客户端:
    def __init__(self) -> None:
        self.config = load_skill_config()
        self.base_url = self.config["resolved_base_url"]
        self.timeout = float(self.config.get("timeout_seconds", 20))
        self.long_term_token = str(self.config.get("long_term_token") or "")

    def _构建请求头(self, 访问令牌: str | None = None) -> dict[str, str]:
        请求头 = {"Content-Type": "application/json"}
        if 访问令牌:
            请求头["Authorization"] = f"Bearer {访问令牌}"
        return 请求头

    def _发送原始请求(
        self,
        路径: str,
        *,
        请求体: dict[str, Any] | None = None,
        访问令牌: str | None = None,
    ) -> dict[str, Any]:
        请求地址 = f"{self.base_url}{路径}"
        请求数据 = None
        if 请求体 is not None:
            请求体数据 = {key: value for key, value in 请求体.items() if value is not None}
            请求数据 = json.dumps(请求体数据, ensure_ascii=False).encode("utf-8")

        请求对象 = urllib.request.Request(
            url=请求地址,
            data=请求数据,
            headers=self._构建请求头(访问令牌),
            method="POST",
        )

        try:
            with urllib.request.urlopen(请求对象, timeout=self.timeout) as 响应:
                return json.loads(响应.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            响应文本 = exc.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(响应文本)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"后端请求失败: HTTP {exc.code}") from error

    def _发送请求(self, 路径: str, *, 请求体: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.long_term_token:
            self._自动准备长效令牌()

        解析结果 = self._发送原始请求(路径, 请求体=请求体, 访问令牌=self.long_term_token)
        if 解析结果.get("status") != 100 and self._可以自动重登():
            self.config["long_term_token"] = ""
            self.long_term_token = ""
            self._自动准备长效令牌()
            解析结果 = self._发送原始请求(路径, 请求体=请求体, 访问令牌=self.long_term_token)

        if 解析结果.get("status") != 100:
            raise RuntimeError(解析结果.get("message") or "后端请求失败")
        return 解析结果.get("data", {})

    def _可以自动重登(self) -> bool:
        手机号 = str(self.config.get("phone") or "").strip()
        密码 = str(self.config.get("password") or "")
        return bool(手机号 and 密码)

    def _自动准备长效令牌(self) -> None:
        已有令牌 = str(self.config.get("long_term_token") or "")
        if 已有令牌:
            self.long_term_token = 已有令牌
            return

        手机号 = str(self.config.get("phone") or "").strip()
        密码 = str(self.config.get("password") or "")
        if not 手机号 or not 密码:
            raise RuntimeError("未配置 long_term_token，且未提供 phone/password，无法自动登录销售系统")

        登录结果 = self._发送原始请求("/user/login", 请求体={"手机号": 手机号, "密码": 密码})
        if 登录结果.get("status") != 100:
            raise RuntimeError(登录结果.get("message") or "登录失败")

        登录数据 = 登录结果.get("data") or {}
        访问令牌 = str(登录数据.get("access_token") or "")
        if not 访问令牌:
            raise RuntimeError("登录成功但未获取到 access_token")

        if 登录数据.get("需要选择团队"):
            访问令牌 = self._切换团队并获取访问令牌(登录数据)

        长效令牌结果 = self._发送原始请求(
            "/user/long-term-token/generate",
            访问令牌=访问令牌,
        )
        if 长效令牌结果.get("status") != 100:
            raise RuntimeError(长效令牌结果.get("message") or "生成长效令牌失败")

        长效令牌数据 = 长效令牌结果.get("data") or {}
        长效令牌 = str(长效令牌数据.get("长效令牌") or "")
        if not 长效令牌:
            raise RuntimeError("长效令牌接口返回成功，但未返回长效令牌")

        self.long_term_token = 长效令牌
        self.config["long_term_token"] = 长效令牌
        save_skill_config(self.config)

    def _切换团队并获取访问令牌(self, 登录数据: dict[str, Any]) -> str:
        用户id = 登录数据.get("用户id")
        可选团队列表 = 登录数据.get("可选团队列表") or []
        配置团队id = self.config.get("user_team_id")

        目标用户团队id = 配置团队id
        if not 目标用户团队id:
            if len(可选团队列表) == 1:
                目标用户团队id = 可选团队列表[0].get("用户团队id")
            else:
                raise RuntimeError("当前账号存在多个团队，请在 config.json 中设置 user_team_id")

        切换结果 = self._发送原始请求(
            "/user/switch-team",
            请求体={"用户id": 用户id, "用户团队id": 目标用户团队id},
        )
        if 切换结果.get("status") != 100:
            raise RuntimeError(切换结果.get("message") or "切换团队失败")

        切换数据 = 切换结果.get("data") or {}
        新访问令牌 = str(切换数据.get("access_token") or "")
        if not 新访问令牌:
            raise RuntimeError("切换团队成功但未获取到 access_token")
        return 新访问令牌

    def 登录并刷新长效令牌(self) -> dict[str, Any]:
        self.config["long_term_token"] = ""
        self.long_term_token = ""
        self._自动准备长效令牌()
        return {"long_term_token": self.long_term_token}

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
