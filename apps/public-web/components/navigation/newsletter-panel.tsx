import Link from "next/link";

import type { Locale } from "../../lib/home-copy";
import { footerStackCopy } from "../../lib/footer-copy";

export function NewsletterPanel({ locale }: Readonly<{ locale: Locale }>) {
  const copy = footerStackCopy[locale].newsletter;

  return (
    <section aria-labelledby="newsletter-heading" className="newsletter-panel">
      <div className="newsletter-panel__copy">
        <p>{copy.eyebrow}</p>
        <h2 id="newsletter-heading">{copy.heading}</h2>
        <span>{copy.text}</span>
      </div>
      <div className="newsletter-panel__state">
        <label>
          <span>{copy.emailLabel}</span>
          <input aria-describedby="newsletter-note" disabled placeholder={copy.placeholder} type="email" />
        </label>
        <button disabled type="button">{copy.comingSoon}</button>
        <small id="newsletter-note">{copy.note}</small>
        <Link className="text-link" href={`/${locale}/insights`}>{copy.exploreInsights}</Link>
      </div>
    </section>
  );
}
