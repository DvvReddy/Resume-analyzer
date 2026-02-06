// components/AssessmentForm.tsx
'use client';

import '../css/assessment-form.css';
import '../css/Button.css';

import { FormEvent, useMemo, useState } from 'react';
import { AssessmentMode, AssessmentResult, QuestionnaireInput, TimelineOption } from '@/lib/scoringSchemas';
import { analyzeProfile } from '@/lib/apiClient';

import LoadingSpinner from './LoadingSpinner';
import Button from './ui/Button';

interface AssessmentFormProps {
  setResult: (r: AssessmentResult | null) => void;
  setLoading: (b: boolean) => void;
  setError: (msg: string | null) => void;
}

function buildQuestionnaire(params: {
  roleApplyingFor: string;
  timeline: TimelineOption;
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
}): QuestionnaireInput {
  return { ...params };
}

export default function AssessmentForm({ setResult, setLoading, setError }: AssessmentFormProps) {
  const [mode, setMode] = useState<AssessmentMode>('resume');
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const [roleApplyingFor, setRoleApplyingFor] = useState('Software Engineer');
  const [timeline, setTimeline] = useState<TimelineOption>('1-3 months');

  const [q1_intro, setQ1] = useState('');
  const [q2_strengths, setQ2] = useState('');
  const [q3_proudest, setQ3] = useState('');
  const [q4_challenge, setQ4] = useState('');
  const [q5_teamwork, setQ5] = useState('');
  const [q6_learned_fast, setQ6] = useState('');
  const [q7_mistake, setQ7] = useState('');
  const [q8_motivation, setQ8] = useState('');
  const [q9_3to5years, setQ9] = useState('');
  const [q10_self_awareness, setQ10] = useState('');

  const questionnaire = useMemo(
    () =>
      buildQuestionnaire({
        roleApplyingFor,
        timeline,
        q1_intro,
        q2_strengths,
        q3_proudest,
        q4_challenge,
        q5_teamwork,
        q6_learned_fast,
        q7_mistake,
        q8_motivation,
        q9_3to5years,
        q10_self_awareness,
      }),
    [
      roleApplyingFor,
      timeline,
      q1_intro,
      q2_strengths,
      q3_proudest,
      q4_challenge,
      q5_teamwork,
      q6_learned_fast,
      q7_mistake,
      q8_motivation,
      q9_3to5years,
      q10_self_awareness,
    ]
  );

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!roleApplyingFor.trim()) {
      setError('Please enter which role you are applying for.');
      return;
    }

    if (mode === 'resume') {
      if (!resumeFile) {
        setError('Please upload your resume PDF or switch to Quick Questions.');
        return;
      }
      if (!resumeFile.name.toLowerCase().endsWith('.pdf')) {
        setError('Only .pdf files are allowed.');
        return;
      }
    }

    if (mode === 'questions') {
      // Keep it strict but still fast: require a few key ones
      if (!q1_intro.trim() || !q3_proudest.trim() || !q4_challenge.trim() || !q9_3to5years.trim()) {
        setError('Please answer Q1, Q3, Q4, and Q9 (required).');
        return;
      }
    }

    try {
      setLoading(true);
      const result = await analyzeProfile({
        mode,
        resumeFile,
        questionnaire,
      });
      setResult(result);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || 'Something went wrong while analyzing your profile. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="af-form">
      <div className="af-toggle-row">
        <button
          type="button"
          onClick={() => setMode('resume')}
          className={`btn-toggle ${mode === 'resume' ? 'btn-toggle-active' : ''}`}
        >
          Upload Resume
        </button>
        <button
          type="button"
          onClick={() => setMode('questions')}
          className={`btn-toggle ${mode === 'questions' ? 'btn-toggle-active' : ''}`}
        >
          Quick Questions
        </button>
      </div>

      <div className="af-section-title">Role details</div>

      <div className="af-two-col">
        <div className="af-field">
          <label className="af-label">Which role are you applying for?</label>
          <input
            type="text"
            value={roleApplyingFor}
            onChange={(e) => setRoleApplyingFor(e.target.value)}
            className="af-input"
            placeholder="e.g., Backend Engineer, Data Analyst"
          />
        </div>

        <div className="af-field">
          <label className="af-label">Next interview timeline</label>
          <select value={timeline} onChange={(e) => setTimeline(e.target.value as TimelineOption)} className="af-input">
            <option value="< 1 month">&lt; 1 month</option>
            <option value="1-3 months">1-3 months</option>
            <option value="3+ months">3+ months</option>
          </select>
        </div>
      </div>

      {mode === 'resume' && (
        <div className="af-field">
          <label className="af-label">Resume (1 page PDF only)</label>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
            className="af-file-input"
          />
          <p className="af-hint">
            We will reject PDFs that don’t look like a resume (keyword validation), and the feedback will be brutally honest.
          </p>
        </div>
      )}

      {mode === 'questions' && (
        <div className="af-questions">
          <div className="af-section-title">Quick questions</div>

          <div className="af-field">
            <label className="af-label">Q1. Introduce yourself professionally (education/current role).</label>
            <textarea value={q1_intro} onChange={(e) => setQ1(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q2. Top 3 strengths, with an example.</label>
            <textarea value={q2_strengths} onChange={(e) => setQ2(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q3. Proudest accomplishment + results.</label>
            <textarea value={q3_proudest} onChange={(e) => setQ3(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q4. Challenge faced + how you overcame it.</label>
            <textarea value={q4_challenge} onChange={(e) => setQ4(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q5. Team example + your contribution.</label>
            <textarea value={q5_teamwork} onChange={(e) => setQ5(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q6. Learned something new quickly (skill/tool/concept).</label>
            <textarea value={q6_learned_fast} onChange={(e) => setQ6(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q7. Mistake/setback + what you learned.</label>
            <textarea value={q7_mistake} onChange={(e) => setQ7(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q8. What motivates you most?</label>
            <textarea value={q8_motivation} onChange={(e) => setQ8(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q9. Where do you see yourself in 3–5 years?</label>
            <textarea value={q9_3to5years} onChange={(e) => setQ9(e.target.value)} className="af-input af-textarea" />
          </div>

          <div className="af-field">
            <label className="af-label">Q10. Feedback you received + what you changed (self-awareness).</label>
            <textarea value={q10_self_awareness} onChange={(e) => setQ10(e.target.value)} className="af-input af-textarea" />
          </div>
        </div>
      )}

      <div className="af-footer-row">
        <span className="af-footer-hint">Designed to be completed in under 2 minutes.</span>
        <Button type="submit" variant="primary">
          <LoadingSpinner className="af-submit-spinner" />
          <span>Scan my profile</span>
        </Button>
      </div>
    </form>
  );
}
