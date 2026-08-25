import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ContactPreviewForm } from "../../../../components/forms/contact-preview-form";
import {
  Breadcrumbs,
  Checklist,
  EditorialCards,
  FaqSection,
  FinalCta,
  ProcessList,
  RelatedPages,
} from "../../../../components/content/editorial-content";
import { SiteFooter } from "../../../../components/navigation/site-footer";
import { DiscoverySearch } from "../../../../components/search/discovery-search";
import { homeCopy, isLocale, locales, type Locale, type Purpose } from "../../../../lib/home-copy";
import { isPageSlug, pageSlugs, siteCopy, type PageSlug } from "../../../../lib/site-copy";
import { richCopy } from "../../../../lib/rich-copy";
import { getDeveloper, getProjects, getProperties } from "../../../../lib/api";

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
  };
}

export default async function InnerPage({ params, searchParams }: InnerPageProps) {
  const [{ locale, page }, query] = await Promise.all([params, searchParams]);

  if (!isLocale(locale) || !isPageSlug(page)) {
    notFound();
  }

  return <LocalizedInnerPage locale={locale} page={page} query={query} />;
}

async function LocalizedInnerPage({
  locale,
  page,
  query,
}: Readonly<{ locale: Locale; page: PageSlug; query: SearchParams }>) {
  const home = homeCopy[locale];
  const site = siteCopy[locale];
  const copy = site.pages[page];

  return (
    <div className={`inner-page inner-page--${page}`} id="top">
      <main id="main-content">
        <section aria-labelledby="page-title" className="inner-hero">
          <div className="inner-hero__orbit" aria-hidden="true" />
          <div className="inner-hero__grid">
            <div className="inner-hero__copy">
              <Breadcrumbs
                items={[
                  { href: `/${locale}`, label: richCopy[locale].homeLabel },
                  { label: copy.title },
                ]}
                label={richCopy[locale].breadcrumb}
              />
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
        {await renderPageContent(locale, page, query)}
        <PageEditorial locale={locale} page={page} />
      </main>
      <SiteFooter copy={home.header} locale={locale} />
    </div>
  );
}

function PageEditorial({ locale, page }: Readonly<{ locale: Locale; page: PageSlug }>) {
  const copy = richCopy[locale].pages[page];

  return (
    <>
      <section aria-labelledby="editorial-intro-title" className="content-section content-section--intro">
        <div className="content-heading"><p>{copy.intro.eyebrow}</p><h2 id="editorial-intro-title">{copy.intro.title}</h2></div>
        <p className="content-lead">{copy.intro.text}</p>
      </section>
      {copy.sections.map((section, index) => (
        <section
          aria-labelledby={`editorial-section-${index}`}
          className={`content-section ${index % 2 === 0 ? "content-section--dark" : ""}`}
          key={section.title}
        >
          <div className="content-heading"><p>{section.eyebrow}</p><h2 id={`editorial-section-${index}`}>{section.title}</h2><span>{section.text}</span></div>
          {index === copy.sections.length - 1 && section.items.length >= 4
            ? <ProcessList items={section.items} />
            : <EditorialCards items={section.items} />}
        </section>
      ))}
      <section aria-labelledby="page-checklist-title" className="content-section content-section--split">
        <div className="content-heading"><p>{copy.checklist.eyebrow}</p><h2 id="page-checklist-title">{copy.checklist.title}</h2><span>{copy.checklist.text}</span></div>
        <Checklist items={copy.checklist.items} />
      </section>
      <FaqSection eyebrow={copy.faq.eyebrow} heading={copy.faq.title} items={copy.faq.items} />
      <RelatedPages heading={copy.related.title} items={copy.related.items} />
      <FinalCta action={copy.cta.action} heading={copy.cta.title} href={copy.cta.href} locale={locale} text={copy.cta.text} />
    </>
  );
}

async function renderPageContent(locale: Locale, page: PageSlug, query: SearchParams) {
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

  return <ContactContent locale={locale} query={query} />;
}

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

async function PropertiesContent({ locale, query }: Readonly<{ locale: Locale; query: SearchParams }>) {
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
  const apiQuery = new URLSearchParams();
  if (selectedPurpose) apiQuery.set("purpose", selectedPurpose);
  if (propertyType) apiQuery.set("property_type", propertyType.value);
  if (location && location.value !== "all") apiQuery.set("emirate", location.value);
  const properties = await getProperties(locale, apiQuery.toString() ? `&${apiQuery}` : "");

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
      <div className="cms-property-results">
        <div className="inner-section__heading"><p>ARE / LIVE CMS</p><h2>{locale === "ar" ? "العقارات المنشورة" : "Published properties"}</h2></div>
        {properties.length ? <div className="cms-property-grid">{properties.map((property) => <article key={property.id}><div className="cms-media-neutral" aria-hidden="true">ARE</div><div><span>{property.emirate} · {property.property_type}</span><h3>{property.title}</h3><p>{property.description}</p><dl><div><dt>{locale === "ar" ? "الغرض" : "Purpose"}</dt><dd>{property.purpose}</dd></div><div><dt>{locale === "ar" ? "السعر" : "Price"}</dt><dd>{property.price_on_request ? (locale === "ar" ? "السعر عند الطلب" : "Price on request") : `${property.currency} ${property.price}`}</dd></div></dl><Link className="text-link" href={`/${locale}/properties/${property.slug}`}>{locale === "ar" ? "عرض التفاصيل" : "View details"}</Link></div></article>)}</div> : <div className="career-opportunities__empty"><span aria-hidden="true">00</span><div><h3>{locale === "ar" ? "لا توجد عقارات منشورة حالياً" : "No published properties yet"}</h3><p>{locale === "ar" ? "لن تظهر هنا إلا السجلات المنشورة والمعتمدة." : "Only approved, published CMS records will appear here."}</p></div></div>}
      </div>
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
        <Link className="text-link" href={`/${locale}/contact`}>{copy.enquiryAction}</Link>
      </div>
    </section>
  );
}

async function OffPlanContent({ locale }: Readonly<{ locale: Locale }>) {
  const copy = siteCopy[locale].offPlan;
  const projects = await getProjects(locale);

  return (
    <>
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
        <Link className="text-link" href={`/${locale}/properties`}>{copy.searchAction}</Link>
      </div>
    </section>
    <section aria-labelledby="published-projects-title" className="inner-section">
      <div className="inner-section__heading">
        <p>ARE / {locale === "ar" ? "المشاريع المنشورة" : "PUBLISHED PROJECTS"}</p>
        <h2 id="published-projects-title">{locale === "ar" ? "مشاريع على المخطط معتمدة" : "Approved Off-Plan projects"}</h2>
      </div>
      {projects.length ? <div className="cms-property-grid">{projects.map((project) => <article key={project.id}><div className="cms-media-neutral" aria-hidden="true">ARE</div><div><span>{project.emirate} · {project.area.name_ar && locale === "ar" ? project.area.name_ar : project.area.name_en}</span><h3>{project.official_name}</h3><p>{project.short_summary}</p><Link className="text-link" href={`/${locale}/off-plan/${project.slug}`}>{locale === "ar" ? "عرض المشروع" : "View project"}</Link></div></article>)}</div> : <div className="career-opportunities__empty"><span aria-hidden="true">00</span><div><h3>{locale === "ar" ? "لا توجد مشاريع منشورة حالياً" : "No published projects yet"}</h3><p>{locale === "ar" ? "لن تظهر هنا إلا المشاريع المعتمدة والمنشورة." : "Only approved, published Project records will appear here."}</p></div></div>}
    </section>
    </>
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

async function ContactContent({ locale, query }: Readonly<{ locale: Locale; query: SearchParams }>) {
  const copy = siteCopy[locale].contact;
  const slug = firstValue(query.topic) === "developer" ? firstValue(query.developer) : undefined;
  const developer = slug ? await getDeveloper(locale, slug) : null;
  const enquiryType = developer ? ({
    "new-booking": { en: "New booking enquiry", ar: "استفسار عن حجز جديد" },
    "primary-sale": { en: "Primary-sale enquiry", ar: "استفسار عن بيع أولي" },
    resale: { en: "Resale enquiry", ar: "استفسار عن إعادة البيع" },
  } as const)[developer.enquiry_types[0] ?? "new-booking"][locale] : undefined;

  return (
    <section aria-labelledby="contact-form-title" className="inner-section contact-experience">
      <div className="contact-experience__context">
        <p>ARE / ENQUIRY</p>
        <h2 id="contact-form-title">{locale === "ar" ? "معاينة استفسار واضحة وآمنة" : "A clear, safe enquiry preview"}</h2>
        <span>{copy.intro}</span>
      </div>
      <ContactPreviewForm
        initialEnquiryType={developer?.enquiry_types[0]}
        locale={locale}
        selectedDeveloper={developer?.name}
        selectedEnquiryLabel={enquiryType}
      />
    </section>
  );
}
