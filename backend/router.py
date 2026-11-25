from backend.llm import invoke_structured
from backend.schemas import RouterDecision

SYSTEM = """You are the router of a resume optimization chat system.
The user ALWAYS has a resume uploaded. Any request to change, optimize, tailor, improve, rewrite or translate the resume MUST get at least one agent.
Agents:
- jd_match: optimize/tailor the resume for a company, role or job description; match score, skill gaps
- section_enhance: improve specific sections (quantify, action verbs, impact statements, consistency, skills relevance)
- translate: translate/localize the resume to another language or market
Rules:
- Use [] ONLY for pure questions/chitchat (put the answer in reply).
- Translation always goes LAST in the list.
- target_section: section name if named (summary, experience, skills, projects, education), else "".
- target_language and market: only for translate.
- target_company / target_role: fill if named.
- needs_jd: true ONLY if the user says 'this job description' / 'this JD' and JD provided is False. A named company or role does NOT need a JD.
Examples:
"Optimize my resume for Google" -> agents=[jd_match], target_company=Google
"Tailor my resume for a data scientist role" -> agents=[jd_match], target_role=data scientist
"Make my skills section more relevant for a data scientist role" -> agents=[section_enhance], target_section=skills, target_role=data scientist
"Improve my experience bullets" -> agents=[section_enhance], target_section=experience
"Translate to Spanish for Mexico" -> agents=[translate], target_language=Spanish, market=Mexico
"Make my summary stronger and translate to French" -> agents=[section_enhance, translate]
"What is a good resume length?" -> agents=[], reply=answer
"""

KEYWORDS_JD = ("optimi", "tailor", "match", "for google", "job description", " jd")
KEYWORDS_ENH = ("improve", "enhance", "rewrite", "stronger", "quantif", "section")
KEYWORDS_TR = ("translate", "translation", "localize")


def _fallback(message: str, d: RouterDecision) -> RouterDecision:
    m = message.lower()
    agents = []
    if any(k in m for k in KEYWORDS_JD):
        agents.append("jd_match")
    if any(k in m for k in KEYWORDS_ENH):
        agents.append("section_enhance")
    if any(k in m for k in KEYWORDS_TR):
        agents.append("translate")
    d.agents = agents
    return d


def route(message: str, history: list, has_jd: bool) -> RouterDecision:
    hist = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    prompt = (
        f"{SYSTEM}\nHistory:\n{hist}\n\n"
        f"JD provided: {has_jd}\nUser message: {message}"
    )
    d = invoke_structured(RouterDecision, prompt, 0)
    if not d.agents and not d.needs_jd:
        d = _fallback(message, d)
    return d