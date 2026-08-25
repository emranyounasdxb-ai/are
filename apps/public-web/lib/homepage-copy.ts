import type { Locale } from "./home-copy";

type HomepageCopy = Readonly<{
  approach: Readonly<{
    eyebrow: string;
    title: string;
    text: string;
    imageAlt: string;
    points: ReadonlyArray<string>;
  }>;
  guidance: Readonly<{
    eyebrow: string;
    title: string;
    text: string;
    communityImageAlt: string;
    imageNote: string;
    items: ReadonlyArray<Readonly<{ title: string; text: string }>>;
  }>;
  developer: Readonly<{
    eyebrow: string;
    title: string;
    verified: string;
    focus: string;
    emirate: string;
    source: string;
    details: string;
    enquire: string;
    imageAlt: string;
    imageNote: string;
  }>;
  insight: Readonly<{
    eyebrow: string;
    title: string;
    read: string;
    editorial: string;
    imageAlt: string;
  }>;
  process: Readonly<{
    eyebrow: string;
    title: string;
    text: string;
    items: ReadonlyArray<Readonly<{ title: string; text: string }>>;
  }>;
  faq: Readonly<{
    eyebrow: string;
    title: string;
    items: ReadonlyArray<Readonly<{ question: string; answer: string }>>;
  }>;
  cta: Readonly<{
    eyebrow: string;
    title: string;
    text: string;
    enquire: string;
    whatsapp: string;
    imageAlt: string;
  }>;
}>;

export const homepageCopy: Readonly<Record<Locale, HomepageCopy>> = {
  en: {
    approach: {
      eyebrow: "THE ALIYAS APPROACH",
      title: "A clear property conversation begins with your requirements.",
      text: "We organise the journey around what you need to understand, compare and verify. The aim is a useful enquiry shaped by current information—not assumptions.",
      imageAlt: "Architectural plans and material samples arranged for a considered property conversation",
      points: [
        "Begin with client requirements",
        "Compare information carefully",
        "Verify current details",
        "Support a clear enquiry journey",
        "Communicate in English and Arabic",
      ],
    },
    guidance: {
      eyebrow: "UAE DISCOVERY GUIDANCE",
      title: "Ask better questions before narrowing the search.",
      text: "Evergreen guidance helps you understand the route before evaluating a specific home, project or developer.",
      communityImageAlt: "Aerial view of a contemporary UAE residential community",
      imageNote: "Illustrative UAE residential imagery",
      items: [
        { title: "Choose the community", text: "Consider daily routine, household priorities, access and the character of the place." },
        { title: "Understand off-plan", text: "Review the developer identity, project information, milestones and documents through current sources." },
        { title: "Compare buying and renting", text: "Define intended use, timeframe, practical needs and the professional advice relevant to your situation." },
        { title: "Stay source-aware", text: "Treat prices, availability and project details as time-sensitive and verify them before acting." },
      ],
    },
    developer: {
      eyebrow: "FEATURED DEVELOPER",
      title: "A source-grounded developer introduction.",
      verified: "Verified",
      focus: "Development focus",
      emirate: "Primary emirate",
      source: "Source note",
      details: "View developer profile",
      enquire: "Enquire about this developer",
      imageAlt: "Architectural detail of a contemporary waterfront residence at dusk",
      imageNote: "Illustrative architectural imagery — not a project listing",
    },
    insight: {
      eyebrow: "FEATURED INSIGHT",
      title: "A practical guide for a more considered search.",
      read: "Read the complete guide",
      editorial: "Source-aware editorial guide",
      imageAlt: "Landscaped pedestrian setting in a contemporary UAE residential community",
    },
    process: {
      eyebrow: "A SIMPLE DISCOVERY PROCESS",
      title: "Four deliberate steps from brief to enquiry.",
      text: "Each step keeps the conversation focused while current property information remains with the published source records.",
      items: [
        { title: "Define requirements", text: "Clarify purpose, preferred places, home type, timeframe and practical priorities." },
        { title: "Explore suitable routes", text: "Compare buying, renting, off-plan and community pathways without assuming inventory." },
        { title: "Review verified information", text: "Check source-grounded details and identify what still needs current confirmation." },
        { title: "Submit an enquiry", text: "Share a focused brief so the next conversation starts with relevant context." },
      ],
    },
    faq: {
      eyebrow: "ARE / FAQ",
      title: "Useful answers before you enquire.",
      items: [
        { question: "Does the homepage show every available property?", answer: "No. Published property records appear through the property directory. Current availability and details should always be reconfirmed." },
        { question: "How should I begin a UAE property search?", answer: "Start with your purpose, location priorities, home type, timeframe and the information you need to verify." },
        { question: "Are developer spotlights partnership endorsements?", answer: "No. A spotlight presents a published, source-grounded directory record and does not imply partnership, exclusivity or allocation." },
        { question: "Can I continue in Arabic?", answer: "Yes. The discovery journey, guidance and enquiry routes are available in English and Arabic." },
      ],
    },
    cta: {
      eyebrow: "YOUR NEXT STEP",
      title: "Turn your priorities into a focused property enquiry.",
      text: "Tell us what you are considering and what you need to verify. You can use the enquiry form or begin a WhatsApp conversation.",
      enquire: "Start an enquiry",
      whatsapp: "WhatsApp +971 56 915 7576",
      imageAlt: "Contemporary waterfront residence illuminated at night",
    },
  },
  ar: {
    approach: {
      eyebrow: "منهج ALIYAS",
      title: "تبدأ المحادثة العقارية الواضحة من متطلباتك.",
      text: "ننظم رحلة البحث حول ما تحتاج إلى فهمه ومقارنته والتحقق منه، بهدف إعداد استفسار مفيد يستند إلى معلومات حالية لا إلى افتراضات.",
      imageAlt: "مخططات معمارية وعينات مواد مرتبة لمحادثة عقارية مدروسة",
      points: [
        "البدء بمتطلبات العميل",
        "مقارنة المعلومات بعناية",
        "التحقق من التفاصيل الحالية",
        "دعم رحلة استفسار واضحة",
        "التواصل باللغتين العربية والإنجليزية",
      ],
    },
    guidance: {
      eyebrow: "إرشادات الاستكشاف في الإمارات",
      title: "اطرح أسئلة أدق قبل تضييق نطاق البحث.",
      text: "تساعدك الإرشادات الدائمة على فهم المسار قبل تقييم منزل أو مشروع أو مطور بعينه.",
      communityImageAlt: "مشهد علوي لمجتمع سكني عصري في الإمارات",
      imageNote: "صور توضيحية للحياة السكنية في الإمارات",
      items: [
        { title: "اختيار المجتمع", text: "فكّر في روتينك اليومي وأولويات الأسرة وسهولة الوصول وطابع المكان." },
        { title: "فهم الشراء على المخطط", text: "راجع هوية المطور ومعلومات المشروع والمراحل والوثائق عبر مصادر حديثة." },
        { title: "مقارنة الشراء والإيجار", text: "حدّد الغرض والمدة والاحتياجات العملية والمشورة المهنية المناسبة لحالتك." },
        { title: "الوعي بالمصادر", text: "تعامل مع الأسعار والتوفر وتفاصيل المشاريع كمعلومات متغيرة وتحقق منها قبل اتخاذ قرار." },
      ],
    },
    developer: {
      eyebrow: "مطور مختار",
      title: "تعريف بالمطور يستند إلى المصادر.",
      verified: "تاريخ التحقق",
      focus: "مجال التطوير",
      emirate: "الإمارة الرئيسية",
      source: "ملاحظة المصدر",
      details: "عرض ملف المطور",
      enquire: "استفسر عن هذا المطور",
      imageAlt: "تفصيل معماري لمسكن عصري على الواجهة المائية عند الغروب",
      imageNote: "صورة معمارية توضيحية — لا تمثل مشروعاً معروضاً",
    },
    insight: {
      eyebrow: "رؤية مختارة",
      title: "دليل عملي لبحث أكثر تأنياً.",
      read: "اقرأ الدليل كاملاً",
      editorial: "دليل تحريري واعٍ بالمصادر",
      imageAlt: "ممشى منسق داخل مجتمع سكني عصري في الإمارات",
    },
    process: {
      eyebrow: "عملية استكشاف بسيطة",
      title: "أربع خطوات مدروسة من المتطلبات إلى الاستفسار.",
      text: "تحافظ كل خطوة على وضوح المحادثة، بينما تبقى معلومات العقارات الحالية ضمن السجلات المنشورة.",
      items: [
        { title: "حدّد المتطلبات", text: "وضّح الغرض والمناطق المفضلة ونوع المنزل والإطار الزمني والأولويات العملية." },
        { title: "استكشف المسارات المناسبة", text: "قارن بين الشراء والإيجار وعلى المخطط والمجتمعات دون افتراض وجود مخزون." },
        { title: "راجع المعلومات المتحقق منها", text: "تحقق من التفاصيل المستندة إلى المصادر وحدّد ما يحتاج إلى تأكيد حديث." },
        { title: "أرسل استفساراً", text: "شارك ملخصاً واضحاً لتبدأ المحادثة التالية بسياق مناسب." },
      ],
    },
    faq: {
      eyebrow: "ARE / الأسئلة الشائعة",
      title: "إجابات مفيدة قبل إرسال الاستفسار.",
      items: [
        { question: "هل تعرض الصفحة الرئيسية كل العقارات المتاحة؟", answer: "لا. تظهر السجلات المنشورة عبر دليل العقارات، ويجب دائماً إعادة التحقق من التوفر والتفاصيل الحالية." },
        { question: "كيف أبدأ البحث عن عقار في الإمارات؟", answer: "ابدأ بتحديد الغرض وأولويات الموقع ونوع المنزل والإطار الزمني والمعلومات التي تحتاج إلى التحقق منها." },
        { question: "هل يعني عرض مطور وجود شراكة أو توصية؟", answer: "لا. يعرض القسم سجلاً منشوراً ومستنداً إلى المصادر، ولا يعني شراكة أو حصرية أو تخصيصاً." },
        { question: "هل يمكنني متابعة الرحلة باللغة العربية؟", answer: "نعم. تتوفر رحلة الاستكشاف والإرشادات ومسارات الاستفسار باللغتين العربية والإنجليزية." },
      ],
    },
    cta: {
      eyebrow: "خطوتك التالية",
      title: "حوّل أولوياتك إلى استفسار عقاري واضح.",
      text: "أخبرنا بما تفكر فيه وما تحتاج إلى التحقق منه عبر نموذج الاستفسار أو محادثة واتساب.",
      enquire: "ابدأ استفساراً",
      whatsapp: "واتساب +971 56 915 7576",
      imageAlt: "مسكن عصري على الواجهة المائية مضاء ليلاً",
    },
  },
};
