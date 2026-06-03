"""Static tests for the three-skill workflow suite.

These tests validate skill boundaries, required contract terms, and
discoverability — no network access or external services needed.
"""

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Skill paths
# ---------------------------------------------------------------------------

PARSER_SKILL = Path("proto-to-requirement/SKILL.md")
INTERVIEWER_SKILL = Path("proto-pm-interviewer/SKILL.md")
BDD_WRITER_SKILL = Path("bdd-engineering-prd-writer/SKILL.md")

ALL_SKILL_PATHS = [PARSER_SKILL, INTERVIEWER_SKILL, BDD_WRITER_SKILL]


def _read_skill(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> dict:
    """Parse simple YAML frontmatter (name, description) without PyYAML.

    Handles single-line values and folded block scalars (``key: >``).
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    assert m is not None, "Missing YAML frontmatter"
    fm_text = m.group(1)
    result = {}
    current_key = None
    current_value_lines = []
    for line in fm_text.split("\n"):
        kv = re.match(r"^(\w[\w-]*)\s*:\s*>(.*)", line)
        if kv:
            if current_key:
                result[current_key] = " ".join(current_value_lines).strip()
            current_key = kv.group(1)
            current_value_lines = [kv.group(2).strip()] if kv.group(2).strip() else []
            continue
        if current_key and re.match(r"^\s{2,}\S", line):
            current_value_lines.append(line.strip())
            continue
        if current_key:
            result[current_key] = " ".join(current_value_lines).strip()
            current_key = None
            current_value_lines = []
        kv = re.match(r"^(\w[\w-]*)\s*:\s*(.+)", line)
        if kv:
            result[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    if current_key:
        result[current_key] = " ".join(current_value_lines).strip()
    return result


# ---------------------------------------------------------------------------
# Discoverability: every skill folder has a valid SKILL.md with frontmatter
# ---------------------------------------------------------------------------

def test_all_three_skill_folders_exist():
    for p in ALL_SKILL_PATHS:
        assert p.is_file(), f"Missing skill file: {p}"


def test_all_three_have_yaml_frontmatter():
    for p in ALL_SKILL_PATHS:
        content = _read_skill(p)
        fm = _parse_frontmatter(content)
        assert "name" in fm, f"{p}: frontmatter missing 'name'"
        assert "description" in fm, f"{p}: frontmatter missing 'description'"


# ---------------------------------------------------------------------------
# Parser skill — stage-boundary tests
# ---------------------------------------------------------------------------

def test_parser_skill_identifies_as_parser_stage():
    content = _read_skill(PARSER_SKILL)
    assert "Stage 1" in content or "parser stage" in content.lower()
    assert "prototype-analysis.md" in content
    assert "structured-data.json" in content
    assert "completeness-report.json" in content


def test_parser_skill_hands_off_to_interviewer():
    content = _read_skill(PARSER_SKILL)
    assert "proto-pm-interviewer" in content


def test_parser_skill_hands_off_to_bdd_writer():
    content = _read_skill(PARSER_SKILL)
    assert "bdd-engineering-prd-writer" in content


def test_parser_skill_does_not_claim_final_bdd_prd_as_own_output():
    content = _read_skill(PARSER_SKILL)
    fm = _parse_frontmatter(content)
    desc = fm.get("description", "")
    assert "stage 1" in desc.lower() or "parser" in desc.lower()


def test_parser_skill_preserves_cli_command():
    content = _read_skill(PARSER_SKILL)
    assert "uv run python3 -m proto_to_requirement.cli" in content


# ---------------------------------------------------------------------------
# PM interviewer skill — contract-term tests
# ---------------------------------------------------------------------------

def test_interviewer_skill_covers_required_categories():
    content = _read_skill(INTERVIEWER_SKILL)
    categories = [
        "Permissions",
        "Modification",
        "Edit Boundaries",
        "Business Logic",
        "State Transitions",
        "Exception Flows",
        "Data Ownership",
        "Approval",
        "Revoke",
        "Missing Background",
    ]
    for cat in categories:
        # Match case-insensitive, allowing for heading/section formatting
        assert cat.lower() in content.lower(), (
            f"Interviewer skill missing category: {cat}"
        )


def test_interviewer_skill_defines_answer_labels():
    content = _read_skill(INTERVIEWER_SKILL)
    labels = [
        "PM confirmed",
        "source-derived",
        "Rejected",
        "Unanswered",
        "Missing context",
    ]
    for label in labels:
        assert label.lower() in content.lower(), (
            f"Interviewer skill missing answer label: {label}"
        )


def test_interviewer_skill_defines_priority_levels():
    content = _read_skill(INTERVIEWER_SKILL)
    assert "P0" in content
    assert "P1" in content
    assert "P2" in content


def test_interviewer_skill_has_non_invention_rule():
    content = _read_skill(INTERVIEWER_SKILL)
    assert "not invent" in content.lower(), (
        "Interviewer skill must forbid inventing PM answers"
    )


def test_interviewer_skill_defines_outputs():
    content = _read_skill(INTERVIEWER_SKILL)
    assert "question" in content.lower()
    assert "interview report" in content.lower()


def test_interviewer_skill_defines_required_inputs():
    content = _read_skill(INTERVIEWER_SKILL)
    assert (
        "prototype-analysis.md" in content
        or "structured-data.json" in content
    )


def test_interviewer_skill_names_parser_as_upstream():
    content = _read_skill(INTERVIEWER_SKILL)
    assert "proto-to-requirement" in content


def test_interviewer_skill_names_bdd_writer_as_downstream():
    content = _read_skill(INTERVIEWER_SKILL)
    assert "bdd-engineering-prd-writer" in content


# ---------------------------------------------------------------------------
# BDD writer skill — contract-term tests
# ---------------------------------------------------------------------------

def test_bdd_writer_skill_uses_feature_rule_scenario_structure():
    content = _read_skill(BDD_WRITER_SKILL)
    assert "Feature" in content
    assert "Rule" in content
    assert "Scenario" in content
    assert "Given" in content
    assert "When" in content
    assert "Then" in content


def test_bdd_writer_skill_defines_evidence_mapping():
    content = _read_skill(BDD_WRITER_SKILL)
    assert "evidence" in content.lower()


def test_bdd_writer_skill_defines_human_confirmation_mapping():
    content = _read_skill(BDD_WRITER_SKILL)
    assert "PM confirmed" in content or "human confirmation" in content.lower()


def test_bdd_writer_skill_defines_p0_p1_p2_treatment():
    content = _read_skill(BDD_WRITER_SKILL)
    assert "P0" in content and "P1" in content and "P2" in content


def test_bdd_writer_skill_p0_not_acceptance_criteria():
    content = _read_skill(BDD_WRITER_SKILL)
    # P0 blockers are explicitly not acceptance criteria
    p0_blocks = "P0" in content and "block" in content.lower()
    p0_not_ac = (
        "P0" in content
        and "not" in content.lower()
        and "acceptance criteria" in content.lower()
    )
    assert p0_blocks or p0_not_ac, (
        "BDD writer must state P0 blockers cannot be acceptance criteria"
    )


def test_bdd_writer_skill_has_repository_inspection_guardrails():
    content = _read_skill(BDD_WRITER_SKILL)
    guardrail_terms = [
        "repository",
        "inspect",
        "existing",
        "add",
        "rename",
        "field",
    ]
    matches = sum(1 for t in guardrail_terms if t.lower() in content.lower())
    assert matches >= 4, (
        f"BDD writer must include repository inspection guardrails; "
        f"matched {matches}/6 terms"
    )


def test_bdd_writer_skill_forbids_page_inventory_substitution():
    content = _read_skill(BDD_WRITER_SKILL)
    has_page = "page" in content.lower()
    has_inventory = (
        "inventor" in content.lower() or "component" in content.lower()
    )
    has_no_page = "no page" in content.lower()
    assert (has_page and has_inventory) or has_no_page, (
        "BDD writer must forbid substituting page/component inventories "
        "for business logic"
    )


def test_bdd_writer_skill_has_non_invention_rule():
    content = _read_skill(BDD_WRITER_SKILL)
    assert (
        "not invent" in content.lower()
        or "never invent" in content.lower()
        or "no invention" in content.lower()
    )


def test_bdd_writer_skill_defines_required_inputs():
    content = _read_skill(BDD_WRITER_SKILL)
    required_inputs = [
        "PM interview",
        "parser",
    ]
    for inp in required_inputs:
        assert inp.lower() in content.lower(), (
            f"BDD writer missing required input: {inp}"
        )


def test_bdd_writer_skill_names_parser_as_upstream():
    content = _read_skill(BDD_WRITER_SKILL)
    assert "proto-to-requirement" in content


def test_bdd_writer_skill_names_interviewer_as_upstream():
    content = _read_skill(BDD_WRITER_SKILL)
    assert "proto-pm-interviewer" in content


# ---------------------------------------------------------------------------
# Cross-skill integration tests
# ---------------------------------------------------------------------------

def test_all_skills_form_complete_workflow_chain():
    """Parser -> Interviewer -> BDD Writer chain must be documented."""
    parser = _read_skill(PARSER_SKILL)
    interviewer = _read_skill(INTERVIEWER_SKILL)
    bdd_writer = _read_skill(BDD_WRITER_SKILL)

    # Parser mentions both downstream stages
    assert "proto-pm-interviewer" in parser
    assert "bdd-engineering-prd-writer" in parser

    # Interviewer mentions upstream parser and downstream BDD writer
    assert "proto-to-requirement" in interviewer
    assert "bdd-engineering-prd-writer" in interviewer

    # BDD writer mentions both upstream stages
    assert "proto-to-requirement" in bdd_writer
    assert "proto-pm-interviewer" in bdd_writer
