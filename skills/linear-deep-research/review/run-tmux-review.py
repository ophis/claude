#!/usr/bin/env python3
# Review draft: reuse one interactive Claude after its foreground/background work ends.
# This checks execution state. Linear writeback remains the Skill's responsibility.
import fcntl
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

SESSION = "linear-research"
BASE = Path.home()
STATE = BASE / ".local/state/linear-research"
WORK = STATE / "work"

def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def command(*args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True,
                          timeout=10, **kwargs).stdout.strip()

def idle():
    rows = command("tmux", "list-panes", "-s", "-t", "=" + SESSION,
                   "-F", "#{pane_id} #{pane_pid}").splitlines()
    require(len(rows) == 1, "expected one research pane")
    pane, pid = rows[0].split()
    entry = json.loads((BASE / ".claude/sessions" / (pid + ".json")).read_text())
    started = command("ps", "-p", pid, "-o", "lstart=")
    require(entry.get("pid") == int(pid) and entry.get("procStart") == started,
            "Claude process does not match registry")
    require(entry.get("kind") == "interactive" and not entry.get("parkedJobId"),
            "not an independent interactive Claude session")
    require(entry.get("status") == "idle", "Claude is busy")
    return pane, pid, started, entry["sessionId"]

def finished(identity):
    paths = list((BASE / ".claude/projects").glob(f"*/{identity[3]}.jsonl"))
    require(len(paths) == 1, "main transcript missing or ambiguous")
    path = paths[0]
    raw = path.read_bytes()
    require(raw.endswith(b"\n"), "transcript still being written")
    pending, workflows, notices, queued, last = set(), {}, "", 0, None
    for line in raw.splitlines():
        row = json.loads(line)
        kind = row.get("type")
        content = row.get("message", {}).get("content", [])
        if kind in {"assistant", "user", "attachment", "queue-operation"}:
            last = row
        if kind == "queue-operation":
            op = row.get("operation")
            require(op in {"enqueue", "dequeue"}, "unknown queue state")
            queued += 1 if op == "enqueue" else -1
        if kind == "user" and isinstance(content, str):
            notices += content + "\n"
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use":
                pending.add(block["id"])
            elif block.get("type") == "tool_result":
                pending.discard(block["tool_use_id"])
        result = row.get("toolUseResult")
        if isinstance(result, dict) and result.get("status") == "async_launched":
            require(result.get("taskType") == "local_workflow", "other background task unconfirmed")
            workflows[result["runId"]] = result["taskId"]
    require(not pending and queued == 0, "tool calls or queued input remain")
    require(last and last.get("type") == "assistant" and
            last["message"].get("stop_reason") == "end_turn" and
            not last.get("isApiErrorMessage"), "main turn has not ended normally")
    end = datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))
    files = list((path.with_suffix("") / "workflows").glob("*.json"))
    require({p.stem for p in files} == set(workflows), "workflow records incomplete")
    for file in files:
        wf = json.loads(file.read_text())
        require(wf.get("status") == "completed", "research not finished: " + file.stem)
        require(f"<task-id>{workflows[file.stem]}</task-id>" in notices,
                "main session has not received the research result")
        require(end >= datetime.fromisoformat(wf["timestamp"].replace("Z", "+00:00")),
                "main session has not finished its turn after research")

def send(text, identity):
    require(idle() == identity, "session changed before input")
    buffer = "linear-" + uuid.uuid4().hex
    command("tmux", "load-buffer", "-b", buffer, "-", input=text)
    command("tmux", "paste-buffer", "-p", "-d", "-b", buffer, "-t", identity[0])
    time.sleep(0.1)
    require(idle() == identity, "session changed; Enter withheld")
    command("tmux", "send-keys", "-t", identity[0], "Enter")

def main():
    os.environ["PATH"] = f"{BASE}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
    os.environ["LC_ALL"] = "C"
    require(sys.argv[1:] in ([], ["--dry-run"]), "usage: run-tmux-review.py [--dry-run]")
    prompt = ("Use the linear-deep-research skill to handle the next Todo issue in the "
              "Deep Research project. Call /deep-research at most once for this issue "
              "in this invocation; do not retry. Finish the report and Linear updates.")
    if "--dry-run" in sys.argv:
        prompt = ("Read the linear-deep-research skill and evaluate only Recover and Pick. "
                  "Report what would happen. Do not modify anything or launch a workflow.")
    WORK.mkdir(parents=True, exist_ok=True)
    with (STATE / "launcher.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("another launcher is active")
        exists = subprocess.run(["tmux", "has-session", "-t", "=" + SESSION],
                                text=True, capture_output=True, timeout=10)
        if exists.returncode:
            require(any(s in exists.stderr for s in ("can't find session", "no server running",
                        "no sessions", "No such file or directory")), exists.stderr.strip())
            claude = shutil.which("claude")
            require(claude, "claude executable not found")
            args = [claude, "--permission-mode", "auto", "--model", "opus",
                    "--effort", "xhigh", prompt]
            command("tmux", "new-session", "-d", "-s", SESSION, "-c", str(WORK),
                    "exec " + shlex.join(args))
            print("started: " + SESSION)
            return
        previous = idle()
        finished(previous)
        require(idle() == previous, "session changed during idle check")
        send("/clear", previous)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                now = idle()
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                time.sleep(0.25)
                continue
            require(now[:3] == previous[:3], "Claude process changed during /clear")
            if now[3] != previous[3]:
                send(prompt, now)
                print("reused: " + SESSION)
                return
            time.sleep(0.25)
        raise RuntimeError("/clear not confirmed; no new task submitted")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.SubprocessError) as error:
        print("skip: " + str(error))
