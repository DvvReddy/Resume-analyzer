// app/layout.tsx
import './globals.css';
import '../css/layout.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'PrepPulse - Interview Readiness Scanner',
  description: 'Check your interview readiness in under 2 minutes.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="layout-body">
        <div className="layout-shell">
          <header className="layout-header">
            <div className="layout-header-inner">
              <div className="layout-logo-row">
                <div className="layout-logo-badge"> </div>
                <div>
                  <div className="layout-logo-title"></div>
                  <div className="layout-logo-subtitle">
                    Interview Readiness Scan
                  </div>
                </div>
              </div>
              <span className="layout-header-tagline">
                AI PrepPulse Hackathon
              </span>
            </div>
          </header>
          <main className="layout-main">{children}</main>
          <footer className="layout-footer">
            <div className="layout-footer-inner">
              <span>Built for UnsaidTalks AI PrepPulse Hackathon</span>
              <span>Interview readiness · &lt; 2 minutes</span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
