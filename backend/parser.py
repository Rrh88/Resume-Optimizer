import io

import pymupdf
from docx import Document

from backend.llm import invoke_structured
from backend.schemas import Resume


def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        doc = pymupdf.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    if name.endswith(".docx"):
        d = Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    raise ValueError("Only PDF or DOCX files are supported")


def parse_resume(filename: str, data: bytes) -> Resume:
    text = extract_text(filename, data)
    if len(text.strip()) < 50:
        raise ValueError("Could not read text from the file (scanned or empty)")
    prompt = (
        "Extract this resume into the given structure. "
        "Do not invent or change any information. "
        "Keep bullets exactly as written. Detect the language code (en, es, hi, etc.).\n\n"
        f"RESUME TEXT:\n{text}"
    )
    return invoke_structured(Resume, prompt, 0)