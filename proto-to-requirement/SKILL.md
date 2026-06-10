---
name: proto-to-requirement
description: >
  Stage 1 of 3: Parse a pure-data Mockitt (MoDao) prototype export into
  structured evidence artifacts. Reads a local export directory, extracts
  pages, interactions, visible text, and annotation-based business rules,
  then writes a prototype analysis report plus structured JSON outputs.
  Hands off to proto-pm-interviewer (stage 2) and bdd-engineering-prd-writer
  (stage 3) for the final BDD engineering PRD.
triggers:
  - "convert this prototype"
  - "generate requirements from Mockitt"
  - "extract PRD from prototype"
  - "proto to requirement"
---

# proto-to-requirement (Stage 1 — Prototype Parser)

Convert a local Mockitt (MoDao) prototype export into structured evidence
artifacts. This is the **parser stage** of a three-stage workflow. It
produces intermediate analysis files — not the final BDD engineering PRD.

The full workflow is:

1. **Parser** (this skill) — extract prototype evidence into
   `prototype-analysis.md`, `structured-data.json`, and
   `completeness-report.json`.
2. **PM Interviewer** (`proto-pm-interviewer`) — use parser evidence and
   auxiliary materials to conduct a structured product-manager interview
   covering permissions, edit boundaries, business logic, exceptions, and
   missing decisions.
3. **BDD Writer** (`bdd-engineering-prd-writer`) — combine parser evidence,
   PM-confirmed answers, manual PRDs, and supporting materials into a
   traceable BDD engineering PRD that coding agents can use.

This MVP is **pure-data only** — it reads exported data files without
browser automation, visual models, or online prototype access.

## When to Use

- A PM or developer has provided a Mockitt export directory (containing
  `mb-proto2/` and `extra/data.*.js`).
- You need to extract structured evidence from a prototype before a PM
  interview or BDD PRD writing session.
- You need a completeness assessment showing how much prototype information
  is captured.

## When Not to Use

- For the final BDD engineering PRD: use `bdd-engineering-prd-writer`
  (stage 3).
- For PM interview preparation: use `proto-pm-interviewer` (stage 2).
- For Axure, Figma, Sketch, or other design tools: not yet supported.
- For online prototype URLs or browser rendering: not yet supported.

## Required Input

A local directory path to an unzipped Mockitt export. The directory must
contain:

- `mb-proto2/` — prototype structure marker
- `extra/data.*.js` — at least one data file (the largest is used as
  primary)

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

### 3. Review Output Files

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

### 5. Hand Off to Later Stages

Parser artifacts are **evidence inputs** for the next stages. Do not
present them as the final PRD.

- **To PM Interviewer** (`proto-pm-interviewer`): pass
  `prototype-analysis.md`, `structured-data.json`,
  `completeness-report.json`, and any draft `requirements.md` or
  manual PRDs as context. The interviewer uses these to build targeted
  questions about permissions, edit boundaries, business logic,
  exceptions, and missing context.
- **To BDD Writer** (`bdd-engineering-prd-writer`): after the PM
  interview is done, pass all parser artifacts plus the PM interview
  report. The writer produces the final traceable BDD engineering PRD.

The `overall_implementability` score in `completeness-report.json`
indicates how much raw evidence is available:

- **≥ 90%** — strong prototype coverage
- **75–89%** — most flows captured; interview needed for gaps
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

For the PM interviewer and BDD writer stages. Contains page inventory,
interaction mapping, text/field candidates, annotation candidates,
unresolved interactions, and completeness notes. This is context for
downstream skills, not a user-facing deliverable.

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
