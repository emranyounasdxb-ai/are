import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Breadcrumbs, FinalCta, RelatedPages } from "../../../../components/content/editorial-content";
import { InsightsExplorer } from "../../../../components/insights/insights-explorer";
import { Reveal } from "../../../../components/motion/reveal";
import { SiteFooter } from "../../../../components/navigation/site-footer";
import { SiteHeader } from "../../../../components/navigation/site-header";
import { homeCopy, isLocale, locales, type Locale } from "../../../../lib/home-copy";
import { insightArticles, verifiedUpdates } from "../../../../lib/insights-data";
import { richCopy } from "../../../../lib/rich-copy";

type Props = Readonly<{ params: Promise<{ locale: string }> }>;
export const dynamicParams = false;
export function generateStaticParams() { return locales.map((locale) => ({ locale })); }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params; if (!isLocale(locale)) notFound();
  return locale === "ar" ? { title: "الرؤى | ALIYAS Real Estate", description: "أدلة عقارية ورؤى سوقية وأخبار رسمية موثقة تساعد على تنظيم البحث العقاري في الإمارات." } : { title: "Insights | ALIYAS Real Estate", description: "Practical property guides, market perspectives and verified official updates for a clearer UAE property search." };
}

export default async function InsightsPage({ params }: Props) { const { locale } = await params; if (!isLocale(locale)) notFound(); return <LocalizedInsights locale={locale} />; }

function LocalizedInsights({ locale }: Readonly<{ locale: Locale }>) {
  const ar = locale === "ar";
  const copy = ar ? {
    eyebrow: "معرفة موثوقة", title: "رؤى تساعدك على طرح أسئلة أفضل.", intro: "مكتبة ثنائية اللغة من الأدلة العملية والرؤى المتوازنة والأخبار المرتبطة بمصادر رسمية. لا تحل هذه المواد محل التحقق الحالي أو المشورة المهنية.", featured: "موضوع مميز", featuredTitle: "ابدأ بروتينك اليومي قبل اختيار المجتمع", featuredText: "إطار يضع الأشخاص والرحلات والاحتياجات العقارية قبل الترتيب العام أو الادعاءات غير الموثقة.", featuredAction: "اقرأ الدليل", library: "مكتبة الرؤى", libraryTitle: "ابحث وصفِّ حسب ما تحتاجه الآن", standards: "معايير التحرير", standardsTitle: "كيف نتعامل مع المعلومات", standardsText: "نفرّق بين الإرشاد العام والمعلومات الحالية، ونربط الأخبار بالمصدر الرسمي، ونذكر تاريخ التحقق، ولا نخترع أسعاراً أو مخزوناً أو توقعات أو نصائح شخصية.", contactTitle: "هل لديك سؤال يحتاج إلى سياق؟", contactText: "رتّب استفسارك بوضوح، ثم تحقق من التفاصيل الحالية والوثائق المناسبة قبل اتخاذ قرار.", contactAction: "جهّز استفساراً", relatedTitle: "واصل الاستكشاف", ctaTitle: "حوّل القراءة إلى موجز واضح.", ctaText: "شارك أولوياتك والأسئلة التي تحتاج إلى تحقق حديث.", ctaAction: "ابدأ محادثة",
  } : {
    eyebrow: "Evidence-aware knowledge", title: "Insights that help you ask better questions.", intro: "A bilingual library of practical guides, balanced perspectives and updates tied to official sources. The material does not replace current verification or professional advice.", featured: "Featured guide", featuredTitle: "Begin with daily life before choosing a community", featuredText: "A people-first framework that puts routines, journeys and property needs ahead of rankings or unsupported claims.", featuredAction: "Read the guide", library: "Insights library", libraryTitle: "Search and filter for what you need now", standards: "Editorial standards", standardsTitle: "How we handle information", standardsText: "We distinguish general guidance from current information, link news to an official source, show verification dates, and do not invent pricing, inventory, forecasts or personal advice.", contactTitle: "Have a question that needs context?", contactText: "Organise the enquiry clearly, then verify current details and appropriate documents before making a decision.", contactAction: "Prepare an enquiry", relatedTitle: "Continue exploring", ctaTitle: "Turn reading into a clear brief.", ctaText: "Share your priorities and the questions that need fresh verification.", ctaAction: "Start a conversation",
  };
  return <div className="insights-page" id="top"><SiteHeader copy={homeCopy[locale].header} locale={locale} /><main id="main-content">
    <section className="editorial-hero"><div className="editorial-hero__inner"><Breadcrumbs items={[{ href: `/${locale}`, label: richCopy[locale].homeLabel }, { label: homeCopy[locale].header.insights }]} label={richCopy[locale].breadcrumb} /><Reveal className="editorial-hero__reveal" distance={18}><p>{copy.eyebrow}</p><h1>{copy.title}</h1><span>{copy.intro}</span></Reveal></div></section>
    <section className="featured-insight"><div><p>{copy.featured}</p><h2>{copy.featuredTitle}</h2><span>{copy.featuredText}</span><Link className="button button--primary" href={`/${locale}/insights/choosing-a-uae-community`}>{copy.featuredAction}<span aria-hidden="true" className="directional-icon">↗</span></Link></div><div aria-hidden="true" className="featured-insight__monogram"><span>ARE</span><small>01 / GUIDE</small></div></section>
    <section aria-labelledby="insights-library-title" className="content-section insights-library"><div className="content-heading"><p>{copy.library}</p><h2 id="insights-library-title">{copy.libraryTitle}</h2></div><InsightsExplorer articles={insightArticles} locale={locale} updates={verifiedUpdates} /></section>
    <section className="content-section content-section--split content-section--dark"><div className="content-heading"><p>{copy.standards}</p><h2>{copy.standardsTitle}</h2></div><p className="content-lead">{copy.standardsText}</p></section>
    <section className="insights-contact"><div><h2>{copy.contactTitle}</h2><p>{copy.contactText}</p></div><Link className="button button--secondary" href={`/${locale}/contact`}>{copy.contactAction}</Link></section>
    <RelatedPages heading={copy.relatedTitle} items={ar ? [{ href: "/ar/properties", label: "العقارات", text: "حوّل أولوياتك إلى موجز بحث." }, { href: "/ar/communities", label: "المجتمعات", text: "ابدأ بإيقاع الحياة اليومي." }, { href: "/ar/off-plan", label: "عقارات على المخطط", text: "افهم مساراً عاماً ومدروساً." }, { href: "/ar/contact", label: "تواصل", text: "نظّم الأسئلة التي تحتاج إلى تحقق." }] : [{ href: "/en/properties", label: "Properties", text: "Turn priorities into a search brief." }, { href: "/en/communities", label: "Communities", text: "Begin with everyday life." }, { href: "/en/off-plan", label: "Off-plan", text: "Understand a careful general pathway." }, { href: "/en/contact", label: "Contact", text: "Organise questions that need verification." }]} />
    <FinalCta action={copy.ctaAction} heading={copy.ctaTitle} href={`/${locale}/contact`} locale={locale} text={copy.ctaText} />
  </main><SiteFooter copy={homeCopy[locale].header} locale={locale} /></div>;
}
