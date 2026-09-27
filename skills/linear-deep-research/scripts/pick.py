#!/usr/bin/env python3
"""Recover, Pick and Claim for the Deep Research queue, via the Linear API.

Prints "<identifier> <url>" of the claimed issue, or nothing when the queue is empty.
--dry-run reports what would happen without changing anything.
The API key is read from the macOS Keychain (service linear-api-key, account frank.agent.w).
"""
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

TEAM = "Frank's Agents"
PROJECT = "Deep Research"
STALE = timedelta(hours=2)
DRY = "--dry-run" in sys.argv[1:]

KEY = subprocess.run(["security", "find-generic-password", "-a", "frank.agent.w", "-s", "linear-api-key", "-w"],
                     capture_output=True, text=True, check=True).stdout.strip()


def gql(query, **variables):
    req = urllib.request.Request("https://api.linear.app/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": KEY})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise SystemExit(f"linear api error: {body['errors']}")
    return body["data"]


def issues(state, extra=None):
    flt = {"project": {"name": {"eq": PROJECT}}, "state": {"name": {"eq": state}}, **(extra or {})}
    return gql("""query($f: IssueFilter) { issues(filter: $f, first: 100) {
                    nodes { id identifier url priority createdAt updatedAt state { name } } } }""", f=flt)["issues"]["nodes"]


def log(msg):
    print(msg, file=sys.stderr)


me = gql("{ viewer { id } }")["viewer"]["id"]
states = {s["name"]: s["id"] for s in gql("""query($t: String!) {
    workflowStates(filter: { team: { name: { eq: $t } } }) { nodes { id name } } }""", t=TEAM)["workflowStates"]["nodes"]}

# Recover: only one run exists at a time, so a stale In Progress issue of ours was left by a run that died.
cutoff = (datetime.now(timezone.utc) - STALE).isoformat()
for issue in issues("In Progress", {"assignee": {"id": {"eq": me}}, "updatedAt": {"lt": cutoff}}):
    log(f"recover: {issue['identifier']} (last updated {issue['updatedAt']})")
    if not DRY:
        gql("mutation($i: String!, $b: String!) { commentCreate(input: { issueId: $i, body: $b }) { success } }",
            i=issue["id"], b="The previous research run was interrupted. Moving this issue back to the Todo queue.")
        gql("mutation($i: String!, $s: String!) { issueUpdate(id: $i, input: { stateId: $s, assigneeId: null }) { success } }",
            i=issue["id"], s=states["Todo"])

# Pick: highest priority first (0 = none = lowest), then oldest.
queue = sorted(issues("Todo"), key=lambda i: (i["priority"] or 5, i["createdAt"]))
if not queue:
    log("pick: queue empty")
    sys.exit(0)
issue = queue[0]
log(f"pick: {issue['identifier']} ({len(queue)} in queue)")
if DRY:
    sys.exit(0)

# Claim: re-check right before claiming so a concurrent change isn't overwritten.
current = gql("query($i: String!) { issue(id: $i) { state { name } } }", i=issue["id"])["issue"]["state"]["name"]
if current != "Todo":
    log(f"claim: {issue['identifier']} is now {current}; skipping")
    sys.exit(0)
gql("mutation($i: String!, $s: String!, $a: String!) { issueUpdate(id: $i, input: { stateId: $s, assigneeId: $a }) { success } }",
    i=issue["id"], s=states["In Progress"], a=me)
print(issue["identifier"], issue["url"])
