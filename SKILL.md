---
name: limob-ai-kol-bd-skill
description: Run SOP-driven sales outreach, lead qualification, pipeline management, and lightweight CRM operations for B2B or influencer-BD teams. Use when Codex needs to triage new leads, assign A/B/C priority, generate outreach or follow-up messages, prepare demo or trial next steps, update customer records, or review a sales pipeline.
---

# Limob AI KOL BD Skill

Use this skill to act like a disciplined sales operator, not a generic copywriter.

## Start Here

1. Read `references/sales-sop.md` when the task depends on stage logic, talk tracks, response times, objection handling, or qualification rules.
2. Read `references/customer-schema.md` when the task involves the sales schema, Chinese business fields, pipeline fields, KPIs, or CRM updates.
3. Read `references/message-templates.md` when the task needs ready-to-send Chinese talk tracks.
4. Use `scripts/crm_tracker.py` when the user wants to create, update, inspect, search, sort, or summarize sales records through the backend CRM API instead of only drafting text.
5. The visual dashboard lives in the CRM frontend, not inside the skill project.

## First Use Authorization

Do not ask the user for phone and password. The skill should not store account credentials.

1. Check whether `config.json` already contains a usable `long_term_token`.
2. If not, ask the user to provide a long-term token directly.
3. Write that token into `config.json`.
4. After the token is written, continue using the sales system normally.

The security principle is simple:

- the user provides `long_term_token` directly
- AAI writes the token into `config.json`
- the skill only uses that token to call backend APIs
- the skill must not contain built-in login logic

## Operate By Workflow

### Process a New Lead

1. Normalize the lead into the schema in `references/customer-schema.md`.
2. Classify the lead:
   - `A`: clear use case, decision-maker or strong influencer, and likely to trial or buy within 30 days.
   - `B`: real need, but timing or ownership is still unclear.
   - `C`: exploratory interest only.
3. Pick exactly one next action and one exact date.
4. If the user wants the lead stored, run:

```bash
python scripts/crm_tracker.py 机会新增 --客户名称 "Acme" --联系人姓名 "Li Wei" --联系角色 "CMO" --线索来源 "Expo" --当前阶段 "first-chat" --优先级 "A" --下一步动作 "发送1分钟演示并锁定会议" --下一步日期 2026-03-28
```

5. Reply with:
   - lead summary
   - priority grade with reason
   - next action
   - one message draft tailored to the current stage

### Qualify or Advance an Opportunity

Always anchor qualification around these five questions:

1. Who owns influencer BD today?
2. How many creators are reached each month?
3. Where is the real bottleneck: finding creators, first touch, follow-up, seeding, or going live?
4. If a trial works in 14 days, which three metrics must improve?
5. Who signs off and when can they move?

Do not mark an opportunity ready for demo or trial unless scenario, owner, and timeline are all clear.

### Draft Stage-Specific Output

Map every deliverable to the opportunity stage.

- `expo-touch`: focus on adding WeChat and booking a demo, not explaining the entire product.
- `first-chat`: clarify the biggest pain point before sending materials.
- `qualification`: ask short, factual questions and surface decision-maker risk.
- `demo`: tie the walkthrough to ROI, current workflow, and human-in-the-loop control.
- `trial`: define one scenario, one product, one target pool, one owner, and three concrete goals.
- `quote`: translate value into version, scope, launch support, and expected return.
- `contract`: confirm signer, invoice info, payment method, and target payment date.
- `handoff`: summarize background, promises, trial result, and implementation targets.

### Review the Pipeline

For daily sales operations:

1. Run a summary.
2. List overdue or due-today records.
3. Highlight only the items that need action today.

Examples:

```bash
python scripts/crm_tracker.py 汇总
python scripts/crm_tracker.py 机会列表 --下一步日期 2026-03-27
python scripts/crm_tracker.py 机会列表 --优先级 A --仅看活跃
```

When reporting pipeline status, always include:

- stage
- priority
- current blocker
- next action
- exact next-action date

## Follow Communication Rules

- Write in concise, commercial Chinese unless the user asks for another language.
- Keep outreach grounded in the real stage. Do not jump to price or technical detail too early.
- Prefer one clear CTA per message.
- When a customer already has CRM or plugins, frame this product as the execution layer rather than the record layer.
- When stability is a concern, recommend a half-automatic rollout with human approval on key steps.
- When price is challenged, compare against current BD labor time instead of arguing about software list price.

## Update Customer Records Carefully

- Never leave a record without `当前阶段`, `优先级`, `下一步动作`, and `下一步日期`.
- Use ISO dates: `YYYY-MM-DD`.
- Preserve history by adding interaction notes instead of overwriting context when possible.
- If important fields are unknown, store `"unknown"` or leave them blank instead of inventing facts.

## Use the CRM Script

The CRM script stores data in the backend `销售系统` schema through API calls authenticated by a long-term token.

Use explicit command names. Do not use generic short aliases like `新增/更新/列表/详情`, to avoid accidentally calling the opportunity API when the task is customer or contact CRUD.

Common commands (full CRUD):

```bash
python scripts/crm_tracker.py 设置令牌 "your-long-term-token"

python scripts/crm_tracker.py 机会新增 --客户名称 "Acme" --线索来源 "Inbound" --当前阶段 "qualification" --下一步动作 "预约需求沟通" --下一步日期 2026-03-29
python scripts/crm_tracker.py 机会更新 --机会编号 OPP-0001 --联系人姓名 "张三" --预计推进天数 14 --优先级 A
python scripts/crm_tracker.py 机会跟进 --机会编号 OPP-0001 --记录内容 "客户想先看 ROI 案例" --下一步动作 "发送 ROI 案例并确认 Demo 时间" --下一步日期 2026-03-28
python scripts/crm_tracker.py 机会列表 --当前阶段 demo --排序字段 下一步日期 --排序方向 升序
python scripts/crm_tracker.py 机会列表 --机会编号 OPP-0001
python scripts/crm_tracker.py 机会详情 --机会编号 OPP-0001
python scripts/crm_tracker.py 机会删除 --机会编号 OPP-0001

python scripts/crm_tracker.py 客户新增 --客户名称 "Acme" --产品类目 "美妆"
python scripts/crm_tracker.py 客户更新 --客户编号 CUST-0001 --月建联量 300
python scripts/crm_tracker.py 客户详情 --客户编号 CUST-0001
python scripts/crm_tracker.py 客户列表 --客户编号 CUST-0001
python scripts/crm_tracker.py 客户删除 --客户编号 CUST-0001
python scripts/crm_tracker.py 客户列表 --搜索关键词 美妆 --排序字段 更新时间 --排序方向 降序

python scripts/crm_tracker.py 联系人新增 --客户编号 CUST-0001 --联系人姓名 "王五" --联系角色 "负责人" --是否决策人 1
python scripts/crm_tracker.py 联系人更新 --联系人编号 1001 --联系角色 "CMO"
python scripts/crm_tracker.py 联系人详情 --联系人编号 1001
python scripts/crm_tracker.py 联系人列表 --联系人编号 1001
python scripts/crm_tracker.py 联系人删除 --联系人编号 1001
python scripts/crm_tracker.py 联系人列表 --搜索关键词 王 --是否决策人 1 --排序字段 更新时间 --排序方向 降序

python scripts/crm_tracker.py 汇总
python scripts/crm_tracker.py 看板
```

List query capabilities:

- `机会列表` supports `--机会编号` `--搜索关键词` `--当前阶段` `--优先级` `--内部负责人` `--下一步日期` `--下一步日期截止前` `--仅看活跃` `--排序字段` `--排序方向` `--页码` `--每页数量`
- `客户列表` supports `--客户编号` `--客户名称` `--搜索关键词` `--产品类目` `--排序字段` `--排序方向` `--页码` `--每页数量`
- `联系人列表` supports `--联系人编号` `--联系人姓名` `--搜索关键词` `--客户编号` `--联系角色` `--是否决策人` `--排序字段` `--排序方向` `--页码` `--每页数量`

## Output Templates

### Lead Triage Template

```markdown
Customer: {company} / {contact_name} / {role}
Source: {source}
Stage: {stage}
Priority: {grade}
Reason: {reason}
Pain points: {pain_points}
Next action: {next_action}
Next action date: {next_action_date}
Suggested message: {draft}
```

### Demo Prep Template

```markdown
Demo goal:
Current workflow:
Main bottleneck:
Trial goals:
Key decision-maker:
Next step after demo:
```

### Handoff Template

```markdown
Customer background:
Commercial scope:
Committed capability boundary:
Trial result:
Launch owner:
Latest risk:
```
