"""Pure-data extraction for Mockitt: pages, interactions, texts, and business rules."""

import re
from .normalize import normalize_id

INTERACTION_TYPES = {
    1: "navigate",
    2: "back",
    3: "modal",
    10: "state_change",
}

ANNOTATION_TYPES = {"i", ")-"}

PAGE_PREFIX = "rbp"

_TEXT_FIELD_RE = re.compile(r"^b/#[0-9A-Fa-f]{6}$")


def extract_pages(components: dict) -> list[dict]:
    """Extract page entries from component index. Pages are rbp*-prefixed components."""
    pages: list[dict] = []
    for cid, comp in components.items():
        norm_id = normalize_id(cid)
        if norm_id.startswith(PAGE_PREFIX):
            name = comp.get("N", norm_id)
            pages.append({
                "page_id": norm_id,
                "page_name": name,
                "state_variants": [],
                "estimated_route": "/" + _slugify(name),
                "components_count": 0,
            })
    return pages


def extract_interactions(components: dict, pages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Extract interactions from component I arrays. Returns (interactions, unresolved)."""
    interactions: list[dict] = []
    unresolved: list[dict] = []
    page_ids = {p["page_id"] for p in pages}
    page_names = {p["page_id"]: p["page_name"] for p in pages}

    for cid, comp in components.items():
        norm_id = normalize_id(cid)
        i_array = comp.get("I", [])
        if not i_array or not isinstance(i_array, list):
            continue

        comp_name = comp.get("N", norm_id)

        for entry in i_array:
            if not isinstance(entry, list) or len(entry) < 2:
                continue

            type_code = entry[0]
            raw_target = str(entry[1]) if entry[1] is not None else ""
            norm_target = normalize_id(raw_target)
            interaction_type = INTERACTION_TYPES.get(type_code, f"unknown_{type_code}")

            resolved_target = ""
            target_id = ""
            target_type = "unknown"
            target_name = ""
            confidence = "unknown"

            if interaction_type == "navigate":
                resolved_target, confidence = _resolve_page_target(entry, page_ids)
                if resolved_target:
                    target_type = "page"
                    target_id = resolved_target
                    target_name = page_names.get(resolved_target, resolved_target)
            elif interaction_type == "modal":
                target_type = "modal"
                target_id = _modal_target_id(entry) or norm_target
                target_name = f"弹窗/浮层 {target_id}" if target_id else "弹窗/浮层"
                confidence = "inferred" if target_id else "unknown"
            elif interaction_type == "back":
                target_type = "history"
                target_id = "history.back"
                target_name = "返回上一页/关闭当前层"
                confidence = "inferred"
            elif interaction_type == "state_change":
                target_type = "state_change"
                target_id = norm_target
                target_name = "当前组件/页面状态切换"
                confidence = "inferred" if target_id else "unknown"

            interaction = {
                "source_component": comp_name,
                "source_component_id": norm_id,
                "interaction_type": interaction_type,
                "target_page": resolved_target,
                "target_type": target_type,
                "target_id": target_id,
                "target_name": target_name,
                "raw_target_id": raw_target if confidence == "unknown" else "",
                "confidence": confidence,
            }
            interactions.append(interaction)

            if confidence == "unknown":
                unresolved.append({
                    "source_component": comp_name,
                    "source_component_id": norm_id,
                    "raw_target_id": raw_target,
                    "interaction_type": interaction_type,
                })

    return interactions, unresolved


def _resolve_page_target(entry: list, page_ids: set[str]) -> tuple[str, str]:
    """Resolve a navigation entry to a page ID, checking direct and nested targets."""
    raw_target = str(entry[1]) if len(entry) > 1 and entry[1] is not None else ""
    norm_target = normalize_id(raw_target)
    if norm_target in page_ids:
        return norm_target, "fact"

    for value in entry[2:]:
        nested = _find_page_id(value, page_ids)
        if nested:
            return nested, "inferred"
    return "", "unknown"


def _find_page_id(value: object, page_ids: set[str]) -> str:
    if isinstance(value, str):
        norm_value = normalize_id(value)
        return norm_value if norm_value in page_ids else ""
    if isinstance(value, list):
        for item in value:
            found = _find_page_id(item, page_ids)
            if found:
                return found
    if isinstance(value, dict):
        for item in value.values():
            found = _find_page_id(item, page_ids)
            if found:
                return found
    return ""


def _modal_target_id(entry: list) -> str:
    """Return the Mockitt modal/layer target ID from an interaction entry."""
    if len(entry) > 4 and isinstance(entry[4], list):
        context = entry[4]
        if len(context) > 2 and context[2]:
            return normalize_id(str(context[2]))
    return ""


def extract_texts(components: dict) -> list[dict]:
    """Extract visible text from component N fields, b/#RRGGBB fields, and rtS fields."""
    texts: list[dict] = []
    seen = set()  # deduplicate

    for cid, comp in components.items():
        norm_id = normalize_id(cid)
        comp_name = comp.get("N", norm_id)

        # N field (component name / label)
        if comp_name and comp_name != norm_id:
            key = (norm_id, "N", comp_name)
            if key not in seen:
                seen.add(key)
                texts.append({
                    "page": "",
                    "component_name": comp_name,
                    "component_id": norm_id,
                    "text_content": comp_name,
                    "field": "N",
                })

        # b/#RRGGBB fields (button text / visible text)
        for key, value in comp.items():
            if not _TEXT_FIELD_RE.match(key):
                continue
            text_val = ""
            if isinstance(value, list) and len(value) > 1:
                text_val = str(value[1]) if value[1] else ""
            elif isinstance(value, str):
                text_val = value
            if text_val:
                k = (norm_id, key, text_val)
                if k not in seen:
                    seen.add(k)
                    texts.append({
                        "page": "",
                        "component_name": comp_name,
                        "component_id": norm_id,
                        "text_content": text_val,
                        "field": key,
                    })

        # rtS field (rich text)
        rt_val = comp.get("rtS")
        if rt_val and isinstance(rt_val, str):
            k = (norm_id, "rtS", rt_val)
            if k not in seen:
                seen.add(k)
                texts.append({
                    "page": "",
                    "component_name": comp_name,
                    "component_id": norm_id,
                    "text_content": rt_val,
                    "field": "rtS",
                })

    return texts


def extract_business_rules(components: dict) -> list[dict]:
    """Extract business rules from annotation-type components (T='i' or T=')-')."""
    rules: list[dict] = []

    for cid, comp in components.items():
        norm_id = normalize_id(cid)
        comp_type = comp.get("T", "")
        comp_name = comp.get("N", norm_id)

        if comp_type not in ANNOTATION_TYPES:
            continue

        rule_text = ""
        if "rtS" in comp and comp["rtS"]:
            rule_text = comp["rtS"] if isinstance(comp["rtS"], str) else ""
        elif "N" in comp and comp["N"]:
            rule_text = comp["N"]

        if rule_text.strip():
            rules.append({
                "rule_text": rule_text.strip(),
                "source_page": "",
                "source_component": comp_name,
                "source_component_id": norm_id,
                "source": "annotation",
            })

    return rules


def _slugify(name: str) -> str:
    """Convert a name to a URL-friendly slug."""
    slug = re.sub(r"[^a-zA-Z0-9一-鿿]+", "-", name.lower())
    return slug.strip("-")
