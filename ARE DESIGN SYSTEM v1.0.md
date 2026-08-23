# ARE DESIGN SYSTEM v1.0

## ALIYAS Real Estate — Future Heritage 2030

| Document field | Value |
| --- | --- |
| Version | 1.0 |
| Status | Recommended design baseline — owner review before production implementation |
| Date | 23 August 2026 |
| Product | ARE — ALIYAS Real Estate |
| Design concept | Future Heritage 2030 |
| Platforms | Public website, administration platform and responsive web experiences |
| Languages | English and Arabic |
| Architecture reference | ARE ARCHITECTURE BLUEPRINT v1.0 |

> A premium UAE real-estate experience where heritage warmth meets intelligent digital architecture.

---

## 1. Purpose

This design system defines the visual, interaction and component foundation for the ALIYAS Real Estate digital platform. It is designed to make every public and administrative screen:

- Premium and trustworthy.
- Modern enough to remain relevant toward 2030.
- Distinctive without becoming theatrical.
- Fast and practical on mobile.
- Consistent across property, project, content, lead and admin journeys.
- Fully usable in English and Arabic.
- Accessible to WCAG 2.2 AA.
- Implementable as reusable design tokens and typed components.

This is not only a mood board. It defines colors, typography, spacing, grids, surfaces, motion, icons, component anatomy, states, page templates, responsive behavior, Arabic RTL rules and implementation governance.

### 1.1 Relationship to the architecture

The design system must not create a second source of business truth. Property, project, price, availability, agent, location and content displays consume approved application data and respect the architecture's verification and publication rules.

The design system covers:

- Public website presentation.
- Admin application presentation.
- Shared tokens and primitives.
- Reusable interaction patterns.
- Responsive and RTL behavior.
- Loading, error, empty, stale and unavailable states.

It does not decide business workflows, permissions, data schema, content approval or public pricing policy.

### 1.2 Existing brand continuity

The prior ARE brand profile establishes:

- Brown as the primary brand family.
- Tan as the secondary brand family.
- Black text and white background foundations.
- Roboto as the typography family.
- A professional, friendly, respectful, minimal, luxury and corporate tone.
- Trust, transparency, customer-centricity and quality as brand values.

The available earlier records do not provide a reliable, conflict-free set of exact logo hex codes. Therefore:

1. The UI palette in this document is a deliberate modern evolution of the brown/tan/black/white identity.
2. The original logo must not be recolored from guessed values.
3. Exact logo colors must be extracted from the approved master SVG/brand file before production.
4. UI tokens and logo artwork remain separate authorities.

---

## 2. Design concept — Future Heritage 2030

### 2.1 Core idea

Future Heritage 2030 combines:

- The warmth of UAE desert, stone, bronze and hospitality.
- The precision of contemporary architecture.
- The clarity of a high-performance digital product.
- The intelligence of contextual search, data and AI assistance.
- The restraint expected from a premium real-estate advisor.

The result should feel advanced because it is intelligent, calm and spatial—not because it is covered in neon or visual effects.

### 2.2 Brand personality

| Attribute | Visual expression |
| --- | --- |
| Trustworthy | Strong contrast, stable grids, clear labels, honest data states |
| Premium | Generous space, cinematic media, controlled bronze detail, refined typography |
| Modern | Variable type, bento composition, contextual controls, crisp motion |
| Friendly | Human language, soft geometry, clear guidance, approachable imagery |
| UAE-rooted | Warm earth palette, architectural light, locally credible photography |
| Intelligent | Predictive search, structured data, map context, subtle digital accent |
| Minimal | Fewer stronger elements; no decorative clutter |
| Corporate | Consistent hierarchy, disciplined components, reliable states |

### 2.3 Futuristic, not gimmicky

Use:

- Architectural asymmetry balanced by a strict grid.
- Layered depth with subtle light and material.
- Large editorial headlines with clean interface typography.
- Context-aware search and progressive disclosure.
- Refined micro-interactions.
- Responsive bento layouts.
- Data-rich cards that remain calm.
- Limited translucent surfaces over media or dark backgrounds.
- One controlled digital accent for AI, live and map interactions.

Avoid:

- Neon cyberpunk palettes.
- Constant glow around every component.
- Excessive glassmorphism.
- Floating elements without hierarchy.
- Scroll hijacking.
- Large 3D scenes that delay interaction.
- Generic real-estate gold-on-black styling everywhere.
- Stock imagery with exaggerated handshakes or smiles.
- Decorative animation that competes with property content.

### 2.4 Visual composition ratio

A typical public page should approximately use:

- 60–70% quiet ivory/white or deep neutral space.
- 20–30% high-quality property/architectural imagery.
- 8–12% brown, bronze and sand brand material.
- 1–3% Digital Aqua for intelligent/live interaction only.

Digital Aqua is a system accent, not a replacement brand color and not a logo color.

---

## 3. Design principles

### 3.1 Property first

The interface frames the property, project, location and customer decision. Decoration must never hide imagery, facts, price policy or the main CTA.

### 3.2 Calm confidence

Premium design uses hierarchy and space, not constant visual noise. Each viewport should have one obvious primary action.

### 3.3 Evidence over hype

Unverified or stale dynamic facts are not made visually authoritative. Unknown pricing uses an enquiry CTA; unavailable inventory receives an honest state.

### 3.4 Mobile is the primary constraint

Every component is designed for thumb reach, short attention, limited bandwidth and variable text length before it is expanded for desktop.

### 3.5 Motion explains

Motion should reveal relationship, state and continuity. It must not delay reading, search or enquiry.

### 3.6 English and Arabic are equal

Arabic is not a translated afterthought. Both locales receive equivalent hierarchy, content capacity, control size and interaction quality.

### 3.7 Accessibility is visible quality

Strong focus, readable contrast, keyboard access, scalable text and reduced motion are part of the premium experience.

### 3.8 One system, two densities

The public website uses spacious editorial composition. The Admin Platform uses denser operational layouts. Both share tokens, interaction states and brand details.

---

## 4. Color system

### 4.1 Core UI palette

| Token name | Hex | Role |
| --- | --- | --- |
| Carbon 950 | #0E0B0A | Premium dark background, footer and cinematic hero |
| Ink 900 | #17110E | Primary light-theme text |
| Espresso 850 | #2B1C16 | Dark elevated surface and deep brand layer |
| Heritage Brown 700 | #5A3827 | Primary brand/action color |
| Architectural Bronze 600 | #7A5135 | Secondary brand detail and accessible bronze text |
| Copper 500 | #A56F48 | Decorative edge, chart accent and hover detail |
| Desert Sand 400 | #C9A77C | Secondary brand surface and selected highlight |
| Champagne 300 | #D9B487 | Dark-mode highlight and warm premium detail |
| Warm Stone 100 | #EEE8E1 | Muted surface, separators and filter background |
| Ivory 50 | #F8F6F2 | Primary warm page background |
| White 0 | #FFFFFF | Cards, forms and high-clarity surface |
| Muted Umber 600 | #625850 | Secondary readable text on light surfaces |
| Digital Aqua 400 | #4CCFC0 | AI, live, map and intelligent system accent only |

### 4.2 Why this palette works

- Brown and tan preserve the established ARE identity.
- Carbon and Ivory create stronger contemporary contrast than generic black and pure beige.
- Bronze and Champagne provide luxury without imitating jewelry branding.
- Digital Aqua creates a controlled 2030 signal for intelligent features.
- Warm neutrals keep property photography natural.

### 4.3 Semantic colors

| Semantic role | Strong | Soft surface | Use |
| --- | --- | --- | --- |
| Success | #1F6B4F | #E7F4EE | Completed, verified, published, healthy |
| Warning | #8A4B12 | #FFF3E3 | Review, stale, expiring, partial |
| Error | #A52A22 | #FDEDEC | Failed, blocked, destructive, invalid |
| Information | #2B5EA8 | #EAF2FF | Neutral information and guidance |
| AI/Live | #147F76 | #DDF8F4 | AI, live availability signal, active map |

Semantic color must never be the only status indicator. Pair it with text and, where useful, an icon.

### 4.4 Accessible color pairs

The following calculated combinations exceed the 4.5:1 normal-text target:

| Foreground | Background | Approximate contrast |
| --- | --- | --- |
| Ink #17110E | Ivory #F8F6F2 | 17.33:1 |
| Muted Umber #625850 | Ivory #F8F6F2 | 6.42:1 |
| Heritage Brown #5A3827 | White #FFFFFF | 10.35:1 |
| White #FFFFFF | Heritage Brown #5A3827 | 10.35:1 |
| Ivory #F8F6F2 | Carbon #0E0B0A | 18.17:1 |
| Warm light text #C8BDB3 | Carbon #0E0B0A | 10.63:1 |
| Digital Aqua #4CCFC0 | Carbon #0E0B0A | 10.27:1 |
| Ink #17110E | Desert Sand #C9A77C | 8.28:1 |
| Architectural Bronze #7A5135 | White #FFFFFF | 6.87:1 |

Contrast must still be tested in the implemented component, including opacity, imagery, hover, disabled and focus states.

### 4.5 Light-theme semantic assignment

| UI role | Color |
| --- | --- |
| Page background | Ivory 50 |
| Primary surface | White 0 |
| Secondary surface | Warm Stone 100 |
| Primary text | Ink 900 |
| Secondary text | Muted Umber 600 |
| Primary action | Heritage Brown 700 |
| Primary action hover | Espresso 850 |
| Selected surface | Desert Sand at 18–24% tint |
| Border | Ink at 12% opacity |
| Strong border | Heritage Brown at 32% opacity |
| Focus ring | Heritage Brown 700 plus White offset |

### 4.6 Dark-theme semantic assignment

| UI role | Color |
| --- | --- |
| Page background | Carbon 950 |
| Primary surface | Espresso 850 |
| Elevated surface | #35231B |
| Primary text | Ivory 50 |
| Secondary text | #C8BDB3 |
| Primary action | Champagne 300 with Ink text |
| Primary action hover | Desert Sand 400 |
| Border | White at 14% opacity |
| Focus ring | Champagne 300 plus Carbon offset |
| AI/live accent | Digital Aqua 400 |

Dark mode is intended for hero sections, immersive property/project sections, the footer and optional user preference. It must not force every public page into a dark visual treatment.

### 4.7 Approved gradients

Use gradients as atmosphere, never as a substitute for readable layout.

| Gradient | Definition | Use |
| --- | --- | --- |
| Heritage Night | linear-gradient(135deg, #0E0B0A 0%, #2B1C16 54%, #5A3827 100%) | Hero and premium CTA backdrop |
| Desert Light | linear-gradient(135deg, #F8F6F2 0%, #EEE8E1 58%, #E3D1B9 100%) | Quiet section background |
| Bronze Edge | linear-gradient(90deg, #7A5135 0%, #D9B487 52%, #A56F48 100%) | 1–2px decorative edge only |
| Intelligence Line | linear-gradient(90deg, #4CCFC0 0%, #D9B487 100%) | AI/live micro-accent only |

Do not place paragraph text directly over a gradient without a tested solid/controlled backing layer.

### 4.8 Color prohibitions

- Do not use Desert Sand or Champagne as normal text on white.
- Do not use Digital Aqua for general branding or every CTA.
- Do not use pure black #000000 for large page surfaces when Carbon provides depth.
- Do not use low-opacity text below accessible contrast.
- Do not use more than one decorative gradient within the same viewport.
- Do not encode property status by color alone.

---

## 5. Typography

### 5.1 Font families

| Script/use | Family | Purpose |
| --- | --- | --- |
| Latin primary | Roboto Flex | Display, headings, body and UI; modern evolution of the approved Roboto family |
| Latin fallback | Roboto, Arial, system-ui, sans-serif | Stable fallback |
| Arabic primary | IBM Plex Sans Arabic | Modern, professional Arabic UI and content |
| Arabic fallback | Tahoma, Arial, sans-serif | System fallback |

Roboto Flex should use optical sizing. Arabic uses its own metrics, line height and weight calibration rather than copying Latin values mechanically.

### 5.2 Font-loading policy

- Self-host approved WOFF2 files where permitted.
- Load only required weights/axes and character subsets.
- Preload only the critical regular and medium files.
- Use font-display: swap or an approved metric-compatible strategy.
- Avoid separate decorative fonts on critical routes.
- Use tabular numerals for prices, areas, reference codes and admin metrics.

### 5.3 Type scale

| Token | Fluid size | Line height | Weight | Typical use |
| --- | --- | --- | --- | --- |
| Display 1 | clamp(3.5rem, 7vw, 7rem) | 0.94–1.00 | 520–600 | Home/project hero |
| Display 2 | clamp(2.75rem, 5vw, 5.5rem) | 0.98–1.04 | 520–600 | Page hero |
| Heading 1 | clamp(2.25rem, 4vw, 4rem) | 1.02–1.10 | 560–650 | Main page title |
| Heading 2 | clamp(1.875rem, 3vw, 3rem) | 1.08–1.15 | 560–650 | Major section |
| Heading 3 | clamp(1.5rem, 2vw, 2rem) | 1.15–1.22 | 600 | Card group/section |
| Heading 4 | 1.25rem | 1.30 | 600 | Card and form heading |
| Body Large | 1.125rem | 1.65 | 400 | Intro and premium editorial copy |
| Body | 1rem | 1.60 | 400 | Standard content |
| Body Small | 0.875rem | 1.50 | 400–500 | Metadata and support |
| Label | 0.8125rem | 1.25 | 600 | Form/control label |
| Overline | 0.75rem | 1.20 | 650 | Category/eyebrow; uppercase Latin only |

### 5.4 Typography behavior

- Display text uses tight Latin tracking between -0.02em and -0.045em.
- Body text uses normal tracking.
- Arabic must not use artificial letter spacing.
- Arabic headings generally require 8–14% more line height than comparable Latin headings.
- Keep body measure near 60–72 Latin characters; Arabic measure should be visually reviewed.
- Avoid fully justified paragraphs.
- Never place important website copy as text baked into an image.
- Use sentence case for UI labels and buttons.
- Avoid all-caps paragraphs; overlines may use uppercase in English only.

### 5.5 Price and data typography

- AED remains visually connected to its value.
- Use tabular numerals for price, area, dates and dashboard metrics.
- Prices are not rendered as current unless the data policy permits it.
- For “Ask for Price”, the CTA receives primary hierarchy; no fake numerical placeholder is shown.
- Reference codes use 0.8125–0.875rem, medium weight and increased tracking.

---

## 6. Spacing and layout

### 6.1 Base unit

The spacing system uses a 4px base. Components consume named tokens rather than arbitrary values.

| Token | Value | Typical use |
| --- | --- | --- |
| space-0 | 0 | Reset |
| space-1 | 4px | Tight icon gap |
| space-2 | 8px | Compact inline gap |
| space-3 | 12px | Small control/content gap |
| space-4 | 16px | Default internal spacing |
| space-5 | 20px | Card compact padding |
| space-6 | 24px | Standard card/form padding |
| space-8 | 32px | Large card padding |
| space-10 | 40px | Component group |
| space-12 | 48px | Mobile section gap |
| space-16 | 64px | Tablet/compact section gap |
| space-20 | 80px | Desktop section gap |
| space-24 | 96px | Large editorial section |
| space-32 | 128px | Hero/landmark separation |

### 6.2 Responsive grid

| Viewport | Columns | Outer margin | Gutter | Content behavior |
| --- | --- | --- | --- | --- |
| 320–479px | 4 | 16px | 12px | Single-column primary flow |
| 480–767px | 4 | 20–24px | 16px | Larger cards; selective two-column content |
| 768–1023px | 8 | 32px | 20px | Tablet split layouts |
| 1024–1439px | 12 | 48–64px | 24px | Full editorial/search layouts |
| 1440px+ | 12 | auto | 24–32px | Max content width; preserve negative space |

Recommended container:

- Standard max width: 1440px.
- Reading max width: 760px.
- Form max width: 680px.
- Dense admin content: fluid with a practical max based on table requirements.
- Full-bleed media may escape the container while text remains aligned.

### 6.3 Section rhythm

- Public desktop: 96–128px vertical section padding.
- Public tablet: 72–96px.
- Public mobile: 48–72px.
- Admin page: 24–40px vertical spacing.
- Keep section headings visually attached to their content.
- Do not alternate background colors mechanically; change surface only when it clarifies a new chapter.

### 6.4 Bento layouts

Bento grids are permitted for featured projects, locations, investment insights and dashboard summaries when:

- The hierarchy remains obvious.
- Reading order is correct in the DOM.
- Cards collapse predictably on mobile.
- No key information is hidden only on hover.
- Image ratios do not cause layout shift.

---

## 7. Shape, borders, depth and material

### 7.1 Radius system

| Token | Value | Use |
| --- | --- | --- |
| radius-xs | 8px | Badge, small control |
| radius-sm | 12px | Input, button, compact card |
| radius-md | 18px | Standard card and panel |
| radius-lg | 24px | Property/project card and modal |
| radius-xl | 32px | Hero search, major feature panel |
| radius-2xl | 40px | Landmark bento/immersive surface |
| radius-pill | 999px | Chips and compact filters |

Use fewer radius sizes on one screen. Cards should not look like unrelated bubbles.

### 7.2 Borders

- Standard light border: 1px solid rgba(23, 17, 14, 0.12).
- Strong light border: 1px solid rgba(90, 56, 39, 0.32).
- Standard dark border: 1px solid rgba(255, 255, 255, 0.14).
- Selected cards may use a 1px Bronze Edge plus a subtle inner highlight.
- Never rely on a faint shadow alone to define an input boundary.

### 7.3 Elevation

| Level | Shadow | Use |
| --- | --- | --- |
| 0 | none | Page surface |
| 1 | 0 8px 24px rgba(23,17,14,0.06) | Standard card |
| 2 | 0 16px 44px rgba(23,17,14,0.10) | Hover/elevated card |
| 3 | 0 28px 80px rgba(14,11,10,0.18) | Drawer/modal |
| Dark glow | 0 24px 80px rgba(201,167,124,0.12) | Selected immersive panel only |

### 7.4 Glass surfaces

Glass is limited to:

- Header over a hero image.
- Expanded hero search.
- AI assistant panel.
- Map controls.
- Selected dark-theme overlays.

Rules:

- Minimum readable backing opacity.
- Backdrop blur typically 16–24px.
- Visible border.
- Solid fallback when blur is unsupported.
- No stacked glass-on-glass panels.
- No long article or form on translucent glass.

### 7.5 Texture

Optional subtle grain or architectural grid may appear at 1–2% opacity on landmark dark surfaces. It must be CSS/SVG-efficient, non-interactive and removed under reduced-data/performance constraints.

---

## 8. Motion system

### 8.1 Motion character

Motion is precise, composed and slightly cinematic. Components settle into place; they do not bounce.

| Token | Duration | Use |
| --- | --- | --- |
| instant | 80–120ms | Press feedback |
| fast | 160–180ms | Hover, icon, small state |
| standard | 240–280ms | Dropdown, chip, card state |
| enter | 360–440ms | Drawer, modal, content reveal |
| landmark | 600–800ms | Hero/media transition only |

### 8.2 Easing

| Token | Value | Use |
| --- | --- | --- |
| ease-standard | cubic-bezier(0.2, 0, 0, 1) | General UI |
| ease-enter | cubic-bezier(0.16, 1, 0.3, 1) | Enter/reveal |
| ease-exit | cubic-bezier(0.4, 0, 1, 1) | Exit |
| ease-emphasized | cubic-bezier(0.2, 0.8, 0.2, 1) | Hero/landmark |

### 8.3 Approved motion patterns

- Buttons: 1–2px visual lift or fill transition, never layout movement.
- Cards: image scale up to 1.03 and elevation change on capable hover devices.
- Navigation: underline/indicator glides to the selected item.
- Search: expands with preserved input focus and no content jump.
- Drawers: enter from the logical inline end, mirrored in RTL.
- Page reveal: opacity plus 12–20px translation for landmark sections only.
- Gallery: crossfade/slide with explicit controls and swipe support.
- AI/live indicator: slow low-amplitude pulse; no constant flashing.

### 8.4 Motion prohibitions

- No scroll hijacking.
- No mandatory animation before content becomes usable.
- No large parallax on mobile.
- No looping hero text movement.
- No auto-rotating carousel without pause/control.
- No animation of width/height when transform/opacity can convey the state.
- No more than one landmark animation competing in a viewport.

### 8.5 Reduced motion

When prefers-reduced-motion is active:

- Remove parallax, smooth-scroll effects, pulsing and large transforms.
- Use near-instant opacity changes.
- Preserve every state and action.
- Do not hide content pending animation.

---

## 9. Iconography and visual symbols

### 9.1 Icon style

- Clean outlined icons with rounded optical joins.
- Default grid: 24px.
- Compact grid: 20px.
- Default stroke: 1.75px.
- Emphasized/large stroke: 2px.
- Match visual weight rather than mathematically forcing every path.
- Use one icon family or one internally normalized set.

### 9.2 Icon rules

- Icons supplement labels; they do not replace unfamiliar actions.
- Directional icons mirror in RTL.
- Universal/non-directional symbols do not mirror.
- Active navigation uses color plus indicator, not a filled icon alone.
- Property facts use consistent bed, bath, area and location icons.
- Avoid mixed filled/outlined styles in the same control group.
- Do not use emoji as product-interface icons.

### 9.3 Brand motif

The signature motif is an abstract architectural frame:

- Two fine lines forming a corner, threshold or skyline edge.
- Bronze Edge gradient or low-opacity sand.
- Used in hero composition, section labels and selected cards.
- Never repeated as wallpaper across the entire page.

The motif should feel like a premium architectural drawing, not an ornamental pattern.

---

## 10. Photography, video and media direction

### 10.1 Art direction

Photography should feel:

- Architectural and editorial.
- Warm-neutral, not over-saturated.
- Real and geographically credible.
- Premium but inhabited.
- Composed with usable negative space.
- Rich in natural light, glass, stone, shadow and water.

Preferred subjects:

- Real UAE properties and approved developer imagery.
- Dubai, Ajman and other approved UAE locations represented accurately.
- Architectural details and spatial perspectives.
- Calm, authentic advisor/client interactions.
- Lifestyle context that supports the property rather than becoming stock advertising.

### 10.2 Avoid

- Fake skylines or geographically inaccurate composites.
- CGI-looking “real” properties unless clearly identified as an approved render.
- Overdone HDR, neon skies or orange/teal grading.
- Posed handshake photography.
- Exaggerated smiles and generic corporate groups.
- Text, prices or badges baked into source imagery.
- Third-party imagery without documented rights.

### 10.3 Image ratios

| Context | Preferred ratio |
| --- | --- |
| Property card | 4:3 |
| Project card | 16:10 or 3:2 |
| Hero | 16:9 or responsive art-directed crop |
| Location bento | 4:5, 1:1 and 16:10 controlled variants |
| Agent portrait | 4:5 |
| Editorial feature | 3:2 |
| Gallery thumbnail | 4:3 |
| Floor/master plan | Source ratio within a neutral viewer |

### 10.4 Media overlays

- Light hero text uses a controlled Carbon overlay/gradient behind text.
- Image badges need an opaque-enough surface and readable contrast.
- Do not apply a global dark filter to all property cards.
- Preserve material and interior color accuracy.
- Hover image treatment must not hide key features.

### 10.5 Video

- No autoplay with sound.
- Hero video requires poster image and performance approval.
- Pause when out of view.
- Provide captions/transcript when speech carries meaning.
- Avoid background video on low-data/mobile conditions.
- Video controls must remain keyboard and screen-reader accessible.

---

## 11. Accessibility and inclusive interaction

### 11.1 Accessibility target

All components target WCAG 2.2 AA and must pass automated and manual review.

### 11.2 Interaction requirements

- Minimum project control target: 44×44px for primary touch interactions.
- Visible keyboard focus on every interactive element.
- Focus order follows the visual/reading order.
- Focus is moved intentionally after modal, drawer and route-state changes.
- Escape closes dismissible overlays.
- Dialogs trap focus and return it to the trigger.
- Forms use persistent labels, instructions and accessible errors.
- Error summaries link to invalid fields on long forms.
- Hover-only information is prohibited.
- Color is never the only carrier of meaning.

### 11.3 Focus treatment

Light surface:

- 2px Heritage Brown ring.
- 2px White offset when required.
- Minimum visible shape equal to or larger than the control boundary.

Dark surface:

- 2px Champagne ring.
- 2px Carbon offset.

Focus must remain visible on cards, chips, map pins, gallery controls and custom selects.

### 11.4 Text and zoom

- Page content must remain usable at 200% text zoom.
- Use rem/em for typography and component sizing where practical.
- Avoid clipping text with fixed heights.
- Buttons and tabs allow label wrapping or responsive alternatives.
- Body copy remains at least 16px in standard reading contexts.

### 11.5 Screen readers

- Property/project cards expose one clear linked title rather than multiple duplicate links.
- Icon-only buttons have accessible names.
- Dynamic result counts and form results use appropriate live regions.
- Skeletons are hidden from assistive technology; loading state is announced once.
- Price, area and units have understandable spoken labels.
- Map information has an equivalent list/table path.

---

## 12. Responsive and RTL behavior

### 12.1 Responsive philosophy

Responsive behavior is not desktop shrinking. At smaller widths:

- Navigation becomes a purposeful drawer.
- Search becomes a focused sheet/route.
- Filters become a bottom sheet or full-screen panel.
- Side-by-side map/list becomes a clear mode switch.
- Sticky CTAs respect safe areas.
- Dense tables become horizontal-scroll tables or task-specific cards without losing data.
- Secondary media and decoration yield to core facts and action.

### 12.2 Public breakpoints

| Pattern | Mobile | Tablet | Desktop |
| --- | --- | --- | --- |
| Header | 64px; logo, language, menu | 72px; compact actions | 80–88px; full navigation |
| Property grid | 1 column | 2 columns | 3 columns; 4 only on wide dense views |
| Project grid | 1 column | 2 columns | 2–3 editorial columns |
| Hero search | Stacked/full-width | 2-row adaptive | Horizontal intelligent search |
| Detail gallery | Swipe gallery | 2-up | Editorial mosaic |
| Detail CTA | Sticky bottom action | Sticky side/bottom by space | Right-side enquiry panel |
| Filters | Bottom/full sheet | Side drawer | Left rail or toolbar |
| Map/list | Toggle modes | Split optional | Resizable split view |

### 12.3 Arabic RTL rules

- Set dir="rtl" at the document/locale boundary.
- Use CSS logical properties: margin-inline, padding-inline, inset-inline and border-inline.
- Mirror navigation direction, drawers, breadcrumbs, arrows and step progression.
- Do not mirror logos, property images, maps, floor plans, play icons or non-directional symbols.
- Keep phone numbers, email, URLs, reference codes and coordinates in controlled LTR spans.
- Preserve AED/value order according to approved Arabic content rules.
- Arabic filters, selects, tables, galleries, forms and dialogs receive independent visual QA.
- Avoid forced uppercase and letter spacing in Arabic.
- Increase Arabic control/content height when glyph metrics need it.

### 12.4 Mixed-script content

- Use unicode-bidi/isolation where mixed Arabic, English and numbers could reorder.
- Property/project names retain approved official spelling.
- Do not transliterate automatically in the UI.
- Truncation must not hide distinguishing parts of Arabic names.

---

## 13. Component architecture

### 13.1 Layers

| Layer | Contents |
| --- | --- |
| Foundations | Color, typography, spacing, grid, elevation, motion and icon rules |
| Primitives | Box, Stack, Grid, Text, Icon, Image, VisuallyHidden and Divider |
| Controls | Button, Link, Input, Select, Checkbox, Radio, Switch, Slider and Chip |
| Feedback | Alert, Toast, Progress, Skeleton, Empty State, Status Badge and Tooltip |
| Navigation | Header, Mega Menu, Breadcrumbs, Tabs, Pagination, Sidebar and Command Search |
| Data display | Card, Definition List, Table, Stat, Timeline, Gallery, Map Pin and Chart frame |
| Domain components | Property Card, Project Card, Lead Row, Agent Card, Price/CTA and AI Handoff |
| Patterns | Search, filters, enquiry, publish workflow, import review and translation review |
| Templates | Home, listing, detail, location, article, careers and admin pages |

### 13.2 Component contract

Every component must define:

- Purpose and allowed contexts.
- Anatomy and slots.
- Variants and sizes.
- Default, hover, pressed, focus, disabled, loading and error states.
- Responsive behavior.
- LTR and RTL behavior.
- Keyboard/screen-reader contract.
- Analytics event boundary where applicable.
- Data-state behavior.
- Performance constraints.

### 13.3 Naming

Use semantic names:

- Button / primary / md.
- PropertyCard / featured.
- StatusBadge / verified.
- Surface / elevated.

Avoid visual-only names such as BrownButton or BigCard.

---

## 14. Core controls

### 14.1 Buttons

| Variant | Visual | Use |
| --- | --- | --- |
| Primary | Heritage Brown fill, White text | Main conversion/action |
| Primary Dark | Champagne fill, Ink text | Main action on dark surface |
| Secondary | Transparent/White surface, Heritage Brown border/text | Secondary action |
| Tertiary | Text/icon with subtle hover surface | Low-emphasis action |
| Ghost Dark | Transparent, Ivory text, visible hover/focus | Dark media overlays |
| Destructive | Error fill or outline | Delete/reject irreversible action |
| AI/Live | Carbon fill with restrained Aqua indicator | AI/live feature action only |

Rules:

- Minimum height: 48px public, 40–44px dense admin.
- Primary mobile actions generally fill available width.
- One primary action per component group.
- Loading keeps width stable and disables duplicate submission.
- Icons are 18–20px and positioned on the logical start/end.
- “Enquire Now”, “Request Current Price” and “Speak to an ARE Advisor” use primary hierarchy when relevant.

### 14.2 Links

- Inline links use underline or another persistent non-color signal.
- Navigation links may use an active bar/shape.
- External links communicate their behavior where necessary.
- Card links use a single semantic title link plus separate buttons only for distinct actions.

### 14.3 Inputs

Public input:

- Height 52–56px.
- Radius 12–16px.
- Persistent label above the field.
- Clear border and focus.
- Support/error text below.

Admin input:

- Height 40–44px.
- Radius 10–12px.
- Supports compact form density without reducing readability.

Never use placeholder text as the only label.

### 14.4 Select, combobox and autocomplete

- Native select where it meets the need.
- Combobox for long locations, communities, developers or projects.
- Keyboard navigation and typed search.
- Visible selected value and clear action.
- Async state includes loading, no results and failure/retry.
- Results show hierarchy, for example Community · Dubai.

### 14.5 Chips and filters

- Height 36–40px.
- Selected state uses Sand tint, strong Brown border and check indicator where useful.
- Removable chips have a separately named remove action.
- Mobile filter count is visible on the trigger.
- “Clear all” is available when more than one filter is active.

### 14.6 Tabs

- Tabs are for peer views, not sequential steps.
- Active tab uses a high-contrast indicator and text weight.
- Overflow uses horizontal scrolling with visible affordance, not tiny labels.
- Tabs preserve route/query state when the content is linkable.
- Admin tabs may become a select or segmented control on small screens.

---

## 15. Public navigation and global components

### 15.1 Header

Desktop anatomy:

1. ARE logo.
2. Buy, Rent, Off-Plan, Locations, Investment, Content and Company navigation.
3. Search trigger.
4. Language switcher.
5. Primary contact/enquiry action.

Behavior:

- Over an immersive hero, use a readable translucent/dark treatment.
- After scroll, transition to a solid high-clarity surface.
- Preserve layout height to avoid page shift.
- Mega menus use meaningful group headings and featured content sparingly.
- Keyboard navigation and escape behavior are mandatory.
- Empty or unapproved navigation categories remain hidden.

Mobile anatomy:

- Logo.
- Language control.
- Search icon.
- Menu trigger.
- Full-height logical-side drawer with primary CTA.

### 15.2 Language switcher

- Label choices as EN and العربية or approved full labels.
- Preserve the equivalent page when a translation exists.
- Explain/fallback gracefully when the counterpart is unavailable.
- Explicit choice persists.
- Do not use flag icons to represent language.

### 15.3 Footer

The footer uses Carbon with Ivory text and controlled Bronze detail.

It may contain:

- Company summary.
- Buy, Rent, Off-Plan and location links.
- Content and company links.
- Offices/contact routes.
- Language switcher.
- Legal/privacy links.
- Social links.
- Newsletter only if approved.

The footer must not become an unstructured link dump.

### 15.4 Breadcrumbs

- Visible on deep entity/content pages.
- Use structured-data-compatible hierarchy.
- Collapse intermediate items on mobile while preserving the current page context.
- Mirror separators and order correctly in RTL.

---

## 16. Search and discovery components

### 16.1 Hero search

The search experience is the primary interactive signature of ARE.

Desktop:

- Large radius-32 surface.
- Buy / Rent / Off-Plan mode.
- Location/community autocomplete.
- Property/project type.
- Bedrooms or relevant criteria.
- Search action.
- Advanced filters progressively disclosed.

Mobile:

- One clear “Search properties and projects” entry control.
- Opens an accessible full-screen or bottom-sheet search flow.
- Retains entered filters when dismissed/reopened.

Futuristic detail:

- Contextual suggestions based on approved data.
- Soft Aqua indicator only when intelligent/AI-assisted search is actually active.
- No fake AI label on ordinary keyword search.

### 16.2 Results toolbar

- Result count.
- Query summary.
- Active-filter chips.
- Sort.
- List/map toggle.
- Save search only when the feature is approved.

### 16.3 Filter panel

Group filters by:

- Intent/listing type.
- Location/community.
- Property type.
- Bedrooms/bathrooms.
- Area.
- Amenities.
- Price only under approved pricing policy.

Show applied count, clear group and clear all. Avoid instant network requests on every tiny mobile change; use an Apply action where it improves control.

### 16.4 Map/list

- Desktop may use a resizable list/map split.
- Mobile uses explicit List and Map modes.
- Selected card and pin remain synchronized.
- Map pins have clear selected/focus states and accessible list equivalents.
- Clustering must communicate count and zoom behavior.

---

## 17. Domain cards

### 17.1 Property card

Anatomy:

1. 4:3 media.
2. Listing/status badges.
3. Save action only if approved.
4. Title.
5. Community and location.
6. Beds, baths and area.
7. Price state or enquiry text.
8. Optional agent/verification context.

Variants:

- Standard.
- Featured.
- Compact list.
- Map-linked.
- Unavailable/archived preview in admin only.

Rules:

- Image does not exceed roughly 55–60% of standard card height.
- Title supports two lines before controlled truncation.
- Critical facts remain visible without hover.
- Unavailable state is explicit; do not make it look available through normal CTA styling.
- Entire card may be clickable, but nested actions must remain valid and accessible.

### 17.2 Project card

Anatomy:

- 16:10 or 3:2 approved image/render.
- Project lifecycle badge.
- Project name.
- Developer.
- Location/community.
- Property types or bedroom range.
- Verified handover information when eligible.
- “View Project” or enquiry action.

Featured project cards may use dark editorial overlays, but text must have a controlled backing gradient.

### 17.3 Developer card

- Approved logo on a neutral brand-safe plate.
- Name.
- Short approved descriptor.
- Project count only when accurate.
- Location/community relationship.
- No partnership claim unless authorized.

### 17.4 Location/community card

- Strong real photography.
- Location name.
- Short factual descriptor.
- Available property/project count only when current.
- Optional map/guide entry.
- Use bento sizes for hierarchy, not random decoration.

### 17.5 Agent card

- Approved 4:5 portrait.
- Name, languages, areas and specialization.
- Contact route.
- Availability/active status only when governed.
- No direct personal contact detail if the lead-routing policy requires centralized contact.

### 17.6 Article/insight card

- Featured image.
- Content type.
- Localized title.
- Excerpt when space permits.
- Author/date according to editorial policy.
- Related location/project signal.

---

## 18. Property and project detail patterns

### 18.1 Detail hero

Recommended desktop structure:

- Breadcrumb and concise status/eyebrow.
- Title and location.
- Primary approved facts.
- Editorial gallery/mosaic.
- Sticky or adjacent enquiry panel.

Mobile:

- Title and location before large media.
- Swipe gallery with count.
- Core facts.
- Sticky bottom CTA with safe-area padding.

### 18.2 Gallery

- First image is the strongest approved cover.
- Keyboard, swipe and thumbnail navigation.
- Visible image count.
- Full-screen viewer with close, next/previous and captions.
- Floor plans and video are typed media, not mixed anonymously.
- Image dimensions are reserved to prevent layout shift.

### 18.3 Fact rail

Use clear labeled facts for:

- Property type.
- Bedrooms and bathrooms.
- Area.
- Location/community.
- Project/developer.
- Approved completion/handover.

Do not turn every fact into a large icon tile.

### 18.4 Price and enquiry panel

Possible states:

| Data state | Visual treatment |
| --- | --- |
| Verified current price permitted | Clear value, basis, currency and relevant freshness label |
| Range permitted | “From” or range with exact approved basis |
| Price unavailable/unverified | “Ask for Price” as primary content |
| Availability uncertain | “Request Latest Availability” |
| Unavailable | Status explanation and related alternatives |

The panel may include name/phone/email form or open a focused enquiry flow. Avoid displaying a long form beside every detail section.

### 18.5 Long-form detail navigation

Desktop may use a sticky section navigator for:

- Overview.
- Amenities.
- Floor plans.
- Location.
- Payment plan when approved.
- Developer.
- FAQs.

The active state must track correctly without covering content. On mobile use a compact scrollable tab row or section menu.

---

## 19. Feedback and system states

### 19.1 Loading

- Use layout-matched skeletons.
- Reserve media dimensions.
- Avoid full-page spinners for normal page loads.
- Announce loading once to assistive technology.
- Admin long jobs show progress, counts and background continuation.

### 19.2 Empty

An empty state contains:

- Plain explanation.
- Context-specific next action.
- Optional quiet illustration/icon.
- No blame-oriented language.

Examples:

- No properties match these filters → Clear or adjust filters.
- No translations pending → Return to content.
- No import conflicts → Continue review.

### 19.3 Error

- Explain what failed in plain language.
- Preserve user input.
- Provide safe retry or recovery.
- Show correlation/reference only when useful for support.
- Do not expose stack traces.

### 19.4 Stale or unverified

Admin:

- Visible Warning badge.
- Last verified/source metadata.
- Review action.

Public:

- Do not imply current certainty.
- Use approved enquiry CTA or suppress the dynamic field.

### 19.5 Disabled

Disabled controls remain readable and explain why when the reason is not obvious. Do not use disabled styling to hide a permission problem; unauthorized actions should be omitted or explained according to product policy.

### 19.6 Toasts and alerts

- Toasts confirm lightweight completed actions.
- Inline alerts explain persistent page/form conditions.
- Destructive or blocking events must not be toast-only.
- Toast duration allows reading and supports pause/dismiss.

---

## 20. AI assistant interface

### 20.1 Visual role

The AI assistant should feel like an ARE service, not a separate chatbot product.

- Carbon/Espresso base.
- Small Digital Aqua live indicator.
- Bronze/Champagne brand edge.
- Roboto Flex and IBM Plex Sans Arabic.
- Clear “AI Assistant” identity and human handoff path.

### 20.2 Entry points

- Global floating trigger after non-obstructive delay or direct user action.
- Contextual “Ask about this property/project”.
- Search no-results assistance.
- Investment/content assistance only within approved knowledge.

The floating control must not cover mobile sticky CTAs, cookie controls or accessibility tools.

### 20.3 Conversation anatomy

- Context header: current property/project when relevant.
- Message stream.
- Suggested questions.
- Composer.
- Privacy/AI notice according to policy.
- “Speak to an ARE Advisor” handoff.
- Retrieval/knowledge freshness disclosure where required.

### 20.4 Trust states

- Grounded answer.
- Clarification needed.
- Current information requires an advisor.
- Handoff in progress.
- Agent connected/lead created.
- Service unavailable with normal enquiry fallback.

Never use visual certainty to make an unverified answer appear authoritative.

---

## 21. Administration design system

### 21.1 Admin visual direction

Admin uses the same brand DNA with higher information density:

- Ivory/White working canvas.
- Ink text.
- Brown active navigation/action.
- Sand selected/filtered surfaces.
- Semantic colors for workflow.
- Digital Aqua only for AI, live processing and system health.
- Minimal decorative imagery.

### 21.2 Shell

Desktop:

- Sidebar: approximately 264–280px expanded; 72–80px collapsed.
- Top bar: 64–72px.
- Main canvas: fluid.
- Page header remains separate from tabs/content where that improves hierarchy.

Tablet/mobile:

- Sidebar becomes a logical-side drawer.
- Page actions collapse into an overflow menu or sticky action bar.
- Tables retain essential fields and provide detail drawers.

### 21.3 Sidebar

- Group modules by operational domain.
- Active item uses Brown text/fill and a clear indicator.
- Icons remain secondary to labels.
- Collapsed state has tooltips and accessible names.
- Badge counts are reserved for actionable queues, not decoration.

### 21.4 Page header

Anatomy:

- Breadcrumb/section.
- Page title.
- Short context or record status.
- Primary action.
- Secondary actions/overflow.
- Optional tabs below with visual separation from the content panel.

Header, tabs and content must not look like one unstructured card.

### 21.5 Data tables

- Sticky header where useful.
- Row height: 52–60px standard; optional compact density 44–48px.
- Checkbox selection.
- Sort indicators.
- Column visibility/persistence where approved.
- Clear empty/loading/error states.
- Status and verification as separate columns/badges.
- Row actions in a consistent logical-end area.
- Horizontal scrolling is explicit; frozen identity column where necessary.

### 21.6 Dashboard cards

Metric cards contain:

- Label.
- Value.
- Time range.
- Trend/comparison only when defined.
- Compact real chart when useful.
- Link to supporting records.

Avoid oversized numbers that duplicate the same count or decorative charts without scale/context.

### 21.7 Admin forms

- Group fields into named sections.
- One column for complex fields; two columns only for naturally related short fields.
- Sticky save/review bar for long records.
- Show save, validation and conflict state.
- Unsaved-change protection.
- Server errors stay associated with the affected section.
- Source, verification, rights and publication controls are visually distinct.

### 21.8 Status badges

Badge anatomy:

- Text.
- Optional compact icon.
- Semantic border/fill.

Never use one status for multiple axes. Display, for example:

- Verification: Verified.
- Publication: Published.
- Availability: Unknown.

### 21.9 Review and comparison

Import, translation and content review should use:

- Side-by-side or inline diff.
- Previous and proposed values.
- Source/evidence panel.
- Accept/reject per field where allowed.
- Sticky decision summary.
- Keyboard-accessible navigation between changes.

### 21.10 Bulk actions

- Appear only after selection.
- Show selected count.
- Preview impact.
- Require confirmation for high-risk changes.
- Long operations become monitored background jobs.
- Completion links to results/errors.

---

## 22. Page template system

### 22.1 Homepage

Recommended order:

1. Immersive hero with clear promise and intelligent search.
2. Buy / Rent / Off-Plan entry.
3. Featured projects.
4. Curated properties.
5. Popular communities in a controlled bento grid.
6. Developer ecosystem.
7. Investment/market insight.
8. Why ARE/trust proof.
9. Latest approved content.
10. AI/advisor CTA.
11. Careers/contact as appropriate.
12. Footer.

Use alternating editorial rhythm, not a stack of identical card grids.

### 22.2 Listing

1. Compact page hero/title.
2. Search/query summary.
3. Filter toolbar/rail.
4. Results and map mode.
5. Pagination.
6. Relevant SEO content below results without obstructing discovery.
7. Related locations/guides.

### 22.3 Property detail

1. Breadcrumb.
2. Title/location and status.
3. Gallery.
4. Fact rail.
5. Price/enquiry.
6. Overview.
7. Amenities.
8. Floor plan/media.
9. Map and nearby landmarks.
10. Agent/advisor.
11. Related properties/projects/content.
12. FAQ where eligible.

### 22.4 Project detail

1. Cinematic approved hero.
2. Name, developer, location and lifecycle.
3. Main CTA/current information request.
4. Overview.
5. Property types and size ranges.
6. Amenities.
7. Master/floor plans.
8. Payment/handover only when verified and authorized.
9. Gallery/video.
10. Location.
11. Developer.
12. FAQs and related projects.

### 22.5 Location/community

1. Geographic/editorial hero.
2. Concise overview.
3. Properties and projects.
4. Market information when approved.
5. Map/landmarks.
6. Developers.
7. Area guides/insights.
8. Nearby areas.
9. FAQ.

### 22.6 Developer

1. Approved brand-safe profile.
2. Factual overview.
3. Projects.
4. Communities.
5. Related insights.
6. Enquiry.

No unapproved partnership language.

### 22.7 Content article

- Reading width near 720–760px.
- Strong headline and provenance/author/date.
- Editorial media.
- Sticky or inline table of contents for long guides.
- Related properties/projects/locations.
- Clear updated date.
- Accessible share controls.
- No excessive inline conversion interruptions.

### 22.8 Careers and contact

Careers:

- Human brand story.
- Searchable open jobs.
- Clear job detail.
- Secure, focused application form.

Contact:

- Intent-first route selection.
- Offices/contact options.
- Short contextual form.
- Confirmation and response expectation only when approved.

---

## 23. Content design and interface language

### 23.1 Voice

ARE interface language is:

- Clear.
- Confident.
- Factual.
- Helpful.
- Respectful.
- Calm.
- Human.

Avoid:

- “Best ever”, “guaranteed return” or unsupported superlatives.
- Artificial urgency.
- Vague buttons such as “Click Here”.
- Technical system language in customer-facing errors.
- Long promotional paragraphs inside operational interfaces.

### 23.2 CTA hierarchy

Primary conversion language may include:

- Enquire Now.
- Ask for Price.
- Request Current Price.
- Request Latest Availability.
- Speak to an ARE Advisor.
- Schedule a Viewing only when the workflow exists.

Secondary discovery language:

- View Property.
- Explore Project.
- View Community.
- Read Guide.
- Compare only when the feature exists.

### 23.3 Labels

- Use nouns for destinations: Properties, Projects, Leads.
- Use verbs for actions: Publish, Assign, Review.
- Keep button text specific and short.
- Use consistent terms across public, admin, email and AI.
- Maintain an English/Arabic terminology glossary.

### 23.4 Error language

Pattern:

1. State what happened.
2. Explain what the user can do.
3. Preserve their work.
4. Provide reference/help only when useful.

Example:

“We could not send your enquiry. Your details are still here—please try again.”

### 23.5 Dynamic data language

- “Last updated” is shown only when it helps the decision.
- “Verified” must have a defined business meaning.
- “Available” must not be inferred from publication.
- Approximate, from and range labels must be explicit.
- Legal/investment claims require approved copy.

---

## 24. Data visualization

### 24.1 Principle

Charts are used only when they communicate a trend, comparison or composition more clearly than a number or table.

### 24.2 Chart palette

Preferred ordered sequence:

1. Heritage Brown #5A3827.
2. Digital Aqua #4CCFC0.
3. Architectural Bronze #7A5135.
4. Information Blue #2B5EA8.
5. Desert Sand #C9A77C.
6. Success Green #1F6B4F.

Charts must:

- Use labels or patterns in addition to color.
- Meet non-text contrast at boundaries or use contrasting separators.
- Include axis/unit/time range.
- Provide an accessible table or summary.
- Avoid 3D chart effects.
- Avoid truncated axes that mislead.

### 24.3 Admin metrics

- Use line charts for time trends.
- Bars for categorical comparison.
- Stacked bars only when composition is necessary and legible.
- Donuts only for a small number of categories.
- Avoid sparklines without a label and time context.

---

## 25. Design token implementation

### 25.1 Token hierarchy

1. Primitive tokens: raw color, spacing, type and radius.
2. Semantic tokens: background, text, action, border and status.
3. Component tokens: button, card, input, navigation and table.
4. Theme/locale overrides: dark and Arabic/RTL.

Components must consume semantic/component tokens rather than raw hex values.

### 25.2 CSS variable baseline

```css
:root {
  color-scheme: light;

  /* Primitive color */
  --are-carbon-950: #0e0b0a;
  --are-ink-900: #17110e;
  --are-espresso-850: #2b1c16;
  --are-brown-700: #5a3827;
  --are-bronze-600: #7a5135;
  --are-copper-500: #a56f48;
  --are-sand-400: #c9a77c;
  --are-champagne-300: #d9b487;
  --are-stone-100: #eee8e1;
  --are-ivory-50: #f8f6f2;
  --are-white: #ffffff;
  --are-muted-600: #625850;
  --are-aqua-400: #4ccfc0;

  /* Semantic color */
  --are-bg-page: var(--are-ivory-50);
  --are-bg-surface: var(--are-white);
  --are-bg-subtle: var(--are-stone-100);
  --are-text-primary: var(--are-ink-900);
  --are-text-secondary: var(--are-muted-600);
  --are-text-inverse: var(--are-ivory-50);
  --are-action-primary: var(--are-brown-700);
  --are-action-primary-hover: var(--are-espresso-850);
  --are-action-on-primary: var(--are-white);
  --are-border-default: rgba(23, 17, 14, 0.12);
  --are-border-strong: rgba(90, 56, 39, 0.32);
  --are-focus: var(--are-brown-700);
  --are-intelligence: var(--are-aqua-400);

  /* Semantic status */
  --are-success: #1f6b4f;
  --are-success-soft: #e7f4ee;
  --are-warning: #8a4b12;
  --are-warning-soft: #fff3e3;
  --are-error: #a52a22;
  --are-error-soft: #fdedec;
  --are-info: #2b5ea8;
  --are-info-soft: #eaf2ff;

  /* Typography */
  --are-font-latin: "Roboto Flex", "Roboto", Arial, system-ui, sans-serif;
  --are-font-arabic: "IBM Plex Sans Arabic", Tahoma, Arial, sans-serif;
  --are-font-body: var(--are-font-latin);
  --are-text-display-1: clamp(3.5rem, 7vw, 7rem);
  --are-text-display-2: clamp(2.75rem, 5vw, 5.5rem);
  --are-text-h1: clamp(2.25rem, 4vw, 4rem);
  --are-text-h2: clamp(1.875rem, 3vw, 3rem);
  --are-text-h3: clamp(1.5rem, 2vw, 2rem);
  --are-text-h4: 1.25rem;
  --are-text-body-lg: 1.125rem;
  --are-text-body: 1rem;
  --are-text-body-sm: 0.875rem;
  --are-text-label: 0.8125rem;

  /* Spacing */
  --are-space-1: 0.25rem;
  --are-space-2: 0.5rem;
  --are-space-3: 0.75rem;
  --are-space-4: 1rem;
  --are-space-5: 1.25rem;
  --are-space-6: 1.5rem;
  --are-space-8: 2rem;
  --are-space-10: 2.5rem;
  --are-space-12: 3rem;
  --are-space-16: 4rem;
  --are-space-20: 5rem;
  --are-space-24: 6rem;
  --are-space-32: 8rem;

  /* Shape */
  --are-radius-xs: 0.5rem;
  --are-radius-sm: 0.75rem;
  --are-radius-md: 1.125rem;
  --are-radius-lg: 1.5rem;
  --are-radius-xl: 2rem;
  --are-radius-2xl: 2.5rem;
  --are-radius-pill: 999px;

  /* Elevation */
  --are-shadow-1: 0 8px 24px rgba(23, 17, 14, 0.06);
  --are-shadow-2: 0 16px 44px rgba(23, 17, 14, 0.1);
  --are-shadow-3: 0 28px 80px rgba(14, 11, 10, 0.18);

  /* Motion */
  --are-duration-instant: 100ms;
  --are-duration-fast: 180ms;
  --are-duration-standard: 260ms;
  --are-duration-enter: 420ms;
  --are-duration-landmark: 700ms;
  --are-ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --are-ease-enter: cubic-bezier(0.16, 1, 0.3, 1);
  --are-ease-exit: cubic-bezier(0.4, 0, 1, 1);
  --are-ease-emphasized: cubic-bezier(0.2, 0.8, 0.2, 1);

  /* Layout */
  --are-container: 90rem;
  --are-reading-width: 47.5rem;
  --are-form-width: 42.5rem;
  --are-control-public: 3.25rem;
  --are-control-admin: 2.75rem;

  /* Layering */
  --are-z-base: 0;
  --are-z-sticky: 100;
  --are-z-dropdown: 200;
  --are-z-overlay: 300;
  --are-z-modal: 400;
  --are-z-toast: 500;
}

[data-theme="dark"] {
  color-scheme: dark;
  --are-bg-page: var(--are-carbon-950);
  --are-bg-surface: var(--are-espresso-850);
  --are-bg-subtle: #35231b;
  --are-text-primary: var(--are-ivory-50);
  --are-text-secondary: #c8bdb3;
  --are-action-primary: var(--are-champagne-300);
  --are-action-primary-hover: var(--are-sand-400);
  --are-action-on-primary: var(--are-ink-900);
  --are-border-default: rgba(255, 255, 255, 0.14);
  --are-border-strong: rgba(217, 180, 135, 0.4);
  --are-focus: var(--are-champagne-300);
}

html {
  background: var(--are-bg-page);
  color: var(--are-text-primary);
  font-family: var(--are-font-body);
  font-optical-sizing: auto;
  text-rendering: optimizeLegibility;
}

html[lang="ar"] {
  --are-font-body: var(--are-font-arabic);
  letter-spacing: normal;
}

:focus-visible {
  outline: 2px solid var(--are-focus);
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 1ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 1ms !important;
  }
}
```

### 25.3 Logical-direction implementation

```css
.component {
  padding-inline: var(--are-space-6);
  margin-block: var(--are-space-8);
  border-inline-start: 2px solid var(--are-border-strong);
}

.directional-icon {
  transform: none;
}

[dir="rtl"] .directional-icon {
  transform: scaleX(-1);
}

.bidi-safe-value {
  direction: ltr;
  unicode-bidi: isolate;
}
```

Only directional icons receive the RTL transform class.

### 25.4 Token rules

- No hardcoded hex in application components unless the value represents external content that cannot be tokenized.
- No arbitrary spacing outside the scale without a documented exception.
- No component-specific z-index above the defined layer without review.
- Theme overrides change semantic tokens, not every component declaration.
- Tokens are versioned and reviewed like code.

---

## 26. Performance rules for visual design

### 26.1 Font budget

- Prefer two active families: Roboto Flex and IBM Plex Sans Arabic.
- Subset by script/locale.
- Avoid loading unused display weights.
- Verify fallback metrics to reduce layout shift.

### 26.2 Image budget

- Use responsive sizes and modern formats.
- The server selects an appropriate source; CSS-only shrinking is insufficient.
- Reserve width/height or aspect-ratio.
- Do not preload every carousel/gallery image.
- Below-the-fold content lazy-loads.
- Hero assets require art direction for mobile and desktop.

### 26.3 Effects budget

- Blur, large shadow and backdrop-filter are limited to landmark surfaces.
- Avoid animated blur and large fixed background effects.
- Use CSS/SVG for small patterns instead of heavy bitmap overlays.
- Disable nonessential visual effects for reduced motion/data or under performance pressure.

### 26.4 JavaScript behavior

- Core page content and navigation remain usable without large animation libraries.
- Use client-side code only where interaction requires it.
- Carousels, maps, AI and advanced filters load progressively.
- Do not ship an entire component library when only a small subset is used.

---

## 27. Design documentation and governance

### 27.1 Source of truth

Recommended hierarchy:

1. Approved master logo/brand assets.
2. ARE DESIGN SYSTEM v1.0.
3. Versioned design tokens.
4. Reusable code components.
5. Page templates/patterns.
6. Individual route composition.

Route-level code must not redefine the brand system.

### 27.2 Design library organization

If maintained in Figma or an equivalent design tool:

- 00 Cover and governance.
- 01 Foundations.
- 02 Tokens/variables.
- 03 Icons and assets.
- 04 Core controls.
- 05 Public components.
- 06 Admin components.
- 07 Patterns.
- 08 Templates.
- 09 English/Arabic examples.
- 10 Deprecated.

### 27.3 Code organization

Recommended conceptual structure:

```text
design-system/
  foundations/
  tokens/
  primitives/
  controls/
  feedback/
  navigation/
  data-display/
  domain/
  patterns/
  templates/
  documentation/
```

Adapt this structure to the verified repository; do not restructure a working codebase blindly.

### 27.4 Component documentation

Each reusable component should document:

- Purpose.
- Usage and non-usage.
- Props/API.
- Variants.
- Examples.
- Accessibility.
- RTL.
- Responsive behavior.
- Data/loading/error states.
- Analytics events.
- Version/change notes.

Use Storybook or an equivalent component explorer only if it fits the repository and does not create unjustified maintenance overhead.

### 27.5 Versioning

- Patch: visual bug or documentation correction without intended API change.
- Minor: additive token, variant or component.
- Major: breaking token, component API or foundational visual change.
- Deprecated tokens/components remain documented until migration is complete.

### 27.6 Change approval

Owner/design approval is required for:

- Primary palette or typography change.
- Logo treatment.
- Global radius/elevation direction.
- Header/navigation redesign.
- Core property/project card anatomy.
- Public CTA hierarchy.
- Arabic/RTL deviation.
- New decorative visual language.

---

## 28. Implementation sequence

### DS-0 — Brand asset audit

- Obtain approved logo SVG/lockups.
- Extract exact logo colors.
- Confirm clear space and minimum sizes.
- Confirm approved verbal positioning/tagline.
- Inventory existing UI/design code.

Exit: no guessed logo or conflicting brand token.

### DS-1 — Foundations

- Implement primitive and semantic tokens.
- Load/subset fonts.
- Establish container, grid and spacing.
- Establish light/dark landmark surfaces.
- Implement focus and reduced motion.

Exit: token playground passes contrast, scaling and RTL checks.

### DS-2 — Core primitives and controls

- Text, Icon, Image, Stack, Grid and Surface.
- Buttons, links, inputs, select/combobox, chips, tabs.
- Alerts, badges, toast, skeleton and empty state.

Exit: documented states, keyboard behavior and responsive tests.

### DS-3 — Public discovery

- Header, mega menu, language switcher and footer.
- Hero search, filter panel, toolbar and pagination.
- Property, project, location, developer, agent and article cards.
- Map/list mode.

Exit: English/Arabic search-to-result journey works on mobile and desktop.

### DS-4 — Detail and conversion

- Detail gallery.
- Fact rail.
- Price/enquiry panel.
- Sticky mobile CTA.
- Long-form navigation.
- Forms and confirmation.
- AI contextual entry.

Exit: property/project enquiry journey meets accessibility and performance criteria.

### DS-5 — Admin system

- Shell, sidebar, header and tabs.
- Tables, filters, forms and drawers.
- Status badges and dashboards.
- Review/diff and bulk-action patterns.
- Job/progress and audit displays.

Exit: representative create-review-publish and lead-assignment workflows are visually complete.

### DS-6 — Templates and hardening

- Homepage and all core public templates.
- Admin page templates.
- Arabic parity.
- Accessibility.
- Performance.
- Visual regression.
- Cross-browser/device review.

Exit: design system release checklist passes.

---

## 29. Quality assurance matrix

| Area | Required verification |
| --- | --- |
| Brand | Brown/tan continuity, logo not recolored from guessed values |
| Typography | Roboto continuity, Arabic pairing, fallback and layout-shift review |
| Color | Normal/large text contrast, non-text contrast and status clarity |
| Components | All defined states and variants |
| Mobile | 320px through modern wide phones; touch and safe-area behavior |
| Tablet | Search, filters, gallery, tables and admin navigation |
| Desktop | 1024px through wide screens; container/negative-space integrity |
| RTL | Direction, typography, mixed data, drawers, tables, map and gallery |
| Keyboard | Full navigation, menus, dialogs, filters and forms |
| Screen reader | Names, roles, state announcements and error association |
| Zoom | 200% text/page zoom without loss of content/function |
| Motion | Reduced motion and no essential animation dependency |
| Performance | Fonts, hero media, image variants, client JS and effects |
| Data states | Loading, empty, partial, stale, unavailable, error and success |
| Content | Long English/Arabic labels and realistic data |
| Visual regression | Core components and templates in light/dark and LTR/RTL |

---

## 30. Design review checklist

Before approving a page:

- Is the main user goal obvious within seconds?
- Is there only one dominant primary action?
- Does the page still work with long Arabic text?
- Is every dynamic fact presented honestly?
- Are all controls keyboard reachable and focus-visible?
- Does the mobile layout preserve facts and CTA priority?
- Are image rights and crop behavior approved?
- Is typography using the defined scale?
- Are colors and spacing token-based?
- Are loading, empty and error states designed?
- Does motion explain rather than decorate?
- Does the page remain premium without its animations?
- Is public performance protected?
- Does the component already exist before creating a new variant?

---

## 31. Key do/don't summary

| Do | Don't |
| --- | --- |
| Use warm architectural neutrals and cinematic imagery | Cover every surface in brown/gold |
| Use Digital Aqua only for intelligent/live context | Turn Aqua into a competing logo color |
| Use large typography with disciplined space | Use oversized text on every section |
| Use restrained glass over media/dark backgrounds | Put forms and articles on transparent glass |
| Use one strong CTA | Show several equal high-emphasis buttons |
| Show honest price/availability states | Imply certainty with visual styling |
| Design Arabic as a full RTL system | Flip the page and assume it is complete |
| Use real responsive art direction | Crop one desktop hero for every screen |
| Use motion for continuity | Animate every card on scroll |
| Keep admin dense and clear | Make admin look like a marketing landing page |
| Reuse documented components | Create route-specific one-off UI |

---

## 32. Open design decisions

| Decision | Recommended baseline | Status |
| --- | --- | --- |
| Exact logo colors | Extract from approved master SVG | Required before production |
| Logo light/dark lockups | Approved full-color plus one-color variants | Required before header/footer lock |
| Latin typography | Roboto Flex with Roboto fallback | Recommended |
| Arabic typography | IBM Plex Sans Arabic | Recommended; Arabic review required |
| Core UI palette | Brown/tan/black/white evolved palette in Section 4 | Recommended |
| Digital accent | Aqua limited to AI/live/map at 1–3% | Recommended |
| Public default | Light editorial pages with selected dark landmark sections | Recommended |
| Admin default | Light high-clarity workspace | Recommended |
| Icon family | One outlined family normalized to this system | Select during DS-2 |
| Default motion | Calm standard profile with reduced-motion parity | Recommended |
| Approved tagline/market positioning | Resolve source conflict through content approval | Pending content authority |

---

## 33. Definition of Done for a design-system component

A component is complete only when:

- It uses approved tokens.
- Its purpose and anatomy are documented.
- All required variants/states exist.
- Mobile, tablet and desktop behavior is defined.
- English and Arabic/RTL behavior is verified.
- Keyboard and screen-reader behavior is verified.
- Focus is visible.
- Contrast passes in actual states.
- Long labels and real data are tested.
- Loading, error, empty and disabled behavior exists where relevant.
- Reduced-motion behavior is correct.
- It does not introduce avoidable layout shift or excessive client code.
- Visual regression coverage exists where useful.
- The component is used consistently by its first real consumer.

---

## 34. Design-system release acceptance

Version 1.0 is ready for implementation approval when:

- The master logo and exact brand colors have been verified.
- Owner accepts the Future Heritage 2030 direction.
- Palette and typography are approved.
- Token names and CSS baseline are accepted.
- Header, search, property card and project card are approved as reference components.
- One English and one Arabic page template prove parity.
- Public and Admin density differences are accepted.
- Accessibility and performance constraints are accepted.
- Implementation is split into bounded tasks rather than one whole-site redesign.

---

## 35. Final visual principle

The ARE experience should look futuristic because it understands the customer, organizes complex real-estate information and moves with precision.

It should not look futuristic because it imitates science fiction.

The final balance is:

> Warm UAE heritage + architectural luxury + intelligent digital clarity.

---

## References

- [Roboto Flex — Google Fonts](https://fonts.google.com/specimen/Roboto%2BFlex)
- [IBM Plex Sans Arabic — Google Fonts](https://fonts.google.com/specimen/IBM%2BPlex%2BSans%2BArabic)
- [WCAG 2.2: Contrast Minimum — W3C WAI](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)
- [WCAG 2.2 Quick Reference — W3C WAI](https://www.w3.org/WAI/WCAG22/quickref/)

---

## Appendix A — Reference component inventory

### Foundations

- Color primitives and semantic tokens.
- Typography styles.
- Spacing/grid.
- Radius/border/shadow.
- Motion/easing.
- Icon rules.
- Breakpoints.
- Z-index layers.

### Shared primitives and controls

- Box, Stack, Grid, Surface and Divider.
- Text and Icon.
- Responsive Image.
- Button and Icon Button.
- Link.
- Input, Textarea and Search Input.
- Select, Combobox and Autocomplete.
- Checkbox, Radio and Switch.
- Chip and Filter Chip.
- Slider when required.
- Tabs and Segmented Control.
- Tooltip.

### Feedback

- Alert.
- Toast.
- Inline Error.
- Progress.
- Skeleton.
- Empty State.
- Status Badge.
- Confirmation Dialog.

### Public navigation

- Header.
- Mega Menu.
- Mobile Navigation Drawer.
- Language Switcher.
- Breadcrumb.
- Pagination.
- Footer.

### Public domain

- Hero Search.
- Results Toolbar.
- Filter Panel.
- Property Card.
- Project Card.
- Developer Card.
- Location Card.
- Agent Card.
- Article Card.
- Gallery.
- Fact Rail.
- Price/Enquiry Panel.
- Map Pin and Map/List Split.
- Related Content Rail.
- AI Assistant.

### Admin

- Admin Shell.
- Sidebar.
- Top Bar.
- Page Header.
- Record Tabs.
- Command/Global Search.
- Data Table.
- Filter Bar.
- Metric Card.
- Chart Frame.
- Form Section.
- Sticky Save Bar.
- Detail Drawer.
- Review Diff.
- Bulk Action Bar.
- Job Progress.
- Audit Timeline.
- Permission/Unavailable State.

---

## Appendix B — Visual acceptance reference screens

The first design review should include:

1. Homepage desktop — English.
2. Homepage mobile — Arabic.
3. Property listing desktop with filters/map.
4. Property listing mobile with filter sheet.
5. Property detail desktop.
6. Project detail mobile — Arabic.
7. Location/community page.
8. Content article.
9. AI assistant grounded-answer and handoff states.
10. Admin dashboard.
11. Admin property table.
12. Admin property create/edit.
13. Admin import comparison.
14. Admin lead detail/assignment.
15. All loading, empty, stale, unavailable and error states.
