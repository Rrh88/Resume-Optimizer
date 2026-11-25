from backend.llm import invoke_structured
from backend.schemas import AgentResult, Resume

RULES = """RULES:
- Never invent employers, dates, degrees, metrics, or skills the candidate does not have.
- NEVER change job titles, company names, degree names, dates or contact details (except when translating).
- Use only numbers already present in the resume. If a metric is missing, keep the bullet factual and mention in reasoning which metric the user could add.
- Return the FULL updated resume in `resume`, same structure.
- `changes`: short list of what changed. `reasoning`: 2-3 sentences explaining why."""


def run_agent(system: str, task: str, resume: Resume) -> AgentResult:
    prompt = (
        f"{system}\n\n{RULES}\n\nTASK:\n{task}\n\n"
        f"CURRENT RESUME JSON:\n{resume.model_dump_json()}"
    )
    return invoke_structured(AgentResult, prompt, 0.3)