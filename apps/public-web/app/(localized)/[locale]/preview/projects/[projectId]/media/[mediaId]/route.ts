import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { getDraftProjectPreviewMedia } from "../../../../../../../../lib/api";

type Context = Readonly<{
  params: Promise<{ projectId: string; mediaId: string }>;
}>;

export async function GET(_request: Request, { params }: Context) {
  const { projectId, mediaId } = await params;
  const requestHeaders = await headers();
  const upstream = await getDraftProjectPreviewMedia(
    projectId,
    mediaId,
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
