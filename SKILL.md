---
name: sales-automation-crm
description: Run SOP-driven sales outreach, lead qualification, pipeline management, and lightweight CRM operations for B2B or influencer-BD teams. Use when Codex needs to triage new leads, assign A/B/C priority, generate outreach or follow-up messages, prepare demo or trial next steps, update customer records, or review a sales pipeline.
---

# Sales Automation CRM

Use this skill to act like a disciplined sales operator, not a generic copywriter.

## Start Here

1. Read `references/sales-sop.md` when the task depends on stage logic, talk tracks, response times, objection handling, or qualification rules.
2. Read `references/customer-schema.md` when the task involves the SQLite schema, Chinese database fields, pipeline fields, KPIs, or CRM updates.
3. Read `references/message-templates.md` when the task needs ready-to-send Chinese talk tracks.
4. Use `scripts/crm_tracker.py` when the user wants to create, update, inspect, or summarize customer records stored in SQLite instead of only drafting text.
5. Use `scripts/launch_dashboard.py` when the user wants one-click launch of the dashboard. It should automatically ensure the local API is running and then open the board.
6. Use `scripts/dashboard_server.py` only when debugging the local dashboard service itself.

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
python scripts/crm_tracker.py add --company "Acme" --contact-name "Li Wei" --role "CMO" --source "Expo" --stage "first-chat" --grade "A" --next-action "Send 1-minute demo and lock a call" --next-action-date 2026-03-28
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
- `trial`: define one scenario, one product, one target pool, one owner, and three success metrics.
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
python scripts/crm_tracker.py summary
python scripts/crm_tracker.py list --due-on 2026-03-27
python scripts/crm_tracker.py list --grade A --active-only
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

- Never leave a record without `stage`, `grade`, `next_action`, and `next_action_date`.
- Use ISO dates: `YYYY-MM-DD`.
- Preserve history by adding interaction notes instead of overwriting context when possible.
- If important fields are unknown, store `"unknown"` or leave them blank instead of inventing facts.

## Use the CRM Script

The CRM script stores data in `data/sales.sqlite3` by default.

Common commands:

```bash
python scripts/crm_tracker.py add --company "Acme" --source "Inbound" --stage "qualification" --next-action "Book discovery call" --next-action-date 2026-03-29
python scripts/crm_tracker.py update --id LEAD-0001 --decision-maker "Zhang San" --timeline-days 14 --grade A
python scripts/crm_tracker.py touch --id LEAD-0001 --note "Client asked for ROI case study" --next-action "Send ROI case and confirm demo time" --next-action-date 2026-03-28
python scripts/crm_tracker.py list --stage demo
python scripts/crm_tracker.py summary
python scripts/launch_dashboard.py
```

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
Trial success metrics:
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
