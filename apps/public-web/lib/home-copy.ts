export const locales = ["en", "ar"] as const;

export type Locale = (typeof locales)[number];
export type Purpose = "buy" | "rent" | "off-plan";

export type HeaderCopy = Readonly<{
  about: string;
  activeLanguage: string;
  buy: string;
  careers: string;
  closeMenu: string;
  communities: string;
  contact: string;
  developers: string;
  home: string;
  insights: string;
  language: string;
  menu: string;
  menuDescription: string;
  navigation: string;
  offPlan: string;
  openMenu: string;
  properties: string;
  rent: string;
  skipLink: string;
  startDiscovering: string;
}>;

export type SearchCopy = Readonly<{
  locationLabel: string;
  locationPlaceholder: string;
  locations: ReadonlyArray<Readonly<{ label: string; value: string }>>;
  previewNote: string;
  propertyTypeLabel: string;
  propertyTypePlaceholder: string;
  propertyTypes: ReadonlyArray<Readonly<{ label: string; value: string }>>;
  purposeLabel: string;
  purposes: Readonly<Record<Purpose, string>>;
  searchButton: string;
  successMessage: string;
  validationMessage: string;
}>;

export type HomeCopy = Readonly<{
  discovery: Readonly<{
    description: string;
    eyebrow: string;
    label: string;
    title: string;
  }>;
  header: HeaderCopy;
  hero: Readonly<{
    description: string;
    eyebrow: string;
    localReview: string;
    primaryAction: string;
    previewLabel: string;
    secondaryAction: string;
    title: string;
    visualLabel: string;
    visualNote: string;
  }>;
  journeys: ReadonlyArray<
    Readonly<{
      className: string;
      eyebrow: string;
      imageAlt: string;
      linkLabel: string;
      purpose: Purpose;
      text: string;
      title: string;
    }>
  >;
  meta: Readonly<{ description: string; title: string }>;
  search: SearchCopy;
  searchHeading: Readonly<{ eyebrow: string; title: string }>;
}>;

export function isLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}

export function isPurpose(value: string | undefined): value is Purpose {
  return value === "buy" || value === "rent" || value === "off-plan";
}

export const homeCopy: Readonly<Record<Locale, HomeCopy>> = {
  en: {
    meta: {
      title: "UAE Property Discovery | ALIYAS Real Estate",
      description:
        "Explore published UAE properties, community guidance, developers and source-aware insights with ALIYAS Real Estate in English and Arabic.",
    },
    header: {
      about: "About",
      activeLanguage: "English",
      buy: "Buy",
      careers: "Careers",
      closeMenu: "Close navigation menu",
      communities: "Communities",
      contact: "Consult Us",
      developers: "Developers",
      home: "Home",
      insights: "Insights",
      language: "Language",
      menu: "Navigation",
      menuDescription: "English homepage preview with an equivalent Arabic experience available.",
      navigation: "Primary navigation",
      openMenu: "Open navigation menu",
      offPlan: "Off-Plan",
      properties: "Properties",
      rent: "Rent",
      skipLink: "Skip to main content",
      startDiscovering: "Start discovering",
    },
    hero: {
      description:
        "Explore UAE property pathways, understand your options and organise the questions that matter before you enquire.",
      eyebrow: "A CONSIDERED ROUTE INTO UAE PROPERTY",
      localReview: "Dubai, United Arab Emirates",
      primaryAction: "Explore Properties",
      previewLabel: "Bilingual property guidance",
      secondaryAction: "Consult an Advisor",
      title: "Find the place that fits the life you are building.",
      visualLabel: "Residential life in Dubai",
      visualNote: "Contemporary luxury residence at dusk in the UAE",
    },
    searchHeading: {
      eyebrow: "Property discovery",
      title: "Begin with what matters to you",
    },
    search: {
      locationLabel: "Location",
      locationPlaceholder: "Choose a location",
      locations: [
        { label: "Across the UAE", value: "uae" },
        { label: "Dubai", value: "dubai" },
        { label: "Ajman", value: "ajman" },
      ],
      previewNote: "Filters open the published property directory. Reconfirm current availability and details before acting.",
      propertyTypeLabel: "Property type",
      propertyTypePlaceholder: "Choose a property type",
      propertyTypes: [
        { label: "Apartment", value: "apartment" },
        { label: "Villa", value: "villa" },
        { label: "Townhouse", value: "townhouse" },
        { label: "Commercial", value: "commercial" },
      ],
      purposeLabel: "Purpose",
      purposes: { buy: "Buy", rent: "Rent", "off-plan": "Off-Plan" },
      searchButton: "Search",
      successMessage: "Opening published property results.",
      validationMessage: "Choose a location and property type before viewing published results.",
    },
    discovery: {
      description:
        "Whether you are ready to buy, looking for a rental, or exploring an off-plan opportunity, begin with the route that matches your goals and move forward with greater clarity.",
      eyebrow: "THREE WAYS TO BEGIN",
      label: "ALIYAS discovery",
      title: "Three clear paths to your next UAE property.",
    },
    journeys: [
      {
        className: "discovery-card--buy",
        eyebrow: "01 / BUY",
        imageAlt: "Contemporary residence exterior representing the buying journey",
        linkLabel: "Explore buying",
        purpose: "buy",
        text: "Shape a search around intended use, preferred places, home type and the information you need to verify.",
        title: "Buy",
      },
      {
        className: "discovery-card--rent",
        eyebrow: "02 / RENT",
        imageAlt: "Contemporary residence interior representing the renting journey",
        linkLabel: "Explore renting",
        purpose: "rent",
        text: "Consider daily routine, household needs, location priorities and the practical terms of a future tenancy.",
        title: "Rent",
      },
      {
        className: "discovery-card--off-plan",
        eyebrow: "03 / OFF-PLAN",
        imageAlt: "Architectural scale model representing the off-plan journey",
        linkLabel: "Understand off-plan",
        purpose: "off-plan",
        text: "Review the route, source documents and questions to clarify before evaluating a specific project.",
        title: "Off-Plan",
      },
    ],
  },
  ar: {
    meta: {
      title: "اكتشاف العقارات في الإمارات | ALIYAS Real Estate",
      description:
        "استكشف العقارات المنشورة وإرشادات المجتمعات والمطورين والرؤى الواعية بالمصادر في الإمارات مع ALIYAS Real Estate.",
    },
    header: {
      about: "من نحن",
      activeLanguage: "العربية",
      buy: "شراء",
      careers: "الوظائف",
      closeMenu: "إغلاق قائمة التنقل",
      communities: "المجتمعات",
      contact: "استشرنا",
      developers: "المطورون",
      home: "الرئيسية",
      insights: "الرؤى",
      language: "اللغة",
      menu: "التنقل",
      menuDescription: "معاينة عربية للصفحة الرئيسية مع تجربة إنجليزية مكافئة.",
      navigation: "التنقل الرئيسي",
      openMenu: "فتح قائمة التنقل",
      offPlan: "المشاريع على المخطط",
      properties: "العقارات",
      rent: "إيجار",
      skipLink: "الانتقال إلى المحتوى الرئيسي",
      startDiscovering: "ابدأ الاستكشاف",
    },
    hero: {
      description:
        "استكشف مسارات العقارات في الإمارات، وافهم خياراتك، ونظّم الأسئلة المهمة قبل إرسال استفسارك.",
      eyebrow: "مسار مدروس إلى عقارات الإمارات",
      localReview: "دبي، الإمارات العربية المتحدة",
      primaryAction: "استكشف العقارات",
      previewLabel: "إرشادات عقارية ثنائية اللغة",
      secondaryAction: "استشر مستشاراً",
      title: "اعثر على المكان الذي يناسب الحياة التي تبنيها.",
      visualLabel: "الحياة السكنية في دبي",
      visualNote: "مسكن فاخر بتصميم عصري عند الغروب في الإمارات",
    },
    searchHeading: {
      eyebrow: "اكتشاف العقارات",
      title: "ابدأ بما يهمك",
    },
    search: {
      locationLabel: "الموقع",
      locationPlaceholder: "اختر موقعاً",
      locations: [
        { label: "جميع أنحاء الإمارات", value: "uae" },
        { label: "دبي", value: "dubai" },
        { label: "عجمان", value: "ajman" },
      ],
      previewNote: "تنقلك عوامل التصفية إلى دليل العقارات المنشورة. تحقق مجدداً من التوفر والتفاصيل الحالية قبل اتخاذ قرار.",
      propertyTypeLabel: "نوع العقار",
      propertyTypePlaceholder: "اختر نوع العقار",
      propertyTypes: [
        { label: "شقة", value: "apartment" },
        { label: "فيلا", value: "villa" },
        { label: "تاون هاوس", value: "townhouse" },
        { label: "عقار تجاري", value: "commercial" },
      ],
      purposeLabel: "الغرض",
      purposes: { buy: "شراء", rent: "إيجار", "off-plan": "على المخطط" },
      searchButton: "بحث",
      successMessage: "جارٍ فتح نتائج العقارات المنشورة.",
      validationMessage: "يرجى اختيار الموقع ونوع العقار قبل عرض النتائج المنشورة.",
    },
    discovery: {
      description:
        "سواء كنت مستعداً للشراء، أو تبحث عن عقار للإيجار، أو تستكشف فرصة في مشروع على المخطط، ابدأ بالمسار الذي يتوافق مع أهدافك وتقدّم بوضوح أكبر.",
      eyebrow: "ثلاثة مسارات للبدء",
      label: "اكتشاف ALIYAS",
      title: "ثلاثة مسارات واضحة نحو عقارك القادم في الإمارات.",
    },
    journeys: [
      {
        className: "discovery-card--buy",
        eyebrow: "01 / شراء",
        imageAlt: "واجهة مسكن عصري تمثل مسار الشراء",
        linkLabel: "استكشف الشراء",
        purpose: "buy",
        text: "نظّم البحث حول الغرض والمناطق ونوع المنزل والمعلومات التي تحتاج إلى التحقق منها.",
        title: "شراء",
      },
      {
        className: "discovery-card--rent",
        eyebrow: "02 / إيجار",
        imageAlt: "تصميم داخلي لمسكن عصري يمثل مسار الإيجار",
        linkLabel: "استكشف الإيجار",
        purpose: "rent",
        text: "فكّر في روتينك اليومي واحتياجات الأسرة وأولويات الموقع والشروط العملية للإيجار.",
        title: "إيجار",
      },
      {
        className: "discovery-card--off-plan",
        eyebrow: "03 / على المخطط",
        imageAlt: "مجسم معماري يمثل مسار المشاريع على المخطط",
        linkLabel: "افهم مسار على المخطط",
        purpose: "off-plan",
        text: "راجع المسار والوثائق والأسئلة التي يلزم توضيحها قبل تقييم مشروع بعينه.",
        title: "على المخطط",
      },
    ],
  },
};
