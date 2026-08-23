# ARE Design Foundation Readiness

| Field | Result |
| --- | --- |
| Task | `ARE-DS-00 — Brand Asset Audit and Design Foundation Readiness`, updated by `ARE-DS-00A — Official Logo Intake and Brand Decision` |
| Audit date | 23 August 2026 |
| Scope | Documentation and implementation readiness only |
| Readiness outcome | **READY WITH GAPS — ARE-DS-01 AUTHORIZED** |

## 1. Executive readiness result

The locked ARE Design System contains enough exact UI color, semantic state, spacing, layout, radius, border, elevation, motion, RTL, focus, and accessibility direction to begin a bounded cross-platform token foundation.

The repository contains one owner-supplied official logo reference: `brand-source/aliyas-real-estate-logo-candidate.png`. The owner has now locked the UI palette/logo relationship, Roboto Flex and IBM Plex Sans Arabic, typography normalization authority, official-source self-hosting/licensing, Lucide icon family, English-logo Arabic-launch policy, cross-platform mapping, media-rights governance, and production-logo method in `docs/ARE_DESIGN_OWNER_DECISIONS.md`. `ARE-DS-01` is authorized as the next bounded task. Actual font assets, icon packages, editable/vector logo source, production logo variants, Arabic/bilingual wordmark, rights-cleared media, and 3D/AR remain deferred gaps; this is not production-brand or homepage readiness.

## 2. Sources reviewed

- `AGENTS.md`.
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`.
- `ARE DESIGN SYSTEM v1.0.md`.
- `docs/ARE_FOUNDATION_LOCK.md`.
- `docs/ARE_IMPLEMENTATION_PLAN.md`.
- `docs/ARE_DESIGN_OWNER_DECISIONS.md`.
- `docs/ARE_MOBILE_FOUNDATION.md`.
- `.agents/skills/are-frontend-implementation/SKILL.md`.
- `.agents/skills/are-mobile-implementation/SKILL.md`.
- `README.md`.
- Root and all three workspace manifests.
- Repository root and all non-generated files and directories, including the expected web public directories and `apps/mobile`.
- Owner-supplied `brand-source/aliyas-real-estate-logo-candidate.png`, inspected read-only at its owner-confirmed SHA-256.

No application, browser, service, Metro server, emulator, or port was started for this audit.

## 3. Existing asset inventory

One relevant existing asset was discovered and accepted by explicit owner confirmation. It is the official visual reference for the current English ALIYAS Real Estate identity, not a production master and not an authorized runtime asset.

| Inspected location | Result |
| --- | --- |
| Repository root | One owner-supplied PNG under `brand-source`; no other image, vector, icon, font, video, document, 3D, or design-source asset |
| `apps/public-web/public` | Directory absent |
| `apps/admin-web/public` | Directory absent |
| `apps/mobile` | Scaffold/configuration files only; no assets |
| Asset/image/font/icon/media/brand/public directories | `brand-source` contains only the approved reference PNG; no runtime/public asset directory exists outside excluded generated/dependency output |
| Source references to relevant asset extensions or asset paths | None |
| Reference-site screenshot | Absent from the repository; no pixel-level audit performed |

### 3.1 Verified logo-reference properties

| Property | Verified result |
| --- | --- |
| Repository path | `brand-source/aliyas-real-estate-logo-candidate.png` |
| Classification | **APPROVED REFERENCE ASSET**; production master **NOT READY**; runtime/public asset **NOT YET AUTHORIZED** |
| SHA-256 | `68568b57031d16ffe5405758c09fd2101859ec6c052dcade440c644cba0e462e` |
| File format and size | Valid PNG; 93,924 bytes |
| Dimensions | 2885 × 2885px |
| Encoded color mode | 4-bit indexed-color PNG, seven palette entries, non-interlaced |
| Transparency | Yes, through a `tRNS` palette-alpha chunk; the canvas is transparent, not solid white |
| Dominant visible color | `#3D2605` at alpha 254; 947,940 pixels (11.3891% of the canvas) |
| Other visible palette colors | Partially transparent antialias tones `#3C2403`, `#3B2302`, `#392101`, `#331C00`, and `#100000` |
| Transparent palette entry | `#47704C` at alpha 0; it is storage data, not a visible logo or background color |
| Alpha distribution | 7,327,224 fully transparent pixels; 996,001 partially transparent visible pixels; alpha range 0–254; no alpha-255 pixels |
| Visible content bounds | x=138–2747, y=365–2320; 2610 × 1956px visible bounds |
| Transparent canvas padding | 138px left, 137px right, 365px top, 564px bottom |
| Resolution metadata | Approximately 488 pixels per inch (`pHYs` 19,213 pixels/metre) |
| Embedded metadata | XMP identifies Canva as creator tool, ALIYAS GROUP/Aliyas Group attribution, creation date 2026-08-23, internal Canva attribution identifiers, and source title `AMAFH Employment.pdf - 1`; EXIF records resolution metadata |
| Duplication | No duplicate or derived logo file discovered |

The unrelated-looking embedded source title and Canva internal identifiers are retained unchanged because metadata stripping is prohibited in this intake. They are another reason this file is a reference rather than the final production export.

Asset classification summary:

| Classification | Count | Evidence |
| --- | ---: | --- |
| Approved | 1 reference asset | Owner-supplied PNG classified **APPROVED REFERENCE ASSET**; this does not authorize runtime use |
| Candidate — owner review required | 0 | No candidate file found |
| Placeholder | 0 | No placeholder asset found |
| Missing | 30 production package/evidence items listed in Section 4 | The reference PNG does not replace the required production package |
| Rights/provenance unknown | 0 files solely classified this way | Owner supply and Canva/ALIYAS metadata establish reference provenance; production lettering/source-rights confirmation remains missing |
| Technically unsuitable | 0 files solely classified this way | The PNG is suitable as a visual reference but not as a production master/runtime asset |

## 4. Missing production asset package

All production items below remain absent. The current PNG verifies the stacked identity visually but is not authority to reconstruct, trace, recolor, crop, or derive any of these outputs. Suggested dimensions, crops, or variants must be defined only from the owner-approved editable/vector source and real consumer requirements.

| Required item | Classification | Minimum evidence or source needed |
| --- | --- | --- |
| Original editable Canva source or equivalent vector source | Missing | Owner-controlled editable source, version, export authority, and rights evidence |
| SVG master | Missing | Approved vector master; no auto-tracing or reconstruction from the PNG |
| Transparent PNG production export | Missing | Approved export from the editable/vector source; the current transparent reference is not runtime-authorized |
| Horizontal navigation lockup | Missing | Approved compact lockup for responsive headers |
| Current stacked lockup production export | Missing | Approved source-derived export matching the current identity without the reference file's metadata/padding ambiguity |
| Monogram-only mark | Missing | Approved standalone mark and safe-area/minimum-size rules |
| Light/inverted variant | Missing | Approved high-contrast artwork for Carbon/Espresso and media surfaces |
| Dark variant | Missing | Approved artwork for light surfaces; do not assume the current brown is the final production specification |
| Single-color variant | Missing | Approved one-color artwork and reproduction rules |
| Favicon source and exports | Missing | Approved mark plus browser-size/export specification |
| Social avatar/export | Missing | Approved monogram-focused square export and safe area |
| Social-sharing image | Missing | Approved template, safe areas, content rules, and rights-cleared media |
| Mobile app icon master | Missing | Approved square master before identifiers/store work |
| Mobile splash source | Missing | Approved source and behavior before store/build configuration |
| Clear-space rule | Missing | Owner-approved exclusion zone derived from the master geometry |
| Minimum-size rule | Missing | Verified thresholds for full lockup, wordmark, monogram, print, and signage |
| Color specifications | Missing | Approved logo color values and reproduction profiles from the master source |
| Typography/lettering ownership confirmation | Missing | Rights and modification/use authority for the custom wordmark and source lettering |
| Property/project and hero imagery | Missing | Rights-cleared originals, provenance, captions, and crop authority |
| Developer logos | Missing | Developer authorization, attribution, and brand-use terms |
| Community/location imagery | Missing | Location-accurate, rights-cleared originals |
| Team/agent photography | Missing | Approved portraits, consent, usage scope, and retention rules |
| Arabic/bilingual wordmark asset | Missing | Not required for launch; the approved English mark serves both locales, while any future Arabic/bilingual artwork requires a separate owner-approved branding task |
| Roboto Flex font files | Missing | Official `googlefonts/roboto-flex` source and OFL 1.1 are approved; exact version/files/formats/hashes remain for `ARE-DS-01` |
| IBM Plex Sans Arabic font files | Missing | Official `IBM/plex` source and OFL 1.1 are approved; exact version/files/formats/hashes remain for `ARE-DS-01` |
| Font licence artifact | Missing | Approved OFL 1.1 text must be committed alongside the exact future font files |
| Video/media and poster frames | Missing | Rights-cleared masters, captions/transcripts where meaningful, and static posters |
| Floor plans and brochures | Missing | Approved documents, rights, public/private classification, and accessible alternatives |
| Optional 3D assets | Missing | Future feasibility evidence only; no format is selected now |
| Media-rights manifest | Missing | Asset ID/checksum, source, owner, licence, attribution, territory, term, and approval status |

## 5. Brand approval and media-rights status

### 5.1 Owner decision and classification

| Decision subject | Recorded status |
| --- | --- |
| Current ALIYAS monogram and English wordmark identity | **OWNER APPROVED** |
| Exact spelling | Must remain `ALIYAS` and `REAL ESTATE` |
| Monogram geometry and wordmark | Must not be redesigned, reconstructed, auto-traced, or replaced without further owner approval |
| Supplied PNG | **APPROVED REFERENCE ASSET**; official visual reference only |
| Production master | **NOT READY** |
| Runtime/public asset | **NOT YET AUTHORIZED**; do not copy into public web, Admin web, or mobile |

The brown/tan/black/white brand continuity and Future Heritage 2030 UI direction remain the governing design authority. The UI palette is not authority for recoloring or reconstructing the logo, and the logo reference does not replace the UI palette. Owner supply and embedded Canva/ALIYAS metadata establish reference provenance, but the original editable source, export authority, typography/lettering ownership confirmation, final production specifications, and broader media-rights evidence remain outstanding.

Public availability or appearance on a developer/reference website would not establish reuse rights. A later media workflow must retain asset checksum, source, ownership/licence evidence, attribution, effective term, related record, approval state, and public/private access status.

### 5.2 Technical and visual logo assessment

| Assessment area | Result |
| --- | --- |
| Architectural/real-estate relevance | The geometric `A` reads as an architectural apex, roofline, or paired tower form and is relevant to a premium real-estate identity without relying on a literal property pictogram. |
| Monogram recognition | The nested `A` construction is distinctive and recognizable at moderate/large sizes. Its internal counter and closely related diagonal strokes require a verified monogram master before very small use. |
| Wordmark hierarchy | Monogram first, `ALIYAS` second, and the smaller `REAL ESTATE` descriptor third is a clear and appropriate hierarchy. |
| Letter spacing | `ALIYAS` uses controlled open spacing; `REAL ESTATE` is deliberately widely tracked. The descriptor spacing supports the premium tone at large sizes but magnifies small-size legibility loss. |
| Alignment and balance | Artwork is horizontally centered with 138px/137px side padding. The stacked arrangement is visually stable; vertical canvas padding is uneven at 365px top and 564px bottom. |
| Surrounding whitespace | Generous transparent space protects the reference composition but makes the full square inefficient for compact runtime placements. Cropping or whitespace removal is not authorized. |
| Small-size readability | The monogram and `ALIYAS` remain the strongest elements; the descriptor loses clarity first. A formal minimum-size test cannot be locked without source-derived exports. |
| `REAL ESTATE` readability | Clear at the supplied large reference size, but too small relative to the full square canvas for favicon, compact navigation, or small social-avatar use. It must not be relied on as accessible text. |
| Header/navigation suitability | The current square stacked PNG is not suitable for direct header use because of its aspect ratio, embedded whitespace, and small descriptor. An approved horizontal responsive lockup is required. |
| Footer suitability | The stacked composition can inform a larger light-surface footer placement, but the current PNG remains runtime-unauthorized and lacks an approved inverted/light variant for the locked dark footer. |
| Light-surface suitability | Nominal `#3D2605` contrast is 14.21:1 on White and 13.16:1 on Ivory, providing strong visual separation. Final rendered contrast still requires production-export testing. |
| Dark-surface suitability | Not suitable as supplied: nominal contrast is only 1.38:1 on Carbon, 1.15:1 on Espresso, and 1.37:1 on Heritage Brown. An owner-approved light/inverted variant is required; do not recolor this PNG. |
| Favicon suitability | Full lockup is unsuitable. An approved monogram-only favicon source and size-specific exports are required. |
| Mobile app-icon suitability | Not ready. A source-derived 1024 × 1024 master with platform-safe composition and approved background behavior is required; the current lockup/transparency must not be used directly. |
| Social-avatar suitability | Full lockup is unsuitable at avatar sizes because the descriptor will disappear. An approved monogram-focused square export is required. |
| Arabic-branding implications | Launch policy is resolved: the approved English mark serves both locales, is never mirrored internally in RTL, and may receive localized accessible naming. Arabic spelling/transliteration or a bilingual lockup must not be invented and remains a future branding task. |
| One-color reproduction | The visible artwork is effectively one dominant brown plus antialias palette entries, but one-color print/digital reproduction is not approved until a source-derived single-color vector exists. |
| Print/signage scalability | 2885px raster resolution and approximately 488ppi metadata may support bounded reference proofs, but they do not provide vector scalability, production color management, or signage authority. |
| Color contrast | Strong on locked light neutrals; weak on locked dark/brown surfaces. Ratios below are nominal comparisons, not a substitute for implemented non-text contrast review. |
| Design System consistency and exact palette conflict | `#3D2605` belongs to the locked brown family and supports the intended identity, but it is not equal to any locked UI token. The Design System explicitly permits logo artwork and UI tokens to remain separate authorities, so no automatic recolor or palette change is justified. |

### 5.3 Locked Design System palette comparison

The dominant visible logo color is `#3D2605` at alpha 254. The following ratios compare its nominal RGB value with every relevant locked core brand/accent and surface color; they do not promote it to a UI token.

| Locked color | Exact value | Contrast with `#3D2605` | Decision relevance |
| --- | --- | ---: | --- |
| Carbon 950 | `#0E0B0A` | 1.38:1 | Insufficient separation; requires approved light/inverted logo |
| Ink 900 | `#17110E` | 1.32:1 | Insufficient separation |
| Espresso 850 | `#2B1C16` | 1.15:1 | Closest dark layer; insufficient separation and not an exact match |
| Heritage Brown 700 | `#5A3827` | 1.37:1 | Primary UI action brown; distinct from logo brown and not a contrast surface |
| Architectural Bronze 600 | `#7A5135` | 2.07:1 | Distinct secondary brand detail; insufficient as a background contrast pair |
| Copper 500 | `#A56F48` | 3.36:1 | Distinct decorative accent; limited separation |
| Desert Sand 400 | `#C9A77C` | 6.29:1 | Strong nominal separation |
| Champagne 300 | `#D9B487` | 7.33:1 | Strong nominal separation |
| Warm Stone 100 | `#EEE8E1` | 11.68:1 | Strong light-surface separation |
| Ivory 50 | `#F8F6F2` | 13.16:1 | Strong preferred light-surface separation |
| White 0 | `#FFFFFF` | 14.21:1 | Strong light-surface separation |
| Muted Umber 600 | `#625850` | 2.05:1 | Distinct text neutral; insufficient as a logo background pair |
| Digital Aqua 400 | `#4CCFC0` | 7.44:1 | Strong numerical separation, but Aqua remains limited to intelligent/live/map context and is not a logo color |

No locked UI color exactly matches `#3D2605`. The owner has resolved the relationship without changing either authority: `#3D2605` is logo-specific Heritage Ink, not a general UI token, while the existing Design System palette remains unchanged and authoritative for interfaces. The current brown logo is limited to sufficient-contrast surfaces; Carbon, Espresso, and other insufficient-contrast dark surfaces require a future approved Ivory/white inverted variant. The editable/vector source must still provide the final production color specification.

## 6. Reference-site compatibility assessment

The owner-approved reference interpretation is compatible with ARE's locked direction at the level of editorial hierarchy, a prominent hero-associated search, spacious rhythm, architectural imagery, clear property/project cards, restrained luxury detail, verified trust evidence, content, lead capture, and a structured dark footer.

The repository does not contain the reference screenshot, so no pixel-level comparison is claimed. The reference must not supply ARE identity or business truth. Its name/logo, text, headings, prices, statistics, testimonials, property names, contact details, images, icons, exact composition, and exact styling are prohibited from copying.

One explicit boundary is typography: no serif family is approved. The reference preference for display-led hierarchy must be met with Roboto Flex's approved variable capabilities; introducing a serif requires an explicit documented owner decision that supersedes the current lock.

## 7. Locked ARE visual direction

ARE is a premium UAE real-estate product with modern 2030-forward presentation, cinematic architectural storytelling, editorial clarity, controlled spatial depth, large rights-cleared imagery, refined bilingual typography, restrained glass/refraction on approved landmark surfaces, purposeful motion, strong mobile behavior, and commercially trustworthy information states.

The implementation must avoid cyberpunk/neon styling, generic SaaS/template appearance, excessive gradients or glass, constant animation, purposeless empty sections, fake luxury claims, invented statistics/listings, and effects that harm readability or performance. Exact colors, typography, spacing, radii, shadows, and motion remain subordinate to the locked Design System.

## 8. Public/admin/mobile distinctions

| Platform | Required interpretation |
| --- | --- |
| Public web | Most expressive surface; SEO/server-first; cinematic media within performance budgets; Motion client islands and Embla only when a real interaction requires them |
| Admin web | Same semantic foundation at operational density; light high-clarity workspace; tables, forms, state, evidence, and speed take priority over cinematic treatment |
| Android/iOS mobile | Native touch-first interpretation; semantic token values may be shared, but not DOM/CSS/Tailwind/Next.js components; safe areas, font scaling, native reading order, and Reanimated/Gesture Handler rules apply |

The current PNG is reference-only across all three platforms. It must not be copied into any runtime application until the appropriate production lockup is owner-approved and a separate implementation task authorizes it.

## 9. Cross-platform token-readiness matrix

| Foundation item | Locked evidence and platform mapping | Readiness classification | Gap or smallest decision |
| --- | --- | --- | --- |
| UI brand colors | Exact core UI palette remains unchanged and authoritative across web/native semantic translation; logo-specific Heritage Ink `#3D2605` remains separate | Ready for implementation | Do not promote Heritage Ink to a general UI token or change the UI palette to match it |
| Logo colors | Owner locked `#3D2605` as logo-specific Heritage Ink and prohibited dark-surface use without an approved light/inverted variant | Requires asset | Editable/vector source, production color specification, and approved variants remain deferred without blocking `ARE-DS-01` |
| Semantic colors | Success, warning, error, information, and AI/live strong/soft pairs are defined | Ready for implementation | Validate implemented contrast and non-color cues |
| Surface hierarchy | Light/dark page, surface, subtle, text, action, and border roles are defined | Ready for implementation | Dark mode is selective, not a blanket default |
| Text hierarchy | Display, heading, body, label, overline, metadata, and data behavior are described | Ready for implementation | Exact font delivery remains gated |
| Borders/dividers | Light, strong, and dark border values and focus offsets are defined | Ready for implementation | Native adapters must preserve visual contrast |
| Typography families | Roboto Flex and IBM Plex Sans Arabic are owner-approved from their official projects under OFL 1.1; no serif or third production family is approved | Ready for implementation | `ARE-DS-01` must acquire and pin exact files, formats, hashes, and OFL text; runtime CDN loading is prohibited |
| Display/body/utility roles | Roles and intended uses are defined | Ready for implementation | Preserve Arabic metric differences |
| Type scale | Semantic roles and ranges exist; owner authorized script/platform optical normalization without changing role hierarchy | Ready for implementation | `ARE-DS-01` may map size, line-height, tracking, and weights per script/platform within the locked roles |
| Font weights | Role ranges exist and may be normalized per script/platform within the approved family/source baseline | Ready for implementation | Select the smallest verified weight/axis set during `ARE-DS-01` font acquisition |
| Spacing scale | 4px scale from 0 through 128px is defined | Ready for implementation | Expose semantic aliases only where real use exists |
| Layout/container system | Web columns, gutters, containers, reading/form widths, and section rhythm are defined | Ready for implementation | CSS container values are not mobile layout primitives |
| Breakpoints | Five public-web ranges and responsive behavior are defined | Ready for implementation | CSS breakpoints are Not applicable to platform on native; native uses window/orientation adaptation |
| Radius scale | Seven exact radii and usage guidance are defined | Ready for implementation | Use fewer sizes per surface |
| Shadow/elevation | Exact web shadows exist; owner authorized shared Flat/Raised/Floating/Overlay intents with native iOS shadow and Android elevation mapping | Ready for implementation | `ARE-DS-01` maps intents to locked values without inventing new purpose or requiring pixel identity |
| Icons | Lucide is owner-approved as the sole general interface family: `lucide-react` for web and `lucide-react-native` for mobile | Ready for implementation | Exact compatible package versions remain uninstalled and must be pinned only in their authorized implementation task |
| Image treatment | Ratios, art direction, overlays, performance, and rights rules exist | Requires asset | Supply rights-cleared masters and responsive crops |
| Cards | Property/project/developer/location/agent/content anatomy and states are defined | Ready for implementation | Component work belongs to later approved tasks |
| Buttons | Variants, heights, hierarchy, loading, icon, and CTA rules are defined | Ready for implementation | Validate each platform's native/keyboard behavior |
| Form controls | Heights, labels, errors, density, and async states are defined | Ready for implementation | Use native controls where they meet mobile needs |
| Search UI | Hero search, results, filters, and map/list behavior are defined | Ready for implementation | Real data/contracts and content remain later gates |
| Navigation | Public header/footer/breadcrumb and Admin shell direction are defined | Ready for implementation | Approved horizontal, responsive, and dark-footer logo lockups plus route/content inventory are required for production |
| Motion durations/easing | Exact representative tokens and approved patterns exist | Ready for implementation | Translate semantic timing to Motion/Reanimated without sharing runtime components |
| Reduced motion | Removal/near-instant behavior and essential-content rule are mandatory | Ready for implementation | Must be verified per platform in implementation tasks |
| RTL behavior | Mirroring, logical properties, mixed-script isolation, and non-mirroring rules are defined | Ready for implementation | Arabic visual/content review remains mandatory |
| Focus states | Exact web rings/offsets and interaction rules exist | Ready for implementation | CSS focus styling is Not applicable to platform on native; preserve native accessibility focus semantics |
| Accessibility | WCAG 2.2 AA target, 44px targets, zoom, labels, state, screen-reader, and data alternatives exist | Ready for implementation | Actual components still require automated and manual verification |
| Web/mobile token equivalence | Shared semantic names/intent with separate web CSS and native adapters is owner-approved; platform-native accessibility and rendering take priority over pixel identity | Ready for implementation | No platform may silently create a different brand palette |

## 10. Typography and font-licensing readiness

Typography authority is resolved. Roboto Flex is the approved English/Latin production family from `googlefonts/roboto-flex`, and IBM Plex Sans Arabic is the approved Arabic production family from `IBM/plex`; both use the SIL Open Font License 1.1. No serif or third production family is approved. System-font stacks remain technical fallbacks only.

Fonts must be self-hosted from verified official sources without a runtime Google Fonts/CDN dependency. `ARE-DS-01` is authorized to select and pin exact source versions, WOFF2/variable assets for web where suitable, compatible TTF/OTF assets for mobile, file hashes, formats, and required OFL texts. Web and mobile must share the approved family/source baseline. Any subsetting or conversion must be reproducible, licensed, validated, and documented.

Semantic type roles remain shared, while `ARE-DS-01` may normalize size, line-height, tracking, and weight for script/platform optical equivalence, readability, and accessibility. Arabic must not inherit Latin letter spacing, and mobile user font scaling remains mandatory.

## 11. Responsive and RTL readiness

Public/admin web have defined viewport bands, grid/gutter behavior, section rhythm, responsive patterns, logical-property direction, mixed-script isolation, and independent Arabic QA requirements. Mobile has an approved native boundary: safe areas, orientation/device adaptation, font scaling, correct reading order, touch-first behavior, directional mirroring, and non-mirroring of logos, media, maps, plans, and other non-directional content.

The specifications are ready for implementation. The approved English ALIYAS Real Estate logo is the official launch mark in both English and Arabic interfaces, must never be mirrored internally in RTL, and may receive localized accessible labels. No Arabic spelling, transliteration, or bilingual lockup may be invented. A future Arabic/bilingual wordmark remains deferred and does not block Arabic interface implementation. Real Arabic content, components, and assistive-technology behavior still require later implementation evidence.

## 12. Motion readiness

- `motion@13.1.1` remains declared only by `apps/public-web`.
- `embla-carousel-react@8.6.0` remains declared only by `apps/public-web`.
- Native browser scrolling remains the web default; no scroll-hijacking engine is approved.
- `react-native-reanimated@4.5.1` and `react-native-gesture-handler@2.32.0` remain declared only by `apps/mobile`.
- Motion must be purposeful, use opacity/transform where possible, preserve essential content, and respect operating-system reduced motion.
- Additional motion, carousel, gesture, smooth-scroll, or animation engines require owner approval.
- Public Motion components must not be reused in React Native; native motion uses small Reanimated-native boundaries.

## 13. 3D/AR readiness

3D/AR is not ready and is not part of this task. No model asset, model rights evidence, engine, format, loader, performance budget, accessibility alternative, or platform delivery strategy exists. GLB, glTF, USDZ, or another format is not selected by this document.

A later post-MVP feasibility task must evaluate accurate/labelled assets, rights, web/native compatibility, representative-device performance, download size, interaction, accessibility, and fallback behavior. An approved static poster and non-3D content alternative must exist before any 3D implementation.

## 14. Accessibility readiness

The governing system is implementation-ready at the requirements level: WCAG 2.2 AA intent, visible focus, keyboard operation, 44×44px targets, persistent labels, accessible errors, non-color state cues, 200% web zoom, screen-reader names/states, reduced motion, media captions/transcripts, data alternatives, and equivalent RTL behavior are all specified.

The logo reference received technical and visual intake assessment only; no component, page, native device build, assistive-technology run, Arabic UI, or production media experience was tested. Accessibility readiness therefore means the acceptance contract is defined, not that a product experience has passed. The baked-in English wordmark must not replace semantic text or accessible naming in a later implementation.

## 15. Implementation blockers

| Scope | Blocker |
| --- | --- |
| Token-only color/spacing/radius/motion foundation | No remaining design-decision blocker; `ARE-DS-01` is authorized as the next bounded task |
| Typography font loading | Official sources, families, licences, self-hosting, and normalization authority are locked; exact acquisition/files/formats/hashes/OFL artifacts remain an `ARE-DS-01` implementation dependency, not an authorization blocker |
| Logo/header/footer/app identity | English launch identity/policy is locked; missing editable/vector source and production variants do not block `ARE-DS-01` but block final branded-page and store-asset completion |
| Icon-bearing components | Lucide is selected; exact `lucide-react`/`lucide-react-native` package versions and installation remain deferred to an authorized component implementation task |
| Production cards, hero, listings, projects, locations, team, social, and app/store visuals | Rights-cleared asset package and operational provenance records remain missing; this does not block the token/typography foundation |
| Cross-platform native elevation/type adaptation | Authority is resolved through shared semantic intents and platform-native mapping; exact implementation remains for `ARE-DS-01` |
| 3D/AR | Entirely deferred to later feasibility |

## 16. Owner decisions required

No owner decision remains required before the bounded `ARE-DS-01` token and typography foundation. `docs/ARE_DESIGN_OWNER_DECISIONS.md` is the binding authority.

### Resolved and binding

- UI palette remains authoritative; logo-specific Heritage Ink `#3D2605` remains separate and contrast-constrained.
- Roboto Flex and IBM Plex Sans Arabic are approved; no serif or third production family.
- Typography may be normalized by platform/script while preserving semantic roles and accessibility.
- Official-source, OFL 1.1, self-hosted font delivery is approved; runtime font CDN use is prohibited.
- Lucide is the sole general interface icon family.
- The English logo is the official launch mark in both locales and is not mirrored in RTL; localized accessible naming is permitted.
- Shared semantic token intent with platform-native elevation, typography, safe-area, focus, RTL, font-scaling, and screen-reader behavior is approved.
- ALIYAS owner or explicitly authorized management is the media approval authority; the minimum provenance record is locked.
- AI-generated/conceptual media requires approval, internal classification, provenance, and non-misleading use.
- Production logo variants must originate from the editable Canva or verified original vector source without tracing, reconstruction, or redrawing.

### Deferred without blocking ARE-DS-01

- Actual font acquisition and exact font versions, files, formats, hashes, and committed OFL texts.
- Exact Lucide package versions and installation.
- Editable Canva/vector logo source and production logo variants.
- Arabic/bilingual wordmark.
- Rights-cleared property/project media and operational provenance storage.
- 3D/AR feasibility and assets.
- Final branded-page, homepage, store-asset, or production readiness.

## 17. ARE-DS-01 entry criteria

`ARE-DS-01 — Cross-Platform Design Tokens and Typography Foundation` is owner-authorized as the next bounded task, but is not executed by this decision lock. It may begin only from its separately verified task state and must:

- Follow `docs/ARE_DESIGN_OWNER_DECISIONS.md` without silently reinterpreting it.
- Verify and record exact official font source versions, files, hashes, formats, and OFL artefacts before committing font assets.
- Define one semantic token intent with separate web and native adapters, not shared DOM/CSS/runtime components.
- Preserve the locked UI palette, logo-specific Heritage Ink separation, semantic typography roles, script/platform normalization authority, native accessibility, and RTL behavior.
- Keep missing logo variants, media, Lucide installation, components, pages, and content explicit and outside scope unless the separate task authorizes them.
- Remain limited to tokens, typography, focus/reduced-motion foundations, RTL-safe semantics, and proportional validation.

## 18. Explicit non-goals

This audit, intake, and decision lock record authority only. They do not implement runtime logo use, derived logo assets, UI, CSS/Tailwind tokens, React Native token files, fonts, icons, other imagery, components, pages, homepage sections, mobile screens, business content, Figma files, packages, dependency changes, advisory remediation, provenance storage, services, browsers, ports, EAS, deployment, or 3D/AR. They do not prove production lettering/media rights, claim production-brand or homepage readiness, or execute `ARE-DS-01`.
