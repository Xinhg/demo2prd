---
name: proto-to-requirement
description: >
  Stage 1 of 4: Parse a pure-data Mockitt (MoDao) prototype export into
  structured evidence artifacts, then automatically perform field-level and
  page-structure analysis. Reads a local export directory, extracts pages,
  interactions, visible text, and annotation-based business rules, then
  produces a prototype analysis report, structured JSON outputs, and a
  field analysis report with 18-dimension field descriptions and page
  structure mapping. Hands off to proto-pm-interviewer (stage 2) for PM
  question checklist generation, user provides PM answers (stage 3), and
  bdd-engineering-prd-writer (stage 4) for the final BDD engineering PRD.
triggers:
  - "convert this prototype"
  - "generate requirements from Mockitt"
  - "extract PRD from prototype"
  - "proto to requirement"
  - "field analysis"
  - "字段解析"
---

# proto-to-requirement (Stage 1 — Prototype Parser + Field Analysis)

Convert a local Mockitt (MoDao) prototype export into structured evidence
artifacts, then automatically analyze fields and page structure. This is
the **parser and field analysis stage** of a four-stage workflow. It
produces intermediate analysis files — not the final BDD engineering PRD.

The full workflow is:

1. **Parser + Field Analysis** (this skill) — extract prototype evidence
   into `prototype-analysis.md`, `structured-data.json`,
   `completeness-report.json`, and then automatically produce
   `field-analysis.md` with page structure, field descriptions, operation
   logic, and preliminary BDD scenarios.
2. **PM Question Checklist** (`proto-pm-interviewer`) — use parser evidence,
   field analysis, and auxiliary materials to generate a printable /
   screen-shareable question checklist for PM meetings, with questions
   designed as multiple-choice where possible.
3. **PM Answer Collection** (user manual step) — user takes the checklist
   into a PM meeting, collects answers, and provides a meeting-notes or
   answer document. AI can auto-fill the answer template from raw meeting
   notes.
4. **BDD Writer** (`bdd-engineering-prd-writer`) — combine parser evidence,
   field analysis, PM answers, manual PRDs, and supporting materials into a
   traceable BDD engineering PRD that coding agents can use.

This MVP is **pure-data only** — it reads exported data files without
browser automation, visual models, or online prototype access.

## When to Use

- A PM or developer has provided a Mockitt export directory (containing
  `mb-proto2/` and `extra/data.*.js`).
- You need to extract structured evidence from a prototype before a PM
  meeting or BDD PRD writing session.
- You need a completeness assessment showing how much prototype information
  is captured.
- You need a field-level analysis to understand what data fields exist in
  the prototype and their properties.

## When Not to Use

- For the final BDD engineering PRD: use `bdd-engineering-prd-writer`
  (stage 4).
- For PM question checklist: use `proto-pm-interviewer` (stage 2).
- For Axure, Figma, Sketch, or other design tools: not yet supported.
- For online prototype URLs or browser rendering: not yet supported.

## Required Input

A local directory path to an unzipped Mockitt export. The directory must
contain:

- `mb-proto2/` — prototype structure marker
- `extra/data.*.js` — at least one data file (the largest is used as
  primary)

Optional auxiliary materials that improve field analysis quality:

- Manual PRDs or requirement documents
- PM meeting notes or interview transcripts
- Existing system documentation

## Workflow

### 1. Identify the Export Directory

Confirm the user's prototype directory exists and contains the expected
Mockitt signatures (`mb-proto2/` + `extra/data.*.js`).

### 2. Run the Extraction

The skill directory itself contains instructions and references. The
parser Python package may not be inside the skill directory after
installation. Before running the CLI, locate the runtime project directory:

- If the current workspace contains `pyproject.toml` and
  `proto_to_requirement/`, run the command from that workspace.
- If installed from this package on Codex, use
  `~/.codex/skill-runtimes/proto-to-requirement-skill-suite` as the
  runtime directory.
- If neither location exists, ask the user to provide or install the
  parser runtime package before attempting extraction.

From the runtime directory, run:

```bash
uv run python3 -m proto_to_requirement.cli <prototype_dir> --output <output_dir>
```

The CLI will:

1. **Probe** the directory to confirm Mockitt format and locate data files.
2. **Unpack** the primary data file (handles JS assignment wrappers, base64,
   gzip, line-delimited records).
3. **Extract** pages, interactions, visible text, and annotation-based
   business rules.
4. **Render** output files into the output directory.

Interaction extraction resolves targets by interaction semantics:

- `navigate` — resolve to the target page, including Mockitt page IDs whose
  stored keys carry suffixes such as `rbp... 6`, `rbp... *`, or `rbp... )`.
- `modal` — resolve to the modal/layer target from the Mockitt context array.
- `back` — resolve as history return / close-current-layer behavior.
- `state_change` — resolve as current component or page state transition.

For real Mockitt exports, the interaction parse rate should be reported as
`parsed_interactions / total_interactions` and should target at least 90%
unless the export genuinely lacks target semantics.

### 3. Review Extraction Output Files

Four files are produced in the output directory:

| File | Description |
|------|-------------|
| `requirements.md` | User-facing requirements draft; provides an initial structured view of the prototype content |
| `prototype-analysis.md` | Intermediate parsing report with page inventory, interaction mapping, text/field candidates, annotation candidates, unresolved interactions, and completeness notes |
| `structured-data.json` | Machine-readable structured extraction |
| `completeness-report.json` | Numeric scores and implementability assessment |

### 4. Interpret Uncertainty Labels

Every extracted fact carries one of three labels:

- `fact` — extracted directly from data, no inference applied
- `inferred` — deduced from context patterns (e.g., interaction target
  resolved through context array)
- `unknown` — information not present in the data (e.g., form fields,
  table columns in pure-data mode)

### 5. Field & Page Structure Analysis (Auto-Executed)

**This step runs automatically after prototype extraction completes.** It
analyzes the parser output to produce a comprehensive field analysis
report. No user interaction is required to trigger this step.

#### Role

You are an engineering-level requirements analysis assistant. Based on the
prototype analysis results, any available product requirement documents,
and any available PM meeting notes, generate field descriptions and
interaction logic descriptions.

#### Information Credibility Priority

When determining field properties, judge information credibility in this
order:

1. Product explicit annotations (highest trust)
2. PM meeting notes / interview records
3. Requirement document body text
4. Prototype structure and layout
5. Field naming and control type inference
6. Default rules (lowest trust)

#### Critical Constraint — Prototype Fields Only

> **DO NOT map fields to actual database columns, table names, or backend
> schema.** The field analysis describes what appears in the prototype UI
> only. This prevents downstream coding agents from misinterpreting field
> descriptions as database migration instructions and corrupting existing
> data structures.

Field descriptions use business-facing names from the prototype (e.g.,
"合同编号", "供应商名称"), never invented database column names (e.g.,
`contract_no`, `supplier_name`).

#### Output Sections

The `field-analysis.md` file must contain these sections:

**5.1 Page Structure**

Describe the hierarchical structure of the prototype:

- Page hierarchy and navigation tree
- Functional areas within each page (header, sidebar, main content,
  modals, drawers)
- Layout relationships between areas
- Page-to-page navigation flow

**5.2 Field Description Table**

A table covering every visible field in the prototype with 18 dimensions:

| Dimension | Description |
|-----------|-------------|
| 字段名称 | Business-facing field name as shown in prototype |
| 所属页面 | Which page this field appears on |
| 所属区域 | Which functional area within the page (e.g., form, table, filter bar, detail panel) |
| 业务含义 | What this field represents in business terms |
| 是否前端展示 | Whether the field is displayed in the UI |
| 是否后端字段 | Whether this likely requires backend storage (inferred, not asserted) |
| 是否可搜索 | Whether the field appears in search/filter areas |
| 是否可新增 | Whether the field appears in creation forms |
| 是否可编辑 | Whether the field appears as editable in edit forms |
| 是否必填 | Whether required indicators (* or validation hints) are visible |
| 填写形式 | Control type: text input, dropdown, date picker, radio, checkbox, etc. |
| 格式要求 | Visible format hints or validation patterns |
| 枚举值或数据来源 | Visible dropdown options, dictionary references, or data sources |
| 默认值 | Any visible default values or placeholder text |
| 依赖关系 | Dependencies on other fields (e.g., cascading selects) |
| 权限规则 | Any visible permission-related behavior (disabled states, hidden fields by role) |
| 置信度 | `high` / `medium` / `low` — based on the credibility priority above |
| 信息来源 | Which source provided this information (prototype annotation, requirement doc, field name inference, etc.) |

**5.3 Operation Logic**

Describe user operations visible in the prototype:

- CRUD operations per entity/page
- Button actions and their expected behaviors
- Batch operations
- Import/export operations
- Approval/workflow operations

**5.4 Field & Operation Dependency Map**

Describe dependencies between fields and operations:

- Which fields are required before an operation can proceed
- Which operations modify which fields
- Cross-page field references
- State-dependent field visibility or editability

**5.5 Preliminary Given-When-Then Scenarios**

Write initial BDD scenarios based on prototype evidence. Mark each
scenario with a confidence level:

```gherkin
# Confidence: high | medium | low
Scenario: <scenario name>
  Given <precondition from prototype evidence>
  When <user action visible in prototype>
  Then <expected outcome inferred from prototype>
```

Only write scenarios where prototype evidence provides reasonable support.
Do not invent business logic.

**5.6 Questions for PM Confirmation**

> **Do not list every field.** Only output questions for items that are:
> - Low confidence (置信度 = `low`)
> - High risk (affects data model, main flow, or permissions)
> - Conflicting (prototype shows one thing, requirement doc says another)

Design questions as **multiple-choice** where possible:

```
Q1: [P0] 「合同编号」字段的生成规则是？
  A. 用户手动输入
  B. 系统按规则自动生成（如：HT-YYYYMMDD-NNN）
  C. 从上游系统同步
  D. 其他：_______
  来源：原型显示为只读字段，但创建表单中也出现了该字段。
```

### 6. Hand Off to Later Stages

Parser artifacts and field analysis are **evidence inputs** for the next
stages. Do not present them as the final PRD.

- **To PM Question Checklist** (`proto-pm-interviewer`): pass
  `prototype-analysis.md`, `structured-data.json`,
  `completeness-report.json`, `field-analysis.md`, and any draft
  `requirements.md` or manual PRDs as context. The checklist generator
  uses these to build a printable question document for PM meetings.
- **To BDD Writer** (`bdd-engineering-prd-writer`): after the PM meeting
  and answer collection, pass all parser artifacts, `field-analysis.md`,
  the PM answer document, and any auxiliary materials. The writer produces
  the final traceable BDD engineering PRD.

The `overall_implementability` score in `completeness-report.json`
indicates how much raw evidence is available:

- **≥ 90%** — strong prototype coverage
- **75–89%** — most flows captured; PM meeting needed for gaps
- **60–74%** — skeleton captured; significant PM input required
- **< 60%** — sparse data; most requirements must come from human input

## Output File Details

### requirements.md — User-Facing Requirements Draft

Generated from parsed prototype data. This is an initial structured view,
not the final BDD engineering PRD. It follows the KOPLINK-style template
covering modules, flows, rules, data, permissions, acceptance criteria,
and implementation impact.

When information is not present in the prototype, the text states
"原型未提供，需补充" or an equivalent `unknown` statement. No backend
APIs, data tables, calculation formulas, approval chains, or permission
matrices are invented.

### prototype-analysis.md — Intermediate Parsing Report

For the PM question checklist and BDD writer stages. Contains page
inventory, interaction mapping, text/field candidates, annotation
candidates, unresolved interactions, and completeness notes. This is
context for downstream skills, not a user-facing deliverable.

### field-analysis.md — Field & Page Structure Analysis Report

Produced automatically after prototype extraction. Contains:

1. **Page structure** — hierarchical page map with functional areas
2. **Field description table** — 18-dimension field analysis
3. **Operation logic** — CRUD and workflow operations per entity
4. **Field & operation dependency map** — cross-field and cross-page
   dependencies
5. **Preliminary GWT scenarios** — initial BDD scenarios with confidence
6. **Questions for PM** — low-confidence, high-risk, and conflicting items
   formatted as multiple-choice questions

This report describes prototype UI fields only. It does **not** map to
database columns or backend schema.

### structured-data.json — Minimum Schema

```json
{
  "tool_info": { "tool_type": "mockitt", "project_name": "..." },
  "pages": [{ "page_id": "...", "page_name": "...", "estimated_route": "..." }],
  "interactions": [{ "source_component": "...", "interaction_type": "navigate|back|modal|state_change", "target_page": "...", "target_type": "page|modal|history|state_change|unknown", "target_id": "...", "target_name": "...", "confidence": "fact|inferred|unknown" }],
  "texts": [{ "component_name": "...", "text_content": "...", "field": "N|b/#RRGGBB|rtS" }],
  "business_rules": [{ "rule_text": "...", "source": "annotation" }],
  "unresolved": [{ "source_component": "...", "raw_target_id": "..." }],
  "completeness": { "overall_implementability": 0.0 }
}
```

### completeness-report.json — Minimum Schema

```json
{
  "scores": { "page_coverage": 0.0, "interaction_mapping": 0.0, "overall_implementability": 0.0 },
  "details": { "total_pages": 0, "resolved_interactions": 0, "unresolved_targets": 0 },
  "assessment": "independent|mostly_independent|partial|insufficient"
}
```

## MVP Limitation

This MVP supports **pure-data Mockitt exports only**. It does **not**
support:

- Axure, Figma, Sketch, or other design tools
- Online prototype URLs
- Browser rendering or visual model analysis

If you need those features, request them explicitly — they are outside the
current scope.
