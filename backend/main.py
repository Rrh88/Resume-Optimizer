from fastapi import FastAPI, File, HTTPException, UploadFile

from backend import firebase_db as fb
from backend.graph import run_chat
from backend.parser import parse_resume
from backend.schemas import ChatRequest

app = FastAPI(title="Resume Optimizer")


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    data = file.file.read()
    try:
        resume = parse_resume(file.filename, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    cid = fb.create_conversation()
    v = fb.save_version(cid, resume.model_dump(), note="Original upload", agent="parser")
    return {"conversation_id": cid, "version": v, "resume": resume.model_dump()}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        return run_chat(req.conversation_id, req.message, req.job_description or "")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/versions/{cid}")
def versions(cid: str):
    return fb.list_versions(cid)


@app.post("/versions/{cid}/restore/{v}")
def restore(cid: str, v: int):
    ver = fb.get_version(cid, v)
    if not ver:
        raise HTTPException(404, "Version not found")
    fb.set_active_version(cid, v)
    return {"active_version": v, "resume": ver["resume"]}


@app.get("/messages/{cid}")
def messages(cid: str):
    return fb.get_messages(cid, 100)