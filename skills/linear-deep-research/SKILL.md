---
name: linear-deep-research
description: Use when asked to pick up, run, or work on an issue in the Deep Research project on the user's Linear board (team "Frank's Agents"), or to handle the next research idea in that queue.
---

# Linear Deep Research

Turns one Deep Research issue into a verified report attached to that issue. Research runs through the built-in `deep-research` Workflow; this skill owns claiming, reporting and board updates.

## Board

- Team `Frank's Agents`, project `Deep Research`.
- Statuses: Backlog (needs user input) → Todo (queue) → In Progress → In Review (report ready) → Done (user only).
- MCP is signed in as the agent account `frank.agent.w`, so `me` is the agent and its work shows under that name.

## Steps

1. **Pick.** Use the issue the user named. Otherwise take the Todo issue in the project with the highest priority (none = lowest), oldest first. Empty queue → stop.
2. **Read** the issue and its comments.
3. **Too vague?** If the question, scope or deliverable is missing, comment 2–4 numbered questions, move the issue to Backlog, and stop.
4. **Claim.** Re-read the status right before claiming. Not Todo anymore → another session has it; stop. Otherwise set In Progress, assignee `me`, and comment that research started.
5. **Research.** One `deep-research` run covers one focused question: it verifies only its top-ranked claims and silently drops the rest. If the issue has several independent parts, launch one run per part in parallel. Each run's `args` is one self-contained question string: the part's question, the shared context, and any "already known" claims for that part phrased as claims to verify. Each run costs ~100 agents / ~4M tokens; if more than 3 runs are needed, confirm with the user first.
6. **Failed runs.** Retry a run once if its error looks transient. If some parts still have no verified findings, publish the report anyway and list those parts under Gaps. If every run failed, comment the failure, move the issue back to Todo, and stop.
7. **Report.** `save_document` with `issue` as the only parent (not `project` too), title `Report: <issue title>`. Write the report in Chinese; on first mention, follow each proper noun or acronym with its English original in parentheses, e.g. 工作树（git worktree）. Sections:
   - Answer and recommendation (one paragraph)
   - Comparison table, when the deliverable asks for one
   - Findings per part, each with its confidence and sources
   - Corrections to anything the issue listed as already known
   - Gaps: parts no run verified, refuted claims, open questions
   Present unverified or single-source points as such, never as fact. The recommendation and comparison table are your synthesis across runs; say so.
8. **Hand off.** Comment a 3–5 line summary plus the document link, set In Review, and reply to the user with the link. Handle one issue per invocation.
