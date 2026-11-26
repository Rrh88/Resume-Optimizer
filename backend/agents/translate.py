from backend.agents.base import run_agent
from backend.knowledge import search_conventions

SYSTEM = (
    "You are a Translation and Localization agent. Translate the ENTIRE resume into the target language. "
    "You MUST translate every one of these fields: summary, every job title, every bullet, "
    "every project name and project description, every degree name and field of study "
    "(for example 'Master of Science in Physics'), every certification name and its date (month names), "
    "and generic skill phrases (for example 'Prompt Engineering'). "
    "Keep unchanged ONLY: the person's name, company names, university and institution names, "
    "tool, library and product names (Python, FastAPI, LangChain, Docker, AWS and similar), email and phone. "
    "Adapt tone and date formats to local hiring conventions. "
    "Set resume.language to the language code. "
    "In reasoning, state the local conventions you applied."
)


def _same(a, b):
    return (a or "").strip().lower() == (b or "").strip().lower()


def _untranslated(old, new):
    issues = []
    for o, n in zip(old.experience, new.experience):
        if o.title and _same(o.title, n.title):
            issues.append("job title: " + o.title)
    for o, n in zip(old.education, new.education):
        if o.degree and _same(o.degree, n.degree):
            issues.append("degree: " + o.degree)
    for o, n in zip(old.certifications, new.certifications):
        if _same(o, n):
            issues.append("certification: " + o)
    for o, n in zip(old.projects, new.projects):
        if o.description and _same(o.description, n.description):
            issues.append("project description: " + o.name)
    return issues


def run(resume, language, market=""):
    conv = search_conventions(market + " " + language + " resume hiring conventions")
    task = (
        "Translate the whole resume to " + language + ". Target market: " + (market or "general") + ".\n"
        "Retrieved local hiring conventions (apply date format and tone; "
        "never add personal data such as photo, date of birth or marital status "
        "that the candidate did not provide):\n" + conv
    )
    r = run_agent(SYSTEM, task, resume)
    if language.strip().lower() not in ("english", "en"):
        issues = _untranslated(resume, r.resume)
        if issues:
            retry = (
                task
                + "\n\nYour previous answer left these fields untranslated. "
                + "Translate them now and return the full resume:\n- "
                + "\n- ".join(issues)
            )
            r2 = run_agent(SYSTEM, retry, resume)
            if len(_untranslated(resume, r2.resume)) <= len(issues):
                r = r2
    return r