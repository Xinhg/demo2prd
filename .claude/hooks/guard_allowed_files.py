#!/usr/bin/env python3
"""Limit Claude Code Edit/Write calls to files allowed by CURRENT_TASK.md."""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path


PLANNER_OWNED = {
    ".agent/SPEC.md",
    ".agent/ARCHITECTURE.md",
    ".agent/PLAN.md",
    ".agent/REVIEW.md",
    ".agent/run-worker-dangerously.sh",
    "AGENTS.md",
}
SECTION_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
BULLET_PATTERN = re.compile(r"^\s*[-*]\s+(.+?)\s*$")


def warn(message: str) -> None:
    print(f"guard_allowed_files.py: warning: {message}", file=sys.stderr)


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def get_target(payload: dict[str, object]) -> tuple[Path, Path, str] | None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    raw_path = tool_input.get("file_path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None

    root_raw = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    root = Path(str(root_raw)).resolve()
    target = Path(raw_path)
    if not target.is_absolute():
        target = root / target
    target = target.resolve(strict=False)
    try:
        relative = target.relative_to(root).as_posix()
    except ValueError:
        relative = os.path.relpath(target, root).replace(os.sep, "/")
    return root, target, relative


def parse_task_sections(contents: str) -> tuple[list[str], list[str]] | None:
    sections: dict[str, list[str]] = {"allowed files": [], "forbidden files": []}
    seen: set[str] = set()
    active: str | None = None

    for line in contents.splitlines():
        heading = SECTION_PATTERN.match(line)
        if heading:
            title = heading.group(1).strip().lower()
            active = title if title in sections else None
            if active is not None:
                seen.add(active)
            continue
        if active is None:
            continue
        bullet = BULLET_PATTERN.match(line)
        if not bullet:
            continue
        pattern = bullet.group(1).strip().strip("`").strip()
        if not pattern or "<" in pattern or pattern.lower() in {"none", "n/a"}:
            continue
        sections[active].append(pattern)

    if seen != set(sections):
        return None
    return sections["allowed files"], sections["forbidden files"]


def matches_pattern(relative: str, absolute: Path, pattern: str) -> bool:
    normalized = pattern.strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.endswith("/"):
        normalized += "**"
    candidate = absolute.as_posix() if normalized.startswith("/") else relative
    return fnmatch.fnmatchcase(candidate, normalized)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as error:
        warn(f"could not parse hook input; allowing tool call ({error})")
        return 0

    target_data = get_target(payload)
    if target_data is None:
        warn("tool input had no file_path; allowing tool call")
        return 0
    root, target, relative = target_data

    if relative in PLANNER_OWNED:
        deny(
            f"Denied edit to {relative}: this file is Codex-owned. "
            "Report concerns in .agent/BLOCKERS.md."
        )
        return 0

    task_path = root / ".agent" / "CURRENT_TASK.md"
    try:
        task_contents = task_path.read_text(encoding="utf-8")
    except OSError as error:
        warn(f"could not read {task_path}; allowing non-planner edit ({error})")
        return 0

    parsed = parse_task_sections(task_contents)
    if parsed is None:
        warn(
            "CURRENT_TASK.md does not contain parseable Allowed files and "
            "Forbidden files sections; allowing non-planner edit"
        )
        return 0
    allowed, forbidden = parsed

    if any(matches_pattern(relative, target, pattern) for pattern in forbidden):
        deny(
            f"Denied edit to {relative}: the path is forbidden by "
            ".agent/CURRENT_TASK.md. Record a blocker if that scope is required."
        )
        return 0

    if allowed and not any(
        matches_pattern(relative, target, pattern) for pattern in allowed
    ):
        deny(
            f"Denied edit to {relative}: it is outside the Allowed files in "
            ".agent/CURRENT_TASK.md. Record a blocker or request revised scope."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
