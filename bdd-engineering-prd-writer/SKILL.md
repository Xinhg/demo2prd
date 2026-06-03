---
name: bdd-engineering-prd-writer
description: >
  Stage 3 of 3: Combine prototype parser evidence, PM interview report,
  manual PRDs, and auxiliary materials into a traceable BDD engineering PRD
  that coding agents can use for planning and implementation. Every
  requirement is backed by evidence or explicit human confirmation.
triggers:
  - "write BDD PRD"
  - "engineering PRD"
  - "BDD engineering PRD"
  - "write engineering requirements"
  - "generate development PRD"
---

# bdd-engineering-prd-writer (Stage 3 — BDD Engineering PRD Writer)

Combine prototype parser evidence, PM-confirmed interview answers, manual
PRDs, and auxiliary materials into a single traceable BDD engineering PRD.
Every requirement is backed by either source evidence or explicit PM
confirmation — never by invention.

This is stage 3 of the three-stage workflow:

1. **Parser** (`proto-to-requirement`) — produces prototype evidence.
2. **PM Interviewer** (`proto-pm-interviewer`) — produces PM interview
   report with confirmed decisions.
3. **BDD Writer** (this skill) — produces the final BDD engineering PRD.

## When to Use

- After both parser artifacts and the PM interview report are available.
- When you need a PRD that a coding agent (Codex, Claude Code, etc.) can
  use directly for engineering planning, task breakdown, and
  implementation.
- When requirements traceability matters: every claim must be attributable
  to parser evidence or PM confirmation.

## When Not to Use

- Before prototype parsing is complete: run `proto-to-requirement` first.
- Before the PM interview is complete: run `proto-pm-interviewer` first.
- When only a raw prototype data dump is needed: that's the parser stage
  output.
- When no human confirmation is available for unresolved parser findings:
  P0 items must be resolved before a development-ready PRD can be produced.

## Required Input

1. **Parser evidence**: `prototype-analysis.md`, `structured-data.json`,
   `completeness-report.json` from the parser stage.
2. **PM interview report**: confirmed decisions, rejected assumptions,
   unanswered questions, and missing context from the interview stage.
3. **Manual PRDs or requirement documents** (if available).
4. **Auxiliary materials** (if available): screenshots, system docs,
   flowcharts, meeting notes, existing codebase references.

## Output

One BDD engineering PRD (`bdd-engineering-prd.md`) suitable for coding
agent consumption. The PRD must be detailed through business logic, not
through page or component inventories.

## BDD PRD Structure

The output PRD follows this structure:

### 开发入口摘要 (Development Entry Summary)

A 1–2 page overview to help a coding agent decide where to start:

- **Must-deliver Epics**: business capabilities grouped by domain, not by
  page names.
- **P0 Blockers**: items that must be confirmed before development can
  start. P0 blockers must **not** appear as acceptance criteria.
- **Out-of-scope for development**: items the input does not support.
- **Repository pre-check list**: objects the coding agent must inspect
  in the target repository before adding or renaming anything.
- **Recommended development order**: dependency-ordered steps.

### P0 / P1 / P2 待确认清单 (Confirmation Items)

| Priority | Meaning | Engineering Rule |
|----------|---------|-----------------|
| P0 | Blocks data model, API contract, or main flow | Must confirm before development; cannot be acceptance criteria |
| P1 | Affects boundary rules, error handling, or UX detail | Can design, but confirm before or during development |
| P2 | Affects copy, defaults, configuration, or polish | Can defer to later iterations |

Every confirmation item must state its source: parser evidence, PM
interview, manual PRD, or auxiliary material.

### Feature / Rule / Scenario (BDD)

Where behavior is sufficiently confirmed, write structured BDD sections:

```gherkin
Feature: <business capability>
  As a <role>
  I need <capability>
  So that <business value>

  Rule: <business rule name>
    <rule description>

  Scenario: <normal path>
    Given <precondition>
    When <user or system action>
    Then <verifiable outcome>

  Scenario: <exception path>
    Given <precondition>
    When <failure condition>
    Then <error handling or rollback>
```

Requirements for BDD sections:

- Feature covers all primary business capabilities in the input.
- If the input has only a title or fragment for a capability, mark it as
  "暂不可开发" (not yet developable) and list what's missing.
- Scenarios must cover normal, exception, duplicate-submission,
  permission-denied, historical-data, boundary-value, and external-failure
  cases where applicable.
- Do not write `Then` clauses from unconfirmed items.
- Do not copy raw page lists, component inventories, or interaction tables
  into BDD sections — describe business logic, using page IDs only as
  evidence anchors.

### Evidence Mapping

Every claim in the PRD must be traceable. Map each requirement to its
source:

| Requirement | Source | Confidence |
|-------------|--------|------------|
| <claim> | Parser `structured-data.json` / PM interview / Manual PRD / Auxiliary | fact / PM confirmed / inferred |

### Human Confirmation Mapping

Document every PM-confirmed decision that overrides or supplements parser
evidence:

| Parser Finding | PM Decision | Impact |
|----------------|-------------|--------|
| <original parser fact or inference> | Confirmed / Rejected / Modified with details | <what changes in the PRD> |

### Coding Agent Guardrails

The coding agent that consumes this PRD must follow these rules:

1. **Repository inspection before modification**: Before adding or renaming
   any of the following, inspect the target repository for existing
   equivalents:
   - Fields, tables, enums, and indexes
   - API routes and contracts
   - Permissions, roles, and access-control patterns
   - External service integrations and configurations
   - Jobs, queues, and scheduled tasks
   - Message templates, notification channels, and i18n keys
   - Database migrations and data contracts
2. **Prefer existing names**: If a field, table, enum, or route with
   equivalent semantics already exists, use it. Do not rename or duplicate.
3. **Mark new additions**: Only add a field, table, enum, or route when
   the repository has no equivalent — and mark it as "新增候选" (new
   candidate) with evidence.
4. **Do not invent backend contracts**: API routes, database schemas,
   permission matrices, and external service integrations must come from
   parser evidence, PM confirmation, manual PRDs, or repository
   inspection — never from invention.
5. **No page-inventory PRDs**: Do not substitute raw page lists, component
   inventories, or interaction tables for business logic description. Page
   IDs and page names are evidence anchors, not the PRD content itself.

### 领域模型与数据结构 (Domain Model & Data)

Describe data entities, their relationships, and constraints. Use
"说明" (description) column headers, not "字段" (field) — to avoid
inducing the coding agent to create fields from description labels.

Every data description must state whether the repository already has an
equivalent, or whether this is a new candidate.

### 接口与后端能力 (API & Backend Capabilities)

Describe required backend capabilities without inventing routes. Each
capability must note whether the repository already has an equivalent
implementation.

### 工程实施拆解 (Engineering Breakdown)

Epic-level breakdown with dependencies, repository pre-checks, open
confirmation items, test focus, and explicit "do not do" constraints.

### P0 / P1 / P2 待确认完整清单 (Full Confirmation Checklist)

Consolidated list of all confirmation items from parser, interview, and
auxiliary sources. P0 items must not appear as acceptance criteria.

### 审查与修正 (Review & Revision)

Before final delivery, self-review the PRD against these checks:

1. Are any requirements invented (not in parser evidence, PM interview, or
   auxiliary materials)?
2. Are any recommendations written as requirements ("建议" vs "必须")?
3. Are any unconfirmed items written as acceptance criteria?
4. Are any database field names, table names, or API routes invented?
5. Are any P0 blockers missing?
6. Are any business rules unsupported by input?
7. Are any external services or dependencies invented?
8. Are BDD scenarios present and covering normal/exception paths?
9. Can the document be directly decomposed into an engineering plan?

If any check fails, revise the PRD before declaring it complete.

## Rules

- **P0 blockers are not acceptance criteria.** They block development; they
  do not describe what success looks like.
- **No invention.** Every claim must map to parser evidence, PM
  confirmation, manual PRD, auxiliary material, or repository inspection.
- **No page-inventory substitution.** Page lists, component inventories,
  and interaction tables are parser artifacts. The BDD PRD describes
  business logic, not UI inventory.
- **Evidence before assertions.** State the source of every requirement.
  If the source is weak, state the confidence.
- **Repository protection.** The PRD must instruct the coding agent to
  inspect before adding or renaming — never assume the repository is a
  blank slate.
