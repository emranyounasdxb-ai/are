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
  assert.match(source, /paymentPlan: plan\?\.raw_source_text\?\.trim\(\) \|\| null/);
  assert.doesNotMatch(source, /paymentPlan: project\.payment_plan/);
  assert.match(source, /plan\?\.milestones \?\? project\.payment_milestones \?\? \[\]/);
});

test("missing milestone percentages render no placeholder text", () => {
  assert.match(
    source,
    /item\.percentage == null \? null : <em>\{item\.percentage\}%<\/em>/,
  );
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
