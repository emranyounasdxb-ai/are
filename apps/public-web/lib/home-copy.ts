export const locales = ["en", "ar"] as const;

export type Locale = (typeof locales)[number];
export type Purpose = "buy" | "rent" | "off-plan";

export type HeaderCopy = Readonly<{
  about: string;
  activeLanguage: string;
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
      title: "UAE Property Discovery | ALIYAS Real Estate",
      description:
        "Explore published UAE properties, community guidance, developers and source-aware insights with ALIYAS Real Estate in English and Arabic.",
    },
    header: {
      about: "About",
      activeLanguage: "English",
      careers: "Careers",
      closeMenu: "Close navigation menu",
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
        "Explore published properties, understand the available pathways and organise the questions that matter before you enquire.",
      eyebrow: "A CONSIDERED ROUTE INTO UAE PROPERTY",
      localReview: "Dubai, United Arab Emirates",
      primaryAction: "Start an enquiry",
      previewLabel: "Bilingual property guidance",
      secondaryAction: "Explore properties",
      title: "Find the place that fits the life you are building.",
      visualLabel: "Residential life in Dubai",
      visualNote: "Illustrative contemporary waterfront residence in the UAE",
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
        "Choose a permanent discovery route. Property records appear only when they are Published through the Admin-managed data source.",
      eyebrow: "Three ways to begin",
      label: "ALIYAS discovery",
      title: "Three clear ways to begin your UAE property search.",
    },
    journeys: [
      {
        className: "discovery-card--buy",
        eyebrow: "01 / Buy",
        linkLabel: "Explore buying",
        purpose: "buy",
        text: "Shape a search around intended use, preferred places, home type and the information you need to verify.",
        title: "Buy",
      },
      {
        className: "discovery-card--rent",
        eyebrow: "02 / Rent",
        linkLabel: "Explore renting",
        purpose: "rent",
        text: "Consider daily routine, household needs, location priorities and the practical terms of a future tenancy.",
        title: "Rent",
      },
      {
        className: "discovery-card--off-plan",
        eyebrow: "03 / Off-Plan",
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
      careers: "الوظائف",
      closeMenu: "إغلاق قائمة التنقل",
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
        "استكشف العقارات المنشورة وافهم المسارات المتاحة ونظّم الأسئلة المهمة قبل إرسال استفسارك.",
      eyebrow: "مسار مدروس إلى عقارات الإمارات",
      localReview: "دبي، الإمارات العربية المتحدة",
      primaryAction: "ابدأ استفساراً",
      previewLabel: "إرشادات عقارية ثنائية اللغة",
      secondaryAction: "استكشف العقارات",
      title: "اعثر على المكان الذي يناسب الحياة التي تبنيها.",
      visualLabel: "الحياة السكنية في دبي",
      visualNote: "صورة توضيحية لمسكن عصري على الواجهة المائية في الإمارات",
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
        "اختر مسار استكشاف دائم. لا تظهر سجلات العقارات إلا بعد نشرها عبر مصدر البيانات الذي تديره لوحة الإدارة.",
      eyebrow: "ثلاث طرق للبدء",
      label: "اكتشاف ALIYAS",
      title: "ثلاث طرق واضحة لبدء بحثك العقاري في الإمارات.",
    },
    journeys: [
      {
        className: "discovery-card--buy",
        eyebrow: "01 / شراء",
        linkLabel: "استكشف الشراء",
        purpose: "buy",
        text: "نظّم البحث حول الغرض والمناطق ونوع المنزل والمعلومات التي تحتاج إلى التحقق منها.",
        title: "شراء",
      },
      {
        className: "discovery-card--rent",
        eyebrow: "02 / إيجار",
        linkLabel: "استكشف الإيجار",
        purpose: "rent",
        text: "فكّر في روتينك اليومي واحتياجات الأسرة وأولويات الموقع والشروط العملية للإيجار.",
        title: "إيجار",
      },
      {
        className: "discovery-card--off-plan",
        eyebrow: "03 / على المخطط",
        linkLabel: "افهم مسار على المخطط",
        purpose: "off-plan",
        text: "راجع المسار والوثائق والأسئلة التي يلزم توضيحها قبل تقييم مشروع بعينه.",
        title: "على المخطط",
      },
    ],
  },
};
