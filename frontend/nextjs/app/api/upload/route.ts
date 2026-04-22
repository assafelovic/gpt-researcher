import { NextResponse } from 'next/server';
import { backendHeaders, backendUrl } from '../_utils/backend';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const response = await fetch(`${backendUrl()}/upload/`, {
      method: 'POST',
      headers: backendHeaders(),
      body: formData,
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('POST /api/upload - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to upload file' },
      { status: 500 }
    );
  }
}
