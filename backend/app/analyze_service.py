import json
from typing import Any, Dict
from .schemas import AssessmentResult, QuestionnaireInput


def build_profile_block(questionnaire: QuestionnaireInput, resume_text: str | None) -> str:
    q = questionnaire

    qa = f"""
Q1 Intro: {q.q1_intro}
Q2 Strengths: {q.q2_strengths}
Q3 Proudest: {q.q3_proudest}
Q4 Challenge: {q.q4_challenge}
Q5 Teamwork: {q.q5_teamwork}
Q6 Learned fast: {q.q6_learned_fast}
Q7 Mistake: {q.q7_mistake}
Q8 Motivation: {q.q8_motivation}
Q9 3-5 years: {q.q9_3to5years}
Q10 Self-awareness: {q.q10_self_awareness}
""".strip()

    base = f"""
ROLE APPLYING FOR: {q.roleApplyingFor}
TIMELINE: {q.timeline}

ANSWERED QUESTIONS (may be empty if resume provided):
{qa}
""".strip()

    if resume_text:
        base += f"\n\nRESUME TEXT:\n{resume_text[:12000]}"  # keep it bounded
    return base


def build_prompt(profile_text: str) -> str:
    # DistilGPT2 is not instruction-tuned, so keep the instruction short and strict.
    return f"""
You are an interviewer. Be brutally honest, direct, and specific. Do not flatter.
If information is missing, say it clearly.

Return ONLY valid JSON exactly matching this schema:
{{
  "overallScore": 0-100,
  "readinessLevel": "Beginner|Emerging|Almost Ready|Interview-Ready",
  "dimensions": {{
    "technical": 0-100,
    "resume": 0-100,
    "communication": 0-100,
    "portfolio": 0-100
  }},
  "strengths": ["..."],
  "gaps": ["..."],
  "timelineSummary": "...",
  "nextSteps": ["..."]
}}

CANDIDATE PROFILE:
{profile_text}

JSON:
""".strip()


def extract_json_object(text: str) -> Dict[str, Any]:
    # Find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    json_str = text[start : end + 1]
    return json.loads(json_str)


def to_assessment_result(model_text: str) -> AssessmentResult:
    obj = extract_json_object(model_text)
    return AssessmentResult.model_validate(obj)
