import Image from "next/image";
import Link from "next/link";
import {
  BadgeCheck,
  BedDouble,
  Building2,
  CalendarDays,
  Clock3,
  HardHat,
  House,
  Landmark,
  MapPin,
  Maximize2,
  MessageCircle,
  Percent,
  Send,
  Sparkles,
  WalletCards,
  type LucideIcon,
} from "lucide-react";

import type { CandidateProjectPreview, PublicProject } from "../../lib/api";
import type { Locale } from "../../lib/home-copy";
import {
  ProjectMediaViewer,
  type ProjectPresentationMedia,
} from "./project-media-viewer";

type PresentationProject = PublicProject | CandidateProjectPreview;

const copy = {
  en: {
    eyebrow: "ARE / OFF-PLAN PROJECT",
    details: "Project at a glance",
    overview: "Overview",
    homes: "Homes and sizes",
    plan: "Payment plan",
    amenities: "Amenities",
    locationSection: "Location and connections",
    media: "Plans and project media",
    developer: "Developer",
    location: "Emirate and area",
    types: "Property type",
    unitTypes: "Home configurations",
    bedrooms: "Bedrooms",
    size: "Size range",
    down: "Down payment",
    handover: "Handover",
    availability: "Availability",
    construction: "Construction",
    notConfirmed: "Not confirmed",
    verification: "Community-level target; verify the applicable date for the selected home.",
    floorPlans: "Floor Plans",
    masterPlan: "Master Plan",
    locationMap: "Location Map",
    gallery: "Gallery",
    nav: "Project sections",
    enquire: "Enquire",
    whatsapp: "WhatsApp",
    ctaEyebrow: "ARE ADVISORY",
    ctaTitle: "Review this Project with an advisor",
    ctaText: "Ask about the current status and verify the details relevant to your preferred home.",
    back: "Back to Off-Plan",
    previewNote: "Private noindex preview — this Project is not publicly published.",
  },
  ar: {
    eyebrow: "ARE / مشروع على الخارطة",
    details: "لمحة عن المشروع",
    overview: "نظرة عامة",
    homes: "المنازل والمساحات",
    plan: "خطة السداد",
    amenities: "المرافق",
    locationSection: "الموقع وسهولة الوصول",
    media: "المخططات ووسائط المشروع",
    developer: "المطور",
    location: "الإمارة والمنطقة",
    types: "نوع العقار",
    unitTypes: "تكوينات المنازل",
    bedrooms: "غرف النوم",
    size: "نطاق المساحة",
    down: "الدفعة الأولى",
    handover: "التسليم",
    availability: "التوفر",
    construction: "حالة الإنشاء",
    notConfirmed: "غير مؤكد",
    verification: "موعد مستهدف على مستوى المجتمع؛ يلزم التحقق من الموعد المطبق على المنزل المختار.",
    floorPlans: "مخططات الطوابق",
    masterPlan: "المخطط العام",
    locationMap: "خريطة الموقع",
    gallery: "معرض الصور",
    nav: "أقسام المشروع",
    enquire: "استفسر",
    whatsapp: "واتساب",
    ctaEyebrow: "استشارات ALIYAS",
    ctaTitle: "راجع هذا المشروع مع مستشار",
    ctaText: "استفسر عن الحالة الحالية وتحقق من التفاصيل المرتبطة بالمنزل الذي تفضله.",
    back: "العودة إلى المشاريع على الخارطة",
    previewNote: "معاينة خاصة غير مفهرسة — لا يمثل هذا المشروع منشوراً عاماً.",
  },
} as const;

export function ProjectDetailPresentation({
  locale,
  project,
  preview = false,
  mediaBaseUrl = "",
}: Readonly<{
  locale: Locale;
  project: PresentationProject;
  preview?: boolean;
  mediaBaseUrl?: string;
}>) {
  const t = copy[locale];
  const normalized = normalizeProject(project, locale, mediaBaseUrl);
  const cover = normalized.media.find((item) => isEligibleCover(item));
  const mediaCategories = buildMediaCategories(normalized.media, locale);
  const hasHomes = Boolean(
    normalized.propertyTypes.length
    || normalized.unitTypes.length
    || normalized.bedrooms.length
    || normalized.size,
  );
  const hasPayment = Boolean(
    normalized.paymentPlan
    || normalized.milestones.length
    || normalized.downPayment,
  );
  const hasAmenities = normalized.amenities.length > 0;
  const hasLocation = Boolean(normalized.area || normalized.emirate || normalized.nearby.length);
  const hasFloorPlans = mediaCategories.some((item) => item.id === "floor-plan");
  const enquiryHref = `/${locale}/contact?topic=off-plan&project=${encodeURIComponent(normalized.enquiryKey)}`;
  const whatsappHref = whatsappUrl(normalized.name, locale);
  const navigation = [
    normalized.overview ? { id: "project-overview", label: t.overview } : null,
    { id: "project-details", label: locale === "ar" ? "تفاصيل المشروع" : "Project details" },
    hasHomes ? { id: "project-homes", label: t.homes } : null,
    hasPayment ? { id: "project-payment", label: t.plan } : null,
    hasAmenities ? { id: "project-amenities", label: t.amenities } : null,
    hasFloorPlans ? { id: "project-media", label: t.floorPlans } : null,
    hasLocation ? { id: "project-location", label: locale === "ar" ? "الموقع" : "Location" } : null,
    { id: "project-enquire", label: t.enquire },
  ].filter((item): item is { id: string; label: string } => item !== null);

  return <main className="project-presentation" id="main-content">
    <section className={`project-presentation__hero ${cover ? "project-presentation__hero--image" : "project-presentation__hero--neutral"}`}>
      {cover ? <Image
        alt={cover.alt}
        className="project-presentation__hero-image"
        fill
        priority
        sizes="100vw"
        src={cover.fullUrl}
        unoptimized
      /> : <div aria-hidden className="project-presentation__hero-art">
        <span/><span/><span/>
        <Image alt="" height={2885} src="/brand/aliyas-real-estate-logo.png" width={2885}/>
      </div>}
      <div className="project-presentation__hero-shade"/>
      <div className="project-presentation__hero-copy">
        <p>{t.eyebrow}</p>
        <h1>{normalized.name}</h1>
        <div className="project-presentation__hero-meta">
          <span><Landmark aria-hidden size={17}/>{normalized.developer}</span>
          <span><MapPin aria-hidden size={17}/>{normalized.area}, {normalized.emirate}</span>
        </div>
        <div className="project-presentation__status-row">
          <span><BadgeCheck aria-hidden size={15}/>{t.availability}: {normalized.availability}</span>
          <span><HardHat aria-hidden size={15}/>{t.construction}: {normalized.construction}</span>
        </div>
        <div className="project-presentation__hero-actions">
          <Link className="button button--primary" href={enquiryHref}><Send aria-hidden size={17}/>{t.enquire}</Link>
          <a className="button star-action--outline" href={whatsappHref} rel="noreferrer" target="_blank"><MessageCircle aria-hidden size={17}/>{t.whatsapp}</a>
        </div>
      </div>
    </section>

    {preview ? <p className="project-presentation__preview-note">{t.previewNote}</p> : null}

    <nav aria-label={t.nav} className="project-presentation__navigator">
      <div>{navigation.map((item) => <a href={`#${item.id}`} key={item.id}>{item.label}</a>)}</div>
    </nav>

    {normalized.overview ? <section className="project-presentation__section project-presentation__section--split" id="project-overview" aria-labelledby="project-overview-title">
      <Heading eyebrow="01" id="project-overview-title" title={t.overview}/>
      <div className="project-presentation__overview">{editorialParagraphs(normalized.overview).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</div>
    </section> : null}

    <section className="project-presentation__section" id="project-details" aria-labelledby="project-details-title">
      <Heading eyebrow="02" id="project-details-title" title={t.details}/>
      <dl className="project-presentation__fact-grid">
        <IconFact icon={Landmark} label={t.developer} value={normalized.developer}/>
        <IconFact icon={MapPin} label={t.location} value={`${normalized.area}, ${normalized.emirate}`}/>
        <IconFact icon={Building2} label={t.types} value={normalized.propertyTypes.join(" · ")}/>
        <IconFact icon={BedDouble} label={t.bedrooms} value={normalized.bedrooms.join(" · ")}/>
        <IconFact icon={Maximize2} label={t.size} value={normalized.size}/>
        <IconFact icon={CalendarDays} label={t.handover} value={normalized.handover}/>
        <IconFact icon={Percent} label={t.down} value={normalized.downPayment}/>
        <IconFact icon={WalletCards} label={t.plan} value={normalized.paymentPlan}/>
        <IconFact icon={BadgeCheck} label={t.availability} value={normalized.availability}/>
        <IconFact icon={HardHat} label={t.construction} value={normalized.construction}/>
      </dl>
      {normalized.handoverNote ? <p className="project-presentation__verification"><Clock3 aria-hidden size={15}/>{normalized.handoverNote}</p> : null}
    </section>

    {hasHomes ? <section className="project-presentation__section" id="project-homes" aria-labelledby="project-homes-title">
      <Heading eyebrow="03" id="project-homes-title" title={t.homes}/>
      <dl className="project-presentation__home-grid">
        <HomeDetail icon={Building2} label={t.types} values={normalized.propertyTypes}/>
        <HomeDetail icon={House} label={t.unitTypes} values={normalized.unitTypes}/>
        <HomeDetail icon={BedDouble} label={t.bedrooms} values={normalized.bedrooms}/>
        <HomeDetail icon={Maximize2} label={t.size} values={normalized.size ? [normalized.size] : []}/>
      </dl>
    </section> : null}

    {hasPayment ? <section className="project-presentation__section project-presentation__section--split" id="project-payment" aria-labelledby="project-payment-title">
      <Heading eyebrow="04" id="project-payment-title" title={t.plan}/>
      <div className="project-presentation__payment">
        {normalized.paymentPlan ? <strong className="project-presentation__plan-ratio">{normalized.paymentPlan}</strong> : null}
        {normalized.downPayment ? <p><Percent aria-hidden size={18}/><span>{t.down}</span><strong>{normalized.downPayment}</strong></p> : null}
        {normalized.milestones.length ? <ol className="project-presentation__milestones">{normalized.milestones.map((item) => <li key={`${item.sequence}-${item.stage}`}>
          <span>{item.sequence.toString().padStart(2, "0")}</span>
          <strong>{item.label || stageLabel(item.stage, locale)}</strong>
          <em>{item.percentage == null ? t.notConfirmed : `${item.percentage}%`}</em>
        </li>)}</ol> : null}
      </div>
    </section> : null}

    {hasAmenities ? <section className="project-presentation__section" id="project-amenities" aria-labelledby="project-amenities-title">
      <Heading eyebrow="05" id="project-amenities-title" title={t.amenities}/>
      <ul className="project-presentation__amenity-grid">{normalized.amenities.map((value) => <li key={value}><Sparkles aria-hidden size={20}/><span>{value}</span></li>)}</ul>
    </section> : null}

    {mediaCategories.length ? <section className="project-presentation__section motion-section--visible" id="project-media" aria-labelledby="project-media-title">
      <Heading eyebrow="06" id="project-media-title" title={t.media}/>
      <ProjectMediaViewer categories={mediaCategories} locale={locale}/>
    </section> : null}

    {hasLocation ? <section className="project-presentation__section project-presentation__section--split" id="project-location" aria-labelledby="project-location-title">
      <Heading eyebrow="07" id="project-location-title" title={t.locationSection}/>
      <div className="project-presentation__location-panel">
        <div><MapPin aria-hidden size={22}/><span>{t.location}</span><strong>{normalized.area}, {normalized.emirate}</strong></div>
        {normalized.nearby.length ? <ul>{normalized.nearby.map((item) => <li key={item.name}>
          <MapPin aria-hidden size={18}/><strong>{item.name}</strong>
          {item.travelTime == null ? null : <span><Clock3 aria-hidden size={15}/>{locale === "ar" ? `${item.travelTime} دقيقة تقريباً` : `Approximately ${item.travelTime} min`}</span>}
        </li>)}</ul> : null}
      </div>
    </section> : null}

    <section className="project-presentation__enquiry" id="project-enquire" aria-labelledby="project-enquire-title">
      <div><p>{t.ctaEyebrow}</p><h2 id="project-enquire-title">{t.ctaTitle}</h2><span>{t.ctaText}</span></div>
      <div><Link className="button button--primary" href={enquiryHref}><Send aria-hidden size={17}/>{t.enquire}</Link><a className="button star-action--outline" href={whatsappHref} rel="noreferrer" target="_blank"><MessageCircle aria-hidden size={17}/>{t.whatsapp}</a></div>
    </section>

    <Link className="article-back" href={`/${locale}/off-plan`}>← {t.back}</Link>
  </main>;
}

type NormalizedProject = {
  name: string;
  overview: string | null;
  developer: string;
  emirate: string;
  area: string;
  enquiryKey: string;
  propertyTypes: string[];
  bedrooms: string[];
  unitTypes: string[];
  size: string | null;
  downPayment: string | null;
  handover: string | null;
  handoverNote: string | null;
  availability: string;
  construction: string;
  paymentPlan: string | null;
  milestones: Array<{ sequence: number; stage: string; label?: string | null; percentage: number | null }>;
  amenities: string[];
  nearby: Array<{ name: string; travelTime: number | null }>;
  media: ProjectPresentationMedia[];
};

function normalizeProject(project: PresentationProject, locale: Locale, mediaBaseUrl: string): NormalizedProject {
  const candidate = "candidate_id" in project;
  const ar = locale === "ar";
  if (candidate) return {
    name: project.project_name,
    overview: project.overview,
    developer: project.developer.name,
    emirate: project.emirate,
    area: project.area,
    enquiryKey: project.project_name,
    propertyTypes: project.property_types,
    bedrooms: project.bedrooms,
    unitTypes: project.unit_types,
    size: sizeLabel(project.size_min, project.size_max, project.size_unit, locale),
    downPayment: project.down_payment_percentage == null ? null : `${project.down_payment_percentage}%`,
    handover: project.handover_quarter && project.handover_year ? handoverLabel(project.handover_quarter, project.handover_year, locale) : null,
    handoverNote: project.handover_quarter && project.handover_year ? copy[locale].verification : null,
    availability: statusLabel(project.availability_status, locale),
    construction: statusLabel(project.construction_status, locale),
    paymentPlan: project.payment_plan,
    milestones: project.payment_milestones,
    amenities: project.amenities,
    nearby: project.nearby_places.map((item) => ({ name: item.name, travelTime: item.travel_time_minutes })),
    media: project.media.map((item) => ({
      id: item.id,
      category: item.category,
      thumbnailUrl: mediaUrl(mediaBaseUrl, item.thumbnail_url),
      fullUrl: mediaUrl(mediaBaseUrl, item.full_url),
      alt: item.alt || project.project_name,
      width: item.width ?? 1200,
      height: item.height ?? 900,
    })),
  };
  const area = ar ? project.area.name_ar : project.area.name_en;
  return {
    name: project.official_name,
    overview: project.full_description || project.short_summary || null,
    enquiryKey: project.slug,
    developer: project.developer.name,
    emirate: project.emirate,
    area,
    propertyTypes: project.property_types,
    bedrooms: project.bedroom_options,
    unitTypes: project.unit_types?.map((item) => item.label) ?? [],
    size: sizeLabel(project.size_min, project.size_max, project.size_unit, locale),
    downPayment: project.down_payment_percentage == null ? null : `${project.down_payment_percentage}%`,
    handover: project.handover_quarter && project.handover_year ? handoverLabel(project.handover_quarter, project.handover_year, locale) : null,
    handoverNote: null,
    availability: statusLabel(project.availability_status, locale),
    construction: statusLabel(project.construction_status, locale),
    paymentPlan: null,
    milestones: project.payment_plan?.milestones.map((item) => ({
      sequence: item.sequence,
      stage: item.stage,
      label: item.label,
      percentage: item.percentage == null ? null : Number(item.percentage),
    })) ?? [],
    amenities: project.amenities?.map((item) => item.label) ?? [],
    nearby: project.nearby_places?.map((item) => ({ name: item.name, travelTime: item.travel_time_minutes })) ?? [],
    media: project.media?.map((item) => ({
      id: item.id,
      category: item.category,
      thumbnailUrl: mediaUrl(mediaBaseUrl, item.url),
      fullUrl: mediaUrl(mediaBaseUrl, item.url),
      alt: item.alt || project.official_name,
      width: item.width ?? 1200,
      height: item.height ?? 900,
    })) ?? [],
  };
}

function IconFact({ icon: Icon, label, value }: Readonly<{ icon: LucideIcon; label: string; value?: string | null }>) {
  if (!value) return null;
  return <div><dt><Icon aria-hidden size={21}/><span>{label}</span></dt><dd>{value}</dd></div>;
}

function HomeDetail({ icon: Icon, label, values }: Readonly<{ icon: LucideIcon; label: string; values: string[] }>) {
  if (!values.length) return null;
  return <div><dt><Icon aria-hidden size={22}/><span>{label}</span></dt><dd>{values.map((value) => <span key={value}>{value}</span>)}</dd></div>;
}

function Heading({ eyebrow, id, title }: Readonly<{ eyebrow: string; id: string; title: string }>) {
  return <div className="project-presentation__heading"><p>{eyebrow}</p><h2 id={id}>{title}</h2></div>;
}

function buildMediaCategories(items: ProjectPresentationMedia[], locale: Locale) {
  const t = copy[locale];
  const categories = [
    { id: "floor-plan" as const, label: t.floorPlans, categories: ["floor-plan"] },
    { id: "master-plan" as const, label: t.masterPlan, categories: ["master-plan"] },
    { id: "location-map" as const, label: t.locationMap, categories: ["location-map"] },
    { id: "gallery" as const, label: t.gallery, categories: ["gallery", "exterior", "interior", "amenities", "construction"] },
  ];
  return categories.map((category) => ({
    id: category.id,
    label: category.label,
    items: items.filter((item) => category.categories.includes(item.category)),
  })).filter((category) => category.items.length > 0);
}

function editorialParagraphs(text: string) {
  const supplied = text.split(/\n{2,}/).map((value) => value.trim()).filter(Boolean);
  if (supplied.length > 1 || text.length < 300) return supplied;
  const sentences = text.match(/[^.!?؟]+[.!?؟]+|[^.!?؟]+$/g)?.map((value) => value.trim()).filter(Boolean) ?? [text];
  const paragraphs: string[] = [];
  for (let index = 0; index < sentences.length; index += 2) paragraphs.push(sentences.slice(index, index + 2).join(" "));
  return paragraphs;
}

function isEligibleCover(item: ProjectPresentationMedia) {
  return item.category === "cover" && item.width >= 1600 && item.height >= 900 && item.width > item.height;
}

function mediaUrl(baseUrl: string, path: string) {
  if (/^https?:\/\//.test(path) || !baseUrl) return path;
  return `${baseUrl.replace(/\/$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
}

function sizeLabel(minimum: string | number | null | undefined, maximum: string | number | null | undefined, unit: string | null | undefined, locale: Locale) {
  if (minimum == null && maximum == null) return null;
  const format = (value: string | number) => Number(value).toLocaleString(locale === "ar" ? "ar-AE" : "en-AE");
  const range = minimum != null && maximum != null ? `${format(minimum)}–${format(maximum)}` : format((minimum ?? maximum) as string | number);
  const localizedUnit = locale === "ar" && unit === "sqft" ? "قدم²" : unit ?? "";
  return `${range} ${localizedUnit}`.trim();
}

function stageLabel(stage: string, locale: Locale) {
  const labels: Record<string, [string, string]> = {
    booking: ["Booking", "عند الحجز"],
    "during-construction": ["During construction", "أثناء الإنشاء"],
    handover: ["On completion", "عند الإنجاز"],
  };
  return labels[stage]?.[locale === "ar" ? 1 : 0] ?? stage.replaceAll("-", " ");
}

function handoverLabel(quarter: string, year: number, locale: Locale) {
  const arQuarter: Record<string, string> = { Q1: "الربع الأول", Q2: "الربع الثاني", Q3: "الربع الثالث", Q4: "الربع الرابع" };
  return locale === "ar" ? `${arQuarter[quarter] ?? quarter} ${year}` : `${quarter} ${year}`;
}

function statusLabel(value: string, locale: Locale) {
  const labels: Record<string, [string, string]> = {
    available: ["Available", "متاح"],
    "limited-availability": ["Limited availability", "توفر محدود"],
    "sold-out": ["Sold out", "نفدت الوحدات"],
    "coming-soon": ["Coming soon", "قريباً"],
    "pre-launch": ["Pre-launch", "قبل الإطلاق"],
    launched: ["Launched", "تم الإطلاق"],
    "under-construction": ["Under construction", "قيد الإنشاء"],
    "near-completion": ["Near completion", "قرب الاكتمال"],
    completed: ["Completed", "مكتمل"],
    "on-hold": ["On hold", "متوقف مؤقتاً"],
    "not-confirmed": ["Not confirmed", "غير مؤكد"],
  };
  return labels[value]?.[locale === "ar" ? 1 : 0] ?? value.replaceAll("-", " ");
}

function whatsappUrl(projectName: string, locale: Locale) {
  const message = locale === "ar"
    ? `مرحباً، أود الاستفسار عن مشروع ${projectName}.`
    : `Hello, I would like to enquire about ${projectName}.`;
  return `https://wa.me/971569157576?text=${encodeURIComponent(message)}`;
}
