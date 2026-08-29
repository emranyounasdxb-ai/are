import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { RelatedPages } from "../../../../../components/content/editorial-content";
import { Reveal } from "../../../../../components/motion/reveal";
import { SiteFooter } from "../../../../../components/navigation/site-footer";
import { getDeveloper, type PublicDeveloper } from "../../../../../lib/api";
import { localizedBrand, toArabicIndicDigits } from "../../../../../lib/arabic-localization";
import { homeCopy, isLocale, type Locale } from "../../../../../lib/home-copy";

type Props = Readonly<{ params: Promise<{ locale: string; slug: string }> }>;

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const developer = await getDeveloper(locale, slug);
  if (!developer) return {};
  return {
    title: `${developer.name} | ${locale === "ar" ? "دليل المطورين" : "Developer Directory"} | ${localizedBrand(locale)}`,
    description: developer.description,
  };
}

export default async function DeveloperDetailPage({ params }: Props) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const developer = await getDeveloper(locale, slug);
  if (!developer) notFound();
  return <LocalizedDeveloper developer={developer} locale={locale} />;
}

function LocalizedDeveloper({ developer, locale }: Readonly<{ developer: PublicDeveloper; locale: Locale }>) {
  const ar = locale === "ar";
  const copy = ar ? {
    eyebrow: "دليل المطورين المنشور",
    intro: "نظرة عامة موثقة",
    introText: "يعرض هذا الملف المعلومات المنشورة من سجل المطور مع مصادرها وتاريخ التحقق منها.",
    focus: "مجال التطوير",
    emirate: "الإمارة الرئيسية",
    presence: "حضور إضافي في السوق",
    projects: "مراجع مختارة لهويات المشاريع",
    projectsNote: "تُعرض هذه الأسماء كمرجع للهوية فقط، ولا تعني التوفر أو الأسعار أو التخصيص.",
    verification: "المصدر والتحقق",
    verified: "تاريخ التحقق",
    note: "ملاحظة التحقق",
    website: "زيارة الموقع الرسمي",
    government: "فتح مصدر السجل",
    additional: "مصادر إضافية",
    enquire: "استفسر عن هذا المطور",
    enquireText: "تحقق من تفاصيل المشروع والتوفر والمعلومات الحالية قبل اتخاذ أي قرار.",
    related: "تابع الاستكشاف",
  } : {
    eyebrow: "PUBLISHED DEVELOPER DIRECTORY",
    intro: "Verified overview",
    introText: "This profile presents the published developer record with its sources and verification date.",
    focus: "Development focus",
    emirate: "Primary emirate",
    presence: "Additional market presence",
    projects: "Selected project identity references",
    projectsNote: "Names are shown for identity reference only and do not imply availability, pricing or allocation.",
    verification: "Source and verification",
    verified: "Verification date",
    note: "Verification note",
    website: "Visit official website",
    government: "Open registry source",
    additional: "Additional sources",
    enquire: "Enquire about this developer",
    enquireText: "Verify project details, availability and current information before making a decision.",
    related: "Continue exploring",
  };

  return (
    <div className="developer-profile-page" id="top">
      <main id="main-content">
        <section className="developer-profile-hero">
          <Reveal className="developer-profile-hero__copy" distance={18}>
            <p>{copy.eyebrow}</p>
            <h1 dir="ltr">{developer.name}</h1>
            <span>{developer.description}</span>
          </Reveal>
          <div className="developer-profile-hero__identity" aria-hidden="true"><span>01</span><small>{developer.primary_emirate}</small></div>
        </section>

        <section aria-labelledby="developer-overview-title" className="developer-profile-section developer-profile-overview">
          <div className="premium-home__heading"><p>{copy.intro}</p><h2 id="developer-overview-title">{copy.introText}</h2></div>
          <dl>
            <div><dt>{copy.focus}</dt><dd>{developer.focus}</dd></div>
            <div><dt>{copy.emirate}</dt><dd>{developer.primary_emirate}</dd></div>
            {developer.other_presence.length ? <div><dt>{copy.presence}</dt><dd>{developer.other_presence.join(" · ")}</dd></div> : null}
          </dl>
        </section>

        {developer.selected_projects.length ? (
          <section aria-labelledby="developer-projects-title" className="developer-profile-section developer-project-references">
            <div><p>{ar ? "علياس العقارية / مراجع الهوية" : "ARE / IDENTITY REFERENCES"}</p><h2 id="developer-projects-title">{copy.projects}</h2><span>{copy.projectsNote}</span></div>
            <ul>{developer.selected_projects.map((project) => <li key={project}>{project}</li>)}</ul>
          </section>
        ) : null}

        <section aria-labelledby="developer-sources-title" className="developer-profile-section developer-profile-sources">
          <div><p>{ar ? "علياس العقارية / المصادر" : "ARE / SOURCES"}</p><h2 id="developer-sources-title">{copy.verification}</h2></div>
          <dl>
            <div><dt>{copy.verified}</dt><dd><time dateTime={developer.verification_date}>{developer.verification_date}</time></dd></div>
            <div><dt>{copy.note}</dt><dd>{developer.verification_note}</dd></div>
          </dl>
          <div className="premium-home__actions">
            <a className="button button--primary animated-gold-border" href={developer.official_website} rel="noreferrer" target="_blank">{copy.website}</a>
            <a className="button button--secondary" href={developer.source_url} rel="noreferrer" target="_blank">{copy.government}</a>
          </div>
          {developer.additional_source_urls.length ? <div className="developer-profile-sources__additional"><strong>{copy.additional}</strong><ul>{developer.additional_source_urls.map((source, index) => <li key={source}><a href={source} rel="noreferrer" target="_blank">{ar ? `المصدر ${toArabicIndicDigits(index + 1)}` : `Source ${index + 1}`}</a></li>)}</ul></div> : null}
        </section>

        <section aria-labelledby="developer-enquiry-title" className="home-closing-v2 developer-profile-enquiry">
          <div><p>{ar ? "علياس العقارية / استفسار المطور" : "ARE / DEVELOPER ENQUIRY"}</p><h2 id="developer-enquiry-title">{copy.enquire}</h2><span>{copy.enquireText}</span></div>
          <Link className="button button--primary animated-gold-border" href={`/${locale}/contact?topic=developer&developer=${developer.slug}`}>{copy.enquire}</Link>
        </section>

        <RelatedPages heading={copy.related} items={ar ? [
          { href: `/${locale}/developers`, label: "دليل المطورين", text: "استكشف السجلات المنشورة الأخرى ومصادرها." },
          { href: `/${locale}/off-plan`, label: "فهم على المخطط", text: "راجع المسار والأسئلة العامة قبل تقييم مشروع." },
          { href: `/${locale}/contact`, label: "تواصل", text: "شارك متطلباتك والأسئلة التي تحتاج إلى التحقق منها." },
        ] : [
          { href: `/${locale}/developers`, label: "Developer directory", text: "Explore other published records and their sources." },
          { href: `/${locale}/off-plan`, label: "Understand off-plan", text: "Review the pathway and general questions before evaluating a project." },
          { href: `/${locale}/contact`, label: "Contact", text: "Share your requirements and the questions you need to verify." },
        ]} />
      </main>
      <SiteFooter copy={homeCopy[locale].header} locale={locale} />
    </div>
  );
}
