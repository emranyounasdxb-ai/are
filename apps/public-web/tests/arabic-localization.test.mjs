import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  intentionalArabicRouteLatinExceptions,
  unexpectedArabicRouteLatin,
  unexpectedArabicRouteWesternDigit,
} from "../scripts/arabic-rendered-audit-policy.mjs";

test("Arabic rendered-text policy rejects English and protected brand fallbacks", () => {
  assert.equal(unexpectedArabicRouteLatin("علياس العقارية"), null);
  assert.equal(unexpectedArabicRouteLatin("ALIYAS Real Estate"), "ALIYAS Real Estate");
  assert.equal(unexpectedArabicRouteLatin("ARE / مشروع"), "ARE / مشروع");
  assert.equal(unexpectedArabicRouteLatin("Project details"), "Project details");
});

test("Arabic rendered-text policy keeps only narrow documented Latin exceptions", () => {
  assert.deepEqual(intentionalArabicRouteLatinExceptions, ["DOCX", "DOC", "EN", "LinkedIn", "PDF", "WhatsApp"]);
  assert.equal(unexpectedArabicRouteLatin("PDF"), null);
  assert.equal(unexpectedArabicRouteLatin("https://example.com/project-2"), null);
  assert.equal(unexpectedArabicRouteLatin("info@example.com"), null);
  assert.equal(unexpectedArabicRouteLatin("+971 56 915 7576"), null);
});

test("Arabic rendered-text policy requires Arabic-Indic user-facing digits", () => {
  assert.equal(unexpectedArabicRouteWesternDigit("غرفتا نوم 2"), "غرفتا نوم 2");
  assert.equal(unexpectedArabicRouteWesternDigit("غرفتا نوم ٢"), null);
  assert.equal(unexpectedArabicRouteWesternDigit("+971 56 915 7576"), null);
  assert.equal(unexpectedArabicRouteWesternDigit("https://example.com/project-2"), null);
});

test("shared Project presentation localizes Arabic digits and never exposes Arabic brand fallbacks", async () => {
  const source = await readFile(new URL("../components/projects/project-detail-presentation.tsx", import.meta.url), "utf8");
  assert.match(source, /localizedDisplayText\(project\.project_name, locale\)/);
  assert.match(source, /toArabicIndicDigits\(year\)/);
  assert.match(source, /localizedArabicList\(project\.amenities\)/);
  assert.match(source, /value\.toLowerCase\(\) === "studio" \? "استوديو"/);
  assert.match(source, /normalizeArabicUserFacingText\(project\.area\)/);
  assert.match(source, /formatLocalized/);
  assert.doesNotMatch(source, /eyebrow: "ARE \/ مشروع/);
  assert.doesNotMatch(source, /ctaEyebrow: "استشارات ALIYAS"/);
});

test("Arabic metadata uses the localized brand on shared and Project routes", async () => {
  const files = await Promise.all([
    "../app/(localized)/[locale]/preview/project-imports/[batchId]/candidates/[candidateId]/page.tsx",
    "../app/(localized)/[locale]/preview/projects/[projectId]/page.tsx",
    "../app/(localized)/[locale]/insights/[slug]/page.tsx",
    "../app/(localized)/[locale]/developers/[slug]/page.tsx",
  ].map((path) => readFile(new URL(path, import.meta.url), "utf8")));
  for (const source of files) assert.match(source, /localizedBrand\(locale\)/);
});
