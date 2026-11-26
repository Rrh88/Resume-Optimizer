# Conversational Resume Optimization System

Chat with your resume. Upload a PDF/DOCX, then ask things like "Optimize my resume for Google", "Translate this to Spanish for the Mexican market" or "Make my skills section more relevant for a data scientist role". A router sends each message to the right agent(s), every change is saved as a version in Firebase, and you can undo, redo and compare versions.

## Implemented agents (3 of 4)
1. **JD Matching Agent**: analyzes a job description (or a target company/role), gives a match score (0-100), lists skill gaps, and restructures the resume to highlight relevant experience.
2. **Section Enhancement Agent**: improves a requested section with action verbs, impact statements and consistent style.
3. **Translation & Localization Agent**: translates and adapts headings, tone and date formats to the target market.

The Company Research agent is not implemented (web research was out of scope for the 24-hour limit).

## Architecture
```mermaid
flowchart TD
    UI[Streamlit chat UI] -->|upload| API[FastAPI]
    UI -->|chat| API
    API --> P[Parser: PDF/DOCX to text to Resume JSON]
    API --> G[LangGraph]
    G --> R[Router: intent to ordered agent list]
    R -->|agents| A[Agents node: JD Match, Section Enhance, Translate in order]
    R -->|question or JD missing| E[Direct reply]
    A --> V[Guard: reject empty or invalid output]
    V --> S[Save new version]
    S --> F[(Firebase Firestore)]
    P --> F
    G -.-> L[Gemini API with fallback models]
```

Flow of one chat message:
1. Message, last messages of history and the active resume version are loaded from Firestore.
2. The **router** returns structured output (agents in order, target section, language, market, company, role, needs_jd).
3. Agents run **sequentially**, each receiving the output resume of the previous one (this is how multi-agent requests like "strengthen my summary, then translate to French" work). Translation always runs last.
4. A guard rejects an agent output if it dropped content (empty name or experience).
5. The result is saved as a new version; the UI shows reasoning, changes, match score and skill gaps.

## Code components
| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI endpoints: `/upload`, `/chat`, `/versions/{id}`, `/versions/{id}/restore/{v}`, `/messages/{id}` |
| `backend/graph.py` | LangGraph orchestration (route, agents, save) and `run_chat` |
| `backend/router.py` | Intent router (LLM structured output + keyword fallback) |
| `backend/parser.py` | PDF (PyMuPDF) / DOCX (python-docx) text extraction and conversion to structured Resume JSON |
| `backend/agents/` | `jd_match.py`, `section_enhance.py`, `translate.py`, shared `base.py` (rules + structured output) |
| `backend/firebase_db.py` | Firestore: conversations, messages, versions, active version |
| `backend/llm.py` | Gemini client with retries and fallback across models |
| `backend/schemas.py` | Pydantic models (Resume, RouterDecision, AgentResult) |
| `frontend/app.py` | Streamlit chat UI: upload, chat, agent reasoning, current resume, undo/redo, version diff |

## Context engineering choices
- **Structured resume state**: the resume is parsed once into JSON (summary, experience, skills, projects, education...). Agents edit sections, not raw text, which makes diffs, versioning and section-level edits reliable.
- **Minimal context per agent**: agents receive only the current resume JSON, the task and the target (JD/company/role/section/language). They do not receive chat history, which keeps cost and noise low.
- **Router gets conversation context**: only the last few messages plus whether a JD was provided, enough to resolve follow-ups.
- **Truthfulness rules in every agent prompt**: never invent employers, dates, metrics or skills; never change job titles, companies, degrees or contact details (except when translating); if a metric is missing, say what the user could add.
- **State management**: every change creates an immutable version in Firestore with note and agent name; an `active_version` pointer enables undo/redo and compare.
- **Validation**: Pydantic structured output for router and agents; a guard rejects outputs that lose core content.
- **Reliability**: retries and automatic fallback across Gemini models (free tier returns 503 under load).

## Tools, APIs and why
- **LangGraph / LangChain**: explicit graph for routing and multi-step workflows.
- **FastAPI**: clean chat API design, typed request/response.
- **Firebase Firestore**: required; stores messages and resume versions.
- **Gemini API (free tier)**: chosen to keep the whole project free; model configured through `GEMINI_MODEL`.
- **PyMuPDF / python-docx**: PDF and DOCX parsing.
- **Streamlit**: fastest way to build the chat UI, spinner as typing indicator, tabs for resume and diff.
- **Vector DB**: not used. Resumes fit in the context window, so retrieval adds complexity without benefit here.

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Create `.env`:
```
GOOGLE_API_KEY=your_key
FIREBASE_CREDENTIALS_PATH=firebase-key.json
GEMINI_MODEL=gemini-3.5-flash-lite
```
Place your Firebase service account JSON as `firebase-key.json` in the project root.

Run (two terminals):
```bash
uvicorn backend.main:app --reload
streamlit run frontend/app.py
```
Open http://localhost:8501, upload a resume, and start chatting.

## Features
- PDF/DOCX upload and parsing
- Intent routing and multi-agent coordination
- Agent reasoning, changes, match score and skill gaps shown in chat
- Follow-up questions and clarifications (e.g. asks for a JD when needed)
- Version history, undo/redo, version diff (bonus)
- Typing indicator while agents work (bonus, spinner)

## Limitations
- No authentication; Firestore runs in test mode (development only).
- Scanned image-only PDFs are not supported (no OCR).
- Company Research agent and exporting the edited resume back to PDF/DOCX are not implemented.
- Free-tier