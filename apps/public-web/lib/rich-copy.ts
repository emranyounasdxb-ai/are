import type { ContentItem, FaqItem, RelatedItem } from "../components/content/editorial-content";
import type { Locale } from "./home-copy";
import type { PageSlug } from "./site-copy";

type PageRichCopy = Readonly<{
  intro: Readonly<{ eyebrow: string; title: string; text: string }>;
  sections: ReadonlyArray<Readonly<{ eyebrow: string; title: string; text: string; items: ReadonlyArray<ContentItem> }>>;
  checklist: Readonly<{ eyebrow: string; title: string; text: string; items: ReadonlyArray<string> }>;
  faq: Readonly<{ eyebrow: string; title: string; items: ReadonlyArray<FaqItem> }>;
  related: Readonly<{ title: string; items: ReadonlyArray<RelatedItem> }>;
  cta: Readonly<{ title: string; text: string; action: string; href: string }>;
}>;

type RichCopy = Readonly<{
  breadcrumb: string;
  homeLabel: string;
  home: PageRichCopy;
  pages: Readonly<Record<PageSlug, PageRichCopy>>;
}>;

const enRelated = {
  properties: { href: "/en/properties", label: "Properties", text: "Shape a search around purpose, place and home type." },
  communities: { href: "/en/communities", label: "Communities", text: "Compare places through the routines that matter to you." },
  offPlan: { href: "/en/off-plan", label: "Off-plan", text: "Prepare the questions behind an informed early-stage search." },
  about: { href: "/en/about", label: "About", text: "Understand the intended principles behind the experience." },
  contact: { href: "/en/contact", label: "Enquire", text: "Prepare a clear, useful property enquiry." },
} as const;

const arRelated = {
  properties: { href: "/ar/properties", label: "العقارات", text: "حدّد بحثك وفق الهدف والمكان ونوع المسكن." },
  communities: { href: "/ar/communities", label: "المجتمعات", text: "قارن الأماكن وفق تفاصيل الحياة اليومية المهمة لك." },
  offPlan: { href: "/ar/off-plan", label: "على المخطط", text: "حضّر الأسئلة اللازمة لبحث مبكر ومدروس." },
  about: { href: "/ar/about", label: "من نحن", text: "تعرّف إلى المبادئ المقصودة وراء هذه التجربة." },
  contact: { href: "/ar/contact", label: "استفسر", text: "جهّز استفساراً عقارياً واضحاً ومفيداً." },
} as const;

const richCopyBase = {
  en: {
    breadcrumb: "Breadcrumb",
    homeLabel: "Home",
    home: {
      intro: {
        eyebrow: "A PEOPLE-FIRST START",
        title: "Property discovery is easier when the brief comes before the shortlist.",
        text: "Begin with how you expect to live, what you need to reach and which questions remain open. This preview helps organise those priorities without presenting invented listings, prices or availability.",
      },
      sections: [
        {
          eyebrow: "YOUR DISCOVERY JOURNEY", title: "Four stages from broad intent to a useful conversation.",
          text: "Each stage narrows the question without rushing you toward a decision.",
          items: [
            { title: "Clarify your purpose", text: "Separate a home search, rental move and early-stage investment conversation so the next questions stay relevant." },
            { title: "Explore places", text: "Compare communities through daily routine, connections and preferred living character." },
            { title: "Shape a brief", text: "Record practical requirements, flexible preferences and points that still need evidence." },
            { title: "Prepare to enquire", text: "Share enough context for a useful response while keeping sensitive information out of an initial message." },
          ],
        },
        {
          eyebrow: "LIFESTYLE LENSES", title: "Look beyond a property type.",
          text: "A useful search also considers the rhythm around the home.",
          items: [
            { title: "Everyday routine", text: "Think about work patterns, household needs and the journeys you expect to repeat most often." },
            { title: "Space and flexibility", text: "Consider how rooms may need to support privacy, guests, work or changing family needs." },
            { title: "Community character", text: "Identify whether energy, calm, convenience or a particular setting matters most to you." },
            { title: "City connection", text: "List the destinations that shape your week and verify realistic routes when comparing areas." },
            { title: "Waterfront or urban setting", text: "Decide which surroundings support your preferences without assuming a particular property is available." },
            { title: "Long-term adaptability", text: "Consider which needs could change and which requirements should remain non-negotiable." },
          ],
        },
      ],
      checklist: {
        eyebrow: "BEFORE YOU ENQUIRE", title: "A simple checklist for a clearer first conversation.",
        text: "You do not need every answer. A few considered details can make the next step more focused.",
        items: ["Your intended purpose: buy, rent or explore off-plan", "A considered budget range, without sharing sensitive financial records", "Preferred areas or the destinations you need to reach", "Home type, space needs and useful flexibility", "An indicative timeframe rather than a forced deadline", "Essential lifestyle needs and questions requiring verification"],
      },
      faq: {
        eyebrow: "COMMON QUESTIONS", title: "Starting your UAE property discovery",
        items: [
          { question: "Can I explore both buying and renting?", answer: "Yes. The discovery search offers buying and renting pathways, while off-plan guidance is available as a separate early-stage journey." },
          { question: "Can I search without choosing a specific community?", answer: "Yes. You can begin across the UAE and refine the brief later as your location priorities become clearer." },
          { question: "Does the website show live property availability?", answer: "Not yet. This preview intentionally does not show inventory, prices, availability or result counts until an approved property-data source is connected." },
          { question: "How can I ask about off-plan opportunities?", answer: "Read the general off-plan guidance, organise the project-specific questions that need verification, then prepare an enquiry without including sensitive documents." },
          { question: "Is the experience available in Arabic?", answer: "Yes. The Arabic routes are written and structured as a complete right-to-left experience rather than a shortened companion page." },
        ],
      },
      related: { title: "Continue your discovery", items: [enRelated.communities, enRelated.offPlan, enRelated.contact] },
      cta: { title: "Ready to turn your priorities into a property brief?", text: "Explore the search pathway or prepare a concise enquiry when you are ready.", action: "Explore properties", href: "/en/properties" },
    },
    pages: {
      properties: {
        intro: { eyebrow: "DEFINE THE SEARCH", title: "Choose the journey before comparing options.", text: "Buying, renting and exploring off-plan opportunities create different questions. This page helps make those questions visible while approved live property data remains pending." },
        sections: [
          { eyebrow: "THREE JOURNEYS", title: "Start with the purpose behind the property.", text: "Use the path that best reflects your current intent.", items: [
            { title: "Buying a home", text: "Consider intended use, location priorities, space needs, timeframe and the professional advice you may need before committing." },
            { title: "Renting a home", text: "Focus on daily routine, household fit, practical terms and the evidence needed to understand the proposed tenancy." },
            { title: "Exploring off-plan", text: "Review timing, project information, payment milestones and due-diligence questions before treating an opportunity as comparable." },
          ]},
          { eyebrow: "COMPARE WITH CONTEXT", title: "Use a framework, not a single headline figure.", text: "A considered comparison keeps verified facts separate from assumptions.", items: [
            { title: "Apartment living", text: "Consider layout, shared access, building arrangements and how the home supports your routine." },
            { title: "Villa or townhouse space", text: "Think about privacy, outdoor areas, upkeep and how additional space would actually be used." },
            { title: "Layout and practical needs", text: "Review room relationships, storage, accessibility and household requirements rather than size alone." },
            { title: "Location and commute", text: "Compare the journeys and destinations that matter to your specific week using current sources." },
            { title: "Amenities and services", text: "Separate essential facilities from preferences and verify what is currently available and applicable." },
            { title: "Move-in timeframe", text: "Match verified availability or project milestones to your own flexibility without assuming a date." },
          ]},
          { eyebrow: "A PRACTICAL PROCESS", title: "From brief to evidence-led review.", text: "The process should remain understandable even before live inventory is available.", items: [
            { title: "Write the brief", text: "Separate essentials, preferences and open questions." },
            { title: "Request approved information", text: "Use verified sources for property, project, contractual and availability details." },
            { title: "Compare consistently", text: "Apply the same criteria to each suitable option instead of changing the standard mid-search." },
            { title: "Decide with appropriate advice", text: "Use qualified legal, financial or technical advice where your circumstances require it." },
          ]},
        ],
        checklist: { eyebrow: "SEARCH CONSIDERATIONS", title: "Details worth clarifying early", text: "These prompts help expose trade-offs before a shortlist becomes distracting.", items: ["Purpose and intended occupancy", "Preferred locations and recurring journeys", "Space, accessibility and household requirements", "Indicative timeframe and flexibility", "Documents and evidence needed for comparison", "Questions for qualified independent advisers"] },
        faq: { eyebrow: "PROPERTY FAQ", title: "Questions before you build a shortlist", items: [
          { question: "Are the properties on this page live listings?", answer: "No. No live inventory is presented. Results will appear only after an approved property-data source is connected." },
          { question: "How do I create a useful property brief?", answer: "Record your purpose, preferred places, essential space needs, flexible preferences, timeframe and questions that require verification." },
          { question: "Should I begin with price or location?", answer: "Begin with your complete situation rather than one factor alone. Location, use, space, timing and the full commitment should be considered together." },
          { question: "What information should I verify?", answer: "Verify the property or project details, availability, contractual documents, applicable costs and any claims relevant to your decision through approved sources." },
          { question: "Does this page provide legal or financial advice?", answer: "No. It offers general discovery guidance. Seek qualified independent advice for your circumstances before making a commitment." },
        ]},
        related: { title: "Explore the context around your search", items: [enRelated.communities, enRelated.offPlan, enRelated.contact] },
        cta: { title: "Have a clearer property brief?", text: "Prepare an enquiry with your purpose, preferred area and the questions you want answered.", action: "Prepare an enquiry", href: "/en/contact" },
      },
      communities: {
        intro: { eyebrow: "PLACE BEFORE PROPERTY", title: "A community shapes the routines around a home.", text: "Explore a place through how you may use it, not through unverified rankings or generic claims. The right questions depend on your household and daily priorities." },
        sections: [
          { eyebrow: "WHAT MATTERS TO YOU", title: "Turn lifestyle preferences into practical questions.", text: "The same location can work differently for different households.", items: [
            { title: "Connection", text: "List the workplaces, schools, services or people you expect to reach regularly, then verify realistic routes for your schedule." },
            { title: "Daily convenience", text: "Identify which everyday services matter and confirm current details from approved sources." },
            { title: "Living character", text: "Consider activity, privacy, landscape and the mix of home types that may suit your preferred rhythm." },
          ]},
          { eyebrow: "SPACE AND ROUTINE", title: "Test a place against an ordinary week.", text: "A useful comparison includes mornings, evenings and weekends—not only a first impression.", items: [
            { title: "Weekday pattern", text: "Map regular departures, returns and household handovers." },
            { title: "Time at home", text: "Think about work, rest, guests and how shared or private spaces may be used." },
            { title: "Future flexibility", text: "Note which needs may change and what would remain essential." },
          ]},
          { eyebrow: "COMMUNITY DISCOVERY", title: "A simple exploration process.", text: "Move from broad interest to verified, personal relevance.", items: [
            { title: "Prioritise", text: "Choose the three or four community qualities that matter most." },
            { title: "Compare", text: "Apply the same questions to each place you are considering." },
            { title: "Verify", text: "Confirm current facilities, access, rules and other specific claims through approved information." },
            { title: "Revisit", text: "Where practical, experience the place at times that reflect your likely routine." },
          ]},
        ],
        checklist: { eyebrow: "QUESTIONS TO ASK", title: "A community-comparison checklist", text: "Use these prompts as a starting point, then add what is unique to your household.", items: ["Which journeys will be repeated most often?", "What level of activity or privacy feels comfortable?", "Which facilities are essential and which are optional?", "How might space needs change over time?", "Which current details need direct verification?"] },
        faq: { eyebrow: "COMMUNITY FAQ", title: "Exploring where to live", items: [
          { question: "What makes a community suitable?", answer: "Suitability is personal. Compare daily journeys, household routines, setting, space needs and verified practical details against your own priorities." },
          { question: "Are travel times shown here?", answer: "No. Travel times change with route, time and conditions, so this preview does not invent them. Check current journeys using an appropriate live source." },
          { question: "How many communities should I compare?", answer: "There is no fixed number. A small, relevant set assessed against consistent criteria is often more useful than a long unstructured list." },
          { question: "Should I visit before choosing?", answer: "Where practical, seeing a place at times that reflect your routine can add context that descriptions cannot provide." },
          { question: "Where can I start a property search?", answer: "Use the Properties page to define purpose, location and home type, then prepare an enquiry if you need approved information." },
        ]},
        related: { title: "Connect place and property", items: [enRelated.properties, enRelated.about, enRelated.contact] },
        cta: { title: "Know what you need from a community?", text: "Use those priorities to shape a more focused property brief.", action: "Build a property brief", href: "/en/properties" },
      },
      "off-plan": {
        intro: { eyebrow: "UNDERSTAND THE ROUTE", title: "Off-plan means considering a property before completion.", text: "That early stage can involve specific timelines, documents and obligations. Begin with your purpose and the evidence you need, and obtain qualified independent advice where appropriate." },
        sections: [
          { eyebrow: "PURPOSE AND TIMEFRAME", title: "Clarify why this route is relevant to you.", text: "A personal-use plan and an investment objective may require different questions and professional advice.", items: [
            { title: "Intended use", text: "Define whether you are exploring a future home, another purpose or are still learning about the route." },
            { title: "Time horizon", text: "Consider how project milestones and your own plans may interact, without assuming dates that have not been verified." },
            { title: "Capacity for commitment", text: "Understand the wider obligations and seek appropriate advice before treating an indicative plan as affordable or suitable." },
          ]},
          { eyebrow: "INFORMATION TO REVIEW", title: "Ask for approved documents, not just highlights.", text: "The exact requirements depend on the project and your circumstances.", items: [
            { title: "Project and developer information", text: "Verify the identities, approvals and project details using current authoritative sources." },
            { title: "Contractual documents", text: "Read the applicable agreement, specifications, rights and obligations, with independent legal advice when needed." },
            { title: "Payment and milestone information", text: "Understand the documented schedule, triggers and your responsibilities; do not rely on an illustrative summary alone." },
          ]},
          { eyebrow: "A CONSIDERED PATH", title: "From initial interest to due diligence.", text: "Each step should reduce uncertainty rather than create urgency.", items: [
            { title: "Define the objective", text: "Write down intended use, timeframe and unresolved questions." },
            { title: "Request evidence", text: "Collect current approved project, developer and contractual information." },
            { title: "Review the full commitment", text: "Consider documented milestones, responsibilities, changes and relevant costs." },
            { title: "Seek independent advice", text: "Use qualified legal, financial or technical advisers for matters outside general property discovery." },
          ]},
        ],
        checklist: { eyebrow: "BUYER QUESTIONS", title: "Questions to carry into an off-plan conversation", text: "These are general prompts, not a substitute for project-specific due diligence.", items: ["What is verified and what remains indicative?", "Which documents govern the proposed purchase?", "What milestones, obligations and change provisions apply?", "Which claims need confirmation from an authoritative source?", "Which independent advisers should review my circumstances?"] },
        faq: { eyebrow: "OFF-PLAN FAQ", title: "General questions about early-stage discovery", items: [
          { question: "What does off-plan property mean?", answer: "It generally refers to property considered before construction is complete. The specific status, documents and obligations must be verified for each project." },
          { question: "Does this page list approved projects?", answer: "No. It provides general discovery guidance only and does not present project inventory, prices, completion dates or availability." },
          { question: "What should I review before proceeding?", answer: "Request current project, developer, contractual, payment and milestone information, and seek qualified advice appropriate to your situation." },
          { question: "Are completion dates guaranteed?", answer: "This preview makes no completion claim. Review the applicable approved documents and obtain advice on the terms relevant to a particular project." },
          { question: "Is this legal or investment advice?", answer: "No. It is general educational content. Decisions should be based on verified information and advice from appropriately qualified professionals." },
        ]},
        related: { title: "Continue with context", items: [enRelated.properties, enRelated.communities, enRelated.contact] },
        cta: { title: "Have project-specific questions to organise?", text: "Prepare an enquiry that separates your priorities from the information still needing verification.", action: "Prepare your questions", href: "/en/contact" },
      },
      about: {
        intro: { eyebrow: "WHO WE ARE", title: "A clearer path through property discovery.", text: "ALIYAS Real Estate is developing a bilingual UAE property experience intended to begin with the customer’s purpose and present information honestly as approved capabilities become available." },
        sections: [
          { eyebrow: "OUR PURPOSE", title: "Help people ask better questions before the next step.", text: "The current experience is intentionally honest about what is available now and what remains to be connected.", items: [
            { title: "Listen before presenting", text: "Start with intended use, routine, priorities and uncertainty rather than a predetermined shortlist." },
            { title: "Separate fact from preview", text: "Identify verified information clearly and do not represent illustrative content as property truth." },
            { title: "Make the pathway understandable", text: "Give each page a useful purpose, clear next step and equivalent English and Arabic experience." },
          ]},
          { eyebrow: "BILINGUAL BY DESIGN", title: "English and Arabic should carry equal meaning.", text: "Arabic is treated as a professional right-to-left product experience, not a shortened translation added after the interface is complete.", items: [
            { title: "Content parity", text: "Core guidance, cautions, links and interactions are available in both languages." },
            { title: "Interface parity", text: "Direction, navigation order, controls and visual flow adapt without losing meaning." },
            { title: "Editorial quality", text: "Natural Arabic phrasing takes priority over literal word-for-word substitution." },
          ]},
          { eyebrow: "CAPABILITY ROADMAP", title: "Grow only when approved foundations are ready.", text: "The public preview establishes discovery pathways. Data-driven capabilities remain visibly pending until their sources and contracts are approved.", items: [
            { title: "Available now", text: "Bilingual navigation, page guidance, search-brief routing and a non-transmitting enquiry preview." },
            { title: "Pending approved data", text: "Live property inventory, prices, availability, result counts and project records." },
            { title: "Future governed growth", text: "Additional capabilities should follow the approved architecture, content authority and validation gates." },
          ]},
        ],
        checklist: { eyebrow: "OUR CONTENT STANDARD", title: "What this preview will not invent", text: "Trust begins by making the limits of the current product visible.", items: ["Property records, projects, prices or availability", "Market statistics, rankings or investment returns", "Contact details or service claims without owner approval", "Travel times, facility claims or guarantees without verification", "Legal, financial or contractual advice"] },
        faq: { eyebrow: "ABOUT FAQ", title: "Understanding the current ARE experience", items: [
          { question: "What is ALIYAS Real Estate building?", answer: "A bilingual UAE property-discovery experience with separate public and administrative foundations, designed to connect approved data and services in later authorised phases." },
          { question: "Is all property information live?", answer: "No. The current public experience does not represent live inventory. It clearly marks data-driven capabilities as pending." },
          { question: "Why is the experience bilingual?", answer: "English and Arabic parity is a core product requirement, intended to make the same pathways and cautions understandable in both languages." },
          { question: "How is content kept trustworthy?", answer: "The preview avoids invented business facts and separates verified, pending and illustrative information." },
          { question: "How can I begin?", answer: "Explore properties or communities to shape your needs, then use the contact preview to prepare a concise enquiry." },
        ]},
        related: { title: "See the approach in practice", items: [enRelated.properties, enRelated.communities, enRelated.contact] },
        cta: { title: "Begin with what matters to you.", text: "Shape a property brief or prepare the questions you would like to explore.", action: "Start discovering", href: "/en/properties" },
      },
      contact: {
        intro: { eyebrow: "CHOOSE AN ENQUIRY TYPE", title: "Give the conversation a useful starting point.", text: "Select the purpose that best matches your question, then share only the context needed for an initial response. This local preview validates the form but sends and stores nothing." },
        sections: [
          { eyebrow: "WHAT TO INCLUDE", title: "A short brief is more useful than a long unstructured message.", text: "Keep the first enquiry focused and avoid sensitive information.", items: [
            { title: "Purpose", text: "Say whether you want to buy, rent, compare communities, explore off-plan or ask a general question." },
            { title: "Preferred location", text: "Name an area when you have one, or describe the destinations you need to reach." },
            { title: "Budget range", text: "Share a broad considered range only if useful; do not include banking or financial documents." },
            { title: "Property type", text: "Describe the home type, space and practical requirements relevant to your household." },
            { title: "Timeframe", text: "Give an indicative timeframe and explain where you have flexibility." },
            { title: "Important requirements", text: "Identify essential lifestyle needs and questions that still require verified information." },
          ]},
          { eyebrow: "WHAT HAPPENS NEXT", title: "This preview stops before transmission.", text: "A future approved phase may connect secure enquiry handling. Until then, the form proves the interaction only.", items: [
            { title: "Review", text: "The browser checks that the required fields are complete and that the message has useful minimum detail." },
            { title: "Preview confirmation", text: "A clear message explains that no information was sent or stored." },
            { title: "Future routing", text: "Secure submission, response times and operational contact details remain pending owner-approved implementation." },
          ]},
        ],
        checklist: { eyebrow: "PRIVACY GUIDANCE", title: "Keep sensitive information out of an initial enquiry", text: "Share only what is necessary to describe the question.", items: ["Do not include passport or identity-document numbers", "Do not include banking, card or account information", "Do not send passwords, access codes or private credentials", "Avoid detailed personal records unless a secure approved process requests them", "Verify the recipient and purpose before sharing documents"] },
        faq: { eyebrow: "CONTACT FAQ", title: "Preparing an enquiry", items: [
          { question: "Does this form send my information?", answer: "No. In this local preview it validates the fields and displays a confirmation, but it does not transmit or store the information." },
          { question: "What enquiry types can I choose?", answer: "You can prepare a buying, renting, community, off-plan or general property enquiry." },
          { question: "What should I write in the message?", answer: "Include your purpose, broad location or property preferences, indicative timeframe and the questions you want answered." },
          { question: "Should I attach personal documents?", answer: "No. This preview has no upload function, and sensitive documents should never be included in an initial unsecured enquiry." },
          { question: "When will I receive a response?", answer: "No response time is claimed because this preview does not submit enquiries. Operational routing remains pending an approved phase." },
        ]},
        related: { title: "Prepare before you enquire", items: [enRelated.properties, enRelated.communities, enRelated.offPlan] },
        cta: { title: "Want to refine your brief first?", text: "Return to property discovery and organise the criteria that matter most.", action: "Explore properties", href: "/en/properties" },
      },
    },
  },
  ar: {
    breadcrumb: "مسار التنقل",
    homeLabel: "الرئيسية",
    home: {
      intro: { eyebrow: "بداية تتمحور حول الإنسان", title: "يصبح اكتشاف العقار أوضح عندما يسبق الموجزُ القائمةَ المختصرة.", text: "ابدأ بطريقة الحياة التي تتطلع إليها، والوجهات المهمة لك، والأسئلة التي لا تزال مفتوحة. تساعدك هذه المعاينة على تنظيم الأولويات من دون عرض عقارات أو أسعار أو حالات توفر غير موثقة." },
      sections: [
        { eyebrow: "رحلة الاكتشاف", title: "أربع مراحل من الفكرة العامة إلى حوار مفيد.", text: "تضيّق كل مرحلة نطاق البحث من دون دفعك إلى قرار متسرع.", items: [
          { title: "حدّد هدفك", text: "ميّز بين شراء منزل أو استئجاره أو استكشاف العقارات على المخطط لتبقى الأسئلة التالية مرتبطة باحتياجك." },
          { title: "استكشف الأماكن", text: "قارن المجتمعات وفق الروتين اليومي وسهولة الوصول وطابع المعيشة المفضل." },
          { title: "صُغ موجزك", text: "سجّل المتطلبات العملية والتفضيلات المرنة والنقاط التي تحتاج إلى معلومات موثقة." },
          { title: "استعد للاستفسار", text: "شارك سياقاً كافياً للحصول على رد مفيد، وتجنب المعلومات الحساسة في الرسالة الأولى." },
        ]},
        { eyebrow: "زوايا أسلوب الحياة", title: "انظر إلى ما هو أبعد من نوع العقار.", text: "يشمل البحث المفيد إيقاع الحياة المحيط بالمنزل.", items: [
          { title: "الروتين اليومي", text: "فكّر في نمط العمل واحتياجات الأسرة والرحلات التي ستتكرر غالباً." },
          { title: "المساحة والمرونة", text: "حدّد كيف يمكن للغرف أن تدعم الخصوصية أو الضيوف أو العمل أو تغير احتياجات الأسرة." },
          { title: "طابع المجتمع", text: "حدّد ما إذا كانت الحيوية أو الهدوء أو السهولة أو البيئة المحيطة هي الأهم لك." },
          { title: "سهولة الوصول إلى المدينة", text: "حدّد الوجهات التي تشكل أسبوعك وتحقق من المسارات الواقعية عند مقارنة المناطق." },
          { title: "بيئة مائية أو حضرية", text: "اختر البيئة التي تلائم تفضيلاتك من دون افتراض توفر عقار بعينه." },
          { title: "المرونة على المدى البعيد", text: "فكّر في الاحتياجات التي قد تتغير والمتطلبات التي يجب أن تبقى أساسية." },
        ]},
      ],
      checklist: { eyebrow: "قبل الاستفسار", title: "قائمة بسيطة لحوار أول أكثر وضوحاً.", text: "لست بحاجة إلى كل الإجابات؛ بعض التفاصيل المدروسة تكفي لجعل الخطوة التالية أكثر تركيزاً.", items: ["الهدف: شراء أو استئجار أو استكشاف عقار على المخطط", "نطاق ميزانية مدروس من دون مشاركة سجلات مالية حساسة", "المناطق المفضلة أو الوجهات التي تحتاج إلى الوصول إليها", "نوع المنزل ومتطلبات المساحة والمرونة", "إطار زمني تقريبي من دون فرض موعد مصطنع", "احتياجات الحياة الأساسية والأسئلة التي تتطلب تحققاً"] },
      faq: { eyebrow: "أسئلة شائعة", title: "بدء رحلة اكتشاف العقار في الإمارات", items: [
        { question: "هل يمكنني استكشاف الشراء والاستئجار معاً؟", answer: "نعم. يوفر بحث الاكتشاف مساري الشراء والاستئجار، بينما يتوفر إرشاد مستقل للعقارات على المخطط." },
        { question: "هل يمكنني البحث من دون اختيار مجتمع محدد؟", answer: "نعم. يمكنك البدء على مستوى الإمارات ثم تضييق الموجز عندما تصبح أولويات الموقع أوضح." },
        { question: "هل يعرض الموقع توفر العقارات مباشرة؟", answer: "ليس بعد. لا تعرض المعاينة مخزوناً أو أسعاراً أو توفراً أو أعداد نتائج إلى أن يتم ربط مصدر بيانات عقارية معتمد." },
        { question: "كيف أسأل عن فرص العقارات على المخطط؟", answer: "اقرأ الإرشاد العام ونظّم الأسئلة الخاصة بالمشروع التي تحتاج إلى تحقق، ثم جهّز استفساراً من دون وثائق حساسة." },
        { question: "هل التجربة متاحة باللغة العربية؟", answer: "نعم. صيغت المسارات العربية كتجربة كاملة من اليمين إلى اليسار وليست نسخة مختصرة." },
      ]},
      related: { title: "تابع رحلة الاكتشاف", items: [arRelated.communities, arRelated.offPlan, arRelated.contact] },
      cta: { title: "هل أنت مستعد لتحويل أولوياتك إلى موجز عقاري؟", text: "استكشف مسار البحث أو جهّز استفساراً موجزاً عندما تكون مستعداً.", action: "استكشف العقارات", href: "/ar/properties" },
    },
    pages: {},
  },
};

// Arabic inner-page content mirrors the English information architecture with professional RTL copy.
const arPages: Record<PageSlug, PageRichCopy> = {
  properties: {
    intro: { eyebrow: "حدّد نطاق البحث", title: "اختر المسار قبل مقارنة الخيارات.", text: "يفتح الشراء والاستئجار والعقار على المخطط أسئلة مختلفة. تساعدك الصفحة على إظهارها بوضوح بينما تبقى بيانات العقارات المباشرة قيد الاعتماد." },
    sections: [
      { eyebrow: "ثلاثة مسارات", title: "ابدأ بالهدف من العقار.", text: "اختر المسار الأقرب إلى نيتك الحالية.", items: [
        { title: "شراء منزل", text: "فكّر في الاستخدام والموقع والمساحة والإطار الزمني والمشورة المهنية التي قد تحتاج إليها قبل الالتزام." },
        { title: "استئجار منزل", text: "ركّز على الروتين اليومي وملاءمة المنزل والشروط العملية والمعلومات اللازمة لفهم عقد الإيجار المقترح." },
        { title: "استكشاف عقار على المخطط", text: "راجع التوقيت ومعلومات المشروع ومراحل الدفع وأسئلة العناية الواجبة قبل المقارنة." },
      ]},
      { eyebrow: "مقارنة ضمن السياق", title: "استخدم إطاراً متكاملاً لا رقماً واحداً.", text: "تفصل المقارنة المدروسة الحقائق الموثقة عن الافتراضات.", items: [
        { title: "السكن في شقة", text: "فكّر في التصميم والمداخل المشتركة وترتيبات المبنى ومدى دعم المنزل لروتينك." },
        { title: "مساحة الفيلا أو التاون هاوس", text: "راجع الخصوصية والمساحات الخارجية والصيانة وكيف ستستخدم المساحة الإضافية فعلياً." },
        { title: "التصميم والاحتياجات العملية", text: "قارن ترابط الغرف والتخزين وسهولة الوصول واحتياجات الأسرة، لا المساحة وحدها." },
        { title: "الموقع والتنقل", text: "قارن الرحلات والوجهات المهمة لأسبوعك باستخدام مصادر حالية." },
        { title: "المرافق والخدمات", text: "افصل الضروري عن المفضل وتحقق مما هو متاح ومطبق حالياً." },
        { title: "موعد الانتقال", text: "وازن التوفر الموثق أو مراحل المشروع مع مرونتك من دون افتراض موعد." },
      ]},
      { eyebrow: "مسار عملي", title: "من الموجز إلى مراجعة تستند إلى الأدلة.", text: "يجب أن يبقى المسار مفهوماً حتى قبل توفر المخزون المباشر.", items: [
        { title: "اكتب الموجز", text: "افصل بين الضروريات والتفضيلات والأسئلة المفتوحة." }, { title: "اطلب المعلومات المعتمدة", text: "اعتمد على مصادر موثقة لتفاصيل العقار أو المشروع والعقود والتوفر." }, { title: "قارن بمعيار ثابت", text: "طبّق المعايير نفسها على كل خيار مناسب." }, { title: "استعن بالمشورة المناسبة", text: "اطلب مشورة قانونية أو مالية أو فنية مؤهلة عندما تتطلب ظروفك ذلك." },
      ]},
    ],
    checklist: { eyebrow: "اعتبارات البحث", title: "تفاصيل تستحق التوضيح مبكراً", text: "تكشف هذه النقاط أوجه المفاضلة قبل أن تشتت القائمة المختصرة تركيزك.", items: ["الهدف والاستخدام المقصود", "المواقع والرحلات المتكررة", "المساحة وسهولة الوصول واحتياجات الأسرة", "الإطار الزمني والمرونة", "الوثائق والمعلومات اللازمة للمقارنة", "أسئلة للمستشارين المستقلين المؤهلين"] },
    faq: { eyebrow: "أسئلة العقارات", title: "قبل إعداد القائمة المختصرة", items: [
      { question: "هل العقارات في هذه الصفحة قوائم مباشرة؟", answer: "لا. لن تظهر النتائج إلا بعد ربط مصدر بيانات عقارية معتمد." }, { question: "كيف أنشئ موجزاً مفيداً؟", answer: "سجّل الهدف والمواقع واحتياجات المساحة والتفضيلات المرنة والإطار الزمني والأسئلة التي تحتاج إلى تحقق." }, { question: "هل أبدأ بالسعر أم بالموقع؟", answer: "ابدأ بالصورة الكاملة؛ يجب النظر إلى الموقع والاستخدام والمساحة والتوقيت والالتزام معاً." }, { question: "ما المعلومات التي يجب التحقق منها؟", answer: "تحقق من تفاصيل العقار أو المشروع والتوفر والعقود والتكاليف وأي ادعاءات مؤثرة عبر مصادر معتمدة." }, { question: "هل تقدم الصفحة مشورة قانونية أو مالية؟", answer: "لا. تقدم إرشاداً عاماً للاكتشاف، وينبغي طلب مشورة مستقلة مؤهلة قبل الالتزام." },
    ]},
    related: { title: "استكشف سياق بحثك", items: [arRelated.communities, arRelated.offPlan, arRelated.contact] },
    cta: { title: "هل أصبح موجزك أوضح؟", text: "جهّز استفساراً يتضمن هدفك والمنطقة والأسئلة التي تريد الإجابة عنها.", action: "جهّز استفسارك", href: "/ar/contact" },
  },
  communities: {
    intro: { eyebrow: "المكان قبل العقار", title: "يشكّل المجتمع تفاصيل الحياة حول المنزل.", text: "استكشف المكان وفق طريقة استخدامك له، بعيداً عن التصنيفات غير الموثقة. تعتمد الأسئلة الصحيحة على أسرتك وأولوياتك اليومية." },
    sections: [
      { eyebrow: "ما يهمك", title: "حوّل تفضيلات الحياة إلى أسئلة عملية.", text: "قد يلائم المكان نفسه أسراً مختلفة بطرق مختلفة.", items: [
        { title: "سهولة الوصول", text: "حدّد أماكن العمل أو المدارس أو الخدمات أو الأشخاص الذين تزورهم بانتظام، ثم تحقق من المسارات الواقعية." }, { title: "الاحتياجات اليومية", text: "حدّد الخدمات التي تهمك وتحقق من تفاصيلها الحالية عبر مصادر معتمدة." }, { title: "طابع المعيشة", text: "فكّر في الحيوية والخصوصية والبيئة وأنواع المساكن الملائمة لإيقاعك." },
      ]},
      { eyebrow: "المساحة والروتين", title: "اختبر المكان على أسبوع عادي.", text: "تشمل المقارنة المفيدة الصباح والمساء وعطلة نهاية الأسبوع.", items: [
        { title: "نمط أيام العمل", text: "ارسم مواعيد المغادرة والعودة وتنقلات الأسرة المعتادة." }, { title: "الوقت في المنزل", text: "فكّر في العمل والراحة والضيوف واستخدام المساحات المشتركة والخاصة." }, { title: "المرونة المستقبلية", text: "دوّن الاحتياجات التي قد تتغير وما سيبقى ضرورياً." },
      ]},
      { eyebrow: "اكتشاف المجتمع", title: "عملية استكشاف بسيطة.", text: "انتقل من الاهتمام العام إلى الملاءمة الشخصية الموثقة.", items: [
        { title: "رتّب الأولويات", text: "اختر ثلاث أو أربع صفات هي الأهم." }, { title: "قارن", text: "استخدم الأسئلة نفسها لكل مكان." }, { title: "تحقق", text: "أكد المرافق وسهولة الوصول والقواعد الحالية من معلومات معتمدة." }, { title: "أعد الزيارة", text: "حيثما أمكن، اختبر المكان في أوقات تشبه روتينك." },
      ]},
    ],
    checklist: { eyebrow: "أسئلة مفيدة", title: "قائمة لمقارنة المجتمعات", text: "ابدأ بهذه النقاط ثم أضف ما يخص أسرتك.", items: ["ما الرحلات الأكثر تكراراً؟", "ما مستوى الحيوية أو الخصوصية الملائم؟", "ما المرافق الضرورية وما الاختياري؟", "كيف قد تتغير احتياجات المساحة؟", "ما التفاصيل الحالية التي تحتاج إلى تحقق مباشر؟"] },
    faq: { eyebrow: "أسئلة المجتمعات", title: "استكشاف مكان السكن", items: [
      { question: "ما الذي يجعل المجتمع مناسباً؟", answer: "الملاءمة شخصية؛ قارن الرحلات والروتين والبيئة والمساحة والتفاصيل العملية الموثقة بأولوياتك." }, { question: "هل تعرض الصفحة أوقات التنقل؟", answer: "لا، لأنها تتغير حسب المسار والوقت والظروف. تحقق منها عبر مصدر مباشر مناسب." }, { question: "كم مجتمعاً ينبغي أن أقارن؟", answer: "لا يوجد عدد ثابت؛ مجموعة صغيرة وذات صلة وفق معايير ثابتة أفضل من قائمة طويلة بلا تنظيم." }, { question: "هل أزور المكان قبل الاختيار؟", answer: "حيثما أمكن، تضيف الزيارة في أوقات تشبه روتينك سياقاً لا توفره الأوصاف." }, { question: "أين أبدأ البحث عن عقار؟", answer: "استخدم صفحة العقارات لتحديد الهدف والموقع ونوع المنزل ثم جهّز استفساراً عند الحاجة." },
    ]},
    related: { title: "اربط المكان بالعقار", items: [arRelated.properties, arRelated.about, arRelated.contact] },
    cta: { title: "هل عرفت ما تحتاج إليه من المجتمع؟", text: "استخدم تلك الأولويات لصياغة موجز عقاري أكثر تركيزاً.", action: "أنشئ موجزاً", href: "/ar/properties" },
  },
  "off-plan": {
    intro: { eyebrow: "افهم المسار", title: "العقار على المخطط يعني دراسة عقار قبل اكتماله.", text: "قد تنطوي هذه المرحلة على جداول ووثائق والتزامات محددة. ابدأ بهدفك والمعلومات التي تحتاج إليها، واطلب مشورة مستقلة مؤهلة عند الحاجة." },
    sections: [
      { eyebrow: "الهدف والإطار الزمني", title: "وضّح سبب ملاءمة هذا المسار لك.", text: "قد يتطلب المنزل المستقبلي والهدف الاستثماري أسئلة ومشورة مختلفة.", items: [
        { title: "الاستخدام المقصود", text: "حدّد ما إذا كنت تستكشف منزلاً مستقبلياً أو غرضاً آخر أو تتعرف إلى المسار." }, { title: "الأفق الزمني", text: "فكّر في تفاعل مراحل المشروع مع خططك من دون افتراض مواعيد غير موثقة." }, { title: "القدرة على الالتزام", text: "افهم الالتزامات الأوسع واطلب المشورة المناسبة قبل اعتبار أي خطة ملائمة." },
      ]},
      { eyebrow: "المعلومات المطلوبة", title: "اطلب الوثائق المعتمدة لا العناوين الجذابة فقط.", text: "تختلف المتطلبات الدقيقة حسب المشروع وظروفك.", items: [
        { title: "معلومات المشروع والمطور", text: "تحقق من الهوية والموافقات والتفاصيل عبر مصادر رسمية حالية." }, { title: "الوثائق التعاقدية", text: "اقرأ الاتفاق والمواصفات والحقوق والالتزامات مع مشورة قانونية مستقلة عند الحاجة." }, { title: "الدفعات والمراحل", text: "افهم الجدول الموثق ومحفزاته ومسؤولياتك، ولا تعتمد على ملخص توضيحي وحده." },
      ]},
      { eyebrow: "مسار مدروس", title: "من الاهتمام إلى العناية الواجبة.", text: "يجب أن تقلل كل خطوة عدم اليقين بدلاً من خلق استعجال.", items: [
        { title: "حدّد الهدف", text: "اكتب الاستخدام والتوقيت والأسئلة المفتوحة." }, { title: "اطلب الأدلة", text: "اجمع معلومات المشروع والمطور والعقود المعتمدة." }, { title: "راجع الالتزام كاملاً", text: "ادرس المراحل والمسؤوليات والتغييرات والتكاليف ذات الصلة." }, { title: "استعن بمشورة مستقلة", text: "ارجع إلى مختصين قانونيين أو ماليين أو فنيين مؤهلين." },
      ]},
    ],
    checklist: { eyebrow: "أسئلة المشتري", title: "أسئلة لحوار العقار على المخطط", text: "هي نقاط عامة وليست بديلاً عن العناية الواجبة الخاصة بالمشروع.", items: ["ما الموثق وما الذي لا يزال تقريبياً؟", "ما الوثائق التي تحكم الشراء المقترح؟", "ما المراحل والالتزامات وأحكام التغيير؟", "ما الادعاءات التي تحتاج إلى مصدر رسمي؟", "من المستشارون المستقلون المناسبون لظروفي؟"] },
    faq: { eyebrow: "أسئلة العقار على المخطط", title: "أسئلة عامة عن الاكتشاف المبكر", items: [
      { question: "ما معنى عقار على المخطط؟", answer: "يشير عموماً إلى عقار تتم دراسته قبل اكتمال بنائه، ويجب التحقق من حالته ووثائقه والتزاماته لكل مشروع." }, { question: "هل تعرض الصفحة مشاريع معتمدة؟", answer: "لا. تقدم إرشاداً عاماً ولا تعرض مشاريع أو أسعاراً أو مواعيد إنجاز أو توفراً." }, { question: "ماذا أراجع قبل المتابعة؟", answer: "اطلب معلومات المشروع والمطور والعقود والدفعات والمراحل، واستعن بمشورة مؤهلة." }, { question: "هل مواعيد الإنجاز مضمونة؟", answer: "لا تقدم المعاينة أي ضمان؛ راجع الوثائق المعتمدة والشروط الخاصة بالمشروع." }, { question: "هل هذه مشورة قانونية أو استثمارية؟", answer: "لا. هذا محتوى تعليمي عام، وينبغي بناء القرار على معلومات موثقة ومشورة مختصة." },
    ]},
    related: { title: "تابع ضمن السياق", items: [arRelated.properties, arRelated.communities, arRelated.contact] },
    cta: { title: "هل لديك أسئلة خاصة بمشروع؟", text: "جهّز استفساراً يفصل أولوياتك عن المعلومات التي لا تزال بحاجة إلى تحقق.", action: "جهّز أسئلتك", href: "/ar/contact" },
  },
  about: {
    intro: { eyebrow: "من نحن", title: "مسار أوضح لاكتشاف العقارات.", text: "تطوّر ALIYAS Real Estate تجربة عقارية ثنائية اللغة في الإمارات، تبدأ بهدف العميل وتعرض المعلومات بصدق مع توفر الإمكانات المعتمدة." },
    sections: [
      { eyebrow: "هدفنا", title: "مساعدة الناس على طرح أسئلة أفضل قبل الخطوة التالية.", text: "توضح التجربة الحالية ما هو متاح وما ينتظر الربط.", items: [
        { title: "نستمع قبل العرض", text: "نبدأ بالاستخدام والروتين والأولويات وما يحتاج إلى توضيح." }, { title: "نفصل الحقيقة عن المعاينة", text: "نعرّف المعلومات الموثقة ولا نعرض المحتوى التوضيحي كحقيقة عقارية." }, { title: "نبسّط المسار", text: "لكل صفحة غرض مفيد وخطوة واضحة وتجربة مكافئة بالعربية والإنجليزية." },
      ]},
      { eyebrow: "ثنائية اللغة منذ البداية", title: "تحمل العربية والإنجليزية المعنى نفسه.", text: "العربية تجربة احترافية من اليمين إلى اليسار، وليست ترجمة مختصرة تضاف لاحقاً.", items: [
        { title: "تكافؤ المحتوى", text: "الإرشادات والتنبيهات والروابط والتفاعلات الأساسية متاحة باللغتين." }, { title: "تكافؤ الواجهة", text: "يتكيف الاتجاه والتنقل وعناصر التحكم من دون فقدان المعنى." }, { title: "جودة التحرير", text: "نفضّل الصياغة العربية الطبيعية على النقل الحرفي." },
      ]},
      { eyebrow: "مسار الإمكانات", title: "نتوسع عندما تصبح الأسس المعتمدة جاهزة.", text: "تؤسس المعاينة مسارات الاكتشاف، بينما تنتظر الخصائص المعتمدة على البيانات مصادرها وعقودها.", items: [
        { title: "متاح الآن", text: "تنقل ثنائي اللغة ومسارات صفحات وتوجيه موجز البحث ومعاينة استفسار غير مرسلة." }, { title: "بانتظار بيانات معتمدة", text: "المخزون والأسعار والتوفر وأعداد النتائج وسجلات المشاريع." }, { title: "نمو مستقبلي منضبط", text: "تتبع الإمكانات الجديدة البنية وسلطة المحتوى وبوابات التحقق المعتمدة." },
      ]},
    ],
    checklist: { eyebrow: "معيار المحتوى", title: "ما لن تخترعه هذه المعاينة", text: "تبدأ الثقة بإظهار حدود المنتج الحالي.", items: ["العقارات أو المشاريع أو الأسعار أو التوفر", "إحصاءات السوق أو التصنيفات أو عوائد الاستثمار", "بيانات اتصال أو ادعاءات خدمة بلا اعتماد", "أوقات تنقل أو مرافق أو ضمانات بلا تحقق", "مشورة قانونية أو مالية أو تعاقدية"] },
    faq: { eyebrow: "أسئلة من نحن", title: "فهم تجربة ARE الحالية", items: [
      { question: "ما الذي تبنيه ALIYAS Real Estate؟", answer: "تجربة ثنائية اللغة لاكتشاف العقارات في الإمارات، مصممة لربط البيانات والخدمات المعتمدة في مراحل لاحقة." }, { question: "هل كل المعلومات العقارية مباشرة؟", answer: "لا. لا تعرض التجربة الحالية مخزوناً مباشراً وتوضح الإمكانات المؤجلة." }, { question: "لماذا التجربة ثنائية اللغة؟", answer: "لأن تكافؤ العربية والإنجليزية متطلب أساسي لتقديم المسارات والتنبيهات نفسها بوضوح." }, { question: "كيف يبقى المحتوى موثوقاً؟", answer: "نتجنب الحقائق المختلقة ونفصل بين المعلومات الموثقة والمؤجلة والتوضيحية." }, { question: "كيف أبدأ؟", answer: "استكشف العقارات أو المجتمعات لتحديد احتياجاتك ثم استخدم معاينة التواصل." },
    ]},
    related: { title: "شاهد النهج عملياً", items: [arRelated.properties, arRelated.communities, arRelated.contact] },
    cta: { title: "ابدأ بما يهمك.", text: "صُغ موجزاً عقارياً أو جهّز الأسئلة التي ترغب في استكشافها.", action: "ابدأ الاكتشاف", href: "/ar/properties" },
  },
  contact: {
    intro: { eyebrow: "اختر نوع الاستفسار", title: "امنح الحوار نقطة بداية مفيدة.", text: "اختر الغرض الأقرب إلى سؤالك ثم شارك السياق اللازم فقط. تتحقق هذه المعاينة المحلية من النموذج ولا ترسل أو تخزن شيئاً." },
    sections: [
      { eyebrow: "ما الذي تذكره", title: "الموجز القصير أفضل من رسالة طويلة غير منظمة.", text: "حافظ على تركيز الاستفسار الأول وتجنب المعلومات الحساسة.", items: [
        { title: "الهدف", text: "وضّح إن كنت تريد الشراء أو الاستئجار أو مقارنة المجتمعات أو استكشاف عقار على المخطط أو طرح سؤال عام." },
        { title: "الموقع المفضل", text: "اذكر المنطقة إن كانت محددة، أو صف الوجهات التي تحتاج إلى الوصول إليها." },
        { title: "نطاق الميزانية", text: "شارك نطاقاً عاماً عند الحاجة، ولا ترفق بيانات بنكية أو وثائق مالية." },
        { title: "نوع العقار", text: "صف نوع المنزل والمساحة والمتطلبات العملية المناسبة لأسرتك." },
        { title: "الإطار الزمني", text: "اذكر توقيتاً تقريبياً ووضّح مواضع المرونة." },
        { title: "المتطلبات المهمة", text: "حدّد احتياجات الحياة الأساسية والأسئلة التي لا تزال بحاجة إلى معلومات موثقة." },
      ]},
      { eyebrow: "ما الذي يحدث لاحقاً", title: "تتوقف هذه المعاينة قبل الإرسال.", text: "قد تربط مرحلة معتمدة لاحقة معالجة آمنة للاستفسارات. حتى ذلك الحين يثبت النموذج التفاعل فقط.", items: [
        { title: "المراجعة", text: "يتحقق المتصفح من اكتمال الحقول ووجود حد أدنى مفيد للرسالة." }, { title: "تأكيد المعاينة", text: "توضح رسالة أن المعلومات لم تُرسل ولم تُخزن." }, { title: "التوجيه المستقبلي", text: "يبقى الإرسال الآمن ووقت الرد وبيانات التواصل التشغيلية قيد الاعتماد." },
      ]},
    ],
    checklist: { eyebrow: "إرشادات الخصوصية", title: "تجنب المعلومات الحساسة في الاستفسار الأول", text: "شارك ما يلزم لوصف السؤال فقط.", items: ["لا تذكر أرقام جواز السفر أو الهوية", "لا تذكر بيانات البنك أو البطاقة أو الحساب", "لا ترسل كلمات المرور أو رموز الدخول", "تجنب السجلات الشخصية المفصلة إلا عبر إجراء آمن معتمد", "تحقق من المستلم والغرض قبل مشاركة الوثائق"] },
    faq: { eyebrow: "أسئلة التواصل", title: "إعداد الاستفسار", items: [
      { question: "هل يرسل النموذج معلوماتي؟", answer: "لا. يتحقق من الحقول ويعرض تأكيداً محلياً، لكنه لا يرسل المعلومات ولا يخزنها." }, { question: "ما أنواع الاستفسار المتاحة؟", answer: "يمكنك إعداد استفسار عن الشراء أو الاستئجار أو المجتمعات أو العقار على المخطط أو سؤال عقاري عام." }, { question: "ماذا أكتب في الرسالة؟", answer: "اذكر الهدف والموقع أو نوع العقار والإطار الزمني التقريبي والأسئلة المطلوبة." }, { question: "هل أرفق وثائق شخصية؟", answer: "لا. لا توفر المعاينة رفع ملفات، ولا ينبغي إرسال وثائق حساسة في استفسار أول غير مؤمّن." }, { question: "متى أتلقى رداً؟", answer: "لا ندّعي وقتاً للرد لأن المعاينة لا ترسل الاستفسار. يبقى التوجيه التشغيلي لمرحلة معتمدة." },
    ]},
    related: { title: "استعد قبل الاستفسار", items: [arRelated.properties, arRelated.communities, arRelated.offPlan] },
    cta: { title: "هل تريد تحسين موجزك أولاً؟", text: "عد إلى اكتشاف العقارات ونظّم المعايير الأكثر أهمية.", action: "استكشف العقارات", href: "/ar/properties" },
  },
};

// The object is declared in two stages to keep English and Arabic editorial blocks readable.
export const richCopy: Readonly<Record<Locale, RichCopy>> = {
  en: richCopyBase.en,
  ar: { ...richCopyBase.ar, pages: arPages },
};
