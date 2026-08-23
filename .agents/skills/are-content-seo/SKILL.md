---
name: are-content-seo
description: Create, rewrite, review, or implement trustworthy bilingual English/Arabic content and search-discovery foundations for ALIYAS Real Estate pages. Use for ARE copy, keyword mapping, metadata, technical SEO, locale SEO, internal links, and evidence-backed structured data; do not use for database migrations, backend architecture, visual design implementation, deployment, or invented business or legal claims.
---

# ARE Content and SEO

## Establish authority

Read the current owner instruction and the relevant repository authorities before acting:

- `AGENTS.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `docs/ARE_DESIGN_OWNER_DECISIONS.md`

Use the frontend skill as an additional authority only when the task explicitly includes frontend implementation. Stop on conflicts or missing content approval instead of filling gaps.

## Select the authorized mode

- For creation or rewriting, deliver only the requested content and approval notes.
- For review, report evidence and recommendations without changing content or code.
- For implementation, change only the approved routes, metadata, or SEO foundation.
- Keep content approval separate from code completion. Do not treat technically integrated copy as owner-approved copy.

## Preserve truth and voice

- Write in a premium, confident, clear, and human ALIYAS voice. Avoid exaggerated claims and generic luxury language.
- Maintain professional Arabic with equivalent meaning, hierarchy, and intent; do not produce a literal low-quality translation.
- Preserve complete RTL behavior and accessible reading order when implementation is authorized.
- Distinguish owner-approved facts from visibly marked non-production placeholders.
- Never fabricate properties, projects, prices, availability, statistics, testimonials, ratings, awards, licences, partnerships, locations, contact details, or legal claims.
- Preserve the official `ALIYAS Real Estate` identity. Do not invent an Arabic logo, Arabic wordmark, transliteration, or bilingual lockup.

## Cover approved content surfaces

Create or review only requested homepage, property, project, community, service, about, contact, FAQ, or editorial content. Keep page purpose, search intent, user questions, and conversion path coherent across English and Arabic.

Map one primary intent and a restrained set of supporting terms per page. Use keywords naturally in headings, body copy, links, and metadata; never stuff, repeat mechanically, or write for crawlers at the expense of people.

## Implement trustworthy discovery foundations

When authorized, define or review:

- Unique page titles and meta descriptions.
- Stable canonical URLs and locale-aware equivalents.
- Open Graph and approved social metadata.
- XML sitemaps and robots directives.
- `hreflang` relationships and locale-safe indexation.
- Semantic heading order and descriptive link text.
- Relevant internal links between approved records and content.
- Descriptive localized image alternative text based on known image purpose.

Use Schema.org/JSON-LD only when every represented fact is evidence-backed, visible where required, eligible for the selected schema, and consistent with canonical data. Never add fake reviews, ratings, prices, listings, or availability to structured data.

Check current official search-engine guidance and current Next.js documentation whenever implementation depends on changing metadata, crawling, indexing, structured-data, or framework behavior. Record the guidance used without presenting it as business-content approval.

## Keep boundaries intact

- Do not design backend architecture, write database migrations, implement unrelated visual design, deploy, or create production business/legal copy without authority.
- Do not turn placeholders into indexable production claims.
- Use public web port `50001` only when runtime verification is explicitly authorized. Never bind or interfere with protected port `3000`.
- Do not push, merge, deploy, or modify production unless explicitly authorized.
- Report only measured checks; never claim production SEO readiness from local inspection alone.
