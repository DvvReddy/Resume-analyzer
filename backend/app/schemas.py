from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


AssessmentMode = Literal["resume", "questions"]
TimelineOption = Literal["< 1 month", "1-3 months", "3+ months"]
ReadinessLevel = Literal["Beginner", "Emerging", "Almost Ready", "Interview-Ready"]


class QuestionnaireInput(BaseModel):
    roleApplyingFor: str = Field(..., min_length=1)
    timeline: TimelineOption

    # Q&A answers (can be empty strings in resume mode)
    q1_intro: str = ""
    q2_strengths: str = ""
    q3_proudest: str = ""
    q4_challenge: str = ""
    q5_teamwork: str = ""
    q6_learned_fast: str = ""
    q7_mistake: str = ""
    q8_motivation: str = ""
    q9_3to5years: str = ""
    q10_self_awareness: str = ""


class Dimensions(BaseModel):
    technical: int = Field(..., ge=0, le=100)
    resume: int = Field(..., ge=0, le=100)
    communication: int = Field(..., ge=0, le=100)
    portfolio: int = Field(..., ge=0, le=100)


class AssessmentResult(BaseModel):
    overallScore: int = Field(..., ge=0, le=100)
    readinessLevel: ReadinessLevel
    dimensions: Dimensions
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    timelineSummary: str
    nextSteps: List[str] = Field(default_factory=list)
