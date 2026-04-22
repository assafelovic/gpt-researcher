import { NextResponse } from 'next/server';
import { backendHeaders, backendUrl } from '../_utils/backend';

export const dynamic = 'force-dynamic';

export async function POST() {
  try {
    const response = await fetch(`${backendUrl()}/api/ws-token`, {
      method: 'POST',
      headers: backendHeaders(),
      cache: 'no-store',
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('POST /api/ws-token - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to create WebSocket token' },
      { status: 500 }
    );
  }
}
