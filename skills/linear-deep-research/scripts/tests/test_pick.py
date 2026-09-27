import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pick  # noqa: E402

NOW = datetime(2026, 9, 27, 3, 0, tzinfo=timezone.utc)
ME, USER = "agent", "user"
STATES = {"Todo": "s-todo", "In Progress": "s-prog", "In Review": "s-review"}


def ago(**kw):
    return (NOW - timedelta(**kw)).isoformat().replace("+00:00", "Z")


class FakeLinear:
    def __init__(self, issues, history=None):
        self.issues = {i["identifier"]: i for i in issues}
        self.history = history or {}
        self.mutations = []

    def __call__(self, query, **v):
        if "viewer" in query:
            return {"viewer": {"id": ME}}
        if "workflowStates" in query:
            return {"workflowStates": {"nodes": [{"id": i, "name": n} for n, i in STATES.items()]}}
        if "history" in query:
            return {"issue": {"history": {"nodes": self.history.get(v["i"], [])}}}
        if "mutation" in query:
            self.mutations.append((query, v))
            issue = self.issues[v["i"]]
            if "commentCreate" in query:
                issue.setdefault("comments", []).append(v["b"])
            else:
                upd = v.get("u") or {"stateId": v["s"], "assigneeId": v["a"]}
                issue["state"] = next(n for n, i in STATES.items() if i == upd["stateId"])
                if "assigneeId" in upd:
                    issue["assignee"] = upd["assigneeId"]
            return {}
        if "issues(filter" in query:
            f = v["f"]
            want = f.get("assignee", {}).get("id", {}).get("eq")
            return {"issues": {"nodes": [dict(i, state={"name": i["state"]}) for i in self.issues.values()
                                         if i["state"] == f["state"]["name"]["eq"] and (want is None or i["assignee"] == want)]}}
        if "state { name }" in query:
            return {"issue": {"state": {"name": self.issues[v["i"]]["state"]}}}
        raise AssertionError(query)


def issue(ident, state, assignee=None, updated=None, priority=0, created="2026-09-01T00:00:00Z"):
    # id == identifier so mutations and history can be keyed by either
    return {"id": ident, "identifier": ident, "url": f"https://linear.app/x/{ident}", "state": state,
            "assignee": assignee, "priority": priority, "createdAt": created, "updatedAt": updated or ago(minutes=5)}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tdir = os.path.join(self.tmp.name, "transcripts")
        os.makedirs(self.tdir)
        self.log = os.path.join(self.tmp.name, "runs.log")
        self.lines = []

    def add(self, kind, ident, sid, minutes_ago):
        ts = (NOW - timedelta(minutes=minutes_ago)).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        extra = "n=1" if kind == "resume" else f"transcript={self.tdir}/{sid}.jsonl"
        self.lines.append(f"{ts} {kind} {ident} session={sid} {extra}")

    def touch(self, rel, minutes_ago):
        p = os.path.join(self.tdir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()
        t = (NOW - timedelta(minutes=minutes_ago)).timestamp()
        os.utime(p, (t, t))

    def run_main(self, fake, *argv):
        with open(self.log, "w") as f:
            f.write("\n".join(self.lines) + "\n")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = pick.main(list(argv) + [self.log], gql=fake, now=NOW, tdir=self.tdir)
        self.err = err.getvalue()
        return rc, out.getvalue().strip()


class ParseAndLiveness(Base):
    def test_parse_ignores_other_lines(self):
        self.add("start", "TASK-1", "a", 60)
        self.add("resume", "TASK-1", "a", 30)
        self.lines += ["pick: TASK-1 (3 in queue)", "2026-09-26 13:04:05 start --dry-run log=/x.jsonl",
                       "2026-09-26 20:45:59 skip: queue empty", "recover: TASK-2 (last updated x)",
                       "2026-09-26 23:00:00 end TASK-1 session=a exit=1"]
        with open(self.log, "w") as f:
            f.write("\n".join(self.lines) + "\n")
        entries = pick.parse_log(self.log)
        self.assertEqual([(e[1], e[2], e[3]) for e in entries], [("start", "TASK-1", "a"), ("resume", "TASK-1", "a")])
        self.assertAlmostEqual(entries[0][0].timestamp(), (NOW - timedelta(minutes=60)).timestamp())

    def test_missing_log_is_empty(self):
        self.assertEqual(pick.parse_log(os.path.join(self.tmp.name, "nope")), [])

    def test_liveness(self):
        self.assertFalse(pick.is_live(self.tdir, "s", NOW))
        self.touch("s.jsonl", 40)
        self.assertFalse(pick.is_live(self.tdir, "s", NOW))
        self.touch("s/subagents/workflows/r/journal.jsonl", 10)
        self.assertTrue(pick.is_live(self.tdir, "s", NOW))
        self.touch("t.jsonl", 29)
        self.assertTrue(pick.is_live(self.tdir, "t", NOW))


def event(status="allowed", five=0.1, **week):
    windows = {"five_hour": {"utilization": five, "resetsAt": 1}}
    windows.update({k: {"utilization": v, "resetsAt": 2} for k, v in week.items()})
    return json.dumps({"type": "rate_limit_event", "rate_limit_info": {
        "status": status, "utilization": five, "rateLimitType": "five_hour", "resetsAt": 1, "unifiedWindows": windows}})


class Gate(unittest.TestCase):
    def ok(self, kind, *lines):
        return pick.gate(kind, list(lines))[0]

    def test_no_event(self):
        self.assertEqual(pick.gate("new", ['{"type":"system"}', "garbage"]), (False, "no rate_limit_event"))

    def test_new(self):
        self.assertTrue(self.ok("new", event(five=0.89)))
        self.assertFalse(self.ok("new", event(five=0.9)))
        self.assertFalse(self.ok("new", event(status="rejected", five=0.1)))
        self.assertFalse(self.ok("new", event(five=0.1, seven_day=1.0)))

    def test_resume(self):
        self.assertTrue(self.ok("resume", event(five=0.89, seven_day=0.99, seven_day_opus=0.5)))
        self.assertFalse(self.ok("resume", event(five=0.9)))
        self.assertFalse(self.ok("resume", event(status="rejected", five=0.1)))
        self.assertFalse(self.ok("resume", event(five=0.1, seven_day=0.2, seven_day_opus=1.0)))
        self.assertTrue(self.ok("resume", event(status="allowed_warning", five=0.5)))

    def test_last_event_wins(self):
        self.assertFalse(self.ok("new", event(five=0.1), event(five=0.9)))
        self.assertTrue(self.ok("new", event(five=0.9), "{}", event(five=0.1)))

    def test_main_reads_stdin(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = pick.main(["--gate", "resume"], gql=None, stdin=io.StringIO(event(five=0.5, seven_day=0.3) + "\n"))
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue().strip(), "status=allowed five_hour=0.5 seven_day=0.3")


class Plan(Base):
    def test_nothing(self):
        fake = FakeLinear([issue("TASK-1", "In Review", ME)])
        self.assertEqual(self.run_main(fake, "--plan"), (0, ""))

    def test_new(self):
        fake = FakeLinear([issue("TASK-1", "Todo")])
        self.assertEqual(self.run_main(fake, "--plan")[1], "new")
        self.assertEqual(fake.mutations, [])

    def test_resume_first_and_second(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=5)), issue("TASK-2", "Todo")])
        self.add("start", "TASK-1", "sid1", 300)
        self.touch("sid1.jsonl", 200)
        self.assertEqual(self.run_main(fake, "--plan")[1], "resume TASK-1 sid1 1 https://linear.app/x/TASK-1")
        self.add("resume", "TASK-1", "sid1", 100)
        self.assertEqual(self.run_main(fake, "--plan")[1], "resume TASK-1 sid1 2 https://linear.app/x/TASK-1")
        self.assertEqual(fake.mutations, [], "candidate is excluded from Recover even when stale")

    def test_resume_cap_falls_back_to_recover(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=5))])
        self.add("start", "TASK-1", "sid1", 300)
        self.add("resume", "TASK-1", "sid1", 200)
        self.add("resume", "TASK-1", "sid1", 150)
        self.assertEqual(self.run_main(fake, "--plan")[1], "new")
        self.assertEqual(fake.issues["TASK-1"]["state"], "Todo")
        self.assertIsNone(fake.issues["TASK-1"]["assignee"])

    def test_live_session_not_resumed_or_recovered(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=5))])
        self.add("start", "TASK-1", "sid1", 300)
        self.touch("sid1/subagents/workflows/r/journal.jsonl", 5)
        self.assertEqual(self.run_main(fake, "--plan"), (0, ""))
        self.assertEqual(fake.mutations, [])

    def test_only_latest_line_is_candidate(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=5)), issue("TASK-2", "In Review", ME)])
        self.add("start", "TASK-1", "sid1", 300)
        self.add("start", "TASK-2", "sid2", 200)
        self.assertEqual(self.run_main(fake, "--plan")[1], "new")
        self.assertEqual(fake.issues["TASK-1"]["state"], "Todo")

    def test_not_ours_not_candidate(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", USER, updated=ago(hours=5))])
        self.add("start", "TASK-1", "sid1", 300)
        self.assertEqual(self.run_main(fake, "--plan"), (0, ""))
        self.assertEqual(fake.mutations, [])

    def test_no_sid_keeps_two_hour_rule(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=3)),
                           issue("TASK-2", "In Progress", ME, updated=ago(hours=1))])
        self.run_main(fake, "--plan")
        self.assertEqual(fake.issues["TASK-1"]["state"], "Todo")
        self.assertIn("interrupted", fake.issues["TASK-1"]["comments"][0])
        self.assertEqual(fake.issues["TASK-2"]["state"], "In Progress")

    def test_attempt_cap_moves_to_review(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(minutes=40))])
        for i, sid in enumerate(["a", "b", "c"]):
            self.add("start", "TASK-1", sid, 400 - i * 50)
        self.add("resume", "TASK-1", "c", 200)
        self.assertEqual(self.run_main(fake, "--plan"), (0, ""))
        self.assertEqual(fake.issues["TASK-1"]["state"], "In Review")
        self.assertEqual(fake.issues["TASK-1"]["comments"], [pick.CAP_COMMENT])

    def capped(self, hist):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=3))], {"TASK-1": hist})
        for i, sid in enumerate("abcd"):
            self.add("start", "TASK-1", sid, 400 - i * 50)
        return fake, self.run_main(fake, "--plan")[1]

    def test_attempt_cap_reset_by_user(self):
        fake, out = self.capped([{"createdAt": ago(minutes=380), "actorId": USER, "toStateId": "s-todo"}])
        self.assertEqual(out, "resume TASK-1 d 1 https://linear.app/x/TASK-1")
        self.assertEqual(fake.mutations, [])

    def test_attempt_cap_not_reset_by_agent_or_other_moves(self):
        fake, out = self.capped([{"createdAt": ago(minutes=380), "actorId": ME, "toStateId": "s-todo"},
                                 {"createdAt": ago(minutes=370), "actorId": USER, "toStateId": "s-prog"},
                                 {"createdAt": ago(minutes=360), "actorId": None, "toStateId": "s-todo"}])
        self.assertEqual(out, "")
        self.assertEqual(fake.issues["TASK-1"]["state"], "In Review")

    def test_dry_run_changes_nothing(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=3)),
                           issue("TASK-2", "In Progress", ME, updated=ago(minutes=40))])
        for sid in "abcd":
            self.add("start", "TASK-2", sid, 300)
        self.add("start", "TASK-3", "z", 100)
        self.run_main(fake, "--plan", "--dry-run")
        self.assertEqual(fake.mutations, [])
        self.assertIn("recover: TASK-1", self.err)
        self.assertIn("recover: TASK-2 reached 4 attempts", self.err)


class Claim(Base):
    def test_priority_then_age(self):
        fake = FakeLinear([issue("TASK-1", "Todo", priority=0, created="2026-01-01T00:00:00Z"),
                           issue("TASK-2", "Todo", priority=3, created="2026-02-01T00:00:00Z"),
                           issue("TASK-3", "Todo", priority=3, created="2026-01-15T00:00:00Z")])
        self.assertEqual(self.run_main(fake, "--claim")[1], "TASK-3 https://linear.app/x/TASK-3")
        self.assertEqual((fake.issues["TASK-3"]["state"], fake.issues["TASK-3"]["assignee"]), ("In Progress", ME))

    def test_capped_todo_goes_to_review(self):
        fake = FakeLinear([issue("TASK-1", "Todo", priority=1), issue("TASK-2", "Todo", priority=2)])
        for sid in "abcd":
            self.add("start", "TASK-1", sid, 300)
        self.assertEqual(self.run_main(fake, "--claim")[1], "TASK-2 https://linear.app/x/TASK-2")
        self.assertEqual(fake.issues["TASK-1"]["state"], "In Review")
        self.assertEqual(fake.issues["TASK-1"]["comments"], [pick.CAP_COMMENT])

    def test_capped_todo_reset_by_user(self):
        hist = {"TASK-1": [{"createdAt": ago(minutes=200), "actorId": USER, "toStateId": "s-todo"}]}
        fake = FakeLinear([issue("TASK-1", "Todo")], hist)
        for sid in "abcd":
            self.add("start", "TASK-1", sid, 300)
        self.assertEqual(self.run_main(fake, "--claim")[1], "TASK-1 https://linear.app/x/TASK-1")

    def test_empty_queue(self):
        self.assertEqual(self.run_main(FakeLinear([]), "--claim"), (0, ""))

    def test_dry_run(self):
        fake = FakeLinear([issue("TASK-1", "Todo")])
        self.assertEqual(self.run_main(fake, "--claim", "--dry-run"), (0, ""))
        self.assertEqual(fake.mutations, [])

    def test_no_mode_recovers_then_claims(self):
        fake = FakeLinear([issue("TASK-1", "In Progress", ME, updated=ago(hours=3))])
        self.assertEqual(self.run_main(fake)[1], "TASK-1 https://linear.app/x/TASK-1")
        self.assertIn("interrupted", fake.issues["TASK-1"]["comments"][0])


if __name__ == "__main__":
    unittest.main()
