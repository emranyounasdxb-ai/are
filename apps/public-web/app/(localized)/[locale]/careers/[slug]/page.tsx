import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Breadcrumbs, Checklist, FinalCta } from "../../../../../components/content/editorial-content";
import { SiteFooter } from "../../../../../components/navigation/site-footer";
import { getJob } from "../../../../../lib/api";
import { homeCopy, isLocale } from "../../../../../lib/home-copy";
import { richCopy } from "../../../../../lib/rich-copy";
import { localizedBrand, normalizeArabicUserFacingText } from "../../../../../lib/arabic-localization";

type Props = { params: Promise<{ locale: string; slug: string }> };
export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const result = await getJob(locale, slug);
  const job = locale === "ar" && result ? localizedJob(result) : result;
  return job ? { title: locale === "ar" ? `${job.title} | الوظائف | ${localizedBrand(locale)}` : `${job.title} | Careers | ALIYAS Real Estate`, description: job.description.slice(0, 155) } : {};
}

export default async function JobDetail({ params }: Props) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const result = await getJob(locale, slug);
  const job = locale === "ar" && result ? localizedJob(result) : result;
  if (!job) notFound();
  const ar = locale === "ar";
  return <div className="career-detail-page" id="top">
    <main id="main-content">
      <section className="article-hero"><div className="article-hero__inner">
        <Breadcrumbs items={[{ href: `/${locale}`, label: richCopy[locale].homeLabel }, { href: `/${locale}/careers`, label: homeCopy[locale].header.careers }, { label: job.title }]} label={richCopy[locale].breadcrumb}/>
        <div className="article-hero__reveal"><p>{job.department}</p><h1>{job.title}</h1><div className="article-meta"><span>{job.location}</span><span>{job.employment_type}</span>{job.closing_date ? <span>{ar ? "تاريخ الإغلاق" : "Closing"}: {job.closing_date}</span> : null}</div></div>
      </div></section>
      <section className="content-section content-section--intro"><div className="content-heading"><p>{ar ? "علياس العقارية / الوظيفة" : "ARE / ROLE"}</p><h2>{ar ? "عن الوظيفة" : "About the role"}</h2></div><p className="content-lead">{job.description}</p></section>
      <section className="content-section content-section--split"><div><h2>{ar ? "المسؤوليات" : "Responsibilities"}</h2><Checklist items={job.responsibilities}/></div><div><h2>{ar ? "المتطلبات" : "Requirements"}</h2><Checklist items={job.requirements}/></div>{job.benefits.length ? <div><h2>{ar ? "المزايا" : "Benefits"}</h2><Checklist items={job.benefits}/></div> : null}</section>
      <Link className="article-back" href={`/${locale}/careers`}>← {ar ? "العودة إلى الوظائف" : "Back to careers"}</Link>
      <FinalCta action={ar ? "قدّم الآن" : "Apply now"} heading={ar ? "هل تتوافق خبرتك مع هذه الوظيفة؟" : "Does your experience align with this role?"} href={`/${locale}/careers?job=${encodeURIComponent(job.slug)}#application`} locale={locale} text={ar ? "استخدم نموذج الطلب الآمن المرتبط بهذه الوظيفة المفتوحة." : "Use the secure application form linked to this open role."}/>
    </main>
    <SiteFooter copy={homeCopy[locale].header} locale={locale}/>
  </div>;
}

function localizedJob<T extends { title:string;description:string;department:string;location:string;employment_type:string;closing_date?:string|null;responsibilities:string[];requirements:string[];benefits:string[] }>(job:T):T {
  return {
    ...job,
    title: normalizeArabicUserFacingText(job.title),
    description: normalizeArabicUserFacingText(job.description),
    department: normalizeArabicUserFacingText(job.department),
    location: normalizeArabicUserFacingText(job.location),
    employment_type: normalizeArabicUserFacingText(job.employment_type),
    closing_date: job.closing_date ? normalizeArabicUserFacingText(job.closing_date) : job.closing_date,
    responsibilities: job.responsibilities.map(normalizeArabicUserFacingText),
    requirements: job.requirements.map(normalizeArabicUserFacingText),
    benefits: job.benefits.map(normalizeArabicUserFacingText),
  };
}
