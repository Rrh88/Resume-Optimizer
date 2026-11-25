from backend import firebase_db as fb
from backend.parser import parse_resume

with open("sample.docx", "rb") as f:
    resume = parse_resume("sample.docx", f.read())
cid = fb.create_conversation()
fb.save_version(cid, resume.model_dump(), note="Original upload", agent="parser")
print("CID:", cid)