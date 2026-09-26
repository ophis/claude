#!/bin/bash
# Picks up the next Todo issue in the Linear "Deep Research" project via the
# linear-deep-research skill, in a detached tmux session. --dry-run only reports
# what Recover and Pick would do.
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
SESSION=linear-research
STATE="$HOME/.local/state/linear-research"
mkdir -p "$STATE/work"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "$(date '+%F %T') skip: previous run still active" >> "$STATE/runs.log"
  exit 0
fi

PROMPT="Use the linear-deep-research skill to pick up the next Todo issue in the Deep Research project and handle it."
PERMS="--permission-mode auto"
if [[ "${1:-}" == "--dry-run" ]]; then
  PROMPT="Read the linear-deep-research skill and evaluate only its Recover and Pick steps. Report which issues Recover would return to Todo and which issue Pick would then take, with reasons. Do not modify anything and do not launch any workflow."
  # Dry runs stay on a read-only allowlist so nothing can be modified.
  PERMS="--allowedTools $(printf '%q' "Skill mcp__linear-server__list_issues mcp__linear-server__get_issue mcp__linear-server__list_comments mcp__linear-server__get_user")"
fi

LOG="$STATE/$(date +%Y%m%d-%H%M%S).jsonl"
echo "$(date '+%F %T') start ${1:-run} log=$LOG" >> "$STATE/runs.log"

tmux new-session -d -s "$SESSION" -c "$STATE/work" \
  "claude -p $(printf '%q' "$PROMPT") --model opus --effort xhigh $PERMS --output-format stream-json --verbose < /dev/null | tee $(printf '%q' "$LOG")"
