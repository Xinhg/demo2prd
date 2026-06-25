---
name: proto-pm-interviewer
description: >
  Stage 2 of 4: Generate a printable / screen-shareable PM question
  checklist from prototype parser evidence, field analysis, and auxiliary
  materials. Questions are designed as multiple-choice where possible for
  high readability in meetings. Also produces a standard answer template
  that AI can auto-fill from raw meeting notes after the meeting.
triggers:
  - "PM question checklist"
  - "prepare PM questions"
  - "proto PM interview"
  - "requirements checklist"
  - "product manager questions"
  - "PM提问清单"
  - "生成提问清单"
---

# proto-pm-interviewer (Stage 2 — PM Question Checklist Generator)

Generate a high-readability PM question checklist for use in product
manager meetings. This skill produces a **printable / screen-shareable
document** — it does **not** conduct a live interview. The user takes this
document into a meeting, asks the PM, and then provides meeting notes or
an answer document for the next stage.

This is stage 2 of the four-stage workflow:

1. **Parser + Field Analysis** (`proto-to-requirement`) — produces
   prototype evidence and field analysis.
2. **PM Question Checklist** (this skill) — generates a meeting-ready
   question document.
3. **PM Answer Collection** (user manual step) — user collects PM answers
   during the meeting and provides notes or filled answer template.
4. **BDD Writer** (`bdd-engineering-prd-writer`) — uses all evidence and
   PM answers to write the final BDD engineering PRD.

## When to Use

- After the parser has produced `prototype-analysis.md`,
  `structured-data.json`, `completeness-report.json`, and
  `field-analysis.md`.
- Before a PM meeting where you need to confirm requirements, resolve
  ambiguities, and close open items from the field analysis.
- When you need a structured, readable document to guide a requirements
  discussion.

## When Not to Use

- Before prototype parsing and field analysis are complete: run
  `proto-to-requirement` first.
- For writing the final PRD: use `bdd-engineering-prd-writer` after PM
  answers are collected.
- When all field analysis items have high confidence and no open items
  exist.

## Required Input

1. **Parser evidence**: `prototype-analysis.md`, `structured-data.json`,
   `completeness-report.json` from the parser stage.
2. **Field analysis**: `field-analysis.md` from the parser stage,
   especially the "Questions for PM Confirmation" section and low-
   confidence field entries.
3. **Auxiliary materials** (optional but recommended):
   - Manual PRDs or requirement documents
   - Screenshots, flowcharts, meeting notes
   - Existing system documentation
   - Draft `requirements.md` from the parser stage

## Output

Two artifacts are produced:

| Output | File | Description |
|--------|------|-------------|
| PM Question Checklist | `pm-question-checklist.md` | A meeting-ready, high-readability question document organized by business domain, with multiple-choice format |
| PM Answer Template | `pm-answer-template.md` | A standard template pre-filled with question IDs for collecting PM answers; AI can auto-fill this from raw meeting notes |

## Question Sources

Questions are generated from multiple sources:

### From Field Analysis (`field-analysis.md`)

- Fields with 置信度 = `low` or `medium`
- Fields where 信息来源 is "field name inference" or "default rules"
- Conflicting field properties across different pages or areas
- Fields with unclear 填写形式, 格式要求, or 枚举值
- Missing 依赖关系 or 权限规则

### From Prototype Analysis

- Interactions marked as `inferred` or `unknown` confidence
- Unresolved navigation targets
- Pages with very few extracted components (possible parser gap)
- Business rules from annotations that are ambiguous

### From Domain Logic

- Permissions: who can view, create, edit, delete, approve each entity?
- Modification boundaries: which fields are editable at which stage?
- Business logic: calculations, validations, cross-entity rules
- State transitions: valid states, allowed transitions, triggers
- Exception flows: duplicate submission, timeout, concurrent edit
- Data ownership: who owns each entity, delegation rules
- Approval/revoke behavior: approval chains, delegation, recall

### Filtering Rule

> **Do not ask about every field.** Only generate questions for items that
> meet at least one criterion:
> - Low confidence in the field analysis
> - High risk (affects data model, main flow, or API contract)
> - Conflicting evidence (prototype vs. requirement doc vs. annotations)
> - Missing critical information (e.g., no visible validation rules for
>   a required field)

## Question Design Principles

### 1. Multiple-Choice First

Design questions as multiple-choice (A/B/C/D) wherever possible. This:
- Reduces PM cognitive load
- Speeds up meeting discussions
- Produces unambiguous, structured answers
- Makes it easy to circle/check answers on paper

Reserve open-ended questions only when the answer space is too broad for
predefined options (e.g., "请描述审批流程的完整链路").

### 2. Grouped by Business Domain

Organize questions by business domain or functional module, **not** by
technical dimension. Example groupings:

- ✅ 合同管理、供应商管理、审批流程
- ❌ 权限问题、字段问题、状态问题

This makes it natural for PMs to discuss related topics together.

### 3. Evidence Context

Every question must include a brief evidence context explaining **why**
this question is being asked:

```
来源：原型「合同详情页」显示「合同金额」为只读，但「编辑合同」弹窗中
该字段出现为可编辑输入框。两处矛盾，需确认。
```

### 4. Priority Labels

Every question carries a priority label:

| Level | Label | Meaning | Meeting Guidance |
|-------|-------|---------|-----------------|
| P0 | 🔴 必须确认 | Blocks data model, API contract, or main flow | Must resolve in this meeting |
| P1 | 🟡 建议确认 | Affects boundary rules, error handling, or UX detail | Try to resolve; can follow up |
| P2 | 🔵 可后续确认 | Affects copy, defaults, configuration, or polish | Discuss if time permits |

### 5. Impact Statement

Each question states the engineering impact of not answering:

```
影响：如不确认，开发无法确定合同编号是用户输入还是系统生成，
将影响表单设计和后端编号生成逻辑。
```

## Checklist Document Structure

The `pm-question-checklist.md` follows this structure:

### Document Header

```markdown
# PM 需求确认提问清单

| 项目 | 值 |
|------|-----|
| 项目名称 | <from prototype> |
| 生成日期 | <date> |
| 基于原型版本 | <prototype identifier> |
| 问题总数 | <count> |
| 🔴 P0 | <count> |
| 🟡 P1 | <count> |
| 🔵 P2 | <count> |

## 使用说明

1. 本清单按业务模块分组，建议按顺序讨论
2. 选择题直接勾选或圈出选项即可
3. 如有补充说明请写在「备注」栏
4. 会后请将本清单或会议记录发给 AI，自动生成解答文档
```

### Question Sections (per business domain)

```markdown
## [模块名称]

### Q01 🔴 [问题标题]

**问题**：[具体问题描述]

| 选项 | 说明 |
|------|------|
| A | [选项A描述] |
| B | [选项B描述] |
| C | [选项C描述] |
| D | 其他：_______ |

**来源**：[为什么问这个问题——引用原型/字段分析中的证据]
**影响**：[不确认会导致什么工程问题]

> PM 选择：____  备注：_________________________
```

### Summary Section

```markdown
## 汇总

### 本次需确认的核心决策

| # | 优先级 | 模块 | 问题摘要 | PM 决策 |
|---|--------|------|----------|---------|
| Q01 | 🔴 | 合同管理 | 合同编号生成规则 | |
| Q02 | 🔴 | 合同管理 | 合同状态流转 | |
| ... | | | | |
```

## Answer Template Structure

The `pm-answer-template.md` is designed for two usage modes:

### Mode 1: Manual Fill

User prints or opens the template and fills in answers during/after the
meeting:

```markdown
# PM 解答文档

| 项目名称 | <from prototype> |
| 会议日期 | _______ |
| 参会人员 | _______ |

## 解答记录

### Q01: [问题标题]
- PM 选择：[ ] A  [ ] B  [ ] C  [ ] D
- 补充说明：
- 确认状态：[ ] 已确认  [ ] 需后续确认  [ ] 不适用

### Q02: [问题标题]
...
```

### Mode 2: AI Auto-Fill from Meeting Notes

User provides raw meeting notes (text, audio transcription, or chat log),
and AI automatically:

1. Matches meeting note content to question IDs
2. Identifies which questions were answered
3. Fills in the answer template with PM responses
4. Labels each answer with a source tag:
   - `PM 明确回答` — PM directly addressed the question
   - `会议内容推断` — answer inferred from meeting discussion context
   - `未提及` — question was not discussed in the meeting
5. Highlights any new questions or requirements that emerged from the
   meeting but were not in the original checklist

The auto-fill prompt for the AI:

```
请根据以下会议记录，自动填写 PM 解答模板。

规则：
1. 将会议记录中的内容匹配到对应问题编号
2. 如果 PM 明确回答了某个问题，标注「PM 明确回答」并记录原文
3. 如果可以从会议讨论推断答案，标注「会议内容推断」并说明推断依据
4. 如果会议未涉及某个问题，标注「未提及」
5. 如果会议中出现了清单外的新需求或新问题，在末尾「新增问题」区记录
```

## Workflow

### 1. Gather Inputs

Collect parser artifacts, field analysis, and any auxiliary materials.
Review field analysis for:
- Low confidence fields (置信度 = `low`)
- Questions already generated in `field-analysis.md` section 5.6
- Unresolved interactions from prototype analysis
- Completeness gaps from `completeness-report.json`

### 2. Generate Question List

For each question source, inspect evidence and generate questions where
information is insufficient for confident engineering:

- Merge questions from `field-analysis.md` section 5.6 (already formatted
  as multiple-choice) with domain logic questions
- Deduplicate questions that address the same decision point
- Assign priorities (P0/P1/P2) based on engineering impact
- Group by business domain / functional module
- Number sequentially (Q01, Q02, ...)

### 3. Format the Checklist

Write `pm-question-checklist.md` following the document structure above.
Ensure:

- Every question has evidence context and impact statement
- Multiple-choice options cover the most likely answers plus "其他"
- The document reads well when printed on A4 paper or displayed on screen
- Summary table at the end lists all questions for quick overview

### 4. Generate the Answer Template

Write `pm-answer-template.md` with:

- Pre-filled question IDs and titles from the checklist
- Checkbox-style answer slots for each option
- Space for supplementary notes
- Confirmation status checkboxes
- A "新增问题" section at the end for capturing new items from the meeting

### 5. Hand Off

After the PM meeting:

- User provides either the filled answer template or raw meeting notes
- If raw meeting notes are provided, AI auto-fills the answer template
- The completed answer document, together with parser artifacts and field
  analysis, is passed to `bdd-engineering-prd-writer` for the final BDD
  engineering PRD

## Rules

- **Do not ask about every field.** Only generate questions for low
  confidence, high risk, or conflicting items.
- **Prefer multiple-choice.** Open-ended questions are a last resort.
- **Group by business domain.** Do not organize by technical category.
- **Include evidence.** Every question must state why it is being asked.
- **State impact.** Every question must state what goes wrong without an
  answer.
- **Do not invent answers.** The checklist contains questions only — no
  assumed or default answers should be presented as confirmed.
- **Do not skip categories.** If a domain has no questions because the
  material is complete, note that explicitly (e.g., "合同管理：字段分析
  置信度均为 high，无需确认").
- **Readable format.** The document must be usable in a meeting without
  AI assistance — printable, scannable, with clear visual hierarchy.
