#!/usr/bin/env python3
"""Linear GraphQL from the command line.

linear.py QUERY [VARS_JSON]   run a query or mutation; QUERY may be @file or - (stdin); prints `data` as JSON
linear.py --type NAME         list a type's fields, input fields or enum values (Query and Mutation are types)
"""
import json
import os
import subprocess
import sys
import urllib.request

TYPE_QUERY = """query($n: String!) { __type(name: $n) { kind
  fields { name args { name type { ...T } } type { ...T } }
  inputFields { name type { ...T } }
  enumValues { name } } }
fragment T on __Type { kind name ofType { kind name ofType { kind name ofType { kind name } } } }"""


def api_key():
    service = os.environ.get("LINEAR_KEYCHAIN_SERVICE")
    if not service and os.environ.get("LINEAR_API_KEY"):
        return os.environ["LINEAR_API_KEY"]
    service = service or "linear-api-key"
    account = os.environ.get("LINEAR_KEYCHAIN_ACCOUNT")
    r = subprocess.run(["security", "find-generic-password", "-s", service, "-w"]
                       + (["-a", account] if account else []), capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"no Linear API key in Keychain service {service}: see {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/README.md")
    return r.stdout.strip()


def gql(query, variables=None):
    key = api_key()
    req = urllib.request.Request("https://api.linear.app/graphql",
                                 data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": key})
    try:
        with urllib.request.urlopen(req) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        body = json.load(e)
    if body.get("errors"):
        raise SystemExit(json.dumps(body["errors"], indent=2))
    return body["data"]


def type_name(t):
    if t["kind"] == "NON_NULL":
        return type_name(t["ofType"]) + "!"
    if t["kind"] == "LIST":
        return f"[{type_name(t['ofType'])}]"
    return t["name"]


def describe(name):
    t = gql(TYPE_QUERY, {"n": name})["__type"]
    if not t:
        raise SystemExit(f"no type {name}")
    for f in t["fields"] or []:
        args = ", ".join(f"{a['name']}: {type_name(a['type'])}" for a in f["args"])
        print(f"{f['name']}({args}): {type_name(f['type'])}" if args else f"{f['name']}: {type_name(f['type'])}")
    for f in t["inputFields"] or []:
        print(f"{f['name']}: {type_name(f['type'])}")
    for v in t["enumValues"] or []:
        print(v["name"])


def main(argv):
    if len(argv) == 2 and argv[0] == "--type":
        return describe(argv[1])
    if not 1 <= len(argv) <= 2 or argv[0].startswith("--"):
        raise SystemExit(__doc__.strip())
    q = argv[0]
    q = sys.stdin.read() if q == "-" else open(q[1:]).read() if q.startswith("@") else q
    print(json.dumps(gql(q, json.loads(argv[1]) if len(argv) == 2 else None), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
