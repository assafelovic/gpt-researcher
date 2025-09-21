import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const backendUrl = process.env.NEXT_PUBLIC_GPTR_API_URL || 'http://localhost:8000';
  
  try {
    const { searchParams, pathname } = new URL(request.url);
    
    // Check if we're requesting a specific report by ID
    const pathParts = pathname.split('/');
    const reportId = pathParts[pathParts.length - 1];
    
    if (reportId && reportId !== 'reports') {
      // Request for a specific report by ID - this should be handled by [id]/route.ts
      console.error(`GET /api/reports - Unexpected path format with ID: ${reportId}`);
      return NextResponse.json(
        { error: 'Invalid request path' },
        { status: 400 }
      );
    }
    
    // Normal list reports request
    const params = new URLSearchParams();
    
    // Forward any query parameters received
    Array.from(searchParams.entries()).forEach(([key, value]) => {
      params.append(key, value);
    });
    
    const queryString = params.toString();
    const endpoint = queryString ? `/api/reports?${queryString}` : '/api/reports';
    
    console.log(`GET ${endpoint} - Proxying request to backend`);
    
    const response = await fetch(`${backendUrl}${endpoint}`);
    
    if (!response.ok) {
      // Handle backend errors
      const errorData = await response.json().catch(() => ({ detail: `Error ${response.status}` }));
      console.error(`GET /api/reports - Backend error: ${JSON.stringify(errorData)}`);
      return NextResponse.json(
        { error: errorData.detail || 'Failed to fetch reports' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    
    // Ensure data has the expected structure
    if (!data.reports) {
      console.warn('Backend response missing reports array, adding empty array');
      data.reports = [];
    }
    
    console.log(`GET /api/reports - Successfully retrieved ${data.reports.length} reports`);
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error('GET /api/reports - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend service' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  const backendUrl = process.env.NEXT_PUBLIC_GPTR_API_URL || 'http://localhost:8000';
  
  try {
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
    
    console.log(`POST /api/reports - Proxying request to backend for ID: ${body.id || 'unknown'}`);
    
    const response = await fetch(`${backendUrl}/api/reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      // Handle backend errors
      const errorData = await response.json().catch(() => ({ detail: `Error ${response.status}` }));
      console.error(`POST /api/reports - Backend error: ${JSON.stringify(errorData)}`);
      return NextResponse.json(
        { error: errorData.detail || 'Failed to create/update report' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    console.log(`POST /api/reports - Successfully created/updated report with ID: ${data.id || body.id || 'unknown'}`);
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error('POST /api/reports - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend service' },
      { status: 500 }
    );
  }
} 