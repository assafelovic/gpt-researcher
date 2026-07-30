import { NextResponse } from "next/server";
import { backendHeaders, backendUrl } from "../../_utils/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const res = await fetch(`${backendUrl()}/api/brain/repos`, {
      headers: backendHeaders(),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      {
        repos: [],
        error: error instanceof Error ? error.message : "Backend unreachable",
      },
      { status: 502 },
    );
  }
}
