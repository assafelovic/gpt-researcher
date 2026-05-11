import { NextResponse } from 'next/server';
import { resolveServerBackendUrl } from '@/helpers/backendUrl';

export async function POST(request: Request) {
  const backendUrl = resolveServerBackendUrl(
    process.env.BACKEND_INTERNAL_URL,
    process.env.BACKEND_URL,
    process.env.NEXT_PUBLIC_GPTR_API_URL,
    process.env.NEXT_PUBLIC_BACKEND_URL,
  );

  try {
    // Parse the request body
    let body;
    try {
      body = await request.json();
    } catch (parseError) {
      console.error('Error parsing request body:', parseError);
      return NextResponse.json(
        { error: 'Ungültiges JSON im Request-Body' },
        { status: 400 }
      );
    }

    console.log(`POST /api/chat - Proxying request to backend`);

    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error('POST /api/chat - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Verbindung zum Backend-Dienst fehlgeschlagen' },
      { status: 500 }
    );
  }
}
