import { unexpectedArabicRouteLatin, unexpectedArabicRouteWesternDigit } from "./arabic-rendered-audit-policy.mjs";

const baseUrl = process.argv.find((value) => value.startsWith("--base-url="))?.split("=")[1];
const routesPath = process.argv.find((value) => value.startsWith("--routes="))?.split("=")[1];
if (!baseUrl) throw new Error("Use --base-url=http://127.0.0.1:50001.");

const cookie = process.env.ARE_ARABIC_AUDIT_COOKIE;
const headers = cookie ? { cookie } : {};
const queue = routesPath
  ? JSON.parse(await (await import("node:fs/promises")).readFile(routesPath, "utf8"))
  : ["/ar"];
const visited = new Set();
const failures = [];

while (queue.length) {
  const route = queue.shift();
  if (visited.has(route)) continue;
  visited.add(route);
  const response = await fetch(new URL(route, baseUrl), { headers, redirect: "follow" });
  if (!response.ok) {
    failures.push({ route, issue: `HTTP ${response.status}` });
    continue;
  }
  const html = await response.text();
  const lang = html.match(/<html[^>]*\blang="([^"]+)"/i)?.[1];
  const dir = html.match(/<html[^>]*\bdir="([^"]+)"/i)?.[1];
  const h1Count = (html.match(/<h1\b/gi) ?? []).length;
  if (lang !== "ar" || dir !== "rtl" || h1Count !== 1) failures.push({ route, issue: `lang=${lang} dir=${dir} h1=${h1Count}` });

  const inspectable = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[\s\S]*?<\/style>/gi, " ")
    .replace(/<meta\b[^>]*(?:name="viewport"|charset=)[^>]*>/gi, " ")
    .replace(/<!--([\s\S]*?)-->/g, " ");
  const snippets = [
    ...inspectable.matchAll(/>([^<>]+)</g),
    ...inspectable.matchAll(/\s(?:aria-label|title|alt|placeholder|content)="([^"]+)"/gi),
  ].map((match) => decodeEntities(match[1]).replace(/\s+/g, " ").trim()).filter(Boolean);
  for (const snippet of new Set(snippets)) {
    const violation = unexpectedArabicRouteLatin(snippet);
    if (violation) failures.push({ route, issue: violation.slice(0, 240) });
    const westernDigit = unexpectedArabicRouteWesternDigit(snippet);
    if (westernDigit) failures.push({ route, issue: `Western digits: ${westernDigit.slice(0, 220)}` });
  }

  if (!routesPath) {
    for (const match of inspectable.matchAll(/href="(\/ar(?:\/[^"?#]*)?)/gi)) {
      if (!match[1].startsWith("/ar/preview") && visited.size + queue.length < 100) queue.push(match[1]);
    }
  }
}

if (failures.length) {
  console.error(JSON.stringify({ audited: visited.size, failures }, null, 2));
  process.exitCode = 1;
} else {
  console.log(JSON.stringify({ audited: visited.size, failures: 0 }));
}

function decodeEntities(value) {
  return value
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#x27;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">");
}
