import type { Locale } from "./home-copy";

export const pageSlugs = ["properties", "communities", "off-plan", "about", "contact"] as const;

export type PageSlug = (typeof pageSlugs)[number];

type PageCopy = Readonly<{
  description: string;
  eyebrow: string;
  metaDescription: string;
  metaTitle: string;
  title: string;
}>;

type SiteCopy = Readonly<{
  common: Readonly<{
    contactAction: string;
    footerDescription: string;
    footerLabel: string;
    footerNavigation: string;
    language: string;
  }>;
  pages: Readonly<Record<PageSlug, PageCopy>>;
  properties: Readonly<{
    criteriaHeading: string;
    criteriaIntro: string;
    criteriaNone: string;
    inventoryNote: string;
  }>;
  communities: Readonly<{
    categories: ReadonlyArray<Readonly<{ label: string; text: string }>>;
    discoveryAction: string;
    enquiryAction: string;
    sectionTitle: string;
  }>;
  offPlan: Readonly<{
    enquiryAction: string;
    searchAction: string;
    steps: ReadonlyArray<Readonly<{ label: string; text: string }>>;
    sectionTitle: string;
  }>;
  about: Readonly<{
    action: string;
    principles: ReadonlyArray<Readonly<{ label: string; text: string }>>;
    sectionTitle: string;
  }>;
  contact: Readonly<{
    emailLabel: string;
    emailPlaceholder: string;
    enquiryTypeLabel: string;
    enquiryTypes: ReadonlyArray<Readonly<{ label: string; value: string }>>;
    intro: string;
    messageLabel: string;
    messagePlaceholder: string;
    nameLabel: string;
    namePlaceholder: string;
    previewNote: string;
    submit: string;
    success: string;
    validation: string;
  }>;
}>;

export function isPageSlug(value: string): value is PageSlug {
  return pageSlugs.includes(value as PageSlug);
}

export const siteCopy: Readonly<Record<Locale, SiteCopy>> = {
  en: {
    common: {
      contactAction: "Enquire",
      footerDescription:
        "A bilingual property-discovery experience designed to become data-driven when approved inventory is connected.",
      footerLabel: "UAE property discovery",
      footerNavigation: "Footer navigation",
      language: "Language",
    },
    pages: {
      properties: {
        description:
          "Shape a clear property brief by location, home type and purpose before approved live inventory is connected.",
        eyebrow: "Property discovery",
        metaDescription:
          "Define a UAE property search brief with ALIYAS Real Estate. Live inventory will appear only after approved data is connected.",
        metaTitle: "Properties | ALIYAS Real Estate",
        title: "Begin with a property brief built around you.",
      },
      communities: {
        description:
          "Explore the character of a place through lifestyle, connection and everyday priorities—without reducing a community to unverified numbers.",
        eyebrow: "Community discovery",
        metaDescription:
          "Explore safe community-discovery pathways across the UAE with ALIYAS Real Estate.",
        metaTitle: "Communities | ALIYAS Real Estate",
        title: "Understand the place before choosing the property.",
      },
      "off-plan": {
        description:
          "Approach an off-plan search through clear questions, documented information and considered next steps.",
        eyebrow: "Off-plan discovery",
        metaDescription:
          "Understand a safe, general off-plan property-discovery journey with ALIYAS Real Estate.",
        metaTitle: "Off-Plan | ALIYAS Real Estate",
        title: "Move from early interest to informed discovery.",
      },
      about: {
        description:
          "ALIYAS Real Estate is shaping a clearer bilingual route from first intent to a more considered property conversation.",
        eyebrow: "Our intended approach",
        metaDescription:
          "Learn about the intended customer approach behind the ALIYAS Real Estate bilingual discovery experience.",
        metaTitle: "About | ALIYAS Real Estate",
        title: "Real estate discovery should begin with clarity.",
      },
      contact: {
        description:
          "Share the outline of what you are looking for. Your enquiry is sent securely for authorized follow-up.",
        eyebrow: "Start a conversation",
        metaDescription:
          "Send a secure property enquiry to ALIYAS Real Estate in English or Arabic.",
        metaTitle: "Contact | ALIYAS Real Estate",
        title: "Tell us what would make your next step useful.",
      },
    },
    properties: {
      criteriaHeading: "Your current criteria",
      criteriaIntro: "This summary reflects only the selections in the URL.",
      criteriaNone: "No complete search criteria have been selected yet.",
      inventoryNote:
        "Live inventory, availability, prices and result counts will appear only when approved property data is connected.",
    },
    communities: {
      categories: [
        { label: "Daily rhythm", text: "Consider how a place supports work, family life and everyday routines." },
        { label: "Connection", text: "Explore the routes and destinations that matter to your own plans." },
        { label: "Living character", text: "Compare the atmosphere and housing patterns that fit your preferences." },
      ],
      discoveryAction: "Build a property brief",
      enquiryAction: "Ask about your priorities",
      sectionTitle: "Three lenses for exploring a community",
    },
    offPlan: {
      enquiryAction: "Discuss your questions",
      searchAction: "Explore property discovery",
      steps: [
        { label: "Clarify intent", text: "Define your use, timing and priorities before comparing opportunities." },
        { label: "Review evidence", text: "Request approved project, developer and contractual information before deciding." },
        { label: "Consider the full commitment", text: "Understand applicable milestones, responsibilities and independent advice needs." },
      ],
      sectionTitle: "A considered off-plan pathway",
    },
    about: {
      action: "Begin an enquiry",
      principles: [
        { label: "Listen first", text: "Start with the customer’s purpose, preferences and unanswered questions." },
        { label: "Present honestly", text: "Separate verified information from anything unavailable, pending or illustrative." },
        { label: "Keep the next step clear", text: "Make each discovery path understandable in English and Arabic." },
      ],
      sectionTitle: "The experience we intend to build",
    },
    contact: {
      emailLabel: "Email",
      emailPlaceholder: "name@example.com",
      enquiryTypeLabel: "Enquiry type",
      enquiryTypes: [
        { label: "Buying a property", value: "buy" },
        { label: "Renting a property", value: "rent" },
        { label: "Choosing a community", value: "communities" },
        { label: "Exploring off-plan", value: "off-plan" },
        { label: "General property question", value: "general" },
      ],
      intro: "Share only the information needed for authorized ALIYAS Admin users to review and respond to your enquiry.",
      messageLabel: "What are you looking for?",
      messagePlaceholder: "Share your purpose, preferred location or the question you want to explore.",
      nameLabel: "Name",
      namePlaceholder: "Your name",
      previewNote: "Your details are stored securely for enquiry handling. Optional marketing consent is separate.",
      submit: "Send enquiry",
      success: "Your enquiry has been received securely.",
      validation: "Please complete your name, a valid email and a short message before continuing.",
    },
  },
  ar: {
    common: {
      contactAction: "استفسر",
      footerDescription:
        "تجربة ثنائية اللغة لاكتشاف العقارات، صُممت لتصبح معتمدة على البيانات عند ربط مخزون عقاري معتمد.",
      footerLabel: "اكتشاف العقارات في الإمارات",
      footerNavigation: "تنقل التذييل",
      language: "اللغة",
    },
    pages: {
      properties: {
        description:
          "حدّد موجزاً واضحاً لبحثك وفق الموقع ونوع العقار والغرض، قبل ربط المخزون المباشر المعتمد.",
        eyebrow: "اكتشاف العقارات",
        metaDescription:
          "حدّد موجز بحثك عن عقار في الإمارات مع ALIYAS Real Estate. سيظهر المخزون المباشر فقط بعد ربط بيانات معتمدة.",
        metaTitle: "العقارات | ALIYAS Real Estate",
        title: "ابدأ بموجز عقاري مصمم حول احتياجاتك.",
      },
      communities: {
        description:
          "استكشف طابع المكان من خلال أسلوب الحياة وسهولة الوصول والأولويات اليومية، من دون اختزال المجتمع في أرقام غير موثقة.",
        eyebrow: "اكتشاف المجتمعات",
        metaDescription: "استكشف مسارات آمنة للتعرّف إلى مجتمعات الإمارات مع ALIYAS Real Estate.",
        metaTitle: "المجتمعات | ALIYAS Real Estate",
        title: "افهم المكان قبل اختيار العقار.",
      },
      "off-plan": {
        description:
          "ابدأ البحث عن عقار على المخطط عبر أسئلة واضحة ومعلومات موثقة وخطوات مدروسة.",
        eyebrow: "اكتشاف العقارات على المخطط",
        metaDescription: "تعرّف إلى مسار عام ومدروس لاكتشاف العقارات على المخطط مع ALIYAS Real Estate.",
        metaTitle: "على المخطط | ALIYAS Real Estate",
        title: "انتقل من الاهتمام الأولي إلى استكشاف واعٍ.",
      },
      about: {
        description:
          "تعمل ALIYAS Real Estate على صياغة مسار ثنائي اللغة أكثر وضوحاً، من النية الأولى إلى حوار عقاري مدروس.",
        eyebrow: "نهجنا المقصود",
        metaDescription: "تعرّف إلى نهج تجربة الاكتشاف الثنائية اللغة لدى ALIYAS Real Estate.",
        metaTitle: "من نحن | ALIYAS Real Estate",
        title: "يجب أن يبدأ اكتشاف العقارات بالوضوح.",
      },
      contact: {
        description:
          "شارك الخطوط العامة لما تبحث عنه. يُرسل استفسارك بأمان للمتابعة من المستخدمين المخولين.",
        eyebrow: "ابدأ حواراً",
        metaDescription: "أرسل استفساراً عقارياً آمناً إلى ALIYAS Real Estate بالإنجليزية أو العربية.",
        metaTitle: "تواصل معنا | ALIYAS Real Estate",
        title: "أخبرنا بما يجعل خطوتك التالية أكثر فائدة.",
      },
    },
    properties: {
      criteriaHeading: "معاييرك الحالية",
      criteriaIntro: "يعكس هذا الملخص الاختيارات الموجودة في الرابط فقط.",
      criteriaNone: "لم يتم اختيار معايير بحث مكتملة بعد.",
      inventoryNote:
        "لن يظهر المخزون المباشر أو التوفر أو الأسعار أو أعداد النتائج إلا بعد ربط بيانات عقارية معتمدة.",
    },
    communities: {
      categories: [
        { label: "إيقاع الحياة اليومية", text: "فكّر في مدى دعم المكان للعمل والحياة العائلية والروتين اليومي." },
        { label: "سهولة الوصول", text: "استكشف الطرق والوجهات المهمة لخططك الشخصية." },
        { label: "طابع السكن", text: "قارن الأجواء وأنماط المساكن التي تناسب تفضيلاتك." },
      ],
      discoveryAction: "أنشئ موجزاً عقارياً",
      enquiryAction: "اسأل عن أولوياتك",
      sectionTitle: "ثلاث زوايا لاستكشاف المجتمع",
    },
    offPlan: {
      enquiryAction: "ناقش أسئلتك",
      searchAction: "استكشف العقارات",
      steps: [
        { label: "حدّد الهدف", text: "وضّح الاستخدام والتوقيت والأولويات قبل مقارنة الفرص." },
        { label: "راجع الأدلة", text: "اطلب المعلومات المعتمدة عن المشروع والمطور والعقود قبل اتخاذ القرار." },
        { label: "افهم الالتزام كاملاً", text: "تعرّف إلى المراحل والمسؤوليات والحاجة إلى مشورة مستقلة مناسبة." },
      ],
      sectionTitle: "مسار مدروس للعقارات على المخطط",
    },
    about: {
      action: "ابدأ استفساراً",
      principles: [
        { label: "نستمع أولاً", text: "نبدأ بهدف العميل وتفضيلاته والأسئلة التي لا تزال بحاجة إلى إجابة." },
        { label: "نقدّم المعلومات بوضوح", text: "نفصل المعلومات الموثقة عما هو غير متاح أو قيد الاعتماد أو توضيحي." },
        { label: "نجعل الخطوة التالية واضحة", text: "نقدّم كل مسار اكتشاف بصورة مفهومة بالإنجليزية والعربية." },
      ],
      sectionTitle: "التجربة التي نعتزم بناءها",
    },
    contact: {
      emailLabel: "البريد الإلكتروني",
      emailPlaceholder: "name@example.com",
      enquiryTypeLabel: "نوع الاستفسار",
      enquiryTypes: [
        { label: "شراء عقار", value: "buy" },
        { label: "استئجار عقار", value: "rent" },
        { label: "اختيار مجتمع", value: "communities" },
        { label: "استكشاف عقار على المخطط", value: "off-plan" },
        { label: "سؤال عقاري عام", value: "general" },
      ],
      intro: "شارك فقط المعلومات اللازمة ليتمكن مستخدمو إدارة ALIYAS المخولون من مراجعة استفسارك والرد عليه.",
      messageLabel: "ما الذي تبحث عنه؟",
      messagePlaceholder: "شارك هدفك أو موقعك المفضل أو السؤال الذي ترغب في استكشافه.",
      nameLabel: "الاسم",
      namePlaceholder: "اسمك",
      previewNote: "تُخزن بياناتك بأمان لمعالجة الاستفسار. والموافقة التسويقية اختيارية ومنفصلة.",
      submit: "أرسل الاستفسار",
      success: "تم استلام استفسارك بأمان.",
      validation: "يرجى إدخال الاسم وبريد إلكتروني صالح ورسالة قصيرة قبل المتابعة.",
    },
  },
};
