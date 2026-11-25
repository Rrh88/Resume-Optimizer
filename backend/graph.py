from typing import TypedDict

from langgraph.graph import END, StateGraph

from backend import firebase_db as fb
from backend.agents import jd_match, section_enhance, translate
from backend.router import route
from backend.schemas import Resume


class State(TypedDict, total=False):
    cid: str
    message: str
    jd: str
    history: list
    resume: dict
    decision: dict
    steps: list
    final_resume: dict
    version: int


def route_node(state):
    d = route(state["message"], state.get("history", []), bool(state.get("jd")))
    return {"decision": d.model_dump()}


def after_route(state):
    d = state["decision"]
    if d["needs_jd"] or not d["agents"]:
        return "end"
    return "agents"


def agents_node(state):
    d = state["decision"]
    resume = Resume(**state["resume"])
    steps = []
    for name in d["agents"]:
        if name == "jd_match":
            r = jd_match.run(resume, jd=state.get("jd", ""), company=d["target_company"], role=d["target_role"])
        elif name == "section_enhance":
            r = section_enhance.run(resume, section=d["target_section"], instruction=state["message"], role=d["target_role"])
        else:
            r = translate.run(resume, d["target_language"] or "English", d["market"])
        lost = (resume.experience and not r.resume.experience) or (resume.name and not r.resume.name)
        if lost:
            steps.append({
                "agent": name,
                "reasoning": "Agent output was invalid (content missing), change rejected.",
                "changes": [], "match_score": None, "skill_gaps": [],
            })
            continue
        resume = r.resume
        steps.append({
            "agent": name,
            "reasoning": r.reasoning,
            "changes": r.changes,
            "match_score": r.match_score,
            "skill_gaps": r.skill_gaps,
        })
    return {"steps": steps, "final_resume": resume.model_dump()}


def save_node(state):
    agents = ",".join(s["agent"] for s in state["steps"])
    v = fb.save_version(state["cid"], state["final_resume"], note=state["message"], agent=agents)
    return {"version": v}


g = StateGraph(State)
g.add_node("route", route_node)
g.add_node("agents", agents_node)
g.add_node("save", save_node)
g.set_entry_point("route")
g.add_conditional_edges("route", after_route, {"agents": "agents", "end": END})
g.add_edge("agents", "save")
g.add_edge("save", END)
graph = g.compile()


def run_chat(cid: str, message: str, jd: str = ""):
    active = fb.get_active_version(cid)
    if not active:
        raise ValueError("No resume uploaded for this conversation")
    old = active["resume"]
    history = fb.get_messages(cid, 10)
    fb.save_message(cid, "user", message)

    out = graph.invoke({
        "cid": cid, "message": message, "jd": jd,
        "history": history, "resume": old,
    })
    d = out["decision"]

    if d["needs_jd"]:
        reply = "Please paste the job description so I can match your resume to it."
        out_steps, new, version = [], old, active["version"]
    elif not d["agents"]:
        reply = d["reply"] or "I can optimize for a company/role, match a job description, enhance a section, or translate your resume."
        out_steps, new, version = [], old, active["version"]
    else:
        out_steps, new, version = out["steps"], out["final_resume"], out["version"]
        reply = "\n".join(f"[{s['agent']}] {s['reasoning']}" for s in out_steps)

    changed = [k for k in new if new.get(k) != old.get(k)]
    fb.save_message(cid, "assistant", reply, reasoning=str(out_steps))
    return {
        "reply": reply,
        "steps": out_steps,
        "changed_sections": changed,
        "version": version,
        "resume": new,
        "decision": d,
        "received_message": message,
    }