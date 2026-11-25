import difflib
import json

import requests
import streamlit as st

API = "http://127.0.0.1:8000"
st.set_page_config(page_title="Resume Optimizer", layout="wide")

ss = st.session_state
ss.setdefault("cid", None)
ss.setdefault("active", 0)
ss.setdefault("resume", None)
ss.setdefault("chat", [])


def api(method, path, **kw):
    try:
        r = requests.request(method, API + path, timeout=300, **kw)
    except Exception as e:
        st.error(f"Backend not reachable: {e}")
        return None
    if r.status_code >= 400:
        try:
            st.error(r.json().get("detail", r.text))
        except Exception:
            st.error(r.text)
        return None
    return r.json()


if not ss.cid and st.query_params.get("cid"):
    ss.cid = st.query_params["cid"]
    _vs = api("GET", f"/versions/{ss.cid}") or []
    if _vs:
        ss.active = _vs[-1]["version"]
        ss.resume = _vs[-1]["resume"]
    for _m in api("GET", f"/messages/{ss.cid}") or []:
        ss.chat.append({"role": _m["role"], "content": _m["content"]})


def restore(v):
    res = api("POST", f"/versions/{ss.cid}/restore/{v}")
    if res:
        ss.active = res["active_version"]
        ss.resume = res["resume"]
        st.rerun()


def show_resume(r):
    st.subheader(r.get("name", ""))
    st.caption(" | ".join(x for x in [r.get("email"), r.get("phone"), r.get("location")] if x))
    if r.get("summary"):
        st.markdown("**Summary**")
        st.write(r["summary"])
    if r.get("experience"):
        st.markdown("**Experience**")
        for e in r["experience"]:
            st.markdown(f"*{e.get('title','')}* - {e.get('company','')} ({e.get('duration','')})")
            for b in e.get("bullets", []):
                st.markdown(f"- {b}")
    if r.get("projects"):
        st.markdown("**Projects**")
        for p in r["projects"]:
            st.markdown(f"*{p.get('name','')}* {p.get('description','')}")
            for b in p.get("bullets", []):
                st.markdown(f"- {b}")
    if r.get("skills"):
        st.markdown("**Skills**")
        st.write(", ".join(r["skills"]))
    if r.get("education"):
        st.markdown("**Education**")
        for e in r["education"]:
            st.markdown(f"- {e.get('degree','')}, {e.get('institution','')} ({e.get('duration','')})")
    if r.get("certifications"):
        st.markdown("**Certifications**")
        for c in r["certifications"]:
            st.markdown(f"- {c}")


def show_steps(steps):
    for s in steps:
        with st.expander(f"Agent: {s['agent']}", expanded=False):
            st.write(s["reasoning"])
            if s.get("match_score") is not None:
                st.metric("Match score", f"{s['match_score']}/100")
            if s.get("skill_gaps"):
                st.write("Skill gaps: " + ", ".join(s["skill_gaps"]))
            for c in s.get("changes", []):
                st.markdown(f"- {c}")


vers = []
with st.sidebar:
    st.header("Resume")
    f = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    if f and st.button("Process resume"):
        with st.spinner("Parsing resume..."):
            res = api("POST", "/upload", files={"file": (f.name, f.getvalue())})
        if res:
            ss.cid = res["conversation_id"]
            st.query_params["cid"] = ss.cid
            ss.active = res["version"]
            ss.resume = res["resume"]
            ss.chat = []
            st.rerun()
    jd = st.text_area("Job description (optional)", height=150, key="jd")

    if ss.cid:
        st.divider()
        st.subheader("Versions")
        vers = api("GET", f"/versions/{ss.cid}") or []
        nums = [v["version"] for v in vers]
        c1, c2 = st.columns(2)
        if c1.button("Undo") and ss.active > 1:
            restore(ss.active - 1)
        if c2.button("Redo") and nums and ss.active < max(nums):
            restore(ss.active + 1)
        st.caption(f"Active: v{ss.active}")
        for v in vers:
            st.write(f"v{v['version']} - {v.get('agent', '')} - {v.get('note', '')[:35]}")

st.title("Chat with your resume")
tab_chat, tab_resume, tab_cmp = st.tabs(["Chat", "Current resume", "Compare versions"])

with tab_chat:
    if not ss.cid:
        st.info("Upload a resume in the sidebar to start.")
    for m in ss.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("changed"):
                st.caption("Changed sections: " + ", ".join(m["changed"]))
            show_steps(m.get("steps", []))

with tab_resume:
    if ss.resume:
        show_resume(ss.resume)

with tab_cmp:
    if len(vers) >= 2:
        nums = [v["version"] for v in vers]
        a = st.selectbox("From version", nums, index=0)
        b = st.selectbox("To version", nums, index=len(nums) - 1)
        vmap = {v["version"]: v["resume"] for v in vers}
        x = json.dumps(vmap[a], indent=2, ensure_ascii=False).splitlines()
        y = json.dumps(vmap[b], indent=2, ensure_ascii=False).splitlines()
        d = "\n".join(difflib.unified_diff(x, y, f"v{a}", f"v{b}", lineterm="", n=1))
        st.code(d or "No differences", language="diff")
    else:
        st.info("Make at least one change to compare versions.")

prompt = st.chat_input("e.g. Optimize my resume for Google", disabled=not ss.cid)
if prompt and ss.cid:
    ss.chat.append({"role": "user", "content": prompt})
    with tab_chat:
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Agents are working..."):
                res = api("POST", "/chat", json={
                    "conversation_id": ss.cid,
                    "message": prompt,
                    "job_description": jd or None,
                })
    if res:
        ss.chat.append({
            "role": "assistant",
            "content": res["reply"],
            "steps": res["steps"],
            "changed": res["changed_sections"],
        })
        ss.active = res["version"]
        ss.resume = res["resume"]
    st.rerun()