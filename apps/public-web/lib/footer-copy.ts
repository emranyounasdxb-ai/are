import type { Locale } from "./home-copy";

type FooterStackCopy = Readonly<{
  newsletter: Readonly<{
    eyebrow: string;
    heading: string;
    text: string;
    emailLabel: string;
    placeholder: string;
    comingSoon: string;
    note: string;
    exploreInsights: string;
  }>;
  app: Readonly<{
    eyebrow: string;
    heading: string;
    text: string;
    comingSoon: string;
    plannedLabel: string;
    plannedItems: ReadonlyArray<string>;
    deviceLabel: string;
  }>;
  footer: Readonly<{
    brandStatement: string;
    whatsapp: string;
    rights: string;
  }>;
}>;

export const footerStackCopy: Readonly<Record<Locale, FooterStackCopy>> = {
  en: {
    newsletter: {
      eyebrow: "ALIYAS / NEWSLETTER",
      heading: "A considered view of UAE property.",
      text: "Occasional bilingual guidance, newly published insights and future verified property releases.",
      emailLabel: "Email address",
      placeholder: "Newsletter launching soon",
      comingSoon: "Coming soon",
      note: "No email address is currently collected.",
      exploreInsights: "Explore Insights",
    },
    app: {
      eyebrow: "FORTHCOMING MOBILE EXPERIENCE",
      heading: "ALIYAS, wherever property takes you.",
      text: "The ALIYAS Real Estate mobile experience is planned for iOS and Android.",
      comingSoon: "Coming soon",
      plannedLabel: "Planned for the mobile experience",
      plannedItems: ["Property discovery", "Saved preferences", "Direct enquiries"],
      deviceLabel: "Forthcoming ALIYAS mobile experience",
    },
    footer: {
      brandStatement: "A clear bilingual route to considered UAE property discovery.",
      whatsapp: "WhatsApp +971 56 915 7576",
      rights: "All rights reserved",
    },
  },
  ar: {
    newsletter: {
      eyebrow: "علياس العقارية / النشرة البريدية",
      heading: "رؤية مدروسة لعقارات الإمارات.",
      text: "إرشادات ثنائية اللغة من حين إلى آخر، ورؤى منشورة حديثاً، وإصدارات عقارية مستقبلية بعد التحقق منها.",
      emailLabel: "البريد الإلكتروني",
      placeholder: "النشرة البريدية تنطلق قريباً",
      comingSoon: "قريباً",
      note: "لا يتم جمع أي بريد إلكتروني حالياً.",
      exploreInsights: "استكشف الرؤى",
    },
    app: {
      eyebrow: "تجربة هاتف قادمة",
      heading: "علياس العقارية معك أينما قادتك رحلتك العقارية.",
      text: "نعمل على تجربة علياس العقارية للهواتف بنظامي آي أو إس وأندرويد.",
      comingSoon: "قريباً",
      plannedLabel: "مخطط للتجربة على الهاتف",
      plannedItems: ["اكتشاف العقارات", "حفظ التفضيلات", "الاستفسارات المباشرة"],
      deviceLabel: "تجربة علياس العقارية القادمة على الهاتف",
    },
    footer: {
      brandStatement: "مسار ثنائي اللغة وواضح لاكتشاف عقارات الإمارات بصورة مدروسة.",
      whatsapp: "واتساب +971 56 915 7576",
      rights: "جميع الحقوق محفوظة",
    },
  },
};
