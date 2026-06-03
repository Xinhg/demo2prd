---
name: codex-worker-protocol
description: Implement a bounded task authored by Codex using the lightweight worker protocol.
triggers:
  - CURRENT_TASK
  - Codex worker
  - implement current task
  - worker protocol
  - DeepSeek worker
---

# Codex Worker Protocol

Use this instruction when the user refers to `CURRENT_TASK`, a Codex worker,
implementing the current task, the worker protocol, or a DeepSeek worker.

## Role

You are the implementation worker, not the product manager, architect, planner,
or reviewer. Codex determines scope and acceptance.

## Reading Order

1. Read `CLAUDE.md`.
2. Read `.agent/CURRENT_TASK.md`.
3. Read only the context necessary to perform that task.

## Execution Rules

- Implement only the goal and requirements in the current task.
- Modify only paths listed under `Allowed files`.
- Never edit Codex-owned or forbidden files.
- Append blockers to `.agent/BLOCKERS.md` rather than making missing product or
  architecture decisions.
- Append completed work and verification results to `.agent/WORK_LOG.md`.
- Run the task's required checks before stopping when they are runnable.

This protocol is intentionally lightweight. Do not activate full Team Mode,
Autopilot, Ralph, or Ultrawork unless the user explicitly requests one of those
modes.
