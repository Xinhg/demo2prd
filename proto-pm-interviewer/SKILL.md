---
name: proto-pm-interviewer
description: >
  Stage 2 of 3: Conduct a structured product-manager interview using
  prototype parser evidence and auxiliary materials. Produces a prioritized
  question list and a PM interview report with confirmed decisions, source
  labels, and open items — without inventing answers on behalf of the PM.
triggers:
  - "interview the PM"
  - "prepare PM questions"
  - "proto PM interview"
  - "requirements interview"
  - "product manager interview"
---

# proto-pm-interviewer (Stage 2 — PM Interview)

Convert prototype parser evidence and auxiliary materials into a structured
product-manager interview. This skill asks and records — it must **not**
invent PM answers, fill gaps as confirmed requirements, or make product
decisions.

This is stage 2 of the three-stage workflow:

1. **Parser** (`proto-to-requirement`) — produces prototype evidence.
2. **PM Interviewer** (this skill) — asks targeted questions and records
   confirmed answers.
3. **BDD Writer** (`bdd-engineering-prd-writer`) — uses parser evidence and
   the PM interview report to write the final BDD engineering PRD.

## When to Use

- After the parser has produced `prototype-analysis.md`,
  `structured-data.json`, and `completeness-report.json`.
- Before writing the BDD engineering PRD — unresolved parser findings must
  be confirmed or rejected by a human product manager.
- When the parser evidence shows gaps in permissions, edit boundaries,
  business logic, state transitions, exceptions, or data ownership.

## When Not to Use

- Before prototype parsing is complete: run `proto-to-requirement` first.
- For writing the final PRD: use `bdd-engineering-prd-writer` after the
  interview report is done.
- When there is no access to a human PM: this skill requires a human
  product manager to answer questions.

## Required Input

1. **Parser evidence**: `prototype-analysis.md`, `structured-data.json`,
   `completeness-report.json` from the parser stage.
2. **Auxiliary materials** (optional but recommended):
   - Manual PRDs or requirement documents
   - Screenshots, flowcharts, meeting notes
   - Existing system documentation
   - Draft `requirements.md` from the parser stage

## Output

Two artifacts are produced:

| Output | Description |
|--------|-------------|
| Interview Question List | Prioritized P0/P1/P2 questions organized by category, ready for a PM interview session |
| PM Interview Report | Structured report recording PM answers with source labels, unresolved items, and follow-up owners |

The question list is an internal backlog for the interview, not a prompt to
dump every question to the PM at once. During a live interview, maintain an
interview record and ask one question per turn.

## Question Categories

Questions are organized into these categories. Every category must be
covered when parser evidence or auxiliary materials suggest a gap:

### Permissions
- Who can view, create, edit, delete, approve, and revoke each entity?
- Are there role-based, data-scope, or conditional permission rules?
- Are there tenant/organization-level boundaries?

### Modification / Edit Boundaries
- Which fields are editable at which lifecycle stage?
- Are there immutable fields after creation or after a specific state?
- Can users edit historical/archived records?

### Business Logic
- What are the primary business flows and their steps?
- What calculations, validations, or transformations apply?
- Are there cross-entity consistency rules?

### State Transitions
- What are the valid states for each entity?
- Which transitions are allowed? Which are irreversible?
- What triggers state changes (user action, system event, schedule)?

### Exception Flows
- What happens on duplicate submission, timeout, or concurrent edit?
- What are the withdrawal, revoke, and rollback behaviors?
- How are partial failures handled?

### Data Ownership
- Who owns each data entity? Can ownership transfer?
- Are there delegation or proxy rules?
- What data is shared or visible across organizational boundaries?

### Approval / Revoke Behavior
- Which operations require approval? What is the approval chain?
- Can approvals be delegated, escalated, or recalled?
- What happens when an approved item is revoked?

### Missing Background Materials
- Are there referenced documents, templates, or external specs not yet
  provided?
- Are there upstream or downstream systems whose contracts are undefined?
- Are there regulatory, compliance, or legal constraints not documented?

## Priority Levels

Every question is assigned a priority:

| Level | Meaning | Engineering Impact |
|-------|---------|-------------------|
| P0 | Blocks data model, API contract, or main flow design | Must confirm before development |
| P1 | Affects boundary rules, error handling, or UX detail | Should confirm before or early in development |
| P2 | Affects copy, defaults, configuration, or polish | Can defer to later iterations |

## Answer / Source Labels

Every recorded answer must carry one of these labels:

| Label | Meaning |
|-------|---------|
| PM confirmed | Explicitly confirmed by the product manager |
| Source-derived | Inferred directly from parser evidence, manual PRDs, or existing system docs |
| Rejected | Explicitly rejected by the PM; the assumption is wrong |
| Unanswered | Question was asked but not yet answered |
| Missing context | Cannot be answered without additional materials or stakeholders |

## Interview Workflow

### 1. Gather Inputs

Collect parser artifacts and any auxiliary materials. Identify the
completeness gaps from `completeness-report.json`.

### 2. Generate Question List

For each question category, inspect parser evidence and auxiliary
materials. Generate questions where:

- The prototype shows a feature but not its rules or constraints.
- Interactions exist but target pages have no business logic description.
- Permissions, validations, or state transitions are referenced but not
  defined.
- Data is displayed but ownership, source, or mutability is unclear.
- Annotations hint at business rules without full specification.

Prioritize questions with P0/P1/P2 based on the definitions above.

Create an interview record before asking the first question. The record must
include the question backlog and enough state for a new agent to continue the
interview without memory of prior turns:

| ID | Priority | Category | Evidence | Question | Decision Needed | Impact | Status | PM Answer | Result |
|----|----------|----------|----------|----------|-----------------|--------|--------|-----------|--------|

Allowed statuses:

- Not asked
- Confirmed
- Partially confirmed
- Still open
- Needs repository check
- Needs external material
- Not applicable

### 3. Conduct the Interview

Conduct the interview incrementally. Do not present the full backlog as
questions. For each turn:

- Pick the next question from the backlog by priority: P0 first, then P1,
  then P2. Within the same priority, ask questions that affect data models,
  API contracts, main flows, templates, external dependencies, and
  permissions before lower-impact UX details.
- Ask one question per turn. The question must be short, specific, and able
  to close one decision point.
- State only the minimum prototype evidence needed for context.
- Record the answer verbatim with the appropriate source label.
- After each PM answer, update the interview record before asking anything
  else.
- Mark the current item as confirmed, partially confirmed, still open,
  needs repository check, needs external material, rejected, or not
  applicable.
- If the answer creates a new blocker, add a new backlog item and reprioritize
  the backlog.
- If the PM defers or doesn't know, label as `Unanswered` and assign a
  follow-up owner.
- Continue until all P0 questions are confirmed, rejected as not applicable,
  or converted into explicit follow-up blockers with owners.

Once all P0 questions are no longer open, the interview has reached the
threshold for the next stage. Recommend handing the parser artifacts and
interview report to `bdd-engineering-prd-writer`, but allow the PM to
continue the interview to complete P1/P2 items and enrich the record.

Each live-interview response must use this structure:

1. **Interview record update**: summarize what changed in the record.
2. **Threshold status**: state how many P0 items remain open and whether the
   threshold for the next stage has been reached.
3. **Next question**: ask one question only, or ask whether to continue the
   interview after the P0 threshold is reached.

### 4. Produce the Interview Report

Write a structured PM interview report containing:

- **Summary**: overall confirmation status, count of P0/P1/P2 items, and
  remaining open items.
- **Confirmed Decisions**: PM-confirmed answers that now become
  requirements.
- **Rejected Assumptions**: parser inferences or assumptions the PM
  explicitly rejected.
- **Unanswered Questions**: open items with P0/P1/P2 priority and
  follow-up owners.
- **Missing Context**: items blocked by unavailable materials or
  stakeholders.

### 5. Hand Off to BDD Writer

Pass the PM interview report, parser artifacts, and all auxiliary materials
to `bdd-engineering-prd-writer` for the final BDD engineering PRD.

## Rules

- **Do not invent PM answers.** If a question is unanswered, record it as
  `Unanswered` — never fill in a plausible answer.
- **Do not skip categories.** If a category has no questions because the
  material is silent, note that explicitly (e.g., "Permissions: no
  permission-related content found in parser evidence or auxiliary
  materials").
- **Distinguish parser inference from PM confirmation.** A fact labeled
  `inferred` by the parser becomes `PM confirmed` or `Rejected` only after
  the PM explicitly addresses it.
- **P0 items must be resolved before the BDD writer can produce a
  development-ready PRD.** Flag unresolved P0 items prominently.
