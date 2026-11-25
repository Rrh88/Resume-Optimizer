from backend.agents.base import run_agent

SYSTEM = (
    "You are a Translation and Localization agent. Translate the resume with professional quality "
    "and adapt tone, headings, date formats and content to local hiring conventions of the target market. "
    "Do not translate names, company names or technical terms. Set resume.language to the language code. "
    "In reasoning, state the local conventions you applied."
)


def run(resume, language, market=""):
    task = f"Translate the whole resume to {language}. Target market: {market or 'general'}."
    return run_agent(SYSTEM, task, resume)