# ARE Design Owner Decisions

## Authority and approval date

| Field | Decision |
| --- | --- |
| Task | `ARE-DS-00B — Design Owner Decisions Lock` |
| Approval date | 23 August 2026 |
| Approval authority | ALIYAS owner |
| Status | **OWNER APPROVED — BINDING** |
| Applies to | Public web, Admin web, Android mobile, and iOS mobile |
| Supersession rule | Only an explicit owner-approved documented decision may supersede this record |

These decisions resolve the bounded design authorities required before `ARE-DS-01`. Future implementation tasks must follow them without reopening, reinterpreting, replacing, or expanding them.

## Scope

This record locks the relationship between the official logo and interface palette, approved typography families and delivery, cross-platform normalization authority, the general icon family, Arabic launch-logo policy, semantic token mapping, media-rights governance, AI-media policy, and production-logo derivation method.

It does not implement tokens, fonts, icons, components, logo variants, application UI, assets, media storage, pages, or an Arabic wordmark. It does not authorize production-brand, homepage, store-asset, deployment, or release completion.

## UI palette and logo-color relationship

- The existing palette in `ARE DESIGN SYSTEM v1.0.md` remains unchanged and authoritative for application interfaces.
- The official reference logo's visible `#3D2605` is a logo-specific **Heritage Ink**.
- Heritage Ink must not automatically become a general UI token, button color, link color, or interface accent.
- The current brown logo may be used only where its implemented contrast is sufficient.
- It must not be placed directly on Carbon, Espresso, or another insufficient-contrast dark surface.
- Dark surfaces require a future owner-approved Ivory/white inverted logo variant.
- The current source PNG must not be recolored, and the Design System palette must not be changed to match it.
- Logo identity and the application-interface palette are related but distinct systems.
- Future production variants must use approved Design System-compatible light/dark treatments without changing the locked geometry.

## Typography families

| Script/use | Approved production family | Rule |
| --- | --- | --- |
| English and Latin | Roboto Flex | Provides the modern, editorial, variable, 2030-forward Latin hierarchy |
| Arabic | IBM Plex Sans Arabic | Provides the corresponding Arabic hierarchy and readability |
| Technical fallback | Approved system-font fallback stack | Fallback only; not a third production family |

- No serif family is approved.
- A decorative serif must not be added to imitate the reference website.
- No third production font family may be introduced without owner approval.

## Typography normalization authority

- Semantic typography roles are shared across platforms.
- Latin and Arabic do not require identical raw pixel metrics.
- Optical equivalence, readability, script characteristics, and accessibility are authoritative.
- `ARE-DS-01` may define platform- and script-specific size, line-height, tracking, and weight mappings where required.
- Normalization must preserve the locked semantic role and hierarchy; it must not change the approved families or create new editorial roles.
- Arabic must never be forced into Latin tracking or letter-spacing behavior.
- Mobile must continue to support user font scaling and platform accessibility settings.

## Font licensing and delivery

| Family | Approved official source | Approved licence |
| --- | --- | --- |
| Roboto Flex | [googlefonts/roboto-flex](https://github.com/googlefonts/roboto-flex) | SIL Open Font License 1.1 |
| IBM Plex Sans Arabic | [IBM/plex](https://github.com/IBM/plex) | SIL Open Font License 1.1 |

- Fonts must be self-hosted from verified official sources. A runtime Google Fonts or other font-CDN dependency is prohibited.
- `ARE-DS-01` must select and pin exact source versions, files, SHA-256 hashes, formats, and licence evidence.
- The required OFL licence text must be committed alongside the installed font files.
- Web may use verified optimized WOFF2/variable assets; mobile may use compatible verified TTF/OTF assets.
- Web and mobile must use the same approved family/source baseline.
- Font files are not downloaded or added by `ARE-DS-00B`.
- Family names must not be modified or renamed.
- Future subsetting or conversion requires a reproducible process, retained licensing, validation, and explicit documentation.

## Icon family

Lucide is the only approved general interface icon family across public web, Admin web, Android, and iOS.

| Platform | Approved later package family |
| --- | --- |
| Public/Admin web | `lucide-react` |
| Android/iOS mobile | `lucide-react-native` |

- Official source: [Lucide](https://lucide.dev/)
- Licence: ISC

- Use outline icons by default with semantic size and stroke tokens.
- Import only icons actually used and preserve tree-shaking.
- Do not mix general-purpose icon libraries, use emoji as UI icons, or mix random filled, outlined, and 3D styles.
- Filled state is allowed only when a real interaction state requires it and Lucide supports the intended treatment.
- Do not manually redraw Lucide paths.
- Brand and social logos are separate official assets, not Lucide interface icons.
- Exact compatible package versions are selected and pinned only by their authorized implementation task. `ARE-DS-00B` installs no package.

## Arabic logo policy

- The approved English ALIYAS Real Estate logo remains the official launch mark in both English and Arabic interfaces.
- Logo artwork must not be mirrored in RTL. Its container/alignment may participate in RTL layout, but internal geometry and lettering remain unchanged.
- Accessible logo labels and alternative text may be localized.
- No Arabic spelling, transliteration, or bilingual lockup may be invented.
- An Arabic/bilingual wordmark remains a future owner-approved branding task.
- Absence of an Arabic wordmark does not block Arabic interface implementation.

## Cross-platform token mapping

- Semantic token names and intent are shared across public web, Admin web, and mobile; rendering does not need to be pixel-identical.
- Web may use CSS variables and the locked web shadows.
- iOS may use native shadow properties. Android may use native elevation and compatible shadow behavior.
- Typography may receive the approved platform/script optical normalization.
- Safe areas, touch targets, font scaling, RTL, focus, and screen-reader behavior remain platform-native.
- Shared semantic intent takes priority over identical implementation mechanics.
- No platform may silently create a different brand palette.

Shared elevation intents are:

- **Flat**
- **Raised**
- **Floating**
- **Overlay**

`ARE-DS-01` may map these intents to existing locked Design System shadow/elevation values without assigning a new purpose or silently inventing a different elevation system.

## Media rights and provenance

- Only owner-approved and rights-cleared media may enter production runtime. This applies to images, video, developer logos, floor plans, brochures, maps, renders, drone footage, agent portraits, social assets, and 3D/AR models.
- Scraping or downloading does not grant publication rights. Reference screenshots are never reusable production assets.
- The ALIYAS owner or explicitly authorized management is the approval authority.
- The future Admin/Data Platform becomes the operational system of record.
- Sensitive contracts or licence evidence must not be committed to the application repository. Only non-sensitive identifiers and approval references may be stored here where needed.

Minimum provenance record:

| Required field | Purpose |
| --- | --- |
| Asset identifier | Stable reference |
| Asset type | Image, video, logo, document, model, or other approved category |
| Source/origin | Acquisition or creation source |
| Creator or rightsholder | Rights authority |
| Licensor, if applicable | Licence grantor |
| Permitted channels | Approved web, mobile, social, print, or other channels |
| Permitted territory | Geographic scope |
| Approval authority | ALIYAS owner or explicitly authorized management |
| Approval date | Effective approval evidence |
| Expiry date, if applicable | Time boundary |
| Evidence reference | Non-sensitive pointer to supporting evidence |
| Modification restrictions | Crop, edit, derivative, attribution, or other limits |
| Publication status | Operational eligibility state |

## AI-generated media policy

- AI-generated media requires owner approval and must be recorded internally as AI-generated or conceptual.
- It must not depict or claim a specific real property as accurate unless verified against approved source material.
- Conceptual imagery must not mislead users about availability, specifications, views, finishes, location, or construction status.
- AI generation does not bypass provenance, rights, approval, accuracy, accessibility, or publication controls.

## Production logo method

- The current official monogram geometry and English lettering remain unchanged.
- Production variants must originate from the editable Canva source or another verified original vector source.
- Auto-tracing, AI reconstruction, approximation, and redrawing are prohibited without approval.
- `brand-source/aliyas-real-estate-logo-candidate.png` remains an unchanged reference under `brand-source`; it is not a runtime asset.

Required future production package:

- SVG/vector master.
- Transparent PNG.
- Horizontal navigation lockup.
- Stacked lockup.
- Monogram-only mark.
- Light/inverted mark.
- Dark mark.
- Single-color mark.
- Favicon.
- Social avatar.
- 1024×1024 app-icon master.
- Splash-safe source.
- Clear-space specification.
- Minimum-size specification.
- Production color specification.

Missing production variants do not block `ARE-DS-01`; they do block final branded-page and store-asset completion.

## Decisions resolved

- Locked UI palette relationship to logo-specific Heritage Ink `#3D2605`.
- Roboto Flex and IBM Plex Sans Arabic production families; no serif.
- Cross-script/platform typography normalization authority.
- Official-source self-hosting and licensing authority.
- Lucide as the sole general interface icon family.
- English-logo launch policy for Arabic interfaces.
- Shared semantic token and native elevation/type-mapping authority.
- Media approval authority and minimum provenance record.
- AI-generated media restrictions.
- Production-logo source and derivation method.

## Items intentionally deferred

- Actual font acquisition, exact versions, file selection, formats, hashes, committed OFL texts, and any reproducible subsetting/conversion.
- Exact `lucide-react` and `lucide-react-native` package versions and installation.
- Editable Canva/vector logo source and every production logo variant.
- Arabic/bilingual wordmark.
- Rights-cleared property/project media and operational provenance storage.
- 3D/AR feasibility, engines, assets, and fallbacks.
- Final branded-page, homepage, store-asset, or production-readiness approval.

These deferrals do not block the bounded `ARE-DS-01` token and typography foundation.

## Change-control rule

- These decisions are owner-approved and binding on future implementation tasks.
- Any change to palette authority, approved fonts, icon family, Arabic logo policy, media-rights authority, or logo geometry requires explicit owner approval and a documented superseding decision.
- Codex and implementation agents must not silently reinterpret, broaden, replace, or partially ignore these decisions.
- A conflict must stop the affected task and be reported rather than resolved by assumption.

## ARE-DS-01 authorization boundary

**`ARE-DS-01 — Cross-Platform Design Tokens and Typography Foundation` is authorized as the next bounded task, but is not executed by `ARE-DS-00B`.**

`ARE-DS-01` may:

- Implement the already locked primitive and semantic token foundation with separate web and native adapters.
- Acquire approved official font assets, verify and record exact versions/files/hashes/formats/licences, and self-host them within the authorized change area.
- Normalize typography by platform and script within the approved semantic roles.
- Map Flat, Raised, Floating, and Overlay intents to existing locked web/native elevation behavior.
- Prepare RTL-safe, reduced-motion, focus, accessibility, and font-scaling foundations within its explicit task scope.

`ARE-DS-01` must not:

- Change the UI palette, promote `#3D2605` to a general UI token, recolor or deploy the reference PNG, or create logo variants.
- Introduce a serif, third production font, alternate icon family, new editorial role, or different platform brand palette.
- Build pages, homepage sections, production branded navigation, broad components, real media, provenance storage, or 3D/AR.
- Expand beyond the separately supplied `ARE-DS-01` implementation authority and validation contract.
