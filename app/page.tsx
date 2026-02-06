// app/page.tsx
'use client';

import '../css/page.css';
import { useState } from 'react';
import AssessmentForm from '@/components/AssessmentForm';
import ResultsPanel from '@/components/ResultsPanel';
import { AssessmentResult } from '@/lib/scoringSchemas';

export default function HomePage() {
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="page-root">
      <div className="page-grid">
        <section className="page-left">
          <h1 className="page-title">
            Know your interview readiness in under{' '}
            <span className="page-title-accent">2 minutes</span>
          </h1>
          <p className="page-subtitle">
            Upload your resume or answer a few focused questions and get an
            instant Interview Readiness Score, strengths, gaps, and a short
            timeline to become interview-ready.
          </p>
          <ul className="page-points">
            <li>Covers Technical Skills, Resume, Communication, and Portfolio.</li>
            <li>Works for any stream or role.</li>
            <li>Designed around the AI PrepPulse Hackathon problem statement.</li>
          </ul>
          {result && (
            <div className="page-tip">
              Tip: Re-run the scan after a few weeks of preparation to see how
              your score changes.
            </div>
          )}
        </section>

        <section className="page-card">
          <AssessmentForm
            setResult={setResult}
            setLoading={setLoading}
            setError={setError}
          />
          <ResultsPanel result={result} loading={loading} error={error} />
        </section>
      </div>
    </div>
  );
}
