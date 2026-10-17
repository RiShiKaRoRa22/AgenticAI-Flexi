import sys, json
from db import init_db
from agents import run

if __name__ == "__main__":
    init_db()
    q = " ".join(sys.argv[1:]) or "Which categories did I overspend in September 2026?"
    res = run(q)
    print("\nPLAN:\n", res["plan"])
    print("\nTOOL CALLS:")
    for t in res["trace"]:
        print(" -", t["tool"], json.dumps(t["input"]))
    print("\nANSWER:\n", res["answer"])
    print("\nREVIEW:", res["review"], "| retried:", res["retried"])
