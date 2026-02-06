// app/api/analyze/route.ts
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

const PY_BACKEND_ANALYZE_URL = 'http://localhost:8000/analyze';

export async function POST(req: NextRequest) {
  try {
    const incoming = await req.formData();

    const res = await fetch(PY_BACKEND_ANALYZE_URL, {
      method: 'POST',
      body: incoming,
    });

    const text = await res.text();

    // Pass through status + body (JSON expected)
    return new NextResponse(text, {
      status: res.status,
      headers: { 'Content-Type': res.headers.get('content-type') || 'application/json' },
    });
  } catch (err: any) {
    console.error('Proxy error in /api/analyze:', err);
    return NextResponse.json(
      { error: err?.message || 'Failed to reach Python backend.' },
      { status: 500 }
    );
  }
}
