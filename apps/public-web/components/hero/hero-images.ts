// Reuse the owner-approved editorial image pack, never catalogue/private media.
// Focal positions are art direction, not mirrored source images.
export const heroImages = {
  buy: { file: "journey-buy.webp", en: "Contemporary residence exterior representing the buying journey", ar: "واجهة مسكن عصري تمثل مسار الشراء", desktop: "58% 52%", mobile: "60% 50%", rtl: "44% 52%", rtlMobile: "48% 50%" },
  rent: { file: "journey-rent.webp", en: "Contemporary residence interior representing the renting journey", ar: "تصميم داخلي لمسكن عصري يمثل مسار الإيجار", desktop: "60% 50%", mobile: "68% 50%", rtl: "36% 50%", rtlMobile: "48% 50%" },
  "off-plan": { file: "journey-offplan.webp", en: "Architectural scale model representing the off-plan journey", ar: "مجسم معماري يمثل مسار المشاريع على المخطط", desktop: "56% 60%", mobile: "54% 58%", rtl: "44% 60%", rtlMobile: "44% 58%" },
  developers: { file: "architecture-detail.webp", en: "Contemporary architectural facade in evening light", ar: "واجهة معمارية عصرية في ضوء المساء", desktop: "58% 50%", mobile: "48% 50%", rtl: "38% 50%", rtlMobile: "38% 50%" },
  communities: { file: "uae-community.webp", en: "Landscaped residential community with waterways", ar: "مجتمع سكني بمساحات خضراء وممرات مائية", desktop: "58% 52%", mobile: "60% 52%", rtl: "42% 52%", rtlMobile: "45% 52%" },
  insights: { file: "insight-community.webp", en: "Quiet landscaped walkway between contemporary residences", ar: "ممشى هادئ تحيط به المساحات الخضراء والمساكن العصرية", desktop: "60% 50%", mobile: "60% 50%", rtl: "40% 50%", rtlMobile: "45% 50%" },
  careers: { file: "aliyas-approach.webp", en: "Architectural workspace with plans and material samples", ar: "مساحة عمل معمارية تضم مخططات وعينات مواد", desktop: "58% 65%", mobile: "54% 64%", rtl: "38% 65%", rtlMobile: "40% 64%" },
  contact: { file: "enquiry-cta.webp", en: "Contemporary residence beside still water at dusk", ar: "مسكن عصري بجوار مياه هادئة عند الغروب", desktop: "62% 50%", mobile: "59% 50%", rtl: "42% 50%", rtlMobile: "50% 50%" },
} as const;

export type HeroImageKey = keyof typeof heroImages;
