import { NextResponse } from 'next/server';
import { backendHeaders, backendUrl } from '../../_utils/backend';

export const dynamic = 'force-dynamic';

export async function DELETE(
  request: Request,
  { params }: { params: { filename: string } }
) {
  try {
    const filename = encodeURIComponent(params.filename);
    const response = await fetch(`${backendUrl()}/files/${filename}`, {
      method: 'DELETE',
      headers: backendHeaders(),
      cache: 'no-store',
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('DELETE /api/files/[filename] - Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to delete uploaded file' },
      { status: 500 }
    );
  }
}
