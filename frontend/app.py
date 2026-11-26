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


HEADINGS = {
    "en": ["Summary", "Experience", "Projects", "Skills", "Education", "Certifications"],
    "es": ["Resumen", "Experiencia", "Proyectos", "Habilidades", "Formación", "Certificaciones"],
    "fr": ["Résumé", "Expérience", "Projets", "Compétences", "Formation", "Certifications"],
    "de": ["Zusammenfassung", "Berufserfahrung", "Projekte", "Kenntnisse", "Ausbildung", "Zertifizierungen"],
    "pt": ["Resumo", "Experiência", "Projetos", "Habilidades", "Formação", "Certificações"],
}


def show_resume(r):
    lang = (r.get("language") or "en")[:2].lower()
    h = HEADINGS.get(lang, HEADINGS["en"])
    st.subheader(r.get("name", ""))
    contact = [r.get("email"), r.get("phone"), r.get("location")]
    st.caption(" | ".join(x for x in contact if x))

    if r.get("summary"):
        st.markdown("**" + h[0] + "**")
        st.write(r["summary"])

    if r.get("experience"):
        st.markdown("**" + h[1] + "**")
        for e in r["experience"]:
            title = e.get("title", "")
            company = e.get("company", "")
            duration = e.get("duration", "")
            st.markdown("*" + title + "* - " + company + " (" + duration + ")")
            for b in e.get("bullets", []):
                st.markdown("- " + b)

    if r.get("projects"):
        st.markdown("**" + h[2] + "**")
        for p in r["projects"]:
            pname = p.get("name", "")
            pdesc = p.get("description", "")
            st.markdown("*" + pname + "* " + pdesc)
            for b in p.get("bullets", []):
                st.markdown("- " + b)

    if r.get("skills"):
        st.markdown("**" + h[3] + "**")
        st.write(", ".join(r["skills"]))

    if r.get("education"):
        st.markdown("**" + h[4] + "**")
        for e in r["education"]:
            degree = e.get("degree", "")
            inst = e.get("institution", "")
            dur = e.get("duration", "")
            line = "- " + degree + ", " + inst + " (" + dur + ")"
            st.markdown(line)

    if r.get("certifications"):
        st.markdown("**" + h[5] + "**")
        for c in r["certifications"]:
            st.markdown("- " + c)


def show_steps(steps):
    for s in steps:
        with st.expander("Agent: " + s["agent"], expanded=False):
            st.write(s["reasoning"])
            if s.get("match_score") is not None:
                st.metric("Match score", str(s["match_score"]) + "/100")
            if s.get("skill_gaps"):
                st.write("Skill gaps: " + ", ".join(s["skill_gaps"]))
            for c in s.get("changes", []):
                st.markdown("- " + c)


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
        st.caption("Active: v" + str(ss.active))
        for v in vers:
            note = v.get("note", "")[:35]
            agent = v.get("agent", "")
            st.write("v" + str(v["version"]) + " - " + agent + " - " + note)

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
        d = "\n".join(difflib.unified_diff(x, y, "v" + str(a), "v" + str(b), lineterm="", n=1))
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