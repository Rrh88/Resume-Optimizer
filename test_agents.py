from backend.parser import parse_resume
from backend.agents import jd_match, section_enhance, translate

with open("sample.docx", "rb") as f:
    resume = parse_resume("sample.docx", f.read())

r = section_enhance.run(resume, section="skills", instruction="make more relevant", role="Data Scientist")
print("ENHANCE:", r.changes, r.reasoning, "\n")

r = jd_match.run(resume, jd="Data Scientist: Python, SQL, ML, NLP, AWS, MLOps.")
print("JD:", r.match_score, r.skill_gaps, r.changes, "\n")

r = translate.run(resume, "Spanish", "Mexico")
print("TRANSLATE:", r.resume.language, r.reasoning)