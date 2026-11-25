from backend.agents.base import run_agent

SYSTEM = (
    "You are a Job Description Matching agent. Analyze the job description "
    "(or the target company/role), compute match_score (0-100) of the resume against it, "
    "list skill_gaps (required skills missing from the resume), and restructure and reword "
    "the resume to highlight the most relevant experience, skills and keywords, truthfully."
)


def run(resume, jd="", company="", role=""):
    task = (
        f"Target company: {company or 'N/A'}\nTarget role: {role or 'N/A'}\n"
        f"Job description:\n{jd or 'Not provided. Infer typical requirements for the company/role.'}"
    )
    return run_agent(SYSTEM, task, resume)