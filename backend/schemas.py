from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Experience(BaseModel):
    company: str = ""
    title: str = ""
    duration: str = ""
    bullets: List[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    duration: str = ""


class Project(BaseModel):
    name: str = ""
    description: str = ""
    bullets: List[str] = Field(default_factory=list)


class Resume(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    language: str = "en"


class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    job_description: Optional[str] = None


class RouterDecision(BaseModel):
    agents: List[Literal["jd_match", "section_enhance", "translate"]] = Field(default_factory=list)
    target_section: str = ""
    target_language: str = ""
    market: str = ""
    target_company: str = ""
    target_role: str = ""
    needs_jd: bool = False
    reply: str = ""


class AgentResult(BaseModel):
    resume: Resume
    reasoning: str = ""
    changes: List[str] = Field(default_factory=list)
    match_score: Optional[int] = None
    skill_gaps: List[str] = Field(default_factory=list)