#!/bin/sh
# Lightweight Stop guard: require worker notes; warn about blockers or checks.
set -eu

input=$(cat || true)
case "$input" in
  *'"stop_hook_active"'*':'*true*)
    exit 0
    ;;
esac

project_dir=${CLAUDE_PROJECT_DIR:-$(pwd)}
if ! cd "$project_dir" 2>/dev/null; then
  printf '%s\n' "stop_check.sh: cannot enter project directory; skipping checks" >&2
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '%s\n' "stop_check.sh: project is not a Git work tree; skipping checks" >&2
  exit 0
fi

changes=$(git status --porcelain --untracked-files=all 2>/dev/null || true)
if [ -z "$changes" ]; then
  exit 0
fi

task_file=.agent/CURRENT_TASK.md
work_log=.agent/WORK_LOG.md
blockers=.agent/BLOCKERS.md

task_id=
if [ -f "$task_file" ]; then
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
fi

# The installed starter template is not an assigned worker task yet.
if [ -z "$task_id" ] || [ "$task_id" = "TASK-000" ]; then
  exit 0
fi

has_log=0
if [ -s "$work_log" ]; then
  if [ -n "$task_id" ]; then
    if awk -v id="$task_id" '
      /^## [0-9][0-9][0-9][0-9]-/ && index($0, id) { found = 1 }
      END { exit(found ? 0 : 1) }
    ' "$work_log"; then
      has_log=1
    fi
  elif grep -Eq '^## [0-9][0-9][0-9][0-9]-' "$work_log"; then
    has_log=1
  fi
fi

if [ "$has_log" -ne 1 ]; then
  printf '%s\n' '{"decision":"block","reason":"Uncommitted changes exist, but .agent/WORK_LOG.md has no dated entry for the current task. Append implementation notes and check results before stopping."}'
  exit 0
fi

blocker_warning=0
if [ -n "$task_id" ] && [ -f "$blockers" ]; then
  if awk -v id="$task_id" '
    function finish_entry() {
      if (matches_task && unresolved) {
        found = 1
      }
    }
    /^## [0-9][0-9][0-9][0-9]-/ {
      finish_entry()
      matches_task = index($0, id) > 0
      unresolved = 0
      in_entry = 1
      next
    }
    in_entry && index($0, id) { matches_task = 1 }
    in_entry && tolower($0) ~ /^- status:[[:space:]]*unresolved/ {
      unresolved = 1
    }
    END {
      finish_entry()
      exit(found ? 0 : 1)
    }
  ' "$blockers"; then
    blocker_warning=1
  fi
fi

checks_warning=0
required_checks=
if [ -f "$task_file" ]; then
  required_checks=$(
    awk '
      /^## Required checks[[:space:]]*$/ { in_checks = 1; next }
      in_checks && /^## / { exit }
      in_checks && /^[[:space:]]*-[[:space:]]+/ {
        value = $0
        sub(/^[[:space:]]*-[[:space:]]+/, "", value)
        lower = tolower(value)
        if (value !~ /<.*>/ && lower != "none" && lower != "n\/a") {
          print value
        }
      }
    ' "$task_file"
  )
fi

if [ -n "$required_checks" ] && [ -n "$task_id" ]; then
  if ! awk -v id="$task_id" '
    /^## [0-9][0-9][0-9][0-9]-/ {
      active = index($0, id) > 0
      next
    }
    active && /^- Tests run:/ &&
      tolower($0) !~ /(not run|none|tbd|<.*>)/ { ran = 1 }
    active && /^- Test results:/ &&
      tolower($0) !~ /(not run|none|tbd|<.*>)/ { result = 1 }
    END { exit(ran && result ? 0 : 1) }
  ' "$work_log"; then
    checks_warning=1
  fi
fi

if [ "$blocker_warning" -eq 1 ] && [ "$checks_warning" -eq 1 ]; then
  printf '%s\n' '{"systemMessage":"Worker state warning: the current task has unresolved blockers and required checks do not appear to be recorded in WORK_LOG.md. Codex should inspect both before acceptance."}'
elif [ "$blocker_warning" -eq 1 ]; then
  printf '%s\n' '{"systemMessage":"Worker state warning: BLOCKERS.md contains an unresolved blocker for the current task. Codex should inspect it before acceptance."}'
elif [ "$checks_warning" -eq 1 ]; then
  printf '%s\n' '{"systemMessage":"Worker state warning: required checks do not appear to be recorded in WORK_LOG.md. Codex should inspect verification before acceptance."}'
fi

exit 0
