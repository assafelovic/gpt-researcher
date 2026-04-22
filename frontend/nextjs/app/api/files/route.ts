import { NextResponse } from 'next/server';
import { backendHeaders, backendUrl } from '../_utils/backend';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const response = await fetch(`${backendUrl()}/files/`, {
      headers: backendHeaders(),
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('GET /api/files - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to fetch uploaded files' },
      { status: 500 }
    );
  }
}
