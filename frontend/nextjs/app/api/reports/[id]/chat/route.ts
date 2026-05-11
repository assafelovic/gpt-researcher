import { NextResponse } from 'next/server';
import { resolveServerBackendUrl } from '@/helpers/backendUrl';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const backendUrl = resolveServerBackendUrl(
    process.env.BACKEND_INTERNAL_URL,
    process.env.BACKEND_URL,
    process.env.NEXT_PUBLIC_GPTR_API_URL,
    process.env.NEXT_PUBLIC_BACKEND_URL,
  );

  try {
    if (!id) {
      return NextResponse.json(
        { error: 'Fehlender Bericht-ID-Parameter' },
        { status: 400 }
      );
    }

    console.log(`GET /api/reports/${id}/chat - Proxying request to backend`);

    const response = await fetch(`${backendUrl}/api/reports/${id}/chat`);
    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error(`GET /api/reports/${id}/chat - Error proxying to backend:`, error);
    return NextResponse.json(
      { error: 'Verbindung zum Backend-Dienst fehlgeschlagen' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const backendUrl = resolveServerBackendUrl(
    process.env.BACKEND_INTERNAL_URL,
    process.env.BACKEND_URL,
    process.env.NEXT_PUBLIC_GPTR_API_URL,
    process.env.NEXT_PUBLIC_BACKEND_URL,
  );

  try {
    if (!id) {
      return NextResponse.json(
        { error: 'Fehlender Bericht-ID-Parameter' },
        { status: 400 }
      );
    }

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

    console.log(`POST /api/reports/${id}/chat - Proxying request to backend`);

    const response = await fetch(`${backendUrl}/api/reports/${id}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error(`POST /api/reports/${id}/chat - Error proxying to backend:`, error);
    return NextResponse.json(
      { error: 'Verbindung zum Backend-Dienst fehlgeschlagen' },
      { status: 500 }
    );
  }
}
