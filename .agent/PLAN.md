# Engineering Plan

This document is owned by Codex. Convert the specification and architecture
into sequenced worker-sized tasks.

## Milestones

- M1: Pure-data Mockitt MVP.
  - Skill folder exists.
  - Python package and CLI exist.
  - Synthetic Mockitt fixture converts into `requirements.md`,
    `structured-data.json`, and `completeness-report.json`.
- M2: Mockitt hardening on real exports.
  - Parser handles larger data files, alternate wrappers, duplicate page names,
    and common malformed records.
  - Output can be reconciled against raw counts.
- M3: Three-skill workflow usability.
  - The parser skill gives a fresh agent enough procedure to run, inspect, and
    hand off parser artifacts without loading the original product brief.
  - Dedicated PM interview and BDD engineering PRD writer skills exist with
    concise instructions, templates, evidence boundaries, and tests.
  - The suite clearly separates parsed facts, PM-confirmed decisions, missing
    background context, and final engineering requirements.
- M4: Additional adapters.
  - Axure probe/unpack support.
  - Figma or HTML fallback support, only after sample fixtures or stable format
    evidence are available.
- M5: Optional visual enhancement.
  - Browser rendering and vision-model observations are added behind an explicit
    opt-in flag.

## Task Sequence

1. `TASK-001`: Implement the pure-data Mockitt MVP scaffold and end-to-end
   synthetic fixture flow.
2. `TASK-002`: Fix review issues from `TASK-001`, including CLI importability,
   probe ordering, missing unpack tests, skill documentation accuracy, and
   repository hygiene.
3. `TASK-003`: Make package importability deterministic by moving away from the
   fragile `src/` editable-path layout.
4. `TASK-004`: Make `uv run pytest` pass in pytest console-script mode while
   preserving the accepted CLI command behavior.
5. `TASK-005`: Harden Mockitt parsing against realistic export variants,
   including archive input, larger files, malformed records, and duplicate page
   names.
6. `TASK-006`: Expand the repository from a parser skill into a three-skill
   workflow by adding PM interviewer and BDD engineering PRD writer skill
   folders, templates, and static tests while preserving parser behavior.
7. `TASK-007`: Add reconciliation/reporting features for raw counts, unresolved
   target analysis, and page-level drilldown summaries.
8. `TASK-008`: Add one non-Mockitt adapter only after Codex supplies a fixture or
   exact source format decision.
9. `TASK-009`: Add optional visual enhancement only after the pure-data path is
   accepted and the user confirms browser/vision dependencies.

## Dependency Order

- `TASK-001` is required before all other tasks.
- `TASK-002` depends on the initial MVP from `TASK-001`.
- `TASK-003` depends on the review fixes from `TASK-002`.
- `TASK-004` depends on the package layout from `TASK-003`.
- `TASK-005` depends on the accepted CLI, parser, and tests from `TASK-004`.
- `TASK-006` depends on a working parser CLI so interview and writer skills can
  reference real parser outputs.
- `TASK-007` depends on stable extraction output shape from `TASK-005`.
- `TASK-008` and `TASK-009` are independent of each other but both depend on the
  pipeline boundaries established in `TASK-001`.

## Risk List

- R-001: Mockitt data wrappers may differ from the source brief.
  - Likelihood: medium.
  - Impact: high.
  - Mitigation: keep probe/unpack modular, log wrapper detection, and preserve
    raw parse failures in output.
- R-002: Synthetic fixtures may overfit the parser.
  - Likelihood: medium.
  - Impact: medium.
  - Mitigation: `TASK-002` must use realistic fixtures or user-provided exports
    before broad acceptance.
- R-003: Page ownership for components may be ambiguous in raw Mockitt data.
  - Likelihood: high.
  - Impact: medium.
  - Mitigation: output page-level facts when resolvable and preserve unknown page
    association when not resolvable.
- R-004: The generated PRD may imply backend behavior unavailable in prototypes.
  - Likelihood: medium.
  - Impact: high.
  - Mitigation: require `fact`, `inferred`, and `unknown` labels and include an
    unknowns section; final BDD PRD requirements must map to source evidence or
    PM confirmation.
- R-005: Worker may expand into Axure/Figma/visual scope.
  - Likelihood: medium.
  - Impact: high.
  - Mitigation: keep `CURRENT_TASK.md` allowed files and requirements tightly
    scoped.

## Test Plan

- Required on every implementation task unless explicitly scoped otherwise:
  - `uv run pytest`
  - `uv run python3 -m proto_to_requirement.cli --help`
- For `TASK-001`, tests must include:
  - unit tests for probe, unpack, normalize, extract, render
  - CLI integration test against a synthetic Mockitt fixture
  - assertions that all three output files are created
- For later real-export hardening tasks:
  - count reconciliation tests
  - malformed record tests
  - archive input tests

## Rollback Strategy

- Revert individual implementation files from the relevant worker task if
  acceptance fails.
- Keep Codex-owned planning docs unchanged unless the failure reveals a product
  or architecture decision that must be revised.
- Because the MVP is local-file only and has no persistent external side effects,
  rollback is limited to removing generated package, tests, and skill resources.

## Definition Of Done

- Codex has accepted all required worker tasks for M1.
- `uv run pytest` passes.
- `uv run python3 -m proto_to_requirement.cli --help` passes.
- A synthetic Mockitt fixture produces `requirements.md`,
  `structured-data.json`, and `completeness-report.json`.
- The generated PRD includes the ten required sections and clear uncertainty
  labels.
- `proto-to-requirement/SKILL.md` is concise, discoverable, and does not require
  the original brief to operate the parser workflow.
- `proto-pm-interviewer/SKILL.md` and `bdd-engineering-prd-writer/SKILL.md` are
  concise, discoverable, and validate the PM interview and BDD writing stages.
- The final workflow can be explained as: parser report -> PM interview report
  -> evidence-backed BDD engineering PRD for coding agents.
