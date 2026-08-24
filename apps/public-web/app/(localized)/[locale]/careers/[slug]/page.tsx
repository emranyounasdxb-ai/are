import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Breadcrumbs, Checklist, FinalCta } from "../../../../../components/content/editorial-content";
import { SiteFooter } from "../../../../../components/navigation/site-footer";
import { SiteHeader } from "../../../../../components/navigation/site-header";
import { getJob } from "../../../../../lib/api";
import { homeCopy, isLocale } from "../../../../../lib/home-copy";
import { richCopy } from "../../../../../lib/rich-copy";

type Props = { params: Promise<{ locale: string; slug: string }> };
export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const job = await getJob(locale, slug);
  return job ? { title: `${job.title} | Careers | ALIYAS Real Estate`, description: job.description.slice(0, 155) } : {};
}

export default async function JobDetail({ params }: Props) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const job = await getJob(locale, slug);
  if (!job) notFound();
  const ar = locale === "ar";
  return <div className="career-detail-page" id="top">
    <SiteHeader copy={homeCopy[locale].header} locale={locale}/>
    <main id="main-content">
      <section className="article-hero"><div className="article-hero__inner">
        <Breadcrumbs items={[{ href: `/${locale}`, label: richCopy[locale].homeLabel }, { href: `/${locale}/careers`, label: homeCopy[locale].header.careers }, { label: job.title }]} label={richCopy[locale].breadcrumb}/>
        <div className="article-hero__reveal"><p>{job.department}</p><h1>{job.title}</h1><div className="article-meta"><span>{job.location}</span><span>{job.employment_type}</span>{job.closing_date ? <span>{ar ? "تاريخ الإغلاق" : "Closing"}: {job.closing_date}</span> : null}</div></div>
      </div></section>
      <section className="content-section content-section--intro"><div className="content-heading"><p>ARE / ROLE</p><h2>{ar ? "عن الوظيفة" : "About the role"}</h2></div><p className="content-lead">{job.description}</p></section>
      <section className="content-section content-section--split"><div><h2>{ar ? "المسؤوليات" : "Responsibilities"}</h2><Checklist items={job.responsibilities}/></div><div><h2>{ar ? "المتطلبات" : "Requirements"}</h2><Checklist items={job.requirements}/></div>{job.benefits.length ? <div><h2>{ar ? "المزايا" : "Benefits"}</h2><Checklist items={job.benefits}/></div> : null}</section>
      <Link className="article-back" href={`/${locale}/careers`}>← {ar ? "العودة إلى الوظائف" : "Back to careers"}</Link>
      <FinalCta action={ar ? "قدّم الآن" : "Apply now"} heading={ar ? "هل تتوافق خبرتك مع هذه الوظيفة؟" : "Does your experience align with this role?"} href={`/${locale}/careers?job=${encodeURIComponent(job.slug)}#application`} locale={locale} text={ar ? "استخدم نموذج الطلب الآمن المرتبط بهذه الوظيفة المفتوحة." : "Use the secure application form linked to this open role."}/>
    </main>
    <SiteFooter copy={homeCopy[locale].header} locale={locale}/>
  </div>;
}
