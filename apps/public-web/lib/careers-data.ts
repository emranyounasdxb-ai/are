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
  { value: "mid", label: { en: "3–5 years", ar: "من 3 إلى 5 سنوات" } },
  { value: "experienced", label: { en: "6–10 years", ar: "من 6 إلى 10 سنوات" } },
  { value: "senior", label: { en: "More than 10 years", ar: "أكثر من 10 سنوات" } },
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
    metaDescription: "Explore professional areas at ALIYAS Real Estate and prepare a frontend-only general expression of interest. No individual vacancy is currently published.",
    breadcrumb: "Careers",
    hero: { eyebrow: "Careers at ALIYAS", title: "Bring clarity, care and professional judgement to every conversation.", text: "Explore the areas where future opportunities may develop and prepare a general expression of interest. This page does not imply that a specific role is currently open.", note: "People-first work. Evidence-aware service. Bilingual ambition." },
    intro: { eyebrow: "A considered introduction", title: "Real estate work begins with understanding people and their priorities.", text: "ALIYAS Real Estate welcomes thoughtful expressions of interest from professionals who value clear communication, responsible handling of information and a considered customer experience. Individual roles will be published only when they are approved and ready for applications." },
    areas: { eyebrow: "Professional interests", title: "Where your experience may contribute", text: "These areas are general application interests, not advertised vacancies." },
    opportunities: { eyebrow: "Current opportunities", title: "Only verified roles will appear here.", emptyTitle: "No individual vacancy is currently published.", emptyText: "You may still prepare a general expression of interest. It will remain a local form preview until secure recruitment processing is separately approved and connected.", action: "Prepare a general application" },
    general: { eyebrow: "General expression of interest", title: "Share the professional context that helps explain your potential contribution.", text: "A useful general application is specific enough to understand, without assuming a vacancy, interview or outcome.", points: [{ title: "Choose a relevant area", text: "Select the professional area closest to your current experience or future direction." }, { title: "Explain your contribution", text: "Describe relevant work, transferable strengths and the kind of responsibility you are prepared to take on." }, { title: "Keep evidence clear", text: "Use accurate dates, role titles and portfolio links, and avoid including unnecessary sensitive information." }] },
    prepare: { eyebrow: "Before you begin", title: "What applicants should prepare", text: "Keep the first expression of interest concise, accurate and relevant.", items: ["An up-to-date CV in PDF, DOC or DOCX format", "A short explanation of relevant experience and interests", "Current location and internationally readable contact details", "Optional LinkedIn or portfolio links using a complete web address", "No identity documents, financial information or unrelated sensitive records"] },
    journey: { eyebrow: "Recruitment journey", title: "A transparent pathway for future approved recruitment", text: "The current page completes only the local preparation step. Later stages require an approved secure recruitment workflow.", items: [{ title: "Prepare", text: "Complete local form checks and review the information you intend to share." }, { title: "Secure submission", text: "This will become available only after the recruitment backend, access controls and privacy rules are approved." }, { title: "Role review", text: "Applications may be considered against a specific approved vacancy or a relevant future need; no review or response is promised by this preview." }, { title: "Candidate communication", text: "Any future interview or next step must be communicated through an approved recruitment process." }] },
    application: { eyebrow: "Application preview", title: "Prepare a general expression of interest", text: "The form validates locally in your browser. It does not send, upload, cache or retain your information or CV." },
    privacy: { eyebrow: "Applicant-data notice", title: "Your information stays on your device in this preview.", text: "Secure online application processing will be enabled only after the recruitment backend, access controls, retention rules and applicant privacy notice are approved.", points: ["No form data or file is submitted or retained.", "Do not include identity documents, banking details or other unnecessary sensitive information.", "A future live process will require separately approved privacy and access controls."] },
    faq: { eyebrow: "Careers FAQ", title: "Questions about expressions of interest", items: [{ question: "Are any roles currently open?", answer: "No individual vacancy is currently published on this page. Verified roles will be listed only after approval." }, { question: "Does completing this form submit an application?", answer: "No. It performs local browser checks only; nothing is transmitted or stored." }, { question: "Which file formats can I select?", answer: "The preview accepts PDF, DOC and DOCX files up to 5 MB and never reads or uploads their contents." }, { question: "Will I receive a response after using the preview?", answer: "No response is triggered because the form is not connected to a recruitment system or mailbox." }, { question: "What should I avoid including?", answer: "Do not include identity documents, financial information, passwords or unrelated sensitive personal records." }] },
    related: { title: "Learn more before applying", items: [{ href: "/en/about", label: "About ALIYAS", text: "Understand the intended approach behind the customer experience." }, { href: "/en/contact", label: "Contact", text: "Use the general contact preview for non-recruitment questions." }, { href: "/en/off-plan", label: "Off-plan services", text: "See how the website explains a considered property journey." }] },
    cta: { title: "Looking for a property conversation instead?", text: "Use the main contact route for property and service enquiries rather than the Careers form.", action: "Go to Contact" },
    form: {
      required: "Required", optional: "Optional", fullName: "Full name", email: "Email address", phone: "Phone number", location: "Current location", interest: "Area or role of interest", experience: "Relevant experience", coverMessage: "Cover message", cv: "CV file", linkedin: "LinkedIn profile URL", portfolio: "Portfolio URL", languages: "Languages", currentTitle: "Current job title", acknowledge: "I understand this is a local preview and that no application, information or file will be submitted or stored.", select: "Select an option", submit: "Check application details", reset: "Clear form", removeFile: "Remove file", fileHint: "PDF, DOC or DOCX; maximum 5 MB.", localFileNote: "The selected file remains on your device and is not read, uploaded or stored.", selectedFile: "Selected file", summaryTitle: "Please review the highlighted fields", summaryIntro: "Correct the following items before checking the application again.", validResult: "Your application details passed the local form checks. Online submission is not yet connected, and no information or file has been transmitted or stored.",
      errors: { fullName: "Enter your full name.", email: "Enter a valid email address.", phone: "Enter a valid international or local phone number.", location: "Enter your current location.", interest: "Select an area or role of interest.", experience: "Select your relevant experience range.", coverMessage: "Write a cover message of at least 30 characters.", cvRequired: "Select a PDF, DOC or DOCX CV file.", cvType: "Select a valid PDF, DOC or DOCX file whose file type matches its extension.", cvSize: "The CV file must not exceed 5 MB.", linkedin: "Enter a complete LinkedIn URL beginning with http:// or https://.", portfolio: "Enter a complete portfolio URL beginning with http:// or https://.", acknowledge: "Confirm that you understand the preview-only application notice." },
    },
  },
  ar: {
    metaTitle: "الوظائف في ALIYAS Real Estate | طلبات الاهتمام العامة",
    metaDescription: "تعرّف إلى المجالات المهنية في ALIYAS Real Estate وجهّز طلب اهتمام عاماً ضمن معاينة محلية لا ترسل البيانات. لا توجد وظيفة منشورة حالياً.",
    breadcrumb: "الوظائف",
    hero: { eyebrow: "الوظائف في ALIYAS", title: "أضف الوضوح والعناية والحكم المهني إلى كل حوار.", text: "تعرّف إلى المجالات التي قد تنشأ فيها فرص مستقبلية، وجهّز طلب اهتمام عاماً. لا تعني هذه الصفحة وجود وظيفة محددة شاغرة حالياً.", note: "عمل يتمحور حول الإنسان. خدمة واعية بالأدلة. طموح ثنائي اللغة." },
    intro: { eyebrow: "مقدمة مدروسة", title: "يبدأ العمل العقاري بفهم الناس وأولوياتهم.", text: "ترحب ALIYAS Real Estate بطلبات الاهتمام المدروسة من المهنيين الذين يقدّرون التواصل الواضح والتعامل المسؤول مع المعلومات وتجربة العميل المتوازنة. لن تُنشر الوظائف الفردية إلا بعد اعتمادها وجاهزيتها لاستقبال الطلبات." },
    areas: { eyebrow: "الاهتمامات المهنية", title: "مجالات قد تسهم فيها خبرتك", text: "هذه مجالات لطلبات الاهتمام العامة وليست إعلانات عن شواغر وظيفية." },
    opportunities: { eyebrow: "الفرص الحالية", title: "لن تظهر هنا إلا الوظائف الموثقة والمعتمدة.", emptyTitle: "لا توجد وظيفة محددة منشورة حالياً.", emptyText: "يمكنك مع ذلك تجهيز طلب اهتمام عام. وسيبقى نموذجاً محلياً للمعاينة إلى أن تُعتمد معالجة التوظيف الآمنة وتُربط بصورة مستقلة.", action: "جهّز طلباً عاماً" },
    general: { eyebrow: "طلب اهتمام عام", title: "شارك السياق المهني الذي يوضح القيمة التي قد تضيفها.", text: "يكون الطلب العام المفيد محدداً بما يكفي للفهم، من دون افتراض وجود شاغر أو مقابلة أو نتيجة.", points: [{ title: "اختر المجال المناسب", text: "حدّد المجال المهني الأقرب إلى خبرتك الحالية أو اتجاهك المستقبلي." }, { title: "وضّح مساهمتك", text: "اشرح الخبرات ذات الصلة والمهارات القابلة للنقل ونوع المسؤولية التي تستعد لتوليها." }, { title: "حافظ على دقة الأدلة", text: "استخدم تواريخ ومسميات وروابط أعمال دقيقة، وتجنب إدراج معلومات حساسة لا حاجة لها." }] },
    prepare: { eyebrow: "قبل البدء", title: "ما الذي ينبغي للمتقدم تجهيزه؟", text: "اجعل طلب الاهتمام الأول موجزاً ودقيقاً ومرتبطاً بالمجال.", items: ["سيرة ذاتية محدثة بصيغة PDF أو DOC أو DOCX", "شرح قصير للخبرات والاهتمامات ذات الصلة", "الموقع الحالي وبيانات اتصال واضحة دولياً", "رابط LinkedIn أو ملف أعمال اختياري بعنوان ويب كامل", "عدم إدراج وثائق هوية أو معلومات مالية أو سجلات حساسة غير مرتبطة"] },
    journey: { eyebrow: "رحلة التوظيف", title: "مسار واضح للتوظيف المعتمد مستقبلاً", text: "تنجز الصفحة الحالية خطوة التجهيز المحلي فقط. أما المراحل اللاحقة فتحتاج إلى مسار توظيف آمن ومعتمد.", items: [{ title: "التجهيز", text: "أكمل التحقق المحلي من الحقول وراجع المعلومات التي تنوي مشاركتها." }, { title: "الإرسال الآمن", text: "لن تتاح هذه الخطوة إلا بعد اعتماد الواجهة الخلفية للتوظيف وضوابط الوصول وقواعد الخصوصية." }, { title: "مراجعة الدور", text: "قد يُنظر في الطلب مقابل وظيفة معتمدة أو احتياج مستقبلي مناسب؛ ولا تعد هذه المعاينة بالمراجعة أو الرد." }, { title: "التواصل مع المرشح", text: "يجب أن تُدار أي مقابلة أو خطوة مستقبلية من خلال إجراء توظيف معتمد." }] },
    application: { eyebrow: "معاينة الطلب", title: "جهّز طلب اهتمام عاماً", text: "يتحقق النموذج محلياً داخل متصفحك، ولا يرسل معلوماتك أو سيرتك الذاتية ولا يرفعها أو يخزنها مؤقتاً أو يحتفظ بها." },
    privacy: { eyebrow: "إشعار بيانات المتقدم", title: "تبقى معلوماتك على جهازك في هذه المعاينة.", text: "لن تتاح معالجة طلبات التوظيف عبر الإنترنت إلا بعد اعتماد الواجهة الخلفية وضوابط الوصول وقواعد الاحتفاظ وإشعار خصوصية المتقدمين.", points: ["لا تُرسل بيانات النموذج أو الملف ولا يُحتفظ بها.", "لا تُدرج وثائق الهوية أو البيانات المصرفية أو معلومات شخصية حساسة لا حاجة لها.", "يتطلب المسار الفعلي المستقبلي ضوابط خصوصية ووصول معتمدة بصورة مستقلة."] },
    faq: { eyebrow: "أسئلة الوظائف", title: "أسئلة عن طلبات الاهتمام", items: [{ question: "هل توجد وظائف شاغرة حالياً؟", answer: "لا توجد وظيفة محددة منشورة في هذه الصفحة. ولن تُدرج الوظائف إلا بعد التحقق منها واعتمادها." }, { question: "هل يعني إكمال النموذج تقديم طلب؟", answer: "لا. يجري النموذج تحققات محلية داخل المتصفح فقط، ولا يرسل أو يخزن أي شيء." }, { question: "ما صيغ الملفات المسموح بها؟", answer: "تقبل المعاينة ملفات PDF وDOC وDOCX حتى 5 ميغابايت، ولا تقرأ محتوياتها أو ترفعها." }, { question: "هل سأحصل على رد بعد استخدام المعاينة؟", answer: "لا ينتج عنها أي رد لأن النموذج غير مرتبط بنظام توظيف أو بريد إلكتروني." }, { question: "ما المعلومات التي ينبغي تجنبها؟", answer: "لا تُدرج وثائق الهوية أو المعلومات المالية أو كلمات المرور أو بيانات شخصية حساسة لا علاقة لها بالطلب." }] },
    related: { title: "تعرّف أكثر قبل تجهيز الطلب", items: [{ href: "/ar/about", label: "عن ALIYAS", text: "تعرّف إلى النهج المقصود وراء تجربة العملاء." }, { href: "/ar/contact", label: "التواصل", text: "استخدم معاينة التواصل العامة للأسئلة غير المتعلقة بالتوظيف." }, { href: "/ar/off-plan", label: "خدمات على المخطط", text: "شاهد كيف يشرح الموقع رحلة عقارية مدروسة." }] },
    cta: { title: "هل تبحث عن حوار عقاري بدلاً من ذلك؟", text: "استخدم مسار التواصل الرئيسي للاستفسارات العقارية والخدمية بدلاً من نموذج الوظائف.", action: "انتقل إلى التواصل" },
    form: {
      required: "مطلوب", optional: "اختياري", fullName: "الاسم الكامل", email: "البريد الإلكتروني", phone: "رقم الهاتف", location: "الموقع الحالي", interest: "المجال أو الدور المطلوب", experience: "الخبرة ذات الصلة", coverMessage: "الرسالة التعريفية", cv: "ملف السيرة الذاتية", linkedin: "رابط ملف LinkedIn", portfolio: "رابط ملف الأعمال", languages: "اللغات", currentTitle: "المسمى الوظيفي الحالي", acknowledge: "أفهم أن هذه معاينة محلية وأنه لن يتم تقديم طلب أو إرسال أو تخزين أي معلومات أو ملف.", select: "اختر من القائمة", submit: "تحقق من تفاصيل الطلب", reset: "مسح النموذج", removeFile: "إزالة الملف", fileHint: "PDF أو DOC أو DOCX؛ بحد أقصى 5 ميغابايت.", localFileNote: "يبقى الملف المحدد على جهازك ولا تتم قراءة محتواه أو رفعه أو تخزينه.", selectedFile: "الملف المحدد", summaryTitle: "يرجى مراجعة الحقول المحددة", summaryIntro: "صحح العناصر التالية قبل التحقق من الطلب مرة أخرى.", validResult: "اجتازت تفاصيل طلبك التحققات المحلية في النموذج. لم يتم ربط الإرسال عبر الإنترنت بعد، ولم تُنقل أو تُخزن أي معلومات أو ملفات.",
      errors: { fullName: "أدخل اسمك الكامل.", email: "أدخل بريداً إلكترونياً صالحاً.", phone: "أدخل رقم هاتف محلياً أو دولياً بصيغة صالحة.", location: "أدخل موقعك الحالي.", interest: "اختر مجالاً أو دوراً مهنياً.", experience: "اختر نطاق خبرتك ذات الصلة.", coverMessage: "اكتب رسالة تعريفية لا تقل عن 30 حرفاً.", cvRequired: "اختر ملف سيرة ذاتية بصيغة PDF أو DOC أو DOCX.", cvType: "اختر ملف PDF أو DOC أو DOCX صالحاً ومتوافقاً مع نوع الملف الظاهر في المتصفح.", cvSize: "يجب ألا يتجاوز ملف السيرة الذاتية 5 ميغابايت.", linkedin: "أدخل رابط LinkedIn كاملاً يبدأ بـ http:// أو https://.", portfolio: "أدخل رابط ملف الأعمال كاملاً يبدأ بـ http:// أو https://.", acknowledge: "أكد فهمك لإشعار معاينة الطلب المحلية." },
    },
  },
};
