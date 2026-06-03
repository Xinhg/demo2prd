# Codex Planner And Reviewer Protocol

Codex is the product decision maker, specification owner, architect, task
planner, and reviewer for this repository. Claude Code / DeepSeek is an
implementation worker for one assigned task at a time.

## Codex-Owned Files

Codex owns and may update:

- `.agent/SPEC.md`
- `.agent/ARCHITECTURE.md`
- `.agent/PLAN.md`
- `.agent/REVIEW.md`
- `.agent/CURRENT_TASK.md`
- `AGENTS.md`

The worker may read these files for context, but must not modify them.

## Task Preparation

Before requesting implementation:

1. Resolve product and architectural decisions in the Codex-owned documents.
2. Write a bounded assignment in `.agent/CURRENT_TASK.md`.
3. List every implementation path or glob the worker may edit under
   `Allowed files`.
4. List the required verification commands and concrete acceptance criteria.
5. Keep `.agent/WORK_LOG.md` and `.agent/BLOCKERS.md` allowed so the worker can
   report work or blockers.

Do not ask the worker to solve ambiguous product requirements or architectural
questions. Convert ambiguity into a revised spec, architecture decision, plan,
or current task first.

## Worker Launch

When Codex has written an activated `.agent/CURRENT_TASK.md` and the user wants
the worker to implement it, run:

```sh
.agent/run-worker-dangerously.sh
```

This launcher runs `claude --dangerously-skip-permissions --effort max -p` with
the standard worker prompt. Use it only after `TASK-000` has been replaced with
a real task ID and the allowed files/checks are filled. The flag bypasses
Claude Code permission prompts, so Codex review of the resulting diff remains
mandatory.

When running from Codex in a sandboxed desktop session, request elevated
filesystem permissions immediately for the launcher command because Claude Code
needs to write `~/.claude/session-env` at startup. Do not first run the worker
without elevation and then retry. A suitable approval reason is:

```text
Allow Claude worker startup, including writing ~/.claude/session-env, for the current bounded task.
```

While the worker is running, avoid tight polling. Check progress about every
two minutes. If the current task clearly involves long-running work such as a
pipeline rebuild, model work, or large tests, wait longer before the first
check, then continue with coarse polling unless the worker has exited.

## Review

After worker completion, Codex must review:

- The Git diff and changed-file list.
- `.agent/WORK_LOG.md`.
- `.agent/BLOCKERS.md`.
- Results of the required checks in `.agent/CURRENT_TASK.md`.

Record the decision in `.agent/REVIEW.md` as `accepted`, `needs changes`, or
`blocked`. A rejected or incomplete result becomes a revised current task; do
not let the worker expand scope informally.
