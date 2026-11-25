import sys

from backend.parser import parse_resume

path = sys.argv[1]
with open(path, "rb") as f:
    data = f.read()
resume = parse_resume(path, data)
print(resume.model_dump_json(indent=2))