---
name: linear
description: Linear via its GraphQL API. Use for any Linear operation instead of the Linear MCP server.
---

# Linear (GraphQL)

`linear.py` below means `python3 ${CLAUDE_SKILL_DIR}/scripts/linear.py`.

```
linear.py 'QUERY' ['{"var": "value"}']
```
- QUERY may be `@file.graphql` or `-` (stdin). Prints the response `data` as JSON; GraphQL errors go to stderr, exit 1.
- API key: `$LINEAR_API_KEY`, else the macOS Keychain item with service `linear-api-key` (account `$LINEAR_KEYCHAIN_ACCOUNT` if set). Never print it. Setup: [README.md](README.md).
- Pass text (comment bodies, descriptions) as variables, never inlined in the query.

## Introspect before querying — never guess a field

```
linear.py --type Query          # root queries with args
linear.py --type Mutation       # all mutations
linear.py --type Issue          # any object, input type or enum, e.g. IssueFilter
```

## Examples

```
linear.py '{ viewer { id name } teams { nodes { id key name } } projects { nodes { id name } } }'
linear.py 'query($i: String!) { issue(id: $i) { title description state { name } comments { nodes { body createdAt user { name } } } } }' '{"i": "ENG-123"}'
linear.py '{ issues(filter: { project: { name: { eq: "<project>" } }, state: { name: { eq: "Todo" } } }, first: 50) { nodes { identifier title priority } } }'
linear.py '{ workflowStates(filter: { team: { key: { eq: "<team key>" } } }) { nodes { id name } } }'
linear.py 'mutation($i: String!, $s: String!) { issueUpdate(id: $i, input: { stateId: $s }) { success } }' '{"i": "ENG-123", "s": "<state id>"}'
linear.py 'mutation($i: String!, $b: String!) { commentCreate(input: { issueId: $i, body: $b }) { success } }' '{"i": "ENG-123", "b": "..."}'
linear.py 'mutation($i: String!, $u: String!, $t: String) { attachmentLinkURL(issueId: $i, url: $u, title: $t) { success } }' '{"i": "ENG-123", "u": "https://...", "t": "Report"}'
```

## Gotchas

- `issue(id:)` and `issueId` accept the identifier (`ENG-123`) or the UUID.
- Statuses belong to the team, not the project. State, project, assignee and label changes take IDs; look them up first.
- `first` is capped at 250.
- Linear normalizes stored Markdown (e.g. `-` bullets become `*`). To edit a description, fetch it and patch the fetched text.
- `history(orderBy: createdAt)` returns newest first; `stateHistory` gives per-state spans.
