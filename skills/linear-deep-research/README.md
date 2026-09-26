# linear-deep-research

Runs the Deep Research queue on the Linear board (team Frank's Agents, project Deep Research): picks the next Todo issue, runs `/deep-research` once, and attaches the report to the issue.

- `SKILL.md` — the procedure Claude follows.
- `scripts/run.sh` — headless runner: `claude -p` in a detached tmux session `linear-research`, one run at a time, logs to `~/.local/state/linear-research/`.
  - `run.sh` — real run. `run.sh --dry-run` — reports what Recover and Pick would do; read-only.
  - Watch: `tmux attach -t linear-research`. Inspect a finished run: `claude --resume <session-id>`.
- `review/` — unused draft (reuses one interactive tmux session); not wired into anything.

Notes:
- `run.sh` sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`; `claude -p` otherwise kills the research workflow after 10 idle minutes.
- One research run costs roughly 40% of the 5-hour window at `--effort xhigh`.
