const FORWARDED_HEADERS = [
  'content-type',
  'content-length',
  'content-disposition',
  'cache-control',
  'etag',
  'last-modified',
];

export const dynamic = 'force-dynamic';

export async function GET(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  if (params.path.some((segment) => segment === '.' || segment === '..' || /[\\/]/.test(segment))) {
    return new Response('Not found', { status: 404 });
  }

  const backendUrl =
    process.env.GPTR_API_URL ||
    process.env.NEXT_PUBLIC_GPTR_API_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  const path = params.path.map(encodeURIComponent).join('/');

  try {
    const response = await fetch(`${backendUrl}/outputs/${path}`, { cache: 'no-store' });
    const headers = new Headers();
    for (const name of FORWARDED_HEADERS) {
      const value = response.headers.get(name);
      if (value) headers.set(name, value);
    }
    return new Response(response.body, { status: response.status, headers });
  } catch (error) {
    console.error(`GET /outputs/${path} - Error proxying to backend:`, error);
    return Response.json({ error: 'Failed to connect to backend service' }, { status: 502 });
  }
}
