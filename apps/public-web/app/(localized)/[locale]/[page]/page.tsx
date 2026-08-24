import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ContactPreviewForm } from "../../../../components/forms/contact-preview-form";
import { SiteFooter } from "../../../../components/navigation/site-footer";
import { SiteHeader } from "../../../../components/navigation/site-header";
import { DiscoverySearch } from "../../../../components/search/discovery-search";
import { homeCopy, isLocale, locales, type Locale, type Purpose } from "../../../../lib/home-copy";
import { isPageSlug, pageSlugs, siteCopy, type PageSlug } from "../../../../lib/site-copy";

type SearchParams = Record<string, string | string[] | undefined>;

type InnerPageProps = Readonly<{
  params: Promise<{ locale: string; page: string }>;
  searchParams: Promise<SearchParams>;
}>;

export const dynamicParams = false;

export function generateStaticParams() {
  return locales.flatMap((locale) => pageSlugs.map((page) => ({ locale, page })));
}

export async function generateMetadata({ params }: InnerPageProps): Promise<Metadata> {
  const { locale, page } = await params;

  if (!isLocale(locale) || !isPageSlug(page)) {
    notFound();
  }

  const copy = siteCopy[locale].pages[page];

  return {
    title: copy.metaTitle,
    description: copy.metaDescription,
    alternates: {
      canonical: `/${locale}/${page}`,
      languages: {
        en: `/en/${page}`,
        ar: `/ar/${page}`,
        "x-default": `/en/${page}`,
      },
    },
  };
}

export default async function InnerPage({ params, searchParams }: InnerPageProps) {
  const [{ locale, page }, query] = await Promise.all([params, searchParams]);

  if (!isLocale(locale) || !isPageSlug(page)) {
    notFound();
  }

  return <LocalizedInnerPage locale={locale} page={page} query={query} />;
}

function LocalizedInnerPage({
  locale,
  page,
  query,
}: Readonly<{ locale: Locale; page: PageSlug; query: SearchParams }>) {
  const home = homeCopy[locale];
  const site = siteCopy[locale];
  const copy = site.pages[page];

  return (
    <div className={`inner-page inner-page--${page}`} id="top">
      <SiteHeader copy={home.header} locale={locale} />
      <main id="main-content">
        <section aria-labelledby="page-title" className="inner-hero">
          <div className="inner-hero__orbit" aria-hidden="true" />
          <div className="inner-hero__grid">
            <div className="inner-hero__copy">
              <p>{copy.eyebrow}</p>
              <h1 id="page-title">{copy.title}</h1>
              <span>{copy.description}</span>
            </div>
            <div className="inner-hero__art" aria-hidden="true">
              <span />
              <span />
              <span />
              <small>ARE / {String(pageSlugs.indexOf(page) + 2).padStart(2, "0")}</small>
            </div>
          </div>
        </section>
        {renderPageContent(locale, page, query)}
      </main>
      <SiteFooter copy={home.header} locale={locale} />
    </div>
  );
}

function renderPageContent(locale: Locale, page: PageSlug, query: SearchParams) {
  if (page === "properties") {
    return <PropertiesContent locale={locale} query={query} />;
  }

  if (page === "communities") {
    return <CommunitiesContent locale={locale} />;
  }

  if (page === "off-plan") {
    return <OffPlanContent locale={locale} />;
  }

  if (page === "about") {
    return <AboutContent locale={locale} />;
  }

  return <ContactContent locale={locale} />;
}

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function PropertiesContent({ locale, query }: Readonly<{ locale: Locale; query: SearchParams }>) {
  const home = homeCopy[locale];
  const copy = siteCopy[locale].properties;
  const locationValue = firstValue(query.location);
  const typeValue = firstValue(query.type);
  const purposeValue = firstValue(query.purpose);
  const location = home.search.locations.find((item) => item.value === locationValue);
  const propertyType = home.search.propertyTypes.find((item) => item.value === typeValue);
  const selectedPurpose = purposeValue === "buy" || purposeValue === "rent" ? purposeValue : undefined;
  const purpose: Purpose = selectedPurpose ?? "buy";
  const hasCriteria = Boolean(location || propertyType || selectedPurpose);

  return (
    <section aria-labelledby="property-search-title" className="inner-section property-workbench">
      <div className="property-workbench__search">
        <div className="inner-section__heading">
          <p>{home.searchHeading.eyebrow}</p>
          <h2 id="property-search-title">{home.searchHeading.title}</h2>
        </div>
        <DiscoverySearch
          copy={home.search}
          initialLocation={location?.value}
          initialPropertyType={propertyType?.value}
          initialPurpose={purpose}
          key={`${location?.value}-${propertyType?.value}-${purpose}`}
          locale={locale}
          purposes={["buy", "rent"]}
        />
      </div>
      <aside className="criteria-summary">
        <p>ARE / FILTER</p>
        <h2>{copy.criteriaHeading}</h2>
        <span>{copy.criteriaIntro}</span>
        {hasCriteria ? (
          <dl>
            {location ? <div><dt>{home.search.locationLabel}</dt><dd>{location.label}</dd></div> : null}
            {propertyType ? <div><dt>{home.search.propertyTypeLabel}</dt><dd>{propertyType.label}</dd></div> : null}
            {selectedPurpose ? <div><dt>{home.search.purposeLabel}</dt><dd>{home.search.purposes[selectedPurpose]}</dd></div> : null}
          </dl>
        ) : (
          <p className="criteria-summary__empty">{copy.criteriaNone}</p>
        )}
        <small>{copy.inventoryNote}</small>
      </aside>
    </section>
  );
}

function CommunitiesContent({ locale }: Readonly<{ locale: Locale }>) {
  const copy = siteCopy[locale].communities;

  return (
    <section aria-labelledby="communities-title" className="inner-section communities-editorial">
      <div className="communities-editorial__title">
        <p>ARE / PLACE</p>
        <h2 id="communities-title">{copy.sectionTitle}</h2>
      </div>
      <div className="community-lenses">
        {copy.categories.map((item, index) => (
          <article key={item.label}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <h3>{item.label}</h3>
            <p>{item.text}</p>
          </article>
        ))}
      </div>
      <div className="inner-actions">
        <Link className="button button--primary" href={`/${locale}/properties`}>{copy.discoveryAction}</Link>
        <Link className="text-link" href={`/${locale}/contact`}>{copy.enquiryAction} <span aria-hidden="true" className="directional-icon">↗</span></Link>
      </div>
    </section>
  );
}

function OffPlanContent({ locale }: Readonly<{ locale: Locale }>) {
  const copy = siteCopy[locale].offPlan;

  return (
    <section aria-labelledby="off-plan-title" className="inner-section off-plan-pathway">
      <div className="off-plan-pathway__heading">
        <p>ARE / PATHWAY</p>
        <h2 id="off-plan-title">{copy.sectionTitle}</h2>
      </div>
      <ol>
        {copy.steps.map((item, index) => (
          <li key={item.label}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <div><h3>{item.label}</h3><p>{item.text}</p></div>
          </li>
        ))}
      </ol>
      <div className="inner-actions">
        <Link className="button button--primary" href={`/${locale}/contact`}>{copy.enquiryAction}</Link>
        <Link className="text-link" href={`/${locale}/properties`}>{copy.searchAction} <span aria-hidden="true" className="directional-icon">↗</span></Link>
      </div>
    </section>
  );
}

function AboutContent({ locale }: Readonly<{ locale: Locale }>) {
  const copy = siteCopy[locale].about;

  return (
    <section aria-labelledby="about-title" className="inner-section about-manifesto">
      <div className="about-manifesto__statement">
        <p>ALIYAS / APPROACH</p>
        <h2 id="about-title">{copy.sectionTitle}</h2>
      </div>
      <div className="about-principles">
        {copy.principles.map((item) => (
          <article key={item.label}><h3>{item.label}</h3><p>{item.text}</p></article>
        ))}
        <Link className="button button--primary" href={`/${locale}/contact`}>{copy.action}</Link>
      </div>
    </section>
  );
}

function ContactContent({ locale }: Readonly<{ locale: Locale }>) {
  const copy = siteCopy[locale].contact;

  return (
    <section aria-labelledby="contact-form-title" className="inner-section contact-experience">
      <div className="contact-experience__context">
        <p>ARE / ENQUIRY</p>
        <h2 id="contact-form-title">{locale === "ar" ? "معاينة استفسار واضحة وآمنة" : "A clear, safe enquiry preview"}</h2>
        <span>{copy.intro}</span>
      </div>
      <ContactPreviewForm locale={locale} />
    </section>
  );
}
