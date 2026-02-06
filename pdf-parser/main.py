from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber, json
from io import BytesIO
from transformers import pipeline  # distilgpt2 first

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ai = pipeline('text-generation', model='distilgpt2')  # Upgrade to Mistral later

@app.post("/analyze")
async def analyze(mode: str = Form(...), questionnaire: str = Form(...), resume: UploadFile = File(None)):
    q = json.loads(questionnaire)  # {"role": "...", "timeline": "...", etc.}
    text = ""
    
    if mode == "resume" and resume:
        content = await resume.read()
        with pdfplumber.open(BytesIO(content)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    
    profile = f"Role: {q['role']}. Timeline: {q['timeline']}. Rating: {q['selfRating']}. Projects: {q['projectsCount']}. Practice: {q['practiceFrequency']}. Intro: {q['selfIntro']}. {'Resume: ' + text if text else ''}"
    
    prompt = f"JSON score (technical,communication,resume,portfolio 0-100), strengths, gaps, plan: {profile}"
    result = ai(prompt, max_new_tokens=150)[0]['generated_text']
    
    # Mock schema match (parse real later)
    return {
        "overallScore": 75,
        "readinessLevel": "Almost Ready",
        "dimensions": {"technical": 80, "resume": 70, "communication": 65, "portfolio": 75},
        "strengths": ["Solid Python skills"],
        "gaps": ["More projects"],
        "timelineSummary": "3-5 weeks",
        "nextSteps": ["Practice interviews"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
