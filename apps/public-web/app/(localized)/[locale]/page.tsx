import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { FaqSection, ProcessList } from "../../../components/content/editorial-content";
import { Reveal } from "../../../components/motion/reveal";
import { SiteFooter } from "../../../components/navigation/site-footer";
import { DiscoverySearch } from "../../../components/search/discovery-search";
import { getDeveloper, getInsight } from "../../../lib/api";
import { homeCopy, isLocale, isPurpose, type Locale } from "../../../lib/home-copy";
import { homepageCopy } from "../../../lib/homepage-copy";

const journeyImages = {
  buy: "/images/home-premium/journey-buy.webp",
  rent: "/images/home-premium/journey-rent.webp",
  "off-plan": "/images/home-premium/journey-offplan.webp",
} as const;

type HomePageProps = Readonly<{
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ purpose?: string | string[] }>;
}>;

export async function generateMetadata({ params }: HomePageProps): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return homeCopy[locale].meta;
}

export default async function HomePage({ params, searchParams }: HomePageProps) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  if (!isLocale(locale)) notFound();
  const requestedPurpose = Array.isArray(query.purpose) ? query.purpose[0] : query.purpose;
  const initialPurpose = isPurpose(requestedPurpose) ? requestedPurpose : "buy";
  return <LocalizedHome initialPurpose={initialPurpose} locale={locale} />;
}

async function LocalizedHome({ locale, initialPurpose }: Readonly<{ locale: Locale; initialPurpose: "buy" | "rent" | "off-plan" }>) {
  const copy = homeCopy[locale];
  const content = homepageCopy[locale];
  const [featuredDeveloper, featuredInsight] = await Promise.all([
    getDeveloper(locale, "emaar-properties"),
    getInsight(locale, "choosing-a-uae-community"),
  ]);
  const insightCopy = featuredInsight?.content[locale];

  return (
    <div className="premium-home" id="top">
      <main id="main-content">
        <section aria-labelledby="hero-title" className="premium-home__hero">
          <div className="premium-home__hero-media">
            <Image
              alt={copy.hero.visualNote}
              className="premium-home__hero-image"
              height={941}
              priority
              sizes="100vw"
              src="/images/home-premium/hero-residence.webp"
              width={1672}
            />
            <div aria-hidden="true" className="premium-home__hero-shade" />
          </div>
          <div className="premium-home__hero-inner">
            <Reveal className="premium-home__hero-copy" distance={18}>
              <p className="premium-home__eyebrow">{copy.hero.eyebrow}</p>
              <h1 id="hero-title">{copy.hero.title}</h1>
              <span>{copy.hero.description}</span>
              <div className="premium-home__actions">
                <Link className="button button--primary" href={`/${locale}/contact`}>{copy.hero.primaryAction}</Link>
                <Link className="button button--secondary" href={`/${locale}/properties`}>{copy.hero.secondaryAction}</Link>
              </div>
            </Reveal>
            <div className="premium-home__image-note">
              <span>{copy.hero.visualLabel}</span>
              <small>{copy.hero.localReview}</small>
            </div>
          </div>
          <div className="premium-home__search">
            <div className="premium-home__search-heading" id="search">
              <p>{copy.searchHeading.eyebrow}</p>
              <h2>{copy.searchHeading.title}</h2>
            </div>
            <DiscoverySearch copy={copy.search} initialPurpose={initialPurpose} key={initialPurpose} locale={locale} />
          </div>
        </section>

        <section aria-labelledby="pathways-title" className="premium-home__section home-pathways-v2">
          <div className="premium-home__heading">
            <p>{copy.discovery.eyebrow}</p>
            <h2 id="pathways-title">{copy.discovery.title}</h2>
            <span>{copy.discovery.description}</span>
          </div>
          <div className="home-pathways-v2__grid home-pathways-v2__grid--image-led">
            {copy.journeys.map((journey, index) => (
              <Link href={journey.purpose === "off-plan" ? `/${locale}/off-plan` : `/${locale}/properties?purpose=${journey.purpose}`} key={journey.purpose}>
                <Image
                  alt={locale === "ar" ? `صورة توضيحية لمسار ${journey.title}` : `Illustrative residence for the ${journey.title} journey`}
                  height={1086}
                  sizes="(max-width: 800px) 100vw, 33vw"
                  src={journeyImages[journey.purpose]}
                  width={1448}
                />
                <span className="home-pathways-v2__shade" aria-hidden="true" />
                <span className="home-pathways-v2__number">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <p>{journey.eyebrow}</p>
                  <h3>{journey.title}</h3>
                  <small>{journey.text}</small>
                  <strong>{journey.linkLabel} <i aria-hidden="true">→</i></strong>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section aria-labelledby="approach-title" className="premium-home__section home-approach-v2">
          <div className="home-approach-v2__media">
            <Image alt={content.approach.imageAlt} height={1086} sizes="(max-width: 900px) 100vw, 55vw" src="/images/home-premium/aliyas-approach.webp" width={1448} />
            <span>{locale === "ar" ? "صورة تحريرية عامة — لا تمثل عقاراً بعينه" : "Generic editorial image — no specific property represented"}</span>
          </div>
          <div className="home-approach-v2__copy">
            <p>{content.approach.eyebrow}</p>
            <h2 id="approach-title">{content.approach.title}</h2>
            <span>{content.approach.text}</span>
            <ul>{content.approach.points.map((point, index) => <li key={point}><small>{String(index + 1).padStart(2, "0")}</small>{point}</li>)}</ul>
            <Link className="text-link" href={`/${locale}/about`}>{locale === "ar" ? "تعرّف إلى ALIYAS" : "Discover the ALIYAS approach"}</Link>
          </div>
        </section>

        <section aria-labelledby="guidance-title" className="premium-home__section home-guidance-v2">
          <div className="home-guidance-v2__composition">
            <figure className="home-guidance-v2__media home-guidance-v2__media--primary">
              <Image alt={content.guidance.communityImageAlt} height={1086} sizes="(max-width: 800px) 100vw, 56vw" src="/images/home-premium/uae-community.webp" width={1448} />
              <figcaption>{content.guidance.imageNote}</figcaption>
            </figure>
            <div className="home-guidance-v2__editorial">
              <div className="premium-home__heading">
                <p>{content.guidance.eyebrow}</p>
                <h2 id="guidance-title">{content.guidance.title}</h2>
                <span>{content.guidance.text}</span>
              </div>
              <div className="home-guidance-v2__links">
                {content.guidance.items.slice(0, 3).map((item, index) => {
                  const href = index === 0 ? `/${locale}/communities` : index === 1 ? `/${locale}/off-plan` : `/${locale}/properties`;
                  return <Link href={href} key={item.title}><span>{String(index + 1).padStart(2, "0")}</span><div><h3>{item.title}</h3><p>{item.text}</p></div></Link>;
                })}
              </div>
            </div>
          </div>
        </section>

        {featuredDeveloper ? (
          <section aria-labelledby="developer-spotlight-title" className="premium-home__section home-developer-spotlight">
            <div className="home-developer-spotlight__intro">
              <p>{content.developer.eyebrow}</p>
              <h2 id="developer-spotlight-title">{content.developer.title}</h2>
            </div>
            <figure className="home-developer-spotlight__media">
              <Image alt={content.developer.imageAlt} height={1086} sizes="(max-width: 1100px) 100vw, 32vw" src="/images/home-premium/architecture-detail.webp" width={1448} />
              <figcaption>{content.developer.imageNote}</figcaption>
            </figure>
            <article>
              <div className="home-developer-spotlight__monogram" aria-hidden="true">01</div>
              <div className="home-developer-spotlight__content">
                <p>{content.developer.verified}: <time dateTime={featuredDeveloper.verification_date}>{featuredDeveloper.verification_date}</time></p>
                <h3 dir="ltr">{featuredDeveloper.name}</h3>
                <span>{featuredDeveloper.description}</span>
                <dl>
                  <div><dt>{content.developer.focus}</dt><dd>{featuredDeveloper.focus}</dd></div>
                  <div><dt>{content.developer.emirate}</dt><dd>{featuredDeveloper.primary_emirate}</dd></div>
                  <div><dt>{content.developer.source}</dt><dd>{featuredDeveloper.verification_note}</dd></div>
                </dl>
                <div className="premium-home__actions">
                  <Link className="button button--primary" href={`/${locale}/developers/${featuredDeveloper.slug}`}>{content.developer.details}</Link>
                  <Link className="button button--secondary" href={`/${locale}/contact?topic=developer&developer=${featuredDeveloper.slug}`}>{content.developer.enquire}</Link>
                </div>
              </div>
            </article>
          </section>
        ) : null}

        {featuredInsight && insightCopy ? (
          <section aria-labelledby="insight-spotlight-title" className="premium-home__section home-insight-spotlight">
            <div>
              <p>{content.insight.eyebrow}</p>
              <h2 id="insight-spotlight-title">{content.insight.title}</h2>
              <span>{content.insight.editorial}</span>
            </div>
            <article className="home-insight-spotlight__article">
              <div className="home-insight-spotlight__media">
                <Image alt={content.insight.imageAlt} height={1086} sizes="(max-width: 1100px) 100vw, 58vw" src="/images/home-premium/insight-community.webp" width={1448} />
              </div>
              <div className="home-insight-spotlight__copy">
              <p>{insightCopy.categoryLabel} · <time dateTime={featuredInsight.updated}>{featuredInsight.updated}</time></p>
              <h3>{insightCopy.title}</h3>
              <span>{insightCopy.metaDescription}</span>
              <Link className="text-link" href={`/${locale}/insights/${featuredInsight.slug}`}>{content.insight.read}</Link>
              </div>
            </article>
          </section>
        ) : null}

        <section aria-labelledby="process-title" className="premium-home__section home-process-v2">
          <div className="premium-home__heading">
            <p>{content.process.eyebrow}</p>
            <h2 id="process-title">{content.process.title}</h2>
            <span>{content.process.text}</span>
          </div>
          <ProcessList items={content.process.items} />
        </section>

        <FaqSection eyebrow={content.faq.eyebrow} heading={content.faq.title} items={content.faq.items} />

        <section aria-labelledby="home-closing-title" className="home-closing-v2 home-closing-v2--image-led home-closing-v2--separated">
          <Image alt={content.cta.imageAlt} className="home-closing-v2__image" height={841} sizes="(max-width: 800px) 100vw, 1200px" src="/images/home-premium/enquiry-cta.webp" width={1870} />
          <span className="home-closing-v2__shade" aria-hidden="true" />
          <div className="home-closing-v2__content"><p>{content.cta.eyebrow}</p><h2 id="home-closing-title">{content.cta.title}</h2><span>{content.cta.text}</span></div>
          <div className="premium-home__actions home-closing-v2__actions">
            <Link className="button button--primary" href={`/${locale}/contact`}>{content.cta.enquire}</Link>
            <a className="button button--secondary" href="https://wa.me/971569157576" rel="noreferrer" target="_blank">{content.cta.whatsapp}</a>
          </div>
        </section>
      </main>
      <SiteFooter copy={copy.header} locale={locale} />
    </div>
  );
}
