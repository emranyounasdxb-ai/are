import { readPrivateFont } from "../../../../lib/private-fonts.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request, { params }: { params: Promise<{version: string; asset: string}> }) {
  const { version, asset } = await params;
  if (version !== "v1" || !/^[a-z0-9-]+\.(woff2|ttf)$/.test(asset)) return new Response(null, { status: 404 });
  if (request.headers.get("sec-fetch-site") === "cross-site") return new Response(null, { status: 403 });
  try {
    const bytes = await readPrivateFont(asset);
    return new Response(new Uint8Array(bytes), { headers: {
      "Content-Type": asset.endsWith(".woff2") ? "font/woff2" : "font/ttf",
      "Cache-Control": "public, max-age=31536000, immutable",
      "Cross-Origin-Resource-Policy": "same-origin",
      "X-Content-Type-Options": "nosniff",
    } });
  } catch {
    return new Response("Font unavailable", { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
