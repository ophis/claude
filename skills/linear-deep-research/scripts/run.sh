#!/bin/bash
# Claims the next Todo issue in the Linear "Deep Research" project (pick.py) and hands it to
# the linear-deep-research skill in a detached tmux session. --dry-run only reports what
# pick.py would recover and pick; no Claude session is started.
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
# claude -p kills background workflows after 10 idle minutes by default; a research run takes longer.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=3600000
DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION=linear-research
STATE="$HOME/.local/state/linear-research"
mkdir -p "$STATE/work"

MAX_5H=0.30

# 5-hour window utilization (0-1), read from the rate-limit events of one tiny Haiku call; empty if unavailable.
five_hour_usage() {
  (cd "$STATE/work" && claude -p "Reply with OK." --model haiku --output-format stream-json --verbose < /dev/null 2>/dev/null) |
    python3 -c '
import json, sys
last = ""
for line in sys.stdin:
    try:
        m = json.loads(line)
    except ValueError:
        continue
    if m.get("type") == "rate_limit_event":
        last = m["rate_limit_info"].get("unifiedWindows", {}).get("five_hour", {}).get("utilization", last)
print(last)'
}

USAGE=$(five_hour_usage)

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "5h usage: ${USAGE:-unknown} (runs only below $MAX_5H)" >&2
  exec python3 "$DIR/pick.py" --dry-run
fi

# Checked before pick.py: Recover assumes no run is active.
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "$(date '+%F %T') skip: previous run still active" >> "$STATE/runs.log"
  exit 0
fi

if [[ -z "$USAGE" ]] || ! python3 -c "import sys; sys.exit(0 if $USAGE < $MAX_5H else 1)"; then
  echo "$(date '+%F %T') skip: 5h usage ${USAGE:-unknown} not below $MAX_5H" >> "$STATE/runs.log"
  exit 0
fi

PICKED=$(python3 "$DIR/pick.py" 2>> "$STATE/runs.log")
if [[ -z "$PICKED" ]]; then
  echo "$(date '+%F %T') skip: queue empty" >> "$STATE/runs.log"
  exit 0
fi
read -r ISSUE URL <<< "$PICKED"

PROMPT="Use the linear-deep-research skill to handle $ISSUE ($URL). The runner has already claimed it."
SID=$(uuidgen | tr 'A-Z' 'a-z')
TRANSCRIPT="$HOME/.claude/projects/$(echo "$STATE/work" | tr '/.' '--')/$SID.jsonl"
echo "$(date '+%F %T') start $ISSUE session=$SID transcript=$TRANSCRIPT" >> "$STATE/runs.log"

tmux new-session -d -s "$SESSION" -c "$STATE/work" \
  "claude -p $(printf '%q' "$PROMPT") --session-id $SID --model opus --effort xhigh --permission-mode auto < /dev/null"
