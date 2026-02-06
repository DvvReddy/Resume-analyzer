// components/ResultsPanel.tsx
'use client';

import '../css/results-panel.css';
import { AssessmentResult } from '@/lib/scoringSchemas';
import LoadingSpinner from './LoadingSpinner';

interface ResultsPanelProps {
  result: AssessmentResult | null;
  loading: boolean;
  error: string | null;
}

export default function ResultsPanel({
  result,
  loading,
  error,
}: ResultsPanelProps) {
  if (loading) {
    return (
      <div className="rp-loading">
        <LoadingSpinner className="rp-loading-spinner" />
        <p>Analyzing your profile…</p>
      </div>
    );
  }

  if (error) {
    return <div className="rp-error">{error}</div>;
  }

  if (!result) {
    return (
      <div className="rp-placeholder">
        Fill in your details and run the scan to see your Interview Readiness
        Score and personalized suggestions here.
      </div>
    );
  }

  const {
    overallScore,
    readinessLevel,
    dimensions,
    strengths,
    gaps,
    timelineSummary,
    nextSteps,
  } = result;

  return (
    <div className="rp-results">
      {/* Main score */}
      <div className="rp-main-score-row">
        <div>
          <div className="rp-score-label">Interview Readiness Score</div>
          <div className="rp-score-value-row">
            <span className="rp-score-number">{overallScore}</span>
            <span className="rp-score-outof">/ 100</span>
          </div>
          <div className="rp-score-level-row">
            Level:{' '}
            <span className="rp-score-level-value">{readinessLevel}</span>
          </div>
        </div>
        <div className="rp-score-bar-wrapper">
          <div className="rp-score-bar-bg">
            <div
              className="rp-score-bar-fill"
              style={{ width: `${overallScore}%` }}
            />
          </div>
          <div className="rp-score-hint">
            Aim for 75+ before high-stakes interviews.
          </div>
        </div>
      </div>

      {/* Sub scores */}
      <div className="rp-dimensions-grid">
        {Object.entries(dimensions).map(([key, value]) => (
          <div key={key} className="rp-dim-card">
            <div className="rp-dim-header">
              <span className="rp-dim-label">
                {dimensionLabel(key as keyof typeof dimensions)}
              </span>
              <span className="rp-dim-value">{value} / 100</span>
            </div>
            <div className="rp-dim-bar-bg">
              <div
                className="rp-dim-bar-fill"
                style={{ width: `${value}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Strengths and gaps */}
      <div className="rp-strengths-gaps-row">
        <div className="rp-list-card">
          <div className="rp-list-title">Top strengths to leverage</div>
          <ul className="rp-list">
            {strengths.map((s, idx) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </div>
        <div className="rp-list-card">
          <div className="rp-list-title">Key gaps to address</div>
          <ul className="rp-list">
            {gaps.map((g, idx) => (
              <li key={idx}>{g}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Timeline and next steps */}
      <div className="rp-timeline-card">
        <div className="rp-timeline-title">
          Suggested timeline to become interview-ready
        </div>
        <div className="rp-timeline-text">{timelineSummary}</div>
        {nextSteps.length > 0 && (
          <>
            <div className="rp-timeline-title">
              Focus areas for the next weeks
            </div>
            <ul className="rp-list">
              {nextSteps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

function dimensionLabel(key: keyof AssessmentResult['dimensions']) {
  switch (key) {
    case 'technical':
      return 'Technical skills';
    case 'resume':
      return 'Resume';
    case 'communication':
      return 'Communication';
    case 'portfolio':
      return 'Portfolio';
    default:
      return key;
  }
}
