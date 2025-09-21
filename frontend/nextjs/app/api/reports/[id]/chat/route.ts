import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const backendUrl = process.env.NEXT_PUBLIC_GPTR_API_URL || 'http://localhost:8000';
  
  try {
    if (!id) {
      return NextResponse.json(
        { error: 'Missing report ID parameter' },
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
      { error: 'Failed to connect to backend service' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const backendUrl = process.env.NEXT_PUBLIC_GPTR_API_URL || 'http://localhost:8000';
  
  try {
    if (!id) {
      return NextResponse.json(
        { error: 'Missing report ID parameter' },
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
        { error: 'Invalid JSON in request body' },
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
      { error: 'Failed to connect to backend service' },
      { status: 500 }
    );
  }
} 