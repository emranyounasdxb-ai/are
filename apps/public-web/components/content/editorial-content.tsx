import Link from "next/link";

import type { Locale } from "../../lib/home-copy";

export type ContentItem = Readonly<{ title: string; text: string }>;
export type FaqItem = Readonly<{ question: string; answer: string }>;
export type RelatedItem = Readonly<{ href: string; label: string; text: string }>;

export function Breadcrumbs({
  items,
  label,
}: Readonly<{ items: ReadonlyArray<Readonly<{ href?: string; label: string }>>; label: string }>) {
  return (
    <nav aria-label={label} className="breadcrumbs">
      <ol>
        {items.map((item, index) => (
          <li key={`${item.label}-${index}`}>
            {item.href ? <Link href={item.href}>{item.label}</Link> : <span aria-current="page">{item.label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function EditorialCards({ items }: Readonly<{ items: ReadonlyArray<ContentItem> }>) {
  return (
    <div className="editorial-cards">
      {items.map((item, index) => (
        <article key={item.title}>
          <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
          <h3>{item.title}</h3>
          <p>{item.text}</p>
        </article>
      ))}
    </div>
  );
}

export function ProcessList({ items }: Readonly<{ items: ReadonlyArray<ContentItem> }>) {
  return (
    <ol className="process-list">
      {items.map((item, index) => (
        <li key={item.title}>
          <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
          <div><h3>{item.title}</h3><p>{item.text}</p></div>
        </li>
      ))}
    </ol>
  );
}

export function Checklist({ items }: Readonly<{ items: ReadonlyArray<string> }>) {
  return (
    <ul className="content-checklist">
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  );
}

export function FaqSection({
  eyebrow,
  heading,
  items,
}: Readonly<{ eyebrow: string; heading: string; items: ReadonlyArray<FaqItem> }>) {
  return (
    <section aria-labelledby="faq-title" className="content-section content-section--faq">
      <div className="content-heading">
        <p>{eyebrow}</p>
        <h2 id="faq-title">{heading}</h2>
      </div>
      <div className="faq-list">
        {items.map((item) => (
          <details key={item.question}>
            <summary>{item.question}<span aria-hidden="true">+</span></summary>
            <p>{item.answer}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

export function RelatedPages({
  heading,
  items,
}: Readonly<{ heading: string; items: ReadonlyArray<RelatedItem> }>) {
  return (
    <section aria-labelledby="related-title" className="content-section content-section--related">
      <div className="content-heading"><h2 id="related-title">{heading}</h2></div>
      <div className="related-grid">
        {items.map((item) => (
          <Link href={item.href} key={item.href}>
            <span>{item.label}</span><p>{item.text}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

export function FinalCta({
  action,
  heading,
  href,
  locale,
  text,
}: Readonly<{ action: string; heading: string; href: string; locale: Locale; text: string }>) {
  return (
    <section aria-labelledby="closing-title" className="closing-cta">
      <div><p>ARE / {locale === "ar" ? "الخطوة التالية" : "NEXT STEP"}</p><h2 id="closing-title">{heading}</h2><span>{text}</span></div>
      <Link className="button button--primary" href={href}>{action}</Link>
    </section>
  );
}
