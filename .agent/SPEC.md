# Product Specification

This document is owned by Codex. Establish product behavior here before
assigning implementation work.

## Product Goal

Build a Codex/Claude-compatible skill suite that turns prototype evidence and
human product confirmation into an engineering-ready BDD PRD. The suite has
three bounded skills:

1. Prototype parsing: parse an offline Mockitt/MoDao export and produce a
   prototype analysis report plus structured evidence.
2. PM interview: convert parser findings and auxiliary materials into a focused
   product-manager interview, especially around permissions, change boundaries,
   business logic, exceptions, and missing decisions.
3. BDD engineering PRD writing: combine parser evidence, PM-confirmed answers,
   and any manual PRD/supporting materials into a fact-supported BDD PRD that a
   coding agent can use directly for engineering planning and implementation.

The implemented first release is a pure-data Mockitt/MoDao parser MVP: it reads
a local Mockitt export directory or archive, extracts page, interaction, text,
and annotation facts, and writes a Markdown requirements draft plus structured
JSON outputs. The next release must make the three-skill workflow explicit and
move interview/BDD-writing contracts into their own discoverable skills.

The source product brief is
`proto-to-requirement-skill-需求规格说明书.md`. This file narrows that brief into
the MVP and later milestones.

## User Stories

- As a product manager, I can point the workflow at a Mockitt export and get a
  readable requirements document without manually clicking through every page.
- As a technical lead, I can give the generated structured data and Markdown PRD
  to an implementation worker as a reliable starting point for coding.
- As a QA engineer, I can inspect page-to-page interaction mappings and unresolved
  targets to design navigation and state tests.
- As a product analyst, I can use the parser report to interview a PM with
  targeted questions instead of asking broad, unstructured requirement questions.
- As an implementation lead, I can require that every BDD PRD statement is backed
  by either prototype/manual-document evidence or an explicit PM confirmation.

## Functional Requirements

- FR-001: The repository must contain a discoverable skill folder
  `proto-to-requirement/` with a required `SKILL.md`.
- FR-002: The skill must document when to use it, required inputs, output files,
  uncertainty labels, and the pure-data MVP limitation.
- FR-003: The Python implementation must be managed with `uv` and executable
  through `uv run`; use `python3` commands, not `python`.
- FR-004: The MVP must accept a local prototype directory. Archive input support
  is desirable after the directory path flow works.
- FR-005: The format probe must identify Mockitt exports by `mb-proto2/` and
  `extra/data.*.js` signatures, locating the likely primary data file and config
  data file.
- FR-006: The unpacker must parse JS assignment wrappers, raw JSON, base64 text,
  gzip/base64 payloads, and line-delimited `id<TAB>{json}` records.
- FR-007: Component IDs must be normalized for cross-reference lookup, including
  known Mockitt suffixes such as trailing ` .` and ` ,`.
- FR-008: The extractor must produce a page list with page IDs, page names, state
  variant IDs, and component counts when available.
- FR-009: The extractor must map interactions from component `I` fields into
  source component, interaction type, target page or unresolved target ID, and
  confidence.
- FR-010: The extractor must collect visible text from component names, visible
  text fields such as `b/#RRGGBB`, and rich text fields such as `rtS`.
- FR-011: The extractor must collect annotation-like components as business rule
  candidates.
- FR-012: The renderer must write `requirements.md`, `structured-data.json`, and
  `completeness-report.json` into an output directory.
- FR-013: The Markdown requirements document must include ten standard sections:
  overview, prototype inventory, page catalog, interaction map, page details,
  forms and inputs, tables and lists, business rules, unknowns and assumptions,
  and completeness assessment.
- FR-014: The structured JSON must preserve source evidence and uncertainty using
  `fact`, `inferred`, and `unknown` labels.
- FR-015: The completeness report must score page coverage, interaction mapping,
  text extraction, business rule extraction, unknown rate, and overall
  implementability.
- FR-016: Failed parsing or unresolved references must not crash the workflow when
  partial output can still be produced; unresolved items must be reported.
- FR-017: The repository must expose three skill boundaries: prototype parsing,
  PM interviewing, and BDD engineering PRD writing.
- FR-018: The prototype parsing skill must identify itself as the parser stage
  and hand off `prototype-analysis.md`, `structured-data.json`,
  `completeness-report.json`, and any draft PRD/manual material to later stages.
- FR-019: The PM interview skill must define inputs, question-generation rules,
  interview-report structure, answer source labels, and priority levels for
  P0/P1/P2 confirmation items.
- FR-020: PM interview questions must prioritize permissions, change boundaries,
  business logic, state transitions, data ownership, exception flows, editability,
  approval/revoke behavior, and missing background material.
- FR-021: The PM interview report must distinguish confirmed decisions, rejected
  assumptions, unanswered questions, missing context, and follow-up owners.
- FR-022: The BDD writer skill must define how to combine parser evidence, PM
  interview answers, manual PRDs, and supporting materials into an
  engineering-ready PRD.
- FR-023: The BDD PRD contract must require evidence mapping and human
  confirmation mapping, and must prevent unconfirmed assumptions from becoming
  acceptance criteria.
- FR-024: The BDD PRD must include Feature / Rule / Scenario sections with
  Given / When / Then acceptance checks where behavior is sufficiently confirmed.
- FR-025: The BDD PRD must tell coding agents to inspect the target repository
  before adding or renaming fields, tables, enums, API routes, permissions,
  jobs, messages, templates, external services, or data migrations.

## Non-Functional Requirements

- NFR-001: The MVP must run without browser automation, visual model APIs, or
  external prototype services.
- NFR-002: The implementation must be deterministic for the same input directory.
- NFR-003: Unit tests must cover format probing, data unpacking, ID normalization,
  page extraction, interaction extraction, text extraction, rendering, and CLI
  execution on a synthetic Mockitt fixture.
- NFR-004: The code should separate probing, unpacking, extraction, rendering, and
  scoring so later Axure/Figma/visual adapters can be added without rewriting the
  Mockitt path.
- NFR-005: The CLI should emit concise errors and write detailed unresolved or
  skipped items into output JSON rather than hiding them.

## Constraints

- Use `python3` command references and `uv` for dependency management.
- The first implementation must stay local-file only. No online Figma API,
  browser rendering, or vision model integration belongs in MVP scope.
- The skill file name is `SKILL.md` to match Codex skill discovery, even though
  the source brief mentions `skill.md`.
- Worker tasks must edit only files listed in `.agent/CURRENT_TASK.md`.

## Edge Cases

- Unknown export format: write a probe result with `tool_type: generic` or
  `unknown`, report unsupported status, and avoid pretending extraction worked.
- Multiple `data.*.js` files: choose the largest likely primary data file and
  retain all candidates in probe metadata.
- Data file cannot be decompressed: retain the failure reason and stop before
  extraction with a user-facing error.
- Line-delimited component records contain malformed JSON: skip only the malformed
  record, record the failure, and continue.
- Interaction target cannot be resolved: preserve the raw target ID and mark the
  target as `unknown`.
- Page names are duplicated: group variants under the same display name while
  preserving unique page IDs.
- Text extraction yields very little content: warn in completeness output because
  this likely signals a parser mismatch.

## Acceptance Criteria

- AC-001: `uv run pytest` passes.
- AC-002: `uv run python3 -m proto_to_requirement.cli --help` exits successfully.
- AC-003: A synthetic Mockitt fixture can be converted end-to-end into the three
  required output files.
- AC-004: The generated `structured-data.json` includes at least pages,
  interactions, text entries, business rules, unresolved items, and completeness.
- AC-005: The generated Markdown PRD contains the ten required sections and marks
  inferred or unknown information explicitly.
- AC-006: The skill instructions in `proto-to-requirement/SKILL.md` are concise
  enough to guide a fresh agent without requiring the original source brief.
- AC-007: The parser, PM interviewer, and BDD writer skills are discoverable as
  separate skill folders with valid `SKILL.md` frontmatter.
- AC-008: The parser skill no longer treats a raw parsing draft as the final BDD
  engineering PRD; it clearly hands evidence to the interview and writer stages.
- AC-009: The PM interviewer skill can be validated from static tests that check
  for permission, change-boundary, business-logic, exception, missing-context,
  and answer-source requirements.
- AC-010: The BDD writer skill can be validated from static tests that check for
  BDD sections, evidence mapping, human confirmation mapping, P0/P1/P2 treatment,
  repository-inspection guardrails, and no invented backend contracts.
- AC-011: `uv run pytest` continues to pass after the skill-suite expansion.
- AC-012: The existing parser CLI behavior and real Mockitt export support remain
  intact while the new skill resources are added.

## Non-Goals

- Visual screenshot analysis and vision model prompts are not part of the MVP.
- Axure, Figma, Sketch, and generic HTML extraction are not part of the first
  worker task.
- Backend API schema discovery, permission matrices, and complete validation
  rules are out of scope for the parser because prototypes do not reliably
  contain them. The PM interview and BDD writer stages may ask for or document
  these facts only when they are supported by human confirmation, manual PRDs,
  target repository evidence, or explicit external materials.
- Installing the skill into `~/.codex/skills` is out of scope for this repo
  unless the user asks for installation.
