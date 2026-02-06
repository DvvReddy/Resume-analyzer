import re
from dataclasses import dataclass
from typing import List


RESUME_KEYWORDS: List[str] = [
    "experience", "work experience", "education", "skills", "projects",
    "internship", "certification", "summary", "objective", "linkedin", "github",
    "achievements", "responsibilities"
]


@dataclass
class ResumeCheck:
    is_resume: bool
    hits: int
    matched: List[str]
    reason: str


def looks_like_resume(text: str, min_hits: int = 3) -> ResumeCheck:
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t).strip()

    matched = [k for k in RESUME_KEYWORDS if k in t]
    hits = len(matched)

    if len(t) < 400:
        return ResumeCheck(False, hits, matched, "Text is too short to be a resume.")

    if hits < min_hits:
        return ResumeCheck(False, hits, matched, f"Not enough resume keywords (need {min_hits}).")

    return ResumeCheck(True, hits, matched, "Looks like a resume.")
