"""ID normalization for known Mockitt component ID suffixes."""

import re

_SUFFIX_PATTERNS = [
    (re.compile(r"\s\.$"), "trailing space-dot"),
    (re.compile(r"\s,$"), "trailing space-comma"),
    (re.compile(r"^([A-Za-z][A-Za-z0-9]{5,}|(?:rbp|rc|ita)[A-Za-z0-9]+)\s+\S{1,3}$"), "mockitt key suffix"),
]


def normalize_id(raw_id: str) -> str:
    """Strip known Mockitt ID suffixes (trailing ' .' and ' ,')."""
    normalized = raw_id
    for pattern, _desc in _SUFFIX_PATTERNS:
        match = pattern.match(normalized)
        if match and match.groups():
            normalized = match.group(1)
        else:
            normalized = pattern.sub("", normalized)
    return normalized


def build_id_map(raw_ids: list[str]) -> dict[str, str]:
    """Build normalized-id -> raw-id lookup from a list of raw IDs."""
    mapping: dict[str, str] = {}
    for rid in raw_ids:
        nid = normalize_id(rid)
        mapping[nid] = rid
    return mapping
