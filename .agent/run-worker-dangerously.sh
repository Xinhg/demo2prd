#!/usr/bin/env bash
set -euo pipefail

worker_prompt='Read CLAUDE.md and .agent/CURRENT_TASK.md. Implement only the current task. Do not modify planner-owned files. If blocked, write to BLOCKERS.md. After implementation, update WORK_LOG.md and run required checks.'

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
cd "$project_dir"
dry_run=0

if [ "$#" -gt 1 ]; then
  printf 'Usage: %s [--dry-run]\n' "$(basename "$0")" >&2
  exit 2
fi

case "${1:-}" in
  "")
    ;;
  --dry-run)
    dry_run=1
    ;;
  -h|--help)
    printf 'Usage: %s [--dry-run]\n' "$(basename "$0")"
    exit 0
    ;;
  *)
    printf 'Usage: %s [--dry-run]\n' "$(basename "$0")" >&2
    exit 2
    ;;
esac

task_file=.agent/CURRENT_TASK.md
if [ ! -f "$task_file" ]; then
  printf 'No %s found. Install the lite protocol before starting the worker.\n' "$task_file" >&2
  exit 1
fi

task_id=$(
  awk '
    /^## Task ID[[:space:]]*$/ { read_id = 1; next }
    read_id && $0 !~ /^[[:space:]]*$/ && $0 !~ /^[[:space:]]*<!--/ {
      gsub(/`/, "", $0)
      print $0
      exit
    }
  ' "$task_file"
)

if [ -z "$task_id" ] || [ "$task_id" = "TASK-000" ]; then
  printf 'CURRENT_TASK.md is not activated. Replace TASK-000 with a real task ID before starting the worker.\n' >&2
  exit 1
fi

if grep -q '<replace-with-implementation-path-or-glob>' "$task_file"; then
  printf 'CURRENT_TASK.md still contains an Allowed files placeholder. Fill it before starting the worker.\n' >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  printf 'claude CLI not found on PATH.\n' >&2
  exit 127
fi

prepare_claude_session_env() {
  if [ -z "${HOME:-}" ]; then
    printf 'HOME is not set; cannot prepare ~/.claude/session-env.\n' >&2
    exit 1
  fi

  claude_dir=$HOME/.claude
  session_env=$claude_dir/session-env

  if ! mkdir -p -- "$claude_dir"; then
    printf 'Cannot create %s. Run the launcher with elevated filesystem permissions.\n' "$claude_dir" >&2
    exit 1
  fi

  if [ -d "$session_env" ]; then
    printf 'Claude session env path exists as a directory; leaving it intact: %s\n' "$session_env"
    return
  fi

  if ! : >> "$session_env"; then
    printf 'Cannot write %s. Run the launcher with elevated filesystem permissions.\n' "$session_env" >&2
    exit 1
  fi

  chmod 600 "$session_env" 2>/dev/null || true
  printf 'Prepared Claude session env: %s\n' "$session_env"
}

printf 'Starting Claude worker for %s in %s\n' "$task_id" "$project_dir"
printf 'Mode: claude --dangerously-skip-permissions --effort max -p <worker prompt>\n'

if [ "$dry_run" -eq 1 ]; then
  printf 'Dry run only; Claude was not started.\n'
  exit 0
fi

prepare_claude_session_env

set +e
claude --dangerously-skip-permissions --effort max -p "$worker_prompt"
status=$?
set -e

printf '\nClaude worker exited with status %s\n' "$status"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '\nPost-worker git status:\n'
  git status --short --branch
fi

exit "$status"
