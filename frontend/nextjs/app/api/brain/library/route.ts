import { NextRequest, NextResponse } from "next/server";
import { backendHeaders, backendUrl } from "../../_utils/backend";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const q = request.nextUrl.searchParams.get("q");
    const target = new URL(`${backendUrl()}/api/brain/library`);
    if (q) target.searchParams.set("q", q);
    const res = await fetch(target, {
      headers: backendHeaders(),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      {
        reports: [],
        query: null,
        total: 0,
        error: error instanceof Error ? error.message : "Backend unreachable",
      },
      { status: 502 },
    );
  }
}
