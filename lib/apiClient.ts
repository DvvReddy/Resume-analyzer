// lib/apiClient.ts
import { AssessmentResult, AssessmentMode, QuestionnaireInput } from './scoringSchemas';

interface AnalyzeProfileArgs {
  mode: AssessmentMode;
  resumeFile: File | null;
  questionnaire: QuestionnaireInput;
}

export async function analyzeProfile({
  mode,
  resumeFile,
  questionnaire,
}: AnalyzeProfileArgs): Promise<AssessmentResult> {
  const formData = new FormData();
  formData.append('mode', mode);
  formData.append('questionnaire', JSON.stringify(questionnaire));
  if (resumeFile) formData.append('resume', resumeFile);

  const res = await fetch('/api/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `API error ${res.status} ${res.statusText}`);
  }

  return (await res.json()) as AssessmentResult;
}
