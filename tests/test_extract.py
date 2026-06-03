"""Tests for extraction module."""

from proto_to_requirement.extract import (
    extract_business_rules,
    extract_interactions,
    extract_pages,
    extract_texts,
)


def make_components():
    """Return a component dict matching the synthetic fixture."""
    return {
        "rbp001": {"N": "Login Page", "T": "*"},
        "rbp002": {"N": "Dashboard", "T": "*"},
        "V001 .": {"N": "Sign In Button", "T": "]", "I": [[1, "rbp002", "", "(", ["", "rbp002", "rc001_state", "h"]]]},
        "V002 ,": {"N": "Forgot Password Link", "T": "P", "I": [[3, "modal_reset_99", "", "("]]},
        "V003 .": {"N": "Welcome Label", "T": "x", "b/#000000": ["", "Welcome Back! Please sign in.", [], []]},
        "V004": {"N": "Password Rule Note", "T": "i", "rtS": "Password must be at least 8 characters and contain a number"},
        "V005": {"N": "GDPR Note", "T": ")-", "rtS": "GDPR consent required before proceeding"},
    }


def test_extract_pages():
    components = make_components()
    pages = extract_pages(components)
    assert len(pages) >= 2
    page_ids = {p["page_id"] for p in pages}
    assert "rbp001" in page_ids
    assert "rbp002" in page_ids
    page_names = {p["page_name"] for p in pages}
    assert "Login Page" in page_names
    assert "Dashboard" in page_names


def test_extract_pages_have_estimated_routes():
    components = make_components()
    pages = extract_pages(components)
    for p in pages:
        assert "estimated_route" in p
        assert p["estimated_route"].startswith("/")


def test_extract_interactions_resolved():
    components = make_components()
    pages = extract_pages(components)
    interactions, unresolved = extract_interactions(components, pages)
    # V001 has a navigate to rbp002 — should be resolved as fact (direct match)
    resolved = [i for i in interactions if i["confidence"] == "fact"]
    assert len(resolved) >= 1
    nav = resolved[0]
    assert nav["interaction_type"] == "navigate"
    assert nav["target_page"] == "rbp002"


def test_extract_interactions_unresolved_for_missing_navigation_target():
    components = make_components()
    components["V999"] = {"N": "Broken Link", "T": "]", "I": [[1, "missing_page", "", "(", [], "(((()"]]}
    pages = extract_pages(components)
    interactions, unresolved = extract_interactions(components, pages)
    assert len(unresolved) >= 1
    un = next(item for item in unresolved if item["source_component"] == "Broken Link")
    assert un["raw_target_id"] == "missing_page"
    assert un["interaction_type"] == "navigate"


def test_extract_texts_from_b_field():
    components = make_components()
    texts = extract_texts(components)
    b_texts = [t for t in texts if t["field"].startswith("b/#")]
    assert len(b_texts) >= 1
    assert "Welcome Back" in b_texts[0]["text_content"]


def test_extract_texts_from_N_field():
    components = make_components()
    texts = extract_texts(components)
    n_texts = [t for t in texts if t["field"] == "N"]
    assert len(n_texts) >= 1


def test_extract_business_rules():
    components = make_components()
    rules = extract_business_rules(components)
    assert len(rules) >= 2
    rule_texts = {r["rule_text"] for r in rules}
    assert "Password must be at least 8 characters and contain a number" in rule_texts
    assert "GDPR consent required before proceeding" in rule_texts
    for r in rules:
        assert r["source"] == "annotation"


def test_extract_interactions_via_context():
    """Test resolution through context array when direct target is not a page."""
    # Component with a direct target that's NOT a page, but context has a valid page
    components = {
        "rbp001": {"N": "Page One", "T": "*"},
        "rbp002": {"N": "Page Two", "T": "*"},
        "V100": {"N": "Go Button", "T": "]", "I": [[1, "some_rc_id", "", "(", ["", "rbp002", "", "h"]]]},
    }
    pages = extract_pages(components)
    interactions, unresolved = extract_interactions(components, pages)
    inferred = [i for i in interactions if i["confidence"] == "inferred"]
    assert len(inferred) >= 1
    assert inferred[0]["target_page"] == "rbp002"
    assert len(unresolved) == 0


def test_extract_interactions_resolves_mockitt_page_suffix_targets():
    components = {
        "rbp001 +": {"N": "Page One", "T": "*"},
        "rbp002 6": {"N": "Page Two", "T": "*"},
        "V100": {"N": "Go Button", "T": "]", "I": [[1, "itaAction", "", "(", ["(  0 ", "rbp002", "rcState", "h", "h"], "(((()", 2, "(", None]]},
    }
    pages = extract_pages(components)
    page_ids = {p["page_id"] for p in pages}
    assert "rbp002" in page_ids

    interactions, unresolved = extract_interactions(components, pages)

    assert len(unresolved) == 0
    assert interactions[0]["target_page"] == "rbp002"
    assert interactions[0]["target_name"] == "Page Two"
    assert interactions[0]["confidence"] == "inferred"


def test_extract_interactions_resolves_non_page_interaction_semantics():
    components = {
        "rbp001": {"N": "Page One", "T": "*"},
        "V200": {
            "N": "Open Dialog",
            "T": "]",
            "I": [[3, "itaModal", "", "(", ["9 0.2s 0 ", "CURRENT_BASKET_REF", "rcDialog"], "(((()"]],
        },
        "V201": {"N": "Close", "T": "y", "I": [[2, "itaBack", "", "(", ["(  0 ", "h", "h"], "((((*", 2, "(", None]]},
        "V202": {"N": "Switch Tab", "T": "_", "I": [[10, "itaState", "", "(", [], "(((()", 2, "(", None]]},
    }
    pages = extract_pages(components)
    interactions, unresolved = extract_interactions(components, pages)

    assert len(interactions) == 3
    assert len(unresolved) == 0

    modal = next(i for i in interactions if i["interaction_type"] == "modal")
    assert modal["target_type"] == "modal"
    assert modal["target_id"] == "rcDialog"
    assert modal["target_name"] == "弹窗/浮层 rcDialog"
    assert modal["confidence"] == "inferred"

    back = next(i for i in interactions if i["interaction_type"] == "back")
    assert back["target_type"] == "history"
    assert back["target_name"] == "返回上一页/关闭当前层"
    assert back["confidence"] == "inferred"

    state = next(i for i in interactions if i["interaction_type"] == "state_change")
    assert state["target_type"] == "state_change"
    assert state["target_id"] == "itaState"
    assert state["target_name"] == "当前组件/页面状态切换"
    assert state["confidence"] == "inferred"
