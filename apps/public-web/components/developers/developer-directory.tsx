"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { developerEmirates, getDeveloperEnquiryLabel, type DeveloperRecord } from "../../lib/developers-data";
import type { Locale } from "../../lib/home-copy";

export function DeveloperDirectory({ developers, locale }: Readonly<{ developers: ReadonlyArray<DeveloperRecord>; locale: Locale }>) {
  const [emirate, setEmirate] = useState("all");
  const [query, setQuery] = useState("");
  const copy = locale === "ar" ? { search: "ابحث عن مطور", placeholder: "اسم المطور أو المشروع", emirate: "الإمارة", all: "كل الإمارات", reset: "إعادة الضبط", results: "مطور", empty: "لا يوجد مطور مطابق. غيّر البحث أو الإمارة.", details: "التفاصيل والمصادر", focus: "مجال التركيز", projects: "مشاريع مختارة", presence: "حضور آخر", website: "الموقع الرسمي", government: "سجل حكومي", verified: "آخر تحقق", enquire: "استفسر عن هذا المطور", note: "ملاحظة التحقق" } : { search: "Search developers", placeholder: "Developer or project name", emirate: "Emirate", all: "All emirates", reset: "Reset", results: "developers", empty: "No developer matches these filters. Change the search or emirate.", details: "Details and sources", focus: "Development focus", projects: "Selected projects", presence: "Other presence", website: "Official website", government: "Government record", verified: "Last verified", enquire: "Enquire about this developer", note: "Verification note" };
  const normalized = query.trim().toLocaleLowerCase(locale);
  const filtered = useMemo(() => developers.filter((developer) => {
    const matchesEmirate = emirate === "all" || developer.primaryEmirate === emirate || developer.otherPresence.includes(emirate);
    const haystack = `${developer.officialName} ${developer.officialArabicName ?? ""} ${developer.selectedProjects.join(" ")} ${developer.focus[locale]}`.toLocaleLowerCase(locale);
    return matchesEmirate && (!normalized || haystack.includes(normalized));
  }), [developers, emirate, locale, normalized]);

  return <div className="developer-directory">
    <div className="directory-controls directory-controls--developers">
      <label><span>{copy.search}</span><input onChange={(event) => setQuery(event.target.value)} placeholder={copy.placeholder} type="search" value={query} /></label>
      <div className="directory-controls__group"><span>{copy.emirate}</span><div aria-label={copy.emirate} className="filter-tabs" role="group">
        {[{ value: "all", label: copy.all }, ...developerEmirates.map((item) => ({ value: item, label: item }))].map((item) => <button aria-pressed={emirate === item.value} key={item.value} onClick={() => setEmirate(item.value)} type="button">{item.label}</button>)}
      </div></div>
      <button className="reset-button" disabled={emirate === "all" && !query} onClick={() => { setEmirate("all"); setQuery(""); }} type="button">{copy.reset}</button>
    </div>
    <p aria-live="polite" className="results-status">{filtered.length ? `${filtered.length} ${copy.results}` : copy.empty}</p>
    <div className="developer-grid">
      {filtered.map((developer) => <article className="developer-card" key={developer.slug}>
        <div className="developer-card__topline"><span>{developer.primaryEmirate}</span><time dateTime={developer.lastVerified}>{copy.verified}: {developer.lastVerified}</time></div>
        <h3 dir="ltr">{developer.officialName}</h3><p>{developer.description[locale]}</p>
        <details><summary>{copy.details}<span aria-hidden="true">+</span></summary><div className="developer-card__details">
          <dl><div><dt>{copy.focus}</dt><dd>{developer.focus[locale]}</dd></div><div><dt>{copy.projects}</dt><dd dir="ltr">{developer.selectedProjects.join(" · ")}</dd></div>{developer.otherPresence.length ? <div><dt>{copy.presence}</dt><dd>{developer.otherPresence.join(" · ")}</dd></div> : null}</dl>
          {developer.note ? <p><strong>{copy.note}:</strong> {developer.note[locale]}</p> : null}
          <div className="source-links"><a href={developer.officialWebsite} rel="noreferrer" target="_blank">{copy.website} ↗</a><a href={developer.governmentSourceUrl} rel="noreferrer" target="_blank">{copy.government} ↗</a></div>
        </div></details>
        <Link className="button button--secondary" href={`/${locale}/contact?topic=developer&developer=${developer.slug}`}>{copy.enquire}</Link>
        <span className="visually-hidden">{getDeveloperEnquiryLabel(developer.enquiryTypes[0], locale)}</span>
      </article>)}
    </div>
  </div>;
}
