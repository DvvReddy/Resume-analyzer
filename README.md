# PrepPulse — Interview Readiness Scanner (MVP)

A lightweight web app that helps students assess interview readiness in under ~2 minutes and receive an overall readiness score, strengths, gaps, and next steps.

## What it does
- Supports two input modes: **Resume upload** (`resume`) or **Quick Questions** (`questions`). 
- Produces a structured result with `overallScore`, `readinessLevel`, dimension scores (technical/resume/communication/portfolio), strengths, gaps, a timeline summary, and next steps. 
- Includes a Python FastAPI service that extracts text from an uploaded PDF (`POST /parse-pdf`). 

## Architecture (current repo)
- **Frontend**: Next.js UI that collects inputs and renders results. 
- **API (Next.js route)**: `POST /api/analyze` receives the form data, calls the Python service to parse the resume PDF into text (`http://localhost:8000/parse-pdf`), then runs AI analysis via `analyzeWithAI` (TypeScript). 
- **Python service**: FastAPI endpoint `POST /parse-pdf` that extracts text using `pdfplumber`. 

> Note: The frontend also contains a client that can call a Python `POST /analyze` endpoint directly (`http://localhost:8000/analyze`) via `FormData`.
## API contract
### `POST /parse-pdf` (FastAPI)
- Input: `multipart/form-data` with `file` (PDF).
- Output: `{ "text": "..." }` 
### Assessment result (returned to UI)
The UI expects this shape:
```ts
{
  overallScore: number,          // 0–100
  readinessLevel: "Beginner" | "Emerging" | "Almost Ready" | "Interview-Ready",
  dimensions: { technical: number, resume: number, communication: number, portfolio: number },
  strengths: string[],
  gaps: string[],
  timelineSummary: string,
  nextSteps: string[]
}
