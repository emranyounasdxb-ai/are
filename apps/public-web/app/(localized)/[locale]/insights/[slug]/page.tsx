import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Checklist, EditorialCards, FaqSection, FinalCta, RelatedPages } from "../../../../../components/content/editorial-content";
import { SiteFooter } from "../../../../../components/navigation/site-footer";
import { Reveal } from "../../../../../components/motion/reveal";
import { homeCopy, isLocale, type Locale } from "../../../../../lib/home-copy";
import { calculateReadingTime, type InsightArticle } from "../../../../../lib/insights-data";
import { getInsight } from "../../../../../lib/api";
import { localizedBrand, normalizeArabicContent, toArabicIndicDigits } from "../../../../../lib/arabic-localization";

type Props = Readonly<{ params: Promise<{ locale: string; slug: string }> }>;
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: Props): Promise<Metadata> { const { locale, slug } = await params; if (!isLocale(locale)) notFound(); const article = await getInsight(locale, slug); if (!article) return {}; const copy = locale === "ar" ? normalizeArabicContent(article.content[locale]) : article.content[locale]; return { title: `${copy.title} | ${localizedBrand(locale)}`, description: copy.metaDescription }; }
export default async function InsightArticlePage({ params }: Props) { const { locale, slug } = await params; if (!isLocale(locale)) notFound(); const article = await getInsight(locale, slug); if (!article) notFound(); return <LocalizedArticle article={article} locale={locale} />; }

function LocalizedArticle({ locale, article }: Readonly<{ locale: Locale; article: InsightArticle }>) {
  const copy = locale === "ar" ? normalizeArabicContent(article.content[locale]) : article.content[locale]; const ar = locale === "ar"; const minutes = calculateReadingTime(article, locale);
  return <div className="article-page" id="top"><main id="main-content">
    <article>
      <header className="article-hero"><div className="article-hero__inner"><Reveal className="article-hero__reveal" distance={18}><p>{copy.categoryLabel} / {ar ? "دليل تحريري واعٍ بالمصادر" : "SOURCE-AWARE EDITORIAL GUIDE"}</p><h1>{copy.title}</h1><span className="article-hero__excerpt">{copy.metaDescription}</span><div className="article-meta"><span>{ar ? "نُشر" : "Published"}: <time dateTime={article.published}>{ar ? toArabicIndicDigits(article.published) : article.published}</time></span><span>{ar ? "حُدث" : "Updated"}: <time dateTime={article.updated}>{ar ? toArabicIndicDigits(article.updated) : article.updated}</time></span><span>{ar ? toArabicIndicDigits(minutes) : minutes} {ar ? "دقائق قراءة" : "min read"}</span></div></Reveal></div></header>
      <div className="article-layout"><aside className="article-toc"><strong>{ar ? "في هذا الدليل" : "In this guide"}</strong><nav aria-label={ar ? "محتويات المقال" : "Article contents"}>{copy.sections.map((section, index) => <a href={`#section-${index + 1}`} key={section.heading}>{section.heading}</a>)}<a href="#checklist">{copy.checklistTitle}</a><a href="#sources">{copy.sourcesTitle}</a></nav></aside><div className="article-body">
        <p className="article-lead">{copy.introduction}</p>
        {copy.sections.map((section, index) => <section id={`section-${index + 1}`} key={section.heading}><span aria-hidden="true">{ar ? toArabicIndicDigits(String(index + 1).padStart(2, "0")) : String(index + 1).padStart(2, "0")}</span><h2>{section.heading}</h2>{section.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</section>)}
        <section className="article-checklist" id="checklist"><h2>{copy.checklistTitle}</h2><p>{copy.checklistIntro}</p><Checklist items={copy.checklist} /></section>
        <section><h2>{copy.considerationsTitle}</h2><EditorialCards items={copy.considerations} /></section>
        <aside className="article-limitation"><h2>{copy.limitationsTitle}</h2><p>{copy.limitations}</p></aside>
        <section className="article-sources" id="sources"><h2>{copy.sourcesTitle}</h2><ul>{article.sources.map((source, index) => <li key={source.url}><a href={source.url} rel="noreferrer" target="_blank">{ar ? `المصدر الرسمي ${toArabicIndicDigits(index + 1)}` : source.name}<span aria-hidden="true">↗</span></a></li>)}</ul><p>{ar ? `تمت مراجعة هذه المراجع في ${toArabicIndicDigits(article.updated)}. أعد التحقق منها قبل الاعتماد على معلومات حالية.` : `These references were reviewed on ${article.updated}. Recheck them before relying on current information.`}</p></section>
        <Link className="article-back" href={`/${locale}/insights`}>← {ar ? "العودة إلى جميع الرؤى" : "Back to all insights"}</Link>
      </div></div>
    </article>
    <FaqSection eyebrow="ARE / FAQ" heading={copy.faqTitle} items={copy.faq} /><RelatedPages heading={copy.relatedTitle} items={copy.related} /><FinalCta action={ar ? "جهّز استفساراً" : "Prepare an enquiry"} heading={ar ? "هل تحتاج إلى تحقق خاص بحالتك؟" : "Need case-specific verification?"} href={`/${locale}/contact`} locale={locale} text={ar ? "استخدم هذا الدليل لتنظيم الأسئلة، ثم تحقق من الوثائق والمعلومات الحالية." : "Use the guide to organise questions, then verify current information and documents."} />
  </main><SiteFooter copy={homeCopy[locale].header} locale={locale} /></div>;
}
