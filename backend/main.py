# main.py (single backend: /parse-pdf + /analyze)
"""
from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional

import pdfplumber
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from transformers import pipeline


# -----------------------------
# App
# -----------------------------
app = FastAPI()

# For local dev (Next.js), you can tighten later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Model (local)
# -----------------------------
# NOTE: distilgpt2 is not instruction-tuned, so JSON compliance may fail sometimes.
# We intentionally DO NOT return static fallback scores; we error if JSON isn't valid.
GEN_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
_gen = pipeline("text-generation", model=GEN_MODEL_ID)


# -----------------------------
# Schema (matches your frontend AssessmentResult)
# -----------------------------
AssessmentMode = Literal["resume", "questions"]
ReadinessLevel = Literal["Beginner", "Emerging", "Almost Ready", "Interview-Ready"]
TimelineOpt = Literal["< 1 month", "1-3 months", "3+ months"]


class QuestionnaireInput(BaseModel):
    # New required field per your request
    roleApplyingFor: str = Field(default="", min_length=0)
    timeline: Optional[TimelineOpt] = None

    # New Q&A fields (can be empty strings)
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

    # Backward compatibility (if your frontend still sends old keys)
    role: Optional[str] = None
    selfIntro: Optional[str] = None


class Dimensions(BaseModel):
    technical: int = Field(..., ge=0, le=100)
    resume: int = Field(..., ge=0, le=100)
    communication: int = Field(..., ge=0, le=100)
    portfolio: int = Field(..., ge=0, le=100)


class AssessmentResult(BaseModel):
    overallScore: int = Field(..., ge=0, le=100)
    readinessLevel: ReadinessLevel
    dimensions: Dimensions
    strengths: List[str]
    gaps: List[str]
    timelineSummary: str
    nextSteps: List[str]


# -----------------------------
# Helpers
# -----------------------------
RESUME_KEYWORDS = [
    "professional Summary"
    "experience",
    "work experience",
    "education",
    "skills",
    "projects",
    "internship",
    "certification",
    "summary",
    "objective",
    "linkedin",
    "github",
    "achievements",
    "responsibilities",
]


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text_parts: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n\n".join(text_parts).strip()


def looks_like_resume(text: str, min_hits: int = 3) -> tuple[bool, int, List[str], str]:
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t).strip()

    matched = [k for k in RESUME_KEYWORDS if k in t]
    hits = len(matched)

    if len(t) < 400:
        return False, hits, matched, "Text is too short to be a resume."
    if hits < min_hits:
        return False, hits, matched, f"Not enough resume keywords (need {min_hits})."
    return True, hits, matched, "Looks like a resume."


def normalize_questionnaire(raw: Dict[str, Any]) -> QuestionnaireInput:

    #Accepts either the new structure or your older structure.
    #Ensures roleApplyingFor is populated.
    
    q = QuestionnaireInput.model_validate(raw)

    # If frontend still uses `role`, map it
    role_apply = (q.roleApplyingFor or "").strip()
    if not role_apply and q.role:
        role_apply = q.role.strip()

    # If still empty, keep empty (we can enforce later)
    q.roleApplyingFor = role_apply
    return q


def build_profile_text(mode: AssessmentMode, q: QuestionnaireInput, resume_text: Optional[str]) -> str:
    role_line = q.roleApplyingFor or "(not provided)"
    timeline_line = q.timeline or "(not provided)"

    qa_block = "\n".join(
        [
            f"Q1 Intro: {q.q1_intro}",
            f"Q2 Strengths: {q.q2_strengths}",
            f"Q3 Proudest accomplishment: {q.q3_proudest}",
            f"Q4 Challenge overcame: {q.q4_challenge}",
            f"Q5 Teamwork: {q.q5_teamwork}",
            f"Q6 Learned fast: {q.q6_learned_fast}",
            f"Q7 Mistake/setback: {q.q7_mistake}",
            f"Q8 Motivation: {q.q8_motivation}",
            f"Q9 3-5 years: {q.q9_3to5years}",
            f"Q10 Self-awareness: {q.q10_self_awareness}",
        ]
    )

    base = (
        f"MODE: {mode}\n"
        f"ROLE APPLYING FOR: {role_line}\n"
        f"TIMELINE: {timeline_line}\n\n"
        f"ANSWERS:\n{qa_block}\n"
    )

    if mode == "resume" and resume_text:
        base += "\nRESUME TEXT:\n" + resume_text[:12000]

    return base


def build_prompt(profile_text: str) -> str:
    # "Brutally true" style
    return (
        "You are an interviewer and evaluator.\n"
        "Be brutally honest, direct, and specific. Do not flatter.\n"
        "If information is missing, say it clearly and reduce scores.\n\n"
        "Return ONLY valid JSON, no markdown, no extra text.\n"
        "JSON schema (must match exactly):\n"
        "{\n"
        '  "overallScore": 0-100,\n'
        '  "readinessLevel": "Beginner|Emerging|Almost Ready|Interview-Ready",\n'
        '  "dimensions": {\n'
        '    "technical": 0-100,\n'
        '    "resume": 0-100,\n'
        '    "communication": 0-100,\n'
        '    "portfolio": 0-100\n'
        "  },\n"
        '  "strengths": ["..."],\n'
        '  "gaps": ["..."],\n'
        '  "timelineSummary": "...",\n'
        '  "nextSteps": ["..."]\n'
        "}\n\n"
        "CANDIDATE PROFILE:\n"
        f"{profile_text}\n\n"
        "JSON:\n"
    )


def extract_json_object(text: str) -> Dict[str, Any]:
    # Find first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    return json.loads(text[start : end + 1])


def run_ai(prompt: str) -> AssessmentResult:
    generated = _gen(
        prompt,
        max_new_tokens=240,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
    )[0]["generated_text"]

    obj = extract_json_object(generated)
    return AssessmentResult.model_validate(obj)


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
async def health():
    return {"ok": True, "model": GEN_MODEL_ID}


@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):

    #Same as your original endpoint: PDF -> extracted text.
    
    try:
        content = await file.read()
        text = extract_text_from_pdf_bytes(content)
        return JSONResponse({"text": text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/analyze")
async def analyze(
    mode: str = Form(...),
    questionnaire: str = Form(...),
    resume: Optional[UploadFile] = File(None),
):
    # Validate mode
    if mode not in ("resume", "questions"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'resume' or 'questions'.")

    # Validate questionnaire JSON
    try:
        q_raw = json.loads(questionnaire)
        q = normalize_questionnaire(q_raw)
    except (json.JSONDecodeError, ValidationError):
        raise HTTPException(status_code=400, detail="Invalid questionnaire JSON.")

    # Enforce roleApplyingFor (your new requirement)
    if not (q.roleApplyingFor or "").strip():
        raise HTTPException(status_code=400, detail="Missing: roleApplyingFor.")

    resume_text: Optional[str] = None

    if mode == "resume":
        if resume is None:
            raise HTTPException(status_code=400, detail="Missing resume file.")
        if not (resume.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
        if "pdf" not in (resume.content_type or "").lower():
            raise HTTPException(status_code=400, detail="File must be a PDF (content-type).")

        pdf_bytes = await resume.read()
        resume_text = extract_text_from_pdf_bytes(pdf_bytes)

        USE_RESUME_GUARD = False
        is_resume, hits, matched, reason = looks_like_resume(resume_text, min_hits=3)
        if not is_resume:
            # No score (as requested)
            raise HTTPException(
                status_code=422,
                detail=f"PDF rejected: not detected as a resume. {reason} (hits={hits}, matched={matched})",
            )

    # If questions mode: require at least a few answers to reduce empty prompt
    if mode == "questions":
        required = [
            ("q1_intro", q.q1_intro),
            ("q3_proudest", q.q3_proudest),
            ("q4_challenge", q.q4_challenge),
            ("q9_3to5years", q.q9_3to5years),
        ]
        missing = [k for k, v in required if not (v or "").strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required answers: {missing}")

    profile_text = build_profile_text(mode=mode, q=q, resume_text=resume_text)
    prompt = build_prompt(profile_text)

    # Run AI -> must parse JSON -> return (no static fallback)
    try:
        assessment = run_ai(prompt)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"AI output was not valid JSON (distilgpt2 limitation). Error: {str(e)}",
        )

    return JSONResponse(assessment.model_dump())
"""

# main.py (single backend: /parse-pdf + /analyze)

from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional

import pdfplumber
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from transformers import pipeline


# -----------------------------
# App
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Model (Qwen-safe init)
# -----------------------------
GEN_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

_gen = pipeline(
    "text-generation",
    model=GEN_MODEL_ID,
    return_full_text=False,
)

# ✅ Override generation config AFTER pipeline creation
_gen.model.generation_config.max_new_tokens = 240
_gen.model.generation_config.do_sample = True
_gen.model.generation_config.temperature = 0.7
_gen.model.generation_config.top_p = 0.9


# -----------------------------
# Schema
# -----------------------------
AssessmentMode = Literal["resume", "questions"]
ReadinessLevel = Literal["Beginner", "Emerging", "Almost Ready", "Interview-Ready"]
TimelineOpt = Literal["< 1 month", "1-3 months", "3+ months"]


class QuestionnaireInput(BaseModel):
    roleApplyingFor: str = Field(default="", min_length=0)
    timeline: Optional[TimelineOpt] = None

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

    # backward compatibility
    role: Optional[str] = None
    selfIntro: Optional[str] = None


class Dimensions(BaseModel):
    technical: int = Field(..., ge=0, le=100)
    resume: int = Field(..., ge=0, le=100)
    communication: int = Field(..., ge=0, le=100)
    portfolio: int = Field(..., ge=0, le=100)


class AssessmentResult(BaseModel):
    overallScore: int = Field(..., ge=0, le=100)
    readinessLevel: ReadinessLevel
    dimensions: Dimensions
    strengths: List[str]
    gaps: List[str]
    timelineSummary: str
    nextSteps: List[str]


# -----------------------------
# Helpers
# -----------------------------
RESUME_KEYWORDS = [
    "professional summary",
    "experience",
    "work experience",
    "education",
    "skills",
    "projects",
    "internship",
    "certification",
    "summary",
    "objective",
    "linkedin",
    "github",
    "achievements",
    "responsibilities",
]


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text_parts: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n\n".join(text_parts).strip()


def looks_like_resume(text: str, min_hits: int = 3) -> tuple[bool, int, List[str], str]:
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t).strip()  # Python 3.14–safe

    matched = [k for k in RESUME_KEYWORDS if k in t]
    hits = len(matched)

    if len(t) < 400:
        return False, hits, matched, "Text is too short to be a resume."
    if hits < min_hits:
        return False, hits, matched, f"Not enough resume keywords (need {min_hits})."
    return True, hits, matched, "Looks like a resume."


def normalize_questionnaire(raw: Dict[str, Any]) -> QuestionnaireInput:
    q = QuestionnaireInput.model_validate(raw)

    role_apply = (q.roleApplyingFor or "").strip()
    if not role_apply and q.role:
        role_apply = q.role.strip()

    q.roleApplyingFor = role_apply
    return q


def build_profile_text(
    mode: AssessmentMode,
    q: QuestionnaireInput,
    resume_text: Optional[str],
) -> str:
    role_line = q.roleApplyingFor or "(not provided)"
    timeline_line = q.timeline or "(not provided)"

    qa_block = "\n".join(
        [
            f"Q1 Intro: {q.q1_intro}",
            f"Q2 Strengths: {q.q2_strengths}",
            f"Q3 Proudest accomplishment: {q.q3_proudest}",
            f"Q4 Challenge overcame: {q.q4_challenge}",
            f"Q5 Teamwork: {q.q5_teamwork}",
            f"Q6 Learned fast: {q.q6_learned_fast}",
            f"Q7 Mistake/setback: {q.q7_mistake}",
            f"Q8 Motivation: {q.q8_motivation}",
            f"Q9 3-5 years: {q.q9_3to5years}",
            f"Q10 Self-awareness: {q.q10_self_awareness}",
        ]
    )

    base = (
        f"MODE: {mode}\n"
        f"ROLE APPLYING FOR: {role_line}\n"
        f"TIMELINE: {timeline_line}\n\n"
        f"ANSWERS:\n{qa_block}\n"
    )

    if mode == "resume" and resume_text:
        base += "\nRESUME TEXT:\n" + resume_text[:12000]

    return base


def build_prompt(profile_text: str) -> str:
    return (
        "You are an interviewer and evaluator.\n"
        "Be brutally honest, direct, and specific. Do not flatter.\n"
        "If information is missing, say it clearly and reduce scores.\n\n"
        "Return ONLY valid JSON, no markdown, no extra text.\n"
        "JSON schema (must match exactly):\n"
        "{\n"
        '  "overallScore": 0-100,\n'
        '  "readinessLevel": "Beginner|Emerging|Almost Ready|Interview-Ready",\n'
        '  "dimensions": {\n'
        '    "technical": 0-100,\n'
        '    "resume": 0-100,\n'
        '    "communication": 0-100,\n'
        '    "portfolio": 0-100\n'
        "  },\n"
        '  "strengths": ["..."],\n'
        '  "gaps": ["..."],\n'
        '  "timelineSummary": "...",\n'
        '  "nextSteps": ["..."]\n'
        "}\n\n"
        "CANDIDATE PROFILE:\n"
        f"{profile_text}\n\n"
        "JSON:\n"
    )


def extract_json_object(text: str) -> Dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    return json.loads(text[start : end + 1])


def run_ai(prompt: str) -> AssessmentResult:
    generated = _gen(prompt)[0]["generated_text"]
    obj = extract_json_object(generated)
    return AssessmentResult.model_validate(obj)


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
async def health():
    return {"ok": True, "model": GEN_MODEL_ID}


@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = extract_text_from_pdf_bytes(content)
        return JSONResponse({"text": text})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/analyze")
async def analyze(
    mode: str = Form(...),
    questionnaire: str = Form(...),
    resume: Optional[UploadFile] = File(None),
):
    if mode not in ("resume", "questions"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'resume' or 'questions'.")

    try:
        q_raw = json.loads(questionnaire)
        q = normalize_questionnaire(q_raw)
    except (json.JSONDecodeError, ValidationError):
        raise HTTPException(status_code=400, detail="Invalid questionnaire JSON.")

    if not (q.roleApplyingFor or "").strip():
        raise HTTPException(status_code=400, detail="Missing: roleApplyingFor.")

    resume_text: Optional[str] = None

    if mode == "resume":
        if resume is None:
            raise HTTPException(status_code=400, detail="Missing resume file.")
        if not (resume.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")
        if "pdf" not in (resume.content_type or "").lower():
            raise HTTPException(status_code=400, detail="File must be a PDF.")

        pdf_bytes = await resume.read()
        resume_text = extract_text_from_pdf_bytes(pdf_bytes)

        is_resume, hits, matched, reason = looks_like_resume(resume_text)
        if not is_resume:
            raise HTTPException(
                status_code=422,
                detail=f"PDF rejected: not detected as a resume. {reason} (hits={hits}, matched={matched})",
            )

    if mode == "questions":
        required = [
            ("q1_intro", q.q1_intro),
            ("q3_proudest", q.q3_proudest),
            ("q4_challenge", q.q4_challenge),
            ("q9_3to5years", q.q9_3to5years),
        ]
        missing = [k for k, v in required if not (v or "").strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required answers: {missing}")

    profile_text = build_profile_text(mode=mode, q=q, resume_text=resume_text)
    prompt = build_prompt(profile_text)

    try:
        assessment = run_ai(prompt)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"AI output was not valid JSON. Error: {str(e)}",
        )

    return JSONResponse(assessment.model_dump())
