import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { getCandidateProjectPreviewMedia } from "../../../../../../../../../../lib/api";

type Context = Readonly<{
  params: Promise<{ candidateId: string; mediaId: string }>;
}>;

export async function GET(request: Request, { params }: Context) {
  const { candidateId, mediaId } = await params;
  const size = new URL(request.url).searchParams.get("size") === "full" ? "full" : "thumbnail";
  const requestHeaders = await headers();
  const upstream = await getCandidateProjectPreviewMedia(
    candidateId,
    mediaId,
    size,
    requestHeaders.get("cookie") ?? "",
  );
  if (!upstream?.ok || !upstream.body) notFound();

  return new Response(upstream.body, {
    headers: {
      "Cache-Control": "private, no-store, max-age=0",
      "Content-Security-Policy": "default-src 'none'; img-src 'self'; sandbox",
      "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
      "X-Content-Type-Options": "nosniff",
      "X-Robots-Tag": "noindex, nofollow, noarchive",
    },
    status: 200,
  });
}
