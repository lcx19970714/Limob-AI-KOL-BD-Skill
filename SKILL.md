---
name: limob-ai-kol-bd-skill
description: 销售系统数据库操作技能（客户/联系人/合作机会/跟进记录的增删改查）。
---

# 销售系统数据库操作技能

本技能只负责调用后端接口执行 CRM 数据操作，不包含销售 SOP、销售话术、销售策略判断。

## 能力范围

1. 客户：新增、更新、删除、详情、列表（支持搜索/筛选/排序/分页）
2. 联系人：新增、更新、删除、详情、列表（支持搜索/筛选/排序/分页）
3. 合作机会：新增、更新、删除、详情、列表（支持搜索/筛选/排序/分页）
4. 跟进记录：新增（通过 `机会跟进` 写入）
5. 汇总与看板：`汇总` / `看板`

## 首次授权（唯一方案）

1. 从 `config.json` 读取 `long_term_token`。
2. 若为空，向用户索取 `long_term_token`。
3. 将 token 写回 `config.json` 后继续执行。

硬约束：

- 不要索取手机号和密码。
- 不要内置登录流程。
- 只存储 `long_term_token`，不存储账号密码。

## 调用契约（唯一路径）

1. 统一通过 `scripts/crm_tracker.py` -> `scripts/skill_api.py` 调后端。
2. 所有接口统一 POST，参数统一放请求体。
3. 请求字段统一用中文，且与后端模型同名。
4. 所有主键统一小写：`客户id`、`联系人id`、`合作机会id`（int）。
5. `date` 字段统一 `YYYY-MM-DD`；`datetime` 字段统一 `YYYY-MM-DD HH:MM:SS`。
6. 禁止兼容兜底写法：`{"$date": ...}`、时间戳绕过、给 `date` 传带时间字符串。
7. 合作机会必须通过 `客户id` + `联系人id` 关联，禁止在机会接口里手填客户名称/联系人姓名建档。
8. 新增前先查重：优先调用 `客户列表` / `联系人列表` / `机会列表`，命中即更新，不重复建档。
9. 后端报错必须原样回传 `message`，禁止主观猜测“缺字段”或“后端 bug”。
10. `团队规模` 不是必填，未知时留空，不要用 `0` 占位。

## 脚本命令

```bash
python scripts/crm_tracker.py 设置令牌

python scripts/crm_tracker.py 机会新增 --客户id 1 --联系人id 1001 --线索来源 "主动咨询" --当前阶段 "资格判断" --下一步动作 "预约需求沟通" --下一步日期 2026-03-29
python scripts/crm_tracker.py 机会更新 --合作机会id 5001 --联系人id 1001 --预计推进天数 14 --优先级 A
python scripts/crm_tracker.py 机会跟进 --合作机会id 5001 --记录内容 "客户担心RPA封号，提出网页端自动采集垂类达人" --下一步动作 "给出半自动方案并安排演示" --下一步日期 2026-03-28
python scripts/crm_tracker.py 机会列表 --当前阶段 "产品演示" --排序字段 下一步日期 --排序方向 升序
python scripts/crm_tracker.py 机会详情 --合作机会id 5001
python scripts/crm_tracker.py 机会删除 --合作机会id 5001

python scripts/crm_tracker.py 客户新增 --客户名称 "杭州某品牌" --产品类目 "美妆"
python scripts/crm_tracker.py 客户更新 --客户id 1 --月建联量 300
python scripts/crm_tracker.py 客户列表 --搜索关键词 美妆 --排序字段 更新时间 --排序方向 降序
python scripts/crm_tracker.py 客户详情 --客户id 1
python scripts/crm_tracker.py 客户删除 --客户id 1

python scripts/crm_tracker.py 联系人新增 --客户id 1 --联系人姓名 "王五" --微信号 "wx_wangwu" --手机号 "13800138000" --联系角色 "负责人" --是否决策人 1
python scripts/crm_tracker.py 联系人更新 --联系人id 1001 --联系角色 "CMO"
python scripts/crm_tracker.py 联系人列表 --搜索关键词 王 --是否决策人 1 --排序字段 更新时间 --排序方向 降序
python scripts/crm_tracker.py 联系人详情 --联系人id 1001
python scripts/crm_tracker.py 联系人删除 --联系人id 1001

python scripts/crm_tracker.py 看板
```

## 列表查询能力

- `机会列表`：`--合作机会id` `--客户id` `--联系人id` `--搜索关键词` `--当前阶段` `--优先级` `--内部负责人` `--下一步日期` `--下一步日期截止前` `--仅看活跃` `--排序字段` `--排序方向` `--页码` `--每页数量`
- `客户列表`：`--客户id` `--客户名称` `--搜索关键词` `--产品类目` `--排序字段` `--排序方向` `--页码` `--每页数量`
- `联系人列表`：`--联系人id` `--联系人姓名` `--微信号` `--手机号` `--搜索关键词` `--客户id` `--联系角色` `--是否决策人` `--排序字段` `--排序方向` `--页码` `--每页数量`
