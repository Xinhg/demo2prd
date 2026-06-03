# Worker Blockers

Append-only blocker log. Record a blocker when implementation cannot proceed
within the current task's requirements or allowed files. Codex resolves scope
or decisions in a subsequent task or review.

Append entries using this format:

```md
## <timestamp> - `<task-id>`

- Status: unresolved
- Blocker: The API response shape is not specified.
- Why it blocks implementation: Two incompatible mappings are possible.
- Proposed options: Codex specifies mapping A or mapping B.
- Files inspected: `src/client.py`, `.agent/SPEC.md`
```

## Entries

<!-- Worker blocker entries are appended below this line. -->
