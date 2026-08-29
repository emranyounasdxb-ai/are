import type { FaqItem, RelatedItem } from "../components/content/editorial-content";
import type { Locale } from "./home-copy";

type LocalizedText = Readonly<Record<Locale, string>>;

export type CareerVacancy = Readonly<{
  slug: string;
  title: LocalizedText;
  location: LocalizedText;
  published: string;
}>;

export const careerVacancies: ReadonlyArray<CareerVacancy> = [];

export const careerInterests = [
  { value: "sales-leasing", label: { en: "Real Estate Sales and Leasing", ar: "المبيعات والتأجير العقاري" } },
  { value: "off-plan-advisory", label: { en: "Off-Plan Property Advisory", ar: "استشارات العقارات على المخطط" } },
  { value: "resale-services", label: { en: "Resale Services", ar: "خدمات إعادة البيع" } },
  { value: "marketing-content", label: { en: "Marketing and Content", ar: "التسويق والمحتوى" } },
  { value: "customer-support", label: { en: "Customer Support", ar: "دعم العملاء" } },
  { value: "operations-administration", label: { en: "Operations and Administration", ar: "العمليات والإدارة" } },
  { value: "general", label: { en: "General Application", ar: "طلب عام" } },
] as const;

export const experienceRanges = [
  { value: "entry", label: { en: "Early career / up to 2 years", ar: "بداية المسيرة / حتى سنتين" } },
  { value: "mid", label: { en: "3–5 years", ar: "من ٣ إلى ٥ سنوات" } },
  { value: "experienced", label: { en: "6–10 years", ar: "من ٦ إلى ١٠ سنوات" } },
  { value: "senior", label: { en: "More than 10 years", ar: "أكثر من ١٠ سنوات" } },
] as const;

type FormCopy = Readonly<{
  required: string;
  optional: string;
  fullName: string;
  email: string;
  phone: string;
  location: string;
  interest: string;
  experience: string;
  coverMessage: string;
  cv: string;
  linkedin: string;
  portfolio: string;
  languages: string;
  currentTitle: string;
  acknowledge: string;
  select: string;
  submit: string;
  reset: string;
  removeFile: string;
  fileHint: string;
  localFileNote: string;
  selectedFile: string;
  summaryTitle: string;
  summaryIntro: string;
  validResult: string;
  errors: Readonly<Record<"fullName" | "email" | "phone" | "location" | "interest" | "experience" | "coverMessage" | "cvRequired" | "cvType" | "cvSize" | "linkedin" | "portfolio" | "acknowledge", string>>;
}>;

export type CareersCopy = Readonly<{
  metaTitle: string;
  metaDescription: string;
  breadcrumb: string;
  hero: Readonly<{ eyebrow: string; title: string; text: string; note: string }>;
  intro: Readonly<{ eyebrow: string; title: string; text: string }>;
  areas: Readonly<{ eyebrow: string; title: string; text: string }>;
  opportunities: Readonly<{ eyebrow: string; title: string; emptyTitle: string; emptyText: string; action: string }>;
  general: Readonly<{ eyebrow: string; title: string; text: string; points: ReadonlyArray<Readonly<{ title: string; text: string }>> }>;
  prepare: Readonly<{ eyebrow: string; title: string; text: string; items: ReadonlyArray<string> }>;
  journey: Readonly<{ eyebrow: string; title: string; text: string; items: ReadonlyArray<Readonly<{ title: string; text: string }>> }>;
  application: Readonly<{ eyebrow: string; title: string; text: string }>;
  privacy: Readonly<{ eyebrow: string; title: string; text: string; points: ReadonlyArray<string> }>;
  faq: Readonly<{ eyebrow: string; title: string; items: ReadonlyArray<FaqItem> }>;
  related: Readonly<{ title: string; items: ReadonlyArray<RelatedItem> }>;
  cta: Readonly<{ title: string; text: string; action: string }>;
  form: FormCopy;
}>;

export const careersCopy: Readonly<Record<Locale, CareersCopy>> = {
  en: {
    metaTitle: "Careers at ALIYAS Real Estate | General Applications",
    metaDescription: "Explore verified ALIYAS Real Estate roles or securely submit a general bilingual career application.",
    breadcrumb: "Careers",
    hero: { eyebrow: "Careers at ALIYAS", title: "Bring clarity, care and professional judgement to every conversation.", text: "Explore the areas where future opportunities may develop and prepare a general expression of interest. This page does not imply that a specific role is currently open.", note: "People-first work. Evidence-aware service. Bilingual ambition." },
    intro: { eyebrow: "A considered introduction", title: "Real estate work begins with understanding people and their priorities.", text: "ALIYAS Real Estate welcomes thoughtful expressions of interest from professionals who value clear communication, responsible handling of information and a considered customer experience. Individual roles will be published only when they are approved and ready for applications." },
    areas: { eyebrow: "Professional interests", title: "Where your experience may contribute", text: "These areas are general application interests, not advertised vacancies." },
    opportunities: { eyebrow: "Current opportunities", title: "Only verified roles will appear here.", emptyTitle: "No individual vacancy is currently published.", emptyText: "You may still submit a general expression of interest for authorized HR review.", action: "Submit a general application" },
    general: { eyebrow: "General expression of interest", title: "Share the professional context that helps explain your potential contribution.", text: "A useful general application is specific enough to understand, without assuming a vacancy, interview or outcome.", points: [{ title: "Choose a relevant area", text: "Select the professional area closest to your current experience or future direction." }, { title: "Explain your contribution", text: "Describe relevant work, transferable strengths and the kind of responsibility you are prepared to take on." }, { title: "Keep evidence clear", text: "Use accurate dates, role titles and portfolio links, and avoid including unnecessary sensitive information." }] },
    prepare: { eyebrow: "Before you begin", title: "What applicants should prepare", text: "Keep the first expression of interest concise, accurate and relevant.", items: ["An up-to-date CV in PDF, DOC or DOCX format", "A short explanation of relevant experience and interests", "Current location and internationally readable contact details", "Optional LinkedIn or portfolio links using a complete web address", "No identity documents, financial information or unrelated sensitive records"] },
    journey: { eyebrow: "Recruitment journey", title: "A transparent application pathway", text: "Applications are submitted securely for review by authorized ALIYAS HR and Admin users.", items: [{ title: "Prepare", text: "Complete the form checks and review the information you intend to share." }, { title: "Secure submission", text: "Your application and private CV are validated and stored outside public directories." }, { title: "Role review", text: "Applications may be considered against a specific open vacancy or a relevant future need; no outcome is promised." }, { title: "Candidate communication", text: "Any interview or next step must be communicated through an approved recruitment process." }] },
    application: { eyebrow: "Secure application", title: "Submit a general expression of interest", text: "Your application and CV are sent securely for authorized HR review." },
    privacy: { eyebrow: "Applicant-data notice", title: "Your CV remains private.", text: "Application information is available only to authorized ALIYAS Admin and HR users. Retention is configurable pending an approved owner policy.", points: ["Your form data and CV are stored privately for application review.", "Do not include identity documents, banking details or other unnecessary sensitive information.", "Optional marketing consent is separate from submitting your application."] },
    faq: { eyebrow: "Careers FAQ", title: "Questions about expressions of interest", items: [{ question: "Are any roles currently open?", answer: "Verified open roles appear on this page when available; a general application remains available." }, { question: "Does completing this form submit an application?", answer: "Yes. A successful submission displays a reference ID and stores the application for authorized review." }, { question: "Which file formats can I select?", answer: "PDF, DOC and DOCX files up to 5 MB are validated and stored privately." }, { question: "Will I receive a response after applying?", answer: "Receipt is confirmed with a reference ID, but no interview, outcome or response time is promised." }, { question: "What should I avoid including?", answer: "Do not include identity documents, financial information, passwords or unrelated sensitive personal records." }] },
    related: { title: "Learn more before applying", items: [{ href: "/en/about", label: "About ALIYAS", text: "Understand the intended approach behind the customer experience." }, { href: "/en/contact", label: "Contact", text: "Use the general contact form for non-recruitment questions." }, { href: "/en/off-plan", label: "Off-plan services", text: "See how the website explains a considered property journey." }] },
    cta: { title: "Looking for a property conversation instead?", text: "Use the main contact route for property and service enquiries rather than the Careers form.", action: "Go to Contact" },
    form: {
      required: "Required", optional: "Optional", fullName: "Full name", email: "Email address", phone: "Phone number", location: "Current location", interest: "Area or role of interest", experience: "Relevant experience", coverMessage: "Cover message", cv: "CV file", linkedin: "LinkedIn profile URL", portfolio: "Portfolio URL", languages: "Languages", currentTitle: "Current job title", acknowledge: "I consent to the secure processing of this application and CV by authorized ALIYAS Admin and HR users.", select: "Select an option", submit: "Submit application", reset: "Clear form", removeFile: "Remove file", fileHint: "PDF, DOC or DOCX; maximum 5 MB.", localFileNote: "The selected file is uploaded only when you submit and is stored privately.", selectedFile: "Selected file", summaryTitle: "Please review the highlighted fields", summaryIntro: "Correct the following items before submitting the application.", validResult: "Your application has been submitted securely.",
      errors: { fullName: "Enter your full name.", email: "Enter a valid email address.", phone: "Enter a valid international or local phone number.", location: "Enter your current location.", interest: "Select an area or role of interest.", experience: "Select your relevant experience range.", coverMessage: "Write a cover message of at least 30 characters.", cvRequired: "Select a PDF, DOC or DOCX CV file.", cvType: "Select a valid PDF, DOC or DOCX file whose file type matches its extension.", cvSize: "The CV file must not exceed 5 MB.", linkedin: "Enter a complete LinkedIn URL beginning with http:// or https://.", portfolio: "Enter a complete portfolio URL beginning with http:// or https://.", acknowledge: "Confirm your consent to authorized processing of the application." },
    },
  },
  ar: {
    metaTitle: "الوظائف في علياس العقارية | طلبات الاهتمام العامة",
    metaDescription: "تعرّف إلى وظائف علياس العقارية الموثقة أو أرسل طلباً مهنياً عاماً آمناً بالعربية أو الإنجليزية.",
    breadcrumb: "الوظائف",
    hero: { eyebrow: "الوظائف في علياس العقارية", title: "أضف الوضوح والعناية والحكم المهني إلى كل حوار.", text: "تعرّف إلى المجالات التي قد تنشأ فيها فرص مستقبلية، وجهّز طلب اهتمام عاماً. لا تعني هذه الصفحة وجود وظيفة محددة شاغرة حالياً.", note: "عمل يتمحور حول الإنسان. خدمة واعية بالأدلة. طموح ثنائي اللغة." },
    intro: { eyebrow: "مقدمة مدروسة", title: "يبدأ العمل العقاري بفهم الناس وأولوياتهم.", text: "ترحب علياس العقارية بطلبات الاهتمام المدروسة من المهنيين الذين يقدّرون التواصل الواضح والتعامل المسؤول مع المعلومات وتجربة العميل المتوازنة. لن تُنشر الوظائف الفردية إلا بعد اعتمادها وجاهزيتها لاستقبال الطلبات." },
    areas: { eyebrow: "الاهتمامات المهنية", title: "مجالات قد تسهم فيها خبرتك", text: "هذه مجالات لطلبات الاهتمام العامة وليست إعلانات عن شواغر وظيفية." },
    opportunities: { eyebrow: "الفرص الحالية", title: "لن تظهر هنا إلا الوظائف الموثقة والمعتمدة.", emptyTitle: "لا توجد وظيفة محددة منشورة حالياً.", emptyText: "يمكنك مع ذلك إرسال طلب اهتمام عام لمراجعته من فريق الموارد البشرية المخول.", action: "أرسل طلباً عاماً" },
    general: { eyebrow: "طلب اهتمام عام", title: "شارك السياق المهني الذي يوضح القيمة التي قد تضيفها.", text: "يكون الطلب العام المفيد محدداً بما يكفي للفهم، من دون افتراض وجود شاغر أو مقابلة أو نتيجة.", points: [{ title: "اختر المجال المناسب", text: "حدّد المجال المهني الأقرب إلى خبرتك الحالية أو اتجاهك المستقبلي." }, { title: "وضّح مساهمتك", text: "اشرح الخبرات ذات الصلة والمهارات القابلة للنقل ونوع المسؤولية التي تستعد لتوليها." }, { title: "حافظ على دقة الأدلة", text: "استخدم تواريخ ومسميات وروابط أعمال دقيقة، وتجنب إدراج معلومات حساسة لا حاجة لها." }] },
    prepare: { eyebrow: "قبل البدء", title: "ما الذي ينبغي للمتقدم تجهيزه؟", text: "اجعل طلب الاهتمام الأول موجزاً ودقيقاً ومرتبطاً بالمجال.", items: ["سيرة ذاتية محدثة بصيغة PDF أو DOC أو DOCX", "شرح قصير للخبرات والاهتمامات ذات الصلة", "الموقع الحالي وبيانات اتصال واضحة دولياً", "رابط LinkedIn أو ملف أعمال اختياري بعنوان ويب كامل", "عدم إدراج وثائق هوية أو معلومات مالية أو سجلات حساسة غير مرتبطة"] },
    journey: { eyebrow: "رحلة التوظيف", title: "مسار واضح لتقديم الطلب", text: "تُرسل الطلبات بأمان لمراجعتها من مستخدمي إدارة علياس العقارية والموارد البشرية المخولين.", items: [{ title: "التجهيز", text: "أكمل التحقق من الحقول وراجع المعلومات التي تنوي مشاركتها." }, { title: "الإرسال الآمن", text: "يتم التحقق من الطلب والسيرة الذاتية الخاصة وتخزينهما خارج المسارات العامة." }, { title: "مراجعة الدور", text: "قد يُنظر في الطلب مقابل وظيفة مفتوحة أو احتياج مستقبلي مناسب، من دون وعد بنتيجة." }, { title: "التواصل مع المرشح", text: "يجب أن تُدار أي مقابلة أو خطوة مستقبلية من خلال إجراء توظيف معتمد." }] },
    application: { eyebrow: "طلب آمن", title: "أرسل طلب اهتمام عاماً", text: "تُرسل معلوماتك وسيرتك الذاتية بأمان لمراجعة فريق الموارد البشرية المخول." },
    privacy: { eyebrow: "إشعار بيانات المتقدم", title: "تبقى سيرتك الذاتية خاصة.", text: "لا تتاح معلومات الطلب إلا لمستخدمي إدارة علياس العقارية والموارد البشرية المخولين. ويمكن ضبط مدة الاحتفاظ بعد اعتماد سياسة المالك.", points: ["تُخزن بيانات النموذج والسيرة الذاتية بشكل خاص لمراجعة الطلب.", "لا تُدرج وثائق الهوية أو البيانات المصرفية أو معلومات شخصية حساسة لا حاجة لها.", "الموافقة التسويقية اختيارية ومنفصلة عن تقديم الطلب."] },
    faq: { eyebrow: "أسئلة الوظائف", title: "أسئلة عن طلبات الاهتمام", items: [{ question: "هل توجد وظائف شاغرة حالياً؟", answer: "تظهر الوظائف المفتوحة الموثقة عند توفرها، ويبقى الطلب العام متاحاً." }, { question: "هل يعني إكمال النموذج تقديم طلب؟", answer: "نعم. يعرض الإرسال الناجح رقماً مرجعياً ويخزن الطلب للمراجعة المخولة." }, { question: "ما صيغ الملفات المسموح بها؟", answer: "تُقبل ملفات PDF وDOC وDOCX حتى 5 ميغابايت بعد التحقق منها وتخزينها بشكل خاص." }, { question: "هل سأحصل على رد بعد التقديم؟", answer: "يؤكد الرقم المرجعي الاستلام، لكن لا يوجد وعد بمقابلة أو نتيجة أو وقت رد." }, { question: "ما المعلومات التي ينبغي تجنبها؟", answer: "لا تُدرج وثائق الهوية أو المعلومات المالية أو كلمات المرور أو بيانات شخصية حساسة لا علاقة لها بالطلب." }] },
    related: { title: "تعرّف أكثر قبل تجهيز الطلب", items: [{ href: "/ar/about", label: "عن علياس العقارية", text: "تعرّف إلى النهج المقصود وراء تجربة العملاء." }, { href: "/ar/contact", label: "التواصل", text: "استخدم نموذج التواصل العام للأسئلة غير المتعلقة بالتوظيف." }, { href: "/ar/off-plan", label: "خدمات على المخطط", text: "شاهد كيف يشرح الموقع رحلة عقارية مدروسة." }] },
    cta: { title: "هل تبحث عن حوار عقاري بدلاً من ذلك؟", text: "استخدم مسار التواصل الرئيسي للاستفسارات العقارية والخدمية بدلاً من نموذج الوظائف.", action: "انتقل إلى التواصل" },
    form: {
      required: "مطلوب", optional: "اختياري", fullName: "الاسم الكامل", email: "البريد الإلكتروني", phone: "رقم الهاتف", location: "الموقع الحالي", interest: "المجال أو الدور المطلوب", experience: "الخبرة ذات الصلة", coverMessage: "الرسالة التعريفية", cv: "ملف السيرة الذاتية", linkedin: "رابط ملف LinkedIn", portfolio: "رابط ملف الأعمال", languages: "اللغات", currentTitle: "المسمى الوظيفي الحالي", acknowledge: "أوافق على المعالجة الآمنة لهذا الطلب والسيرة الذاتية من مستخدمي إدارة علياس العقارية والموارد البشرية المخولين.", select: "اختر من القائمة", submit: "أرسل الطلب", reset: "مسح النموذج", removeFile: "إزالة الملف", fileHint: "PDF أو DOC أو DOCX؛ بحد أقصى ٥ ميغابايت.", localFileNote: "يُرفع الملف المحدد عند الإرسال فقط ويُخزن بشكل خاص.", selectedFile: "الملف المحدد", summaryTitle: "يرجى مراجعة الحقول المحددة", summaryIntro: "صحح العناصر التالية قبل إرسال الطلب.", validResult: "تم إرسال طلبك بأمان.",
      errors: { fullName: "أدخل اسمك الكامل.", email: "أدخل بريداً إلكترونياً صالحاً.", phone: "أدخل رقم هاتف محلياً أو دولياً بصيغة صالحة.", location: "أدخل موقعك الحالي.", interest: "اختر مجالاً أو دوراً مهنياً.", experience: "اختر نطاق خبرتك ذات الصلة.", coverMessage: "اكتب رسالة تعريفية لا تقل عن ٣٠ حرفاً.", cvRequired: "اختر ملف سيرة ذاتية بصيغة PDF أو DOC أو DOCX.", cvType: "اختر ملف PDF أو DOC أو DOCX صالحاً ومتوافقاً مع نوع الملف الظاهر في المتصفح.", cvSize: "يجب ألا يتجاوز ملف السيرة الذاتية ٥ ميغابايت.", linkedin: "أدخل رابط LinkedIn كاملاً يبدأ بـ http:// أو https://.", portfolio: "أدخل رابط ملف الأعمال كاملاً يبدأ بـ http:// أو https://.", acknowledge: "أكد موافقتك على المعالجة المخولة للطلب." },
    },
  },
};
