---
name: linear-deep-research
description: Use when asked to pick up, run, or work on an issue in the Deep Research project on the user's Linear board (team "Frank's Agents"), or to handle the next research idea in that queue.
---

# Linear Deep Research

Turns one Deep Research issue into a verified Markdown report pushed to the user's `private_docs` GitHub repo and linked from the issue. Research runs through the built-in `deep-research` Workflow; this skill owns claiming, reporting and board updates.

## Board

- Team `Frank's Agents`, project `Deep Research`.
- Statuses: Todo (queue) → In Progress → In Review (needs the user: report ready, questions, or stuck) → Done (user only). The agent never uses Backlog.
- MCP is signed in as the agent account `frank.agent.w`, so `me` is the agent and its work shows under that name.

## Steps

1. **Pick.** If the invocation names an issue, use it. Otherwise run `python3 ${CLAUDE_SKILL_DIR}/scripts/pick.py`: it returns issues left by dead runs to Todo, then claims the next Todo issue and prints `<ID> <url>`. No output → queue empty; stop.
2. **Read** the issue and its comments.
3. **Too vague?** If the question, scope or deliverable is missing, comment 2–4 numbered questions, move the issue to In Review, and stop.
4. **Claim.** If `pick.py` or the runner already claimed it, only comment that research started. Otherwise re-read the status right before claiming: not Todo anymore → another session has it; stop. Else set In Progress, assignee `me`, and comment that research started.
5. **Research.** Call the built-in `/deep-research` Workflow exactly once for the whole issue in this invocation. Combine all subquestions, shared context, and any "already known" claims from the description and the user's comments into one self-contained `args` string; where they conflict, the user's comments override the description (ignore the agent's own comments); phrase existing claims as claims to verify and prioritize the questions most important to the deliverable. Do not launch separate runs for individual parts or additional runs to fill coverage gaps. The workflow verifies only its top-ranked claims, so list uncovered or unverified parts under Gaps.
6. **Failed or partial run.** Do not automatically retry or launch a replacement research run in this invocation. If the run produces usable findings, including supported refutations, publish the report and list missing or unverified parts under Gaps. If it fails and yields no usable findings, comment the failure, move the issue back to Todo, and stop.
7. **Report.** Write `~/playground/private_docs/Deep Research/<issue ID>-<short-kebab-slug>.md`, starting with `# Report: <issue ID> <issue title>`. Commit only that file (`git add <file>` then `git commit -m "Add <issue ID> report: <short title>" -- <file>`; leave any other changes in the repo alone) and `git push`. Add its GitHub URL, `https://github.com/ophis/private_docs/blob/main/Deep%20Research/<file name>`, to the issue's links with `save_issue` `links`. Do not create a Linear document. Write the report in Chinese; on first mention, follow each proper noun or acronym with its English original in parentheses, e.g. 工作树（git worktree）. Sections:
   - Answer and recommendation (one paragraph)
   - Comparison table, when the deliverable asks for one
   - Findings per part, each with its confidence and sources
   - Corrections to anything the issue listed as already known
   - Gaps: unverified parts, refuted claims, open questions
   Present unverified or single-source points as such, never as fact. The recommendation and comparison table are your synthesis of findings from the single run; say so.
8. **Hand off.** Comment a 3–5 line summary plus the GitHub link, set In Review, and reply to the user with the link. Handle one issue per invocation.

## Resume rule

A prompt starting "Resumed run" continues this session after an interruption. It is the one exception to steps 5–6; check in order:

1. No Workflow call yet in this session → continue from step 5; it is still the single run.
2. The run's `~/.claude/projects/<project>/<session id>/subagents/workflows/<runId>/journal.jsonl` shows agents that failed on rate_limit, or has no final result → call the Workflow with `resumeFromRunId` once. Judge from the journal only, never `/private/tmp`.
3. Otherwise → steps 7–8, doing only what is missing: report committed and pushed, link on the issue, hand-off comment, In Review.

Never repeat the "research started" comment. Failures left after the resume → publish with Gaps.
