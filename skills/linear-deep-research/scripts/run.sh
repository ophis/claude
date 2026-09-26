#!/bin/bash
# Picks up the next Todo issue in the Linear "Deep Research" project via the
# linear-deep-research skill, in a detached tmux session. --dry-run only reports
# which issue would be picked.
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
TOOLS="Skill Workflow WebSearch WebFetch mcp__linear-server__list_issues mcp__linear-server__get_issue mcp__linear-server__list_comments mcp__linear-server__list_issue_statuses mcp__linear-server__save_issue mcp__linear-server__save_comment mcp__linear-server__save_document"
if [[ "${1:-}" == "--dry-run" ]]; then
  PROMPT="Read the linear-deep-research skill and follow only its Pick step. Report which issue it would pick and why. Do not modify anything and do not launch any workflow."
  TOOLS="Skill mcp__linear-server__list_issues mcp__linear-server__get_issue"
fi

LOG="$STATE/$(date +%Y%m%d-%H%M%S).jsonl"
echo "$(date '+%F %T') start ${1:-run} log=$LOG" >> "$STATE/runs.log"

tmux new-session -d -s "$SESSION" -c "$STATE/work" \
  "claude -p $(printf '%q' "$PROMPT") --model opus --effort xhigh --allowedTools $(printf '%q' "$TOOLS") --output-format stream-json --verbose < /dev/null | tee $(printf '%q' "$LOG")"
