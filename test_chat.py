import sys

from backend.graph import run_chat

cid = sys.argv[1]
msg = sys.argv[2]
out = run_chat(cid, msg)
print("RECEIVED:", repr(msg))
print("DECISION:", out.get("decision"))
print("REPLY:", out["reply"])
print("CHANGED:", out["changed_sections"])