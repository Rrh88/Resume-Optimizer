from backend import firebase_db as fb

cid = fb.create_conversation()
fb.save_message(cid, "user", "hello")
v = fb.save_version(cid, {"name": "Test"}, note="test")
print("OK", cid, v, fb.get_active_version(cid))