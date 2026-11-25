from backend.agents.base import run_agent

SYSTEM = (
    "You are a Section Enhancement agent. Improve the requested section using strong action verbs, "
    "impact statements (action + result), consistent tense and style, and relevance to the target role. "
    "Keep other sections unchanged except for consistency fixes."
)


def run(resume, section="", instruction="", role=""):
    task = (
        f"Section to improve: {section or 'all sections'}\n"
        f"User request: {instruction}\nTarget role: {role or 'N/A'}"
    )
    return run_agent(SYSTEM, task, resume)