# Current Worker Task

This document is written by Codex. The worker implements exactly one current
task and does not edit this file.

## Task ID

`TASK-006`

## Goal

Expand the project from a working Mockitt parser skill into the intended
three-skill workflow: prototype parsing, PM interview, and BDD engineering PRD
writing.

## Context

Read these files before implementing:

1. `CLAUDE.md`
2. `.agent/SPEC.md`
3. `.agent/ARCHITECTURE.md`
4. `.agent/PLAN.md`
5. `.agent/REVIEW.md`
6. `proto-to-requirement/SKILL.md`
7. `proto-to-requirement/references/prd-writing-prompt.md`

`TASK-005` is accepted. The parser CLI supports the real Mockitt
`window["hzv5"]["flpk"]` gzip/base64 chunk format and passed the real export
thresholds. The current gap is product/workflow structure: the repository still
mostly exposes a single `proto-to-requirement` skill, while the product goal now
requires three separate stages:

1. Prototype parsing skill: parse Mockitt/MoDao prototype data and output parser
   reports/evidence.
2. PM interview skill: use parser reports and auxiliary materials to interview a
   product manager, focused on permissions, modification boundaries, business
   logic, exceptions, missing context, and human decisions.
3. BDD engineering PRD writer skill: combine parser evidence, PM-confirmed
   answers, manual PRDs, and supporting materials into a BDD PRD that coding
   agents can use for engineering planning and development.

Keep this task narrow. Do not add Axure/Figma/browser/vision support, online
prototype access, skill installation, or a new parser feature. Do not change
the accepted CLI behavior except for documentation references if needed. Use
`uv` for dependency management and use `python3` commands rather than `python`.

## Allowed files

- `proto-to-requirement/SKILL.md`
- `proto-to-requirement/references/prd-writing-prompt.md`
- `proto-pm-interviewer/**`
- `bdd-engineering-prd-writer/**`
- `tests/**`
- `.agent/WORK_LOG.md`
- `.agent/BLOCKERS.md`

## Forbidden files

These remain forbidden even if a broad allowed glob would match them.

- `.agent/SPEC.md`
- `.agent/ARCHITECTURE.md`
- `.agent/PLAN.md`
- `.agent/REVIEW.md`
- `.agent/CURRENT_TASK.md`
- `.agent/run-worker-dangerously.sh`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/**`
- `.omc/**`
- `proto_to_requirement/**`
- `pyproject.toml`
- `uv.lock`
- `.gitignore`
- `output/**`
- `proto-to-requirement-skill-需求规格说明书.md`

## Requirements

- Keep `proto-to-requirement/SKILL.md` as the prototype parser stage:
  - describe the parser output as evidence/draft material, not as the final BDD
    engineering PRD
  - preserve the existing parser CLI command
  - explicitly hand off `prototype-analysis.md`, `structured-data.json`,
    `completeness-report.json`, and any draft/manual PRD materials to the PM
    interview and BDD writer stages
  - remove or relocate BDD-writing instructions that make the parser skill look
    responsible for the final BDD PRD
- Add a new discoverable PM interview skill folder, expected path:
  - `proto-pm-interviewer/SKILL.md`
  - optional templates under `proto-pm-interviewer/templates/`
- The PM interviewer skill must define:
  - when to use it
  - required inputs
  - outputs: interview question list and PM interview report
  - priority levels P0/P1/P2
  - answer/source labels such as PM confirmed, source-derived, rejected,
    unanswered, and missing context
  - question categories for permissions, modification/edit boundaries,
    business logic, state transitions, exception flows, data ownership,
    approval/revoke behavior, and missing background materials
  - a rule that the skill asks and records questions; it must not invent PM
    answers
- Add a new discoverable BDD writer skill folder, expected path:
  - `bdd-engineering-prd-writer/SKILL.md`
  - optional references/templates under `bdd-engineering-prd-writer/`
- The BDD writer skill must define:
  - when to use it
  - required inputs: parser report/structured data, PM interview report, manual
    PRDs, and auxiliary materials
  - output: one BDD engineering PRD
  - evidence mapping and human confirmation mapping
  - P0/P1/P2 treatment, including a rule that P0 blockers cannot become
    acceptance criteria
  - Feature / Rule / Scenario structure using Given / When / Then where behavior
    is sufficiently confirmed
  - coding-agent guardrails requiring repository inspection before adding or
    renaming fields, tables, enums, API routes, permissions, external services,
    jobs, templates, messages, migrations, or data contracts
  - a rule against copying raw page/component/interaction inventories into the
    final PRD as a substitute for business logic
- Add static tests for the three-skill suite:
  - all three skill folders have a valid `SKILL.md` with YAML frontmatter
  - parser skill mentions parser-stage handoff and does not present the final
    BDD PRD as its own output
  - PM interviewer skill covers the required categories, labels, priorities, and
    non-invention rule
  - BDD writer skill covers BDD structure, evidence mapping, human confirmation,
    P0/P1/P2, repository-inspection guardrails, and non-invention rule
  - tests should not depend on network access or external services
- Update or move the existing PRD writing prompt/reference only if needed to
  make the stage boundary clear. If moved, update tests accordingly.
- Do not claim nonexistent scripts or commands in any `SKILL.md`.
- Remove generated `__pycache__` files from implementation and tests before
  stopping.

## Acceptance criteria

- `proto-to-requirement/SKILL.md` is clearly the parser-stage skill and points to
  later interview/BDD stages for final engineering PRD work.
- `proto-pm-interviewer/SKILL.md` exists and can guide a fresh agent to produce
  PM questions and a PM interview report focused on permissions, edit
  boundaries, business logic, and missing decisions.
- `bdd-engineering-prd-writer/SKILL.md` exists and can guide a fresh agent to
  produce an evidence-backed BDD engineering PRD from parser and interview
  artifacts.
- Static tests validate the three skill boundaries and core contract terms.
- Existing parser tests still pass.
- `git status --short --untracked-files=all` shows no `__pycache__` entries.
- The worker changes only allowed files.

## Required checks

- `uv run python3 -m proto_to_requirement.cli --help`
- `uv run pytest`
- `git status --short --untracked-files=all`

## Expected worker output

- Code/resource changes limited to `Allowed files`.
- An appended entry in `.agent/WORK_LOG.md`.
- An appended entry in `.agent/BLOCKERS.md` if anything prevents completion.
- Recorded results for every required check.
