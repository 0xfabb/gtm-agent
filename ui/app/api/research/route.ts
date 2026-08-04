import type { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8500";

export async function POST(request: NextRequest) {
  const body = await request.text();

  const backendResponse = await fetch(`${BACKEND_URL}/api/research`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });

  return new Response(backendResponse.body, {
    status: backendResponse.status,
    headers: { "content-type": "text/event-stream" },
  });
}
