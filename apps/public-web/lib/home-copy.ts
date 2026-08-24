export const locales = ["en", "ar"] as const;

export type Locale = (typeof locales)[number];
export type Purpose = "buy" | "rent" | "off-plan";

export type HeaderCopy = Readonly<{
  about: string;
  activeLanguage: string;
  careers: string;
  closeMenu: string;
  company: string;
  companyMenuLabel: string;
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
      title: "ALIYAS Real Estate | UAE Property Discovery",
      description:
        "Explore properties, communities and opportunities across the UAE with ALIYAS Real Estate.",
    },
    header: {
      about: "About",
      activeLanguage: "English",
      careers: "Careers",
      closeMenu: "Close navigation menu",
      company: "Company",
      companyMenuLabel: "Open Company navigation",
      communities: "Communities",
      contact: "Enquire",
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
      skipLink: "Skip to main content",
      startDiscovering: "Start discovering",
    },
    hero: {
      description:
        "Explore properties, communities and opportunities designed around the way you want to live and invest.",
      eyebrow: "UAE REAL ESTATE, REIMAGINED",
      localReview: "Local review",
      primaryAction: "Explore Properties",
      previewLabel: "English preview",
      secondaryAction: "Discover How It Works",
      title: "Discover Exceptional Living Across the UAE",
      visualLabel: "Conceptual architectural study",
      visualNote: "Replaceable preview composition — no property is represented.",
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
      previewNote: "Preview only — no live inventory is queried.",
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
      successMessage:
        "Search preview ready. Live property search will be connected with approved property data.",
      validationMessage: "Choose a location and property type before continuing the preview.",
    },
    discovery: {
      description:
        "Choose the journey that matches your intent. Live results will follow only when approved property data is connected.",
      eyebrow: "Three ways to begin",
      label: "ALIYAS discovery",
      title: "A clearer first step into UAE real estate.",
    },
    journeys: [
      {
        className: "discovery-card--buy",
        eyebrow: "01 / Buy",
        linkLabel: "Choose buying",
        purpose: "buy",
        text: "Explore a considered path to finding your next home or investment.",
        title: "Buy",
      },
      {
        className: "discovery-card--rent",
        eyebrow: "02 / Rent",
        linkLabel: "Choose renting",
        purpose: "rent",
        text: "Find a place that fits the way you want to live across the UAE.",
        title: "Rent",
      },
      {
        className: "discovery-card--off-plan",
        eyebrow: "03 / Off-Plan",
        linkLabel: "Choose off-plan",
        purpose: "off-plan",
        text: "Discover the questions that matter before exploring a new project.",
        title: "Off-Plan",
      },
    ],
  },
  ar: {
    meta: {
      title: "ALIYAS Real Estate | اكتشاف العقارات في الإمارات",
      description:
        "استكشف العقارات والمجتمعات والفرص في جميع أنحاء دولة الإمارات مع ALIYAS Real Estate.",
    },
    header: {
      about: "من نحن",
      activeLanguage: "العربية",
      careers: "الوظائف",
      closeMenu: "إغلاق قائمة التنقل",
      company: "الشركة",
      companyMenuLabel: "فتح قائمة الشركة",
      communities: "المجتمعات",
      contact: "استفسر",
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
      skipLink: "الانتقال إلى المحتوى الرئيسي",
      startDiscovering: "ابدأ الاستكشاف",
    },
    hero: {
      description:
        "استكشف العقارات والمجتمعات والفرص المصممة لتناسب أسلوب حياتك واستثمارك.",
      eyebrow: "عقارات الإمارات، برؤية جديدة",
      localReview: "مراجعة محلية",
      primaryAction: "استكشف العقارات",
      previewLabel: "معاينة عربية",
      secondaryAction: "اكتشف كيف تعمل التجربة",
      title: "اكتشف أسلوب حياة استثنائياً في جميع أنحاء الإمارات",
      visualLabel: "دراسة معمارية تصوّرية",
      visualNote: "تكوين تجريبي قابل للاستبدال — لا يمثّل أي عقار.",
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
      previewNote: "معاينة فقط — لا يتم الاستعلام عن مخزون عقاري مباشر.",
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
      successMessage:
        "معاينة البحث جاهزة. سيتم ربط البحث المباشر بعد اعتماد بيانات العقارات.",
      validationMessage: "يرجى اختيار الموقع ونوع العقار قبل متابعة المعاينة.",
    },
    discovery: {
      description:
        "اختر المسار الذي يطابق هدفك. ستظهر النتائج المباشرة فقط بعد ربط بيانات عقارية معتمدة.",
      eyebrow: "ثلاث طرق للبدء",
      label: "اكتشاف ALIYAS",
      title: "خطوة أولى أكثر وضوحاً في عقارات الإمارات.",
    },
    journeys: [
      {
        className: "discovery-card--buy",
        eyebrow: "01 / شراء",
        linkLabel: "اختر الشراء",
        purpose: "buy",
        text: "استكشف مساراً مدروساً للعثور على منزلك أو استثمارك القادم.",
        title: "شراء",
      },
      {
        className: "discovery-card--rent",
        eyebrow: "02 / إيجار",
        linkLabel: "اختر الإيجار",
        purpose: "rent",
        text: "اعثر على مكان يناسب أسلوب حياتك في دولة الإمارات.",
        title: "إيجار",
      },
      {
        className: "discovery-card--off-plan",
        eyebrow: "03 / على المخطط",
        linkLabel: "اختر على المخطط",
        purpose: "off-plan",
        text: "تعرّف إلى الأسئلة المهمة قبل استكشاف مشروع جديد.",
        title: "على المخطط",
      },
    ],
  },
};
