#!/usr/bin/env python3
"""Deny Claude Code Edit/Write calls targeting Codex-owned files."""

from __future__ import annotations

import json
import os
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


def warn(message: str) -> None:
    print(f"guard_planner_docs.py: {message}", file=sys.stderr)


def deny(relative_path: str) -> None:
    reason = (
        f"Denied edit to {relative_path}: this file is Codex-owned. "
        "Report concerns or missing decisions in .agent/BLOCKERS.md."
    )
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


def target_relative_to_project(payload: dict[str, object]) -> str | None:
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
        return target.relative_to(root).as_posix()
    except ValueError:
        return os.path.relpath(target, root).replace(os.sep, "/")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as error:
        warn(f"could not parse hook input; allowing tool call ({error})")
        return 0

    relative_path = target_relative_to_project(payload)
    if relative_path is None:
        warn("tool input had no file_path; allowing tool call")
        return 0

    if relative_path in PLANNER_OWNED:
        deny(relative_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
