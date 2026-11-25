import os
import uuid
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
    firebase_admin.initialize_app(cred)

db = firestore.client()


def now():
    return datetime.now(timezone.utc).isoformat()


def create_conversation() -> str:
    cid = str(uuid.uuid4())
    db.collection("conversations").document(cid).set(
        {"created_at": now(), "current_version": 0}
    )
    return cid


def save_message(cid: str, role: str, content: str, reasoning: str = ""):
    db.collection("conversations").document(cid).collection("messages").add(
        {"role": role, "content": content, "reasoning": reasoning, "created_at": now()}
    )


def get_messages(cid: str, limit: int = 20):
    docs = (
        db.collection("conversations").document(cid).collection("messages")
        .order_by("created_at").stream()
    )
    msgs = [d.to_dict() for d in docs]
    return msgs[-limit:]


def save_version(cid: str, resume: dict, note: str = "", agent: str = "") -> int:
    ref = db.collection("conversations").document(cid)
    snap = ref.get().to_dict() or {}
    v = snap.get("current_version", 0) + 1
    ref.collection("versions").document(str(v)).set(
        {"version": v, "resume": resume, "note": note, "agent": agent, "created_at": now()}
    )
    ref.update({"current_version": v, "active_version": v})
    return v


def get_version(cid: str, v: int):
    d = (
        db.collection("conversations").document(cid)
        .collection("versions").document(str(v)).get()
    )
    return d.to_dict() if d.exists else None


def get_active_version(cid: str):
    snap = db.collection("conversations").document(cid).get().to_dict() or {}
    v = snap.get("active_version", 0)
    return get_version(cid, v) if v else None


def set_active_version(cid: str, v: int):
    db.collection("conversations").document(cid).update({"active_version": v})


def list_versions(cid: str):
    docs = (
        db.collection("conversations").document(cid)
        .collection("versions").order_by("version").stream()
    )
    return [d.to_dict() for d in docs]