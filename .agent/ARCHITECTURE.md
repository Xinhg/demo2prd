# Architecture

This document is owned by Codex. Keep implementation boundaries and decisions
clear enough that worker tasks do not require architectural invention.

## System Overview

The repository produces two layers:

1. A workflow skill suite with one folder per stage:
   - `proto-to-requirement/`: prototype parsing and extraction evidence.
   - `proto-pm-interviewer/`: PM interview preparation and report writing.
   - `bdd-engineering-prd-writer/`: final BDD engineering PRD writing.
2. A Python package, `proto_to_requirement`, that performs deterministic local
   extraction and rendering for the Mockitt parser MVP.

The MVP pipeline is:

```text
prototype directory
  -> format probe
  -> data unpack
  -> component index
  -> page / interaction / text / annotation extraction
  -> structured data merge
  -> prototype-analysis.md + draft requirements.md + JSON outputs + completeness report
  -> PM interview questions/report
  -> evidence-backed BDD engineering PRD
```

## Module Boundaries

- `proto-to-requirement/SKILL.md`: parser-stage agent instructions. It should
  stay concise, point to the CLI for deterministic extraction, and hand off
  parser artifacts to the interview and BDD writer skills.
- `proto-to-requirement/scripts/`: optional thin command wrappers only. Business
  logic should live in `proto_to_requirement/`.
- `proto-pm-interviewer/SKILL.md`: interview-stage instructions. It turns
  parser artifacts, manual PRDs, and system context into prioritized PM
  questions and a structured interview report. It must not answer questions on
  behalf of the PM.
- `proto-pm-interviewer/templates/`: report and question-list templates used by
  agents when composing interview artifacts.
- `bdd-engineering-prd-writer/SKILL.md`: writing-stage instructions. It turns
  parser evidence, PM-confirmed answers, and auxiliary materials into the final
  BDD engineering PRD.
- `bdd-engineering-prd-writer/templates/` and `references/`: reusable BDD PRD
  outline, evidence-map guidance, and engineering guardrails.
- `proto_to_requirement/cli.py`: argument parsing, input/output path
  orchestration, and user-facing exit codes.
- `proto_to_requirement/probe.py`: identify export type, data candidates,
  wrappers, encoding, and compression hints.
- `proto_to_requirement/unpack.py`: read data files, unwrap JS assignments,
  decode/decompress, and parse JSON or line-delimited component records.
- `proto_to_requirement/models.py`: dataclasses or typed dictionaries for
  probe results, components, extracted facts, structured output, and completeness.
- `proto_to_requirement/normalize.py`: ID normalization and utility functions
  shared by extractors.
- `proto_to_requirement/extract.py`: pure-data Mockitt extraction for pages,
  interactions, texts, annotations, and unresolved references.
- `proto_to_requirement/render.py`: write `requirements.md`,
  `structured-data.json`, and `completeness-report.json`.
- `tests/`: unit and integration tests, including synthetic Mockitt fixtures.

## Data Flow

- Input trust boundary: local prototype files are untrusted. The implementation
  reads them as data and must not execute JS content.
- Probe output: a JSON-serializable object containing `tool_type`, candidate
  data files, selected primary/config files, detected wrapper, encoding,
  compression, and warnings.
- Unpack output: a component index keyed by normalized ID, raw component count,
  parse failures, and optional metadata.
- Extraction output: page catalog, interactions, text entries, business rule
  candidates, unresolved references, warnings, and source counts.
- Render output: three files in the requested output directory.
- Interview output: an interview question list and a PM interview report. Every
  answer must state whether it is confirmed by PM, derived from source material,
  rejected, unanswered, or blocked by missing context.
- BDD PRD output: a final engineering PRD with evidence mapping, confirmation
  mapping, BDD Feature/Rule/Scenario sections, P0/P1/P2 open items, and coding
  agent guardrails.

## File Ownership

- Codex-owned planner files:
  - `.agent/SPEC.md`
  - `.agent/ARCHITECTURE.md`
  - `.agent/PLAN.md`
  - `.agent/REVIEW.md`
  - `.agent/CURRENT_TASK.md`
  - `AGENTS.md`
- Worker-writable implementation files are only those listed in
  `.agent/CURRENT_TASK.md`.
- `.agent/WORK_LOG.md` and `.agent/BLOCKERS.md` are append-only worker reporting
  files.

## External Dependencies

- Required:
  - Python 3.10+
  - `uv`
  - Python standard library modules for JSON, gzip, zlib, base64, pathlib, and
    argparse
- Test-only:
  - `pytest`
- Not allowed in MVP:
  - Browser automation
  - Vision model APIs
  - Network calls to prototype services

## Error Handling

- Probe failures return explicit unsupported/unknown results instead of raising
  opaque exceptions.
- Decode/decompress attempts should be tried in a fixed order: raw text, JS
  string unwrap, base64, gzip, zlib, raw zlib, and brotli only if the standard
  runtime supports it.
- Malformed records are recorded in warnings and skipped individually.
- Unresolved targets and orphan interactions remain in output with raw IDs.
- CLI exits non-zero only when no meaningful output can be produced, such as
  missing input path, unreadable primary data file, or completely unsupported
  input.

## Testing Strategy

- Unit tests:
  - format probe recognizes Mockitt signatures and candidate ordering
  - JS assignment/string unwrapping and gzip/base64 decoding
  - line-delimited component record parsing
  - ID suffix normalization
  - page, interaction, text, and annotation extraction
  - completeness scoring
- Integration tests:
  - synthetic Mockitt fixture runs through the CLI and writes all three outputs
  - unresolved interaction target is preserved and counted
- Manual checks:
  - `uv run python3 -m proto_to_requirement.cli --help`
  - inspect generated Markdown sections for ten-section structure

## Architecture Decisions

- AD-001: Build a Python package plus skill folder instead of putting all logic
  into standalone scripts. Rationale: extraction logic needs tests and later
  adapters; thin scripts keep the skill easy to use without duplicating code.
- AD-002: The first release supports only Mockitt pure-data extraction. Rationale:
  the source brief has concrete Mockitt format evidence; Axure/Figma/visual
  support would force speculative architecture and weak acceptance criteria.
- AD-003: Use `SKILL.md` as the skill entrypoint. Rationale: Codex skill
  discovery requires uppercase `SKILL.md`.
- AD-004: Treat design files as data, never executable code. Rationale:
  prototype exports can contain JavaScript wrappers, but executing them would be
  unsafe and unnecessary for extraction.
- AD-005: Use a top-level `proto_to_requirement/` package for the MVP. Rationale:
  the required command is `uv run python3 -m proto_to_requirement.cli --help`,
  and this environment did not reliably process editable `.pth` files for a
  `src/` layout.
- AD-006: Keep interview and BDD-writing as separate skill folders instead of
  expanding the parser skill. Rationale: parser evidence, PM confirmation, and
  engineering specification writing have different authority boundaries and
  failure modes.
- AD-007: Treat generated parser `requirements.md` as a draft/user-facing
  extraction product, not as the final BDD engineering PRD. Rationale: backend
  rules, permission matrices, edit boundaries, and implementation contracts
  require human confirmation or repository evidence before they can drive coding.
