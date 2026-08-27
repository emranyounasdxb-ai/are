import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CareersApplicationForm } from "../../../../components/careers/careers-application-form";
import { Checklist, EditorialCards, FaqSection, FinalCta, ProcessList, RelatedPages } from "../../../../components/content/editorial-content";
import { PageHero } from "../../../../components/hero/page-hero";
import { SiteFooter } from "../../../../components/navigation/site-footer";
import { careerInterests, careersCopy } from "../../../../lib/careers-data";
import { getJobs } from "../../../../lib/api";
import { homeCopy, isLocale, locales, type Locale } from "../../../../lib/home-copy";

type Props = Readonly<{ params: Promise<{ locale: string }>; searchParams: Promise<{ job?: string }> }>;

export const dynamicParams = false;

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const copy = careersCopy[locale];
  return { title: copy.metaTitle, description: copy.metaDescription };
}

export default async function CareersPage({ params, searchParams }: Props) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return <LocalizedCareers jobSlug={(await searchParams).job} locale={locale} />;
}

async function LocalizedCareers({ jobSlug, locale }: Readonly<{ jobSlug?: string; locale: Locale }>) {
  const copy = careersCopy[locale];
  const isArabic = locale === "ar";
  const careerVacancies = await getJobs(locale);

  return (
    <div className="careers-page" id="top">
      <main id="main-content">
        <PageHero description={copy.hero.text} eyebrow={copy.hero.eyebrow} image="careers" locale={locale} title={copy.hero.title}
          primary={{ label: copy.opportunities.action, href: "#application" }}
          secondary={{ label: homeCopy[locale].hero.secondaryAction, href: `/${locale}/contact` }}
          note={<><span>ARE / CAREERS</span><p>{copy.hero.note}</p></>} />

        <section aria-labelledby="careers-intro-title" className="content-section content-section--intro">
          <div className="content-heading"><p>{copy.intro.eyebrow}</p><h2 id="careers-intro-title">{copy.intro.title}</h2></div>
          <p className="content-lead">{copy.intro.text}</p>
        </section>

        <section aria-labelledby="career-areas-title" className="career-areas content-section">
          <div className="content-heading"><p>{copy.areas.eyebrow}</p><h2 id="career-areas-title">{copy.areas.title}</h2><span>{copy.areas.text}</span></div>
          <ol>{careerInterests.map((interest, index) => <li key={interest.value}><span>{String(index + 1).padStart(2, "0")}</span><h3>{interest.label[locale]}</h3><small>{isArabic ? "مجال اهتمام عام" : "General area of interest"}</small></li>)}</ol>
        </section>

        <section aria-labelledby="opportunities-title" className="career-opportunities">
          <div className="career-opportunities__heading"><p>{copy.opportunities.eyebrow}</p><h2 id="opportunities-title">{copy.opportunities.title}</h2></div>
          {careerVacancies.length === 0 ? <div className="career-opportunities__empty"><span aria-hidden="true">00</span><div><h3>{copy.opportunities.emptyTitle}</h3><p>{copy.opportunities.emptyText}</p><Link className="button button--primary animated-gold-border" href="#application">{copy.opportunities.action}</Link></div></div> : <div className="career-vacancy-grid">{careerVacancies.map((job)=><article key={job.id}><span>{job.department}</span><h3>{job.title}</h3><p>{job.location} · {job.employment_type}</p><Link className="text-link" href={`/${locale}/careers/${job.slug}`}>{isArabic?"عرض الوظيفة":"View role"}</Link></article>)}</div>}
        </section>

        <section aria-labelledby="general-interest-title" className="content-section content-section--dark">
          <div className="content-heading"><p>{copy.general.eyebrow}</p><h2 id="general-interest-title">{copy.general.title}</h2><span>{copy.general.text}</span></div>
          <EditorialCards items={copy.general.points} />
        </section>

        <section aria-labelledby="prepare-title" className="content-section content-section--split">
          <div className="content-heading"><p>{copy.prepare.eyebrow}</p><h2 id="prepare-title">{copy.prepare.title}</h2><span>{copy.prepare.text}</span></div>
          <Checklist items={copy.prepare.items} />
        </section>

        <section aria-labelledby="journey-title" className="content-section career-journey">
          <div className="content-heading"><p>{copy.journey.eyebrow}</p><h2 id="journey-title">{copy.journey.title}</h2><span>{copy.journey.text}</span></div>
          <ProcessList items={copy.journey.items} />
        </section>

        <section aria-labelledby="application-title" className="career-application" id="application">
          <div className="career-application__heading"><p>{copy.application.eyebrow}</p><h2 id="application-title">{copy.application.title}</h2><span>{copy.application.text}</span></div>
          <CareersApplicationForm jobSlug={jobSlug} locale={locale} />
        </section>

        <section aria-labelledby="privacy-title" className="career-privacy content-section content-section--split">
          <div className="content-heading"><p>{copy.privacy.eyebrow}</p><h2 id="privacy-title">{copy.privacy.title}</h2><span>{copy.privacy.text}</span></div>
          <Checklist items={copy.privacy.points} />
        </section>

        <FaqSection eyebrow={copy.faq.eyebrow} heading={copy.faq.title} items={copy.faq.items} />
        <RelatedPages heading={copy.related.title} items={copy.related.items} />
        <FinalCta action={copy.cta.action} heading={copy.cta.title} href={`/${locale}/contact`} locale={locale} text={copy.cta.text} />
      </main>
      <SiteFooter copy={homeCopy[locale].header} locale={locale} />
    </div>
  );
}
