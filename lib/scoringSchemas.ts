// lib/scoringSchemas.ts

export type AssessmentMode = 'resume' | 'questions';

export type TimelineOption = '< 1 month' | '1-3 months' | '3+ months';

export interface QuestionnaireInput {
  roleApplyingFor: string;
  timeline: TimelineOption;

  // Q&A answers (send empty strings for resume mode)
  q1_intro: string;
  q2_strengths: string;
  q3_proudest: string;
  q4_challenge: string;
  q5_teamwork: string;
  q6_learned_fast: string;
  q7_mistake: string;
  q8_motivation: string;
  q9_3to5years: string;
  q10_self_awareness: string;
}

export interface AssessmentResult {
  overallScore: number; // 0–100
  readinessLevel: 'Beginner' | 'Emerging' | 'Almost Ready' | 'Interview-Ready';
  dimensions: {
    technical: number;
    resume: number;
    communication: number;
    portfolio: number;
  };
  strengths: string[];
  gaps: string[];
  timelineSummary: string;
  nextSteps: string[];
}
