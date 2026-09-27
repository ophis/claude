# linear-deep-research

Runs the Deep Research queue on the Linear board (team Frank's Agents, project Deep Research): picks the next Todo issue, runs `/deep-research` once, and files the report under the project with a link on the issue.

- `SKILL.md` — the procedure Claude follows.
- `scripts/pick.py` — recovers issues left by dead runs, then claims the next Todo issue via the Linear API. Needs the agent account's API key in the Keychain: `security add-generic-password -a frank.agent.w -s linear-api-key -w`.
- `scripts/run.sh` — headless runner: runs `pick.py`, then `claude -p` on the claimed issue in a detached tmux session `linear-research`, one run at a time, logs one line per run with the session ID and transcript path to `~/.local/state/linear-research/runs.log`. Empty queue → no Claude session.
  - `run.sh` — real run. `run.sh --dry-run` — reports what `pick.py` would recover and pick; changes nothing, starts no Claude.
  - Watch: `tmux attach -t linear-research`. Inspect a finished run: `claude --resume <session-id>`.
- `review/` — unused draft (reuses one interactive tmux session); not wired into anything.

Notes:
- `run.sh` sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`; `claude -p` otherwise kills the research workflow after 10 idle minutes.
- One research run costs roughly 40% of the 5-hour window at `--effort xhigh`.
