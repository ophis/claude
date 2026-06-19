# CLAUDE.md — user-level preferences

- **Language:** The user may write in Chinese, but **all assistant output and all implementation are in English** — code, comments, commit messages, docs, file contents. Respond in English regardless of the language the user writes in.
- **Minimal necessary principle:** Output only what's necessary — get it minimal the first time so nothing needs trimming after. Applies to every output: responses, docs, code, comments. Cut filler, restatement, hedging, rationale, "X not Y" framing, and examples a rule already implies; keep load-bearing detail (a guard, a gotcha, a functional requirement). Specifics: default to no code comments (add one only for a pitfall/gotcha/non-obvious reason, ≤3 lines); docs say it once, direct instructions. Unsure a line earns its place → drop it.
- **Responses (hard rule):** Never verbose. Lead with the result; no preamble, recap. Default to a few lines.
