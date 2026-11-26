from backend.agents.base import run_agent
from backend.knowledge import search_conventions

SYSTEM = (
    "You are a Translation and Localization agent. Translate the resume with professional quality "
    "and adapt tone, headings, date formats and content to local hiring conventions of the target market. "
    "Do not translate names, company names or technical terms. Set resume.language to the language code. "
    "In reasoning, state the local conventions you applied."
)


def run(resume, language, market=""):
    conv = search_conventions(f"{market} {language} resume hiring conventions")
    task = (
        f"Translate the whole resume to {language}. Target market: {market or 'general'}.\n"
        f"Retrieved local hiring conventions (apply headings, date format and tone; "
        f"never add personal data such as photo, date of birth or marital status that the candidate did not provide):\n{conv}"
    )
    return run_agent(SYSTEM, task, resume)