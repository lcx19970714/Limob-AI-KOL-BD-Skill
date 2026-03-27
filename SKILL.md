---
name: limob-ai-kol-bd-skill
description: 面向销售 SOP 的线索分级、跟进推进、管道管理与轻量 CRM 写入技能。
---

# Limob AI KOL BD Skill

本技能定位为“销售执行层”，不是通用文案生成器。

## 先读什么

1. 涉及阶段推进、话术、异议处理时，先读 `references/sales-sop.md`。
2. 涉及字段、表结构、CRM 写入时，先读 `references/customer-schema.md`。
3. 涉及可直接发送话术时，读 `references/message-templates.md`。
4. 需要真实 CRUD、搜索、筛选、排序、汇总时，使用 `scripts/crm_tracker.py`。
5. 可视化看板在 CRM 前端，不在 skill 项目内实现。

## 首次授权（唯一方案）

1. 从 `config.json` 读取 `long_term_token`。
2. 若为空，直接向用户索取 `long_term_token`。
3. 将 token 写回 `config.json` 后继续执行。

硬约束：

- 不要向用户索取手机号和密码。
- 不要在 skill 内置登录流程。
- 只存储 `long_term_token`，不存储账号密码。

## 调用契约（唯一路径）

1. 统一通过 `scripts/crm_tracker.py` -> `scripts/skill_api.py` 调后端。
2. 只允许显式命令：`机会*`、`客户*`、`联系人*`。
3. 禁止通用短命令：`新增/更新/列表/详情`。
4. 请求字段统一用中文，且与后端模型同名。
5. `date` 字段统一 `YYYY-MM-DD`；`datetime` 字段统一 `YYYY-MM-DD HH:MM:SS`。
6. 禁止兼容兜底写法：`{"$date": ...}`、时间戳绕过、给 `date` 传带时间字符串。
7. 合作机会必须通过 `客户id` 关联客户；联系人通过 `联系人id` 关联，禁止在机会接口里手填客户名称/联系人姓名建档。
8. 标准顺序：先建客户，再建联系人，最后建合作机会。

## 销售执行流程

### 新线索处理

1. 先按 schema 归一化线索信息。
2. 再给优先级：
   - `A`：场景明确、决策链清晰、30 天内有较大成交概率。
   - `B`：需求明确，但时机/负责人未完全清楚。
   - `C`：探索阶段，短期不推进。
3. 每次只给一个下一步动作和一个明确日期。
4. 需要入库时执行：

```bash
python scripts/crm_tracker.py 机会新增 --客户id CUS-0001 --联系人id 1001 --线索来源 "展会" --当前阶段 "first-chat" --优先级 "A" --下一步动作 "发送1分钟演示并锁定会议" --下一步日期 2026-03-28
```

### 每日管道动作

```bash
python scripts/crm_tracker.py 汇总
python scripts/crm_tracker.py 机会列表 --下一步日期 2026-03-27
python scripts/crm_tracker.py 机会列表 --优先级 A --仅看活跃
```

输出管道状态时，至少包含：

- 当前阶段
- 优先级
- 当前阻塞点
- 下一步动作
- 下一步日期

## 记录更新规范

- 合作机会记录不得缺少：`当前阶段`、`优先级`、`下一步动作`、`下一步日期`。
- 日期统一 ISO 规范：`YYYY-MM-DD`。
- 尽量补充跟进记录，不直接覆盖历史上下文。
- 未知信息可留空或写 `"unknown"`，禁止臆造。

## CRM 脚本命令

```bash
python scripts/crm_tracker.py 设置令牌 "your-long-term-token"

python scripts/crm_tracker.py 机会新增 --客户id CUS-0001 --联系人id 1001 --线索来源 "Inbound" --当前阶段 "qualification" --下一步动作 "预约需求沟通" --下一步日期 2026-03-29
python scripts/crm_tracker.py 机会更新 --合作机会id OPP-0001 --联系人id 1001 --预计推进天数 14 --优先级 A
python scripts/crm_tracker.py 机会跟进 --合作机会id OPP-0001 --记录内容 "客户想先看 ROI 案例" --下一步动作 "发送 ROI 案例并确认 Demo 时间" --下一步日期 2026-03-28
python scripts/crm_tracker.py 机会列表 --当前阶段 demo --排序字段 下一步日期 --排序方向 升序
python scripts/crm_tracker.py 机会详情 --合作机会id OPP-0001
python scripts/crm_tracker.py 机会删除 --合作机会id OPP-0001

python scripts/crm_tracker.py 客户新增 --客户名称 "Acme" --产品类目 "美妆"
python scripts/crm_tracker.py 客户更新 --客户id CUST-0001 --月建联量 300
python scripts/crm_tracker.py 客户列表 --搜索关键词 美妆 --排序字段 更新时间 --排序方向 降序
python scripts/crm_tracker.py 客户详情 --客户id CUST-0001
python scripts/crm_tracker.py 客户删除 --客户id CUST-0001

python scripts/crm_tracker.py 联系人新增 --客户id CUST-0001 --联系人姓名 "王五" --联系角色 "负责人" --是否决策人 1
python scripts/crm_tracker.py 联系人更新 --联系人id 1001 --联系角色 "CMO"
python scripts/crm_tracker.py 联系人列表 --搜索关键词 王 --是否决策人 1 --排序字段 更新时间 --排序方向 降序
python scripts/crm_tracker.py 联系人详情 --联系人id 1001
python scripts/crm_tracker.py 联系人删除 --联系人id 1001

python scripts/crm_tracker.py 看板
```

列表查询能力：

- `机会列表`：`--合作机会id` `--客户id` `--联系人id` `--搜索关键词` `--当前阶段` `--优先级` `--内部负责人` `--下一步日期` `--下一步日期截止前` `--仅看活跃` `--排序字段` `--排序方向` `--页码` `--每页数量`
- `客户列表`：`--客户id` `--客户名称` `--搜索关键词` `--产品类目` `--排序字段` `--排序方向` `--页码` `--每页数量`
- `联系人列表`：`--联系人id` `--联系人姓名` `--搜索关键词` `--客户id` `--联系角色` `--是否决策人` `--排序字段` `--排序方向` `--页码` `--每页数量`

## 沟通风格

- 默认使用简洁商业中文。
- 一条消息只放一个明确 CTA。
- 话术必须与当前阶段匹配，不越阶段推进。
- 客户担心稳定性时，优先建议“半自动 + 人工确认”的落地路径。



