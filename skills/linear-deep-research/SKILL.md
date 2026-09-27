---
name: linear-deep-research
description: Use when asked to pick up, run, or work on an issue in the Deep Research project on the user's Linear board (team "Frank's Agents"), or to handle the next research idea in that queue.
---

# Linear Deep Research

Turns one Deep Research issue into a verified report filed under the project and linked from the issue. Research runs through the built-in `deep-research` Workflow; this skill owns claiming, reporting and board updates.

## Board

- Team `Frank's Agents`, project `Deep Research`.
- Statuses: Backlog (needs user input) → Todo (queue) → In Progress → In Review (report ready) → Done (user only).
- MCP is signed in as the agent account `frank.agent.w`, so `me` is the agent and its work shows under that name.

## Steps

1. **Pick.** If the invocation names an issue, use it. Otherwise run `python3 ${CLAUDE_SKILL_DIR}/scripts/pick.py`: it returns issues left by dead runs to Todo, then claims the next Todo issue and prints `<ID> <url>`. No output → queue empty; stop.
2. **Read** the issue and its comments.
3. **Too vague?** If the question, scope or deliverable is missing, comment 2–4 numbered questions, move the issue to Backlog, and stop.
4. **Claim.** If `pick.py` or the runner already claimed it, only comment that research started. Otherwise re-read the status right before claiming: not Todo anymore → another session has it; stop. Else set In Progress, assignee `me`, and comment that research started.
5. **Research.** Call the built-in `/deep-research` Workflow exactly once for the whole issue in this invocation. Combine all subquestions, shared context, and any "already known" claims into one self-contained `args` string; phrase existing claims as claims to verify and prioritize the questions most important to the deliverable. Do not launch separate runs for individual parts or additional runs to fill coverage gaps. The workflow verifies only its top-ranked claims, so list uncovered or unverified parts under Gaps.
6. **Failed or partial run.** Do not automatically retry or launch a replacement research run in this invocation. If the run produces usable findings, including supported refutations, publish the report and list missing or unverified parts under Gaps. If it fails and yields no usable findings, comment the failure, move the issue back to Todo, and stop.
7. **Report.** `save_document` with `project` `Deep Research` as the only parent (not `issue` too), title `Report: <issue ID> <issue title>`, so all reports list on the project page. Then add the document URL to the issue's links with `save_issue` `links`. Write the report in Chinese; on first mention, follow each proper noun or acronym with its English original in parentheses, e.g. 工作树（git worktree）. Sections:
   - Answer and recommendation (one paragraph)
   - Comparison table, when the deliverable asks for one
   - Findings per part, each with its confidence and sources
   - Corrections to anything the issue listed as already known
   - Gaps: unverified parts, refuted claims, open questions
   Present unverified or single-source points as such, never as fact. The recommendation and comparison table are your synthesis of findings from the single run; say so.
8. **Hand off.** Comment a 3–5 line summary plus the document link, set In Review, and reply to the user with the link. Handle one issue per invocation.
