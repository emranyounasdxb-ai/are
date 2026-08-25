import Link from "next/link";
import { notFound } from "next/navigation";

import { FinalCta } from "../../../../../components/content/editorial-content";
import { SiteFooter } from "../../../../../components/navigation/site-footer";
import { getProject } from "../../../../../lib/api";
import { homeCopy, isLocale } from "../../../../../lib/home-copy";

type Props = Readonly<{ params: Promise<{ locale: string; slug: string }> }>;

export const dynamic = "force-dynamic";

export default async function ProjectDetailPage({ params }: Props) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const project = await getProject(locale, slug);
  if (!project) notFound();
  const ar = locale === "ar";
  const areaName = ar ? project.area.name_ar : project.area.name_en;
  return <div className="property-detail-page" id="top"><main id="main-content"><section className="inner-hero"><div className="inner-hero__grid"><div className="inner-hero__copy"><p>ARE / {ar ? "مشروع منشور" : "PUBLISHED PROJECT"}</p><h1>{project.official_name}</h1><span>{project.short_summary}</span></div><div className="property-detail-neutral" aria-hidden="true"><strong>ARE</strong><span>{project.emirate}</span></div></div></section><section className="content-section content-section--split"><div className="content-heading"><p>ARE / {ar ? "التفاصيل" : "DETAILS"}</p><h2>{ar ? "تفاصيل المشروع المعتمدة" : "Approved project details"}</h2><span>{project.full_description}</span></div><dl className="property-facts"><div><dt>{ar ? "الإمارة" : "Emirate"}</dt><dd>{project.emirate}</dd></div><div><dt>{ar ? "المنطقة" : "Area"}</dt><dd>{areaName}</dd></div><div><dt>{ar ? "المطور" : "Developer"}</dt><dd>{project.developer.name}</dd></div><div><dt>{ar ? "التوفر" : "Availability"}</dt><dd>{project.availability_status}</dd></div><div><dt>{ar ? "حالة البناء" : "Construction"}</dt><dd>{project.construction_status}</dd></div></dl></section><Link className="article-back" href={`/${locale}/off-plan`}>← {ar ? "العودة إلى المشاريع" : "Back to Off-Plan"}</Link><FinalCta action={ar ? "استفسر" : "Enquire"} heading={ar ? "هل يناسب هذا المشروع متطلباتك؟" : "Does this project fit your brief?"} href={`/${locale}/contact?topic=off-plan&project=${project.slug}`} locale={locale} text={ar ? "تحقق من التوفر والمعلومات الحالية قبل اتخاذ أي قرار." : "Verify current availability and details before making a decision."}/></main><SiteFooter copy={homeCopy[locale].header} locale={locale}/></div>;
}
