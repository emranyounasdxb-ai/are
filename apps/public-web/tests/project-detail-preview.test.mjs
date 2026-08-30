import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(
  new URL("../components/projects/project-detail-presentation.tsx", import.meta.url),
  "utf8",
);
const previewPage = readFileSync(
  new URL(
    "../app/(localized)/[locale]/preview/project-imports/[batchId]/candidates/[candidateId]/page.tsx",
    import.meta.url,
  ),
  "utf8",
);

test("candidate payment plans are normalized to renderable text and milestone values", () => {
  assert.match(source, /const paymentEligible = Boolean/);
  assert.match(source, /plan\?\.is_complete/);
  assert.match(source, /!plan\.requires_review/);
  assert.match(source, /plan\.milestones\?\.length/);
  assert.match(source, /paymentPlan: paymentEligible && !ar/);
  assert.doesNotMatch(source, /paymentPlan: project\.payment_plan/);
  assert.match(source, /const milestones = paymentEligible \? plan\?\.milestones \?\? \[\] : \[\]/);
});

test("missing milestone percentages render no placeholder text", () => {
  assert.match(source, /item\.percentage == null/);
  assert.match(source, /localizedDisplayText\(`\$\{item\.percentage\}%`, locale\)/);
});

test("omitted optional candidate collections use empty presentation defaults", () => {
  for (const value of [
    "property_types",
    "bedrooms",
    "unit_types",
    "amenities",
    "nearby_places",
    "media",
  ]) {
    assert.match(source, new RegExp(`project\\.${value} \\?\\? \\[\\]`));
  }
  assert.match(previewPage, /\(project\.media \?\? \[\]\)\.map/);
});

test("private preview metadata uses the localized Project name", () => {
  assert.match(previewPage, /const projectName = localizedDisplayText\(project\.project_name, locale\)/);
  assert.match(previewPage, /title: `\$\{projectName\} \| \$\{localizedBrand\(locale\)\}`/);
  assert.match(previewPage, /normalizeArabicUserFacingText\(project\.overview \?\? projectName\)/);
  assert.match(previewPage, /description,/);
  assert.doesNotMatch(previewPage, /title: "Private Project preview/);
});

test("project media keeps amenities and plan/map categories separate from gallery", () => {
  assert.match(
    source,
    /id: "amenities" as const, label: t\.amenities, categories: \["amenities"\]/,
  );
  assert.match(source, /categories: \["floor-plan"\]/);
  assert.match(source, /categories: \["master-plan"\]/);
  assert.match(source, /categories: \["location-map"\]/);
  assert.match(
    source,
    /categories: \["gallery", "exterior", "interior", "construction"\]/,
  );
  assert.doesNotMatch(
    source,
    /categories: \["gallery", "exterior", "interior", "amenities"/,
  );
});

test("missing handover and incomplete payment plans use the canonical localized phone CTA", () => {
  assert.match(source, /callUs: "Call us"/);
  assert.match(source, /callUs: "اتصل بنا"/);
  assert.match(source, /href=\{COMPANY_PHONE_TEL\}/);
  assert.match(source, /const hasVerifiedPayment = Boolean/);
  assert.match(source, /normalized\.handover[\s\S]*ContactFact/);
  assert.doesNotMatch(source, /value=\{normalized\.handover \|\| t\.notConfirmed\}/);
});

test("owner-created native 2-to-1 Project Heroes remain eligible without upscaling", () => {
  assert.match(source, /item\.width >= 1400 && item\.height >= 600/);
  assert.doesNotMatch(source, /item\.height >= 900/);
});
