import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Reveal } from "../../../components/motion/reveal";
import {
  Breadcrumbs,
  FaqSection,
  FinalCta,
  ProcessList,
} from "../../../components/content/editorial-content";
import { SiteFooter } from "../../../components/navigation/site-footer";
import { SiteHeader } from "../../../components/navigation/site-header";
import { DiscoverySearch } from "../../../components/search/discovery-search";
import { homeCopy, isLocale, isPurpose, type Locale } from "../../../lib/home-copy";
import { developers } from "../../../lib/developers-data";
import { insightArticles } from "../../../lib/insights-data";
import { richCopy } from "../../../lib/rich-copy";

type HomePageProps = Readonly<{
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ purpose?: string | string[] }>;
}>;

export async function generateMetadata({ params }: HomePageProps): Promise<Metadata> {
  const { locale } = await params;

  if (!isLocale(locale)) {
    notFound();
  }

  const copy = homeCopy[locale];

  return {
    title: copy.meta.title,
    description: copy.meta.description,
  };
}

export default async function HomePage({ params, searchParams }: HomePageProps) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);

  if (!isLocale(locale)) {
    notFound();
  }

  const requestedPurpose = Array.isArray(query.purpose) ? query.purpose[0] : query.purpose;
  const initialPurpose = isPurpose(requestedPurpose) ? requestedPurpose : "buy";

  return <LocalizedHome locale={locale} initialPurpose={initialPurpose} />;
}

function LocalizedHome({ locale, initialPurpose }: { locale: Locale; initialPurpose: "buy" | "rent" | "off-plan" }) {
  const copy = homeCopy[locale];
  const editorial = richCopy[locale].home;
  const selectedDevelopers = ["emaar-properties", "aldar-properties", "al-hamra"]
    .map((slug) => developers.find((developer) => developer.slug === slug))
    .filter((developer): developer is (typeof developers)[number] => Boolean(developer));

  return (
    <div id="top">
      <SiteHeader copy={copy.header} locale={locale} />

      <main id="main-content">
        <section aria-labelledby="hero-title" className="hero-section">
          <div className="hero-orbit hero-orbit--one" aria-hidden="true" />
          <div className="hero-orbit hero-orbit--two" aria-hidden="true" />

          <div className="hero-shell">
            <Breadcrumbs items={[{ label: richCopy[locale].homeLabel }]} label={richCopy[locale].breadcrumb} />
            <div className="hero-grid">
              <div className="hero-copy">
                <Reveal className="hero-eyebrow" delay={0.04} distance={10}>
                  <span aria-hidden="true" />
                  <p>{copy.hero.eyebrow}</p>
                </Reveal>

                <Reveal delay={0.1} distance={20}>
                  <h1 id="hero-title">{copy.hero.title}</h1>
                </Reveal>

                <Reveal delay={0.16} distance={16}>
                  <p className="hero-description">{copy.hero.description}</p>
                </Reveal>

                <div className="hero-actions">
                  <Link className="button button--primary" href={`/${locale}/properties`}>
                    {copy.hero.primaryAction}
                  </Link>
                  <Link className="button button--secondary" href={`/${locale}/about`}>
                    {copy.hero.secondaryAction}
                  </Link>
                </div>

                <div className="hero-coordinate">
                  <span>{copy.hero.previewLabel}</span>
                  <span aria-hidden="true" />
                  <span>UAE</span>
                  <small>{copy.hero.localReview}</small>
                </div>
              </div>

              <Reveal className="hero-visual-wrap" delay={0.14} distance={24}>
                <div className="architectural-scene">
                  <div className="scene-glow" aria-hidden="true" />
                  <div className="scene-grid" aria-hidden="true" />
                  <div className="scene-sun" aria-hidden="true" />
                  <div className="scene-tower scene-tower--rear" aria-hidden="true" />
                  <div className="scene-tower scene-tower--main" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </div>
                  <div className="scene-tower scene-tower--front" aria-hidden="true" />
                  <div className="scene-plinth" aria-hidden="true" />
                  <div className="scene-frame" aria-hidden="true">
                    <span>ARE / 01</span>
                  </div>
                  <div className="scene-caption">
                    <span>{copy.hero.visualLabel}</span>
                    <p>{copy.hero.visualNote}</p>
                  </div>
                </div>
              </Reveal>
            </div>

            <div className="search-panel">
              <div className="search-panel__heading" id="search">
                <div>
                  <span>{copy.searchHeading.eyebrow}</span>
                  <h2>{copy.searchHeading.title}</h2>
                </div>
                <p>01 — 03</p>
              </div>
              <DiscoverySearch
                copy={copy.search}
                initialPurpose={initialPurpose}
                key={initialPurpose}
                locale={locale}
              />
            </div>
          </div>
        </section>

        <section aria-labelledby="discovery-title" className="discovery-section" id="discovery">
          <div className="section-intro" id="approach">
            <div className="section-kicker">
              <span>{copy.discovery.eyebrow}</span>
              <span>{copy.discovery.label}</span>
            </div>
            <div>
              <h2 id="discovery-title">{copy.discovery.title}</h2>
            </div>
            <div>
              <p>{copy.discovery.description}</p>
            </div>
          </div>

          <div className="discovery-grid">
            {copy.journeys.map((card) => (
              <article
                className={`discovery-card ${card.className}`}
                id={card.purpose === "off-plan" ? "off-plan" : undefined}
                key={card.purpose}
              >
                <div className="discovery-card__visual" aria-hidden="true">
                  <span className="discovery-card__plane discovery-card__plane--one" />
                  <span className="discovery-card__plane discovery-card__plane--two" />
                  <span className="discovery-card__line" />
                </div>
                <div className="discovery-card__content">
                  <p>{card.eyebrow}</p>
                  <h3>{card.title}</h3>
                  <p className="discovery-card__description">{card.text}</p>
                  <Link
                    href={
                      card.purpose === "off-plan"
                        ? `/${locale}/off-plan`
                        : `/${locale}/properties?purpose=${card.purpose}`
                    }
                  >
                    {card.linkLabel}
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section aria-labelledby="home-intro-title" className="content-section content-section--intro home-clarity">
          <div className="content-heading">
            <p>{editorial.intro.eyebrow}</p>
            <h2 id="home-intro-title">{editorial.intro.title}</h2>
          </div>
          <p className="content-lead">{editorial.intro.text}</p>
        </section>

        <section aria-labelledby="home-developers-title" className="content-section home-developers">
          <div className="content-heading">
            <p>{locale === "ar" ? "مطوّرون مختارون" : "SELECTED UAE DEVELOPERS"}</p>
            <h2 id="home-developers-title">{locale === "ar" ? "ابدأ بالهوية الموثقة والمصدر الرسمي." : "Start with a verified identity and official source."}</h2>
            <span>{locale === "ar" ? "مجموعة موجزة من دليلنا الذي يضم 20 مطوراً؛ وتتطلب المشاريع والأسعار والتوفر تحققاً حديثاً." : "A concise selection from our 20-record directory. Projects, pricing and availability still require fresh verification."}</span>
          </div>
          <div className="home-developer-list">
            {selectedDevelopers.map((developer, index) => (
              <article key={developer.slug}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3 dir="ltr">{developer.officialName}</h3>
                  <p>{developer.focus[locale]}</p>
                </div>
              </article>
            ))}
          </div>
          <Link className="button button--secondary home-section-action" href={`/${locale}/developers`}>
            {locale === "ar" ? "استكشف دليل المطورين" : "Explore the developer directory"}
          </Link>
        </section>

        <section aria-label={locale === "ar" ? "مسارات مميزة" : "Featured pathways"} className="feature-pathways">
          <Link href={`/${locale}/communities`}>
            <span>{locale === "ar" ? "دليل المجتمعات" : "COMMUNITY FEATURE"}</span>
            <h2>{locale === "ar" ? "ابدأ بالمكان الذي يدعم يومك." : "Begin with the place that supports your day."}</h2>
            <p>{locale === "ar" ? "قارن طابع المكان والروتين وسهولة الوصول قبل اختيار نوع المسكن." : "Compare character, routine and connection before narrowing the home type."}</p>
          </Link>
          <Link href={`/${locale}/off-plan`}>
            <span>{locale === "ar" ? "دليل على المخطط" : "OFF-PLAN GUIDE"}</span>
            <h2>{locale === "ar" ? "افهم المسار قبل مقارنة الفرص." : "Understand the pathway before comparing opportunities."}</h2>
            <p>{locale === "ar" ? "تعرّف إلى الأسئلة العامة عن الوثائق والمراحل والعناية الواجبة." : "Learn the general questions behind documents, milestones and due diligence."}</p>
          </Link>
        </section>

        <section aria-labelledby="home-process-title" className="content-section content-section--dark home-process">
          <div className="content-heading"><p>{editorial.sections[0].eyebrow}</p><h2 id="home-process-title">{editorial.sections[0].title}</h2><span>{editorial.sections[0].text}</span></div>
          <ProcessList items={editorial.sections[0].items} />
        </section>

        <section aria-labelledby="home-insights-title" className="content-section home-insights">
          <div className="content-heading">
            <p>{locale === "ar" ? "أحدث الرؤى" : "LATEST INSIGHTS"}</p>
            <h2 id="home-insights-title">{locale === "ar" ? "اقرأ، ثم تحقّق مما يخص قرارك." : "Read first, then verify what matters to your decision."}</h2>
          </div>
          <div className="home-insight-grid">
            {insightArticles.map((article) => {
              const articleCopy = article.content[locale];
              return (
                <article key={article.slug}>
                  <p>{articleCopy.categoryLabel} · <time dateTime={article.updated}>{article.updated}</time></p>
                  <h3><Link href={`/${locale}/insights/${article.slug}`}>{articleCopy.title}</Link></h3>
                  <span>{articleCopy.metaDescription}</span>
                </article>
              );
            })}
          </div>
          <Link className="text-link home-section-action" href={`/${locale}/insights`}>
            {locale === "ar" ? "استكشف جميع الرؤى" : "Explore all insights"}
          </Link>
        </section>
        <FaqSection eyebrow={editorial.faq.eyebrow} heading={editorial.faq.title} items={editorial.faq.items.slice(0, 4)} />
        <FinalCta action={editorial.cta.action} heading={editorial.cta.title} href={editorial.cta.href} locale={locale} text={editorial.cta.text} />
      </main>
      <SiteFooter copy={copy.header} locale={locale} />
    </div>
  );
}
