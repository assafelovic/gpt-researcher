import { NextResponse } from 'next/server';
import { backendHeaders, backendUrl } from '../../_utils/backend';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const response = await fetch(`${backendUrl()}/api/hlt/readiness`, {
      method: 'GET',
      headers: backendHeaders(),
      cache: 'no-store',
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('GET /api/hlt/readiness - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to load HLT readiness' },
      { status: 500 }
    );
  }
}
