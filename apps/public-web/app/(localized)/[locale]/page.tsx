import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Reveal } from "../../../components/motion/reveal";
import { SiteFooter } from "../../../components/navigation/site-footer";
import { SiteHeader } from "../../../components/navigation/site-header";
import { DiscoverySearch } from "../../../components/search/discovery-search";
import { homeCopy, isLocale, isPurpose, type Locale } from "../../../lib/home-copy";

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
    alternates: {
      canonical: `/${locale}`,
      languages: {
        en: "/en",
        ar: "/ar",
        "x-default": "/en",
      },
    },
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

  return (
    <div id="top">
      <SiteHeader copy={copy.header} locale={locale} />

      <main id="main-content">
        <section aria-labelledby="hero-title" className="hero-section">
          <div className="hero-orbit hero-orbit--one" aria-hidden="true" />
          <div className="hero-orbit hero-orbit--two" aria-hidden="true" />

          <div className="hero-shell">
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
                    <span aria-hidden="true" className="directional-icon">
                      ↗
                    </span>
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
                    <span aria-hidden="true" className="directional-icon">
                      ↗
                    </span>
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
      <SiteFooter copy={copy.header} locale={locale} />
    </div>
  );
}
