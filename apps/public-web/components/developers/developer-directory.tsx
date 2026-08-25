"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { PublicDeveloper } from "../../lib/api";
import type { Locale } from "../../lib/home-copy";

export function DeveloperDirectory({ developers, locale, unavailable = false }: Readonly<{ developers: ReadonlyArray<PublicDeveloper>; locale: Locale; unavailable?: boolean }>) {
  const [emirate, setEmirate] = useState("all");
  const [query, setQuery] = useState("");
  const copy = locale === "ar" ? { search: "ابحث عن مطور", placeholder: "اسم المطور أو المشروع", emirate: "الإمارة", all: "كل الإمارات", reset: "إعادة الضبط", results: "مطور", empty: "لا يوجد مطور مطابق. غيّر البحث أو الإمارة.", unavailable: "دليل المطورين غير متاح مؤقتاً. يرجى المحاولة مرة أخرى لاحقاً.", details: "التفاصيل والمصادر", focus: "مجال التركيز", projects: "مشاريع مختارة", presence: "حضور آخر", website: "الموقع الرسمي", government: "سجل حكومي", verified: "آخر تحقق", enquire: "استفسر عن هذا المطور", note: "ملاحظة التحقق" } : { search: "Search developers", placeholder: "Developer or project name", emirate: "Emirate", all: "All emirates", reset: "Reset", results: "developers", empty: "No developer matches these filters. Change the search or emirate.", unavailable: "The developer directory is temporarily unavailable. Please try again later.", details: "Details and sources", focus: "Development focus", projects: "Selected projects", presence: "Other presence", website: "Official website", government: "Government record", verified: "Last verified", enquire: "Enquire about this developer", note: "Verification note" };
  const enquiryLabels = locale === "ar" ? { "new-booking": "استفسار عن حجز جديد", "primary-sale": "استفسار عن بيع أولي", resale: "استفسار عن إعادة البيع" } : { "new-booking": "New booking enquiry", "primary-sale": "Primary-sale enquiry", resale: "Resale enquiry" };
  const developerEmirates = useMemo(() => [...new Set(developers.flatMap((item) => [item.primary_emirate, ...item.other_presence]))].sort(), [developers]);
  const normalized = query.trim().toLocaleLowerCase(locale);
  const filtered = useMemo(() => developers.filter((developer) => {
    const matchesEmirate = emirate === "all" || developer.primary_emirate === emirate || developer.other_presence.includes(emirate);
    const haystack = `${developer.name} ${developer.selected_projects.join(" ")} ${developer.focus}`.toLocaleLowerCase(locale);
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
    <p aria-live="polite" className="results-status">{unavailable ? copy.unavailable : filtered.length ? `${filtered.length} ${copy.results}` : copy.empty}</p>
    <div className="developer-grid">
      {filtered.map((developer) => <article className="developer-card" id={developer.slug} key={developer.slug}>
        <div className="developer-card__topline"><span>{developer.primary_emirate}</span><time dateTime={developer.verification_date}>{copy.verified}: {developer.verification_date}</time></div>
        <h3 dir="ltr">{developer.name}</h3><p>{developer.description}</p>
        <details><summary>{copy.details}<span aria-hidden="true">+</span></summary><div className="developer-card__details">
          <dl><div><dt>{copy.focus}</dt><dd>{developer.focus}</dd></div><div><dt>{copy.projects}</dt><dd dir="ltr">{developer.selected_projects.join(" · ")}</dd></div>{developer.other_presence.length ? <div><dt>{copy.presence}</dt><dd>{developer.other_presence.join(" · ")}</dd></div> : null}</dl>
          {developer.verification_note ? <p><strong>{copy.note}:</strong> {developer.verification_note}</p> : null}
          <div className="source-links"><a href={developer.official_website} rel="noreferrer" target="_blank">{copy.website} ↗</a><a href={developer.source_url} rel="noreferrer" target="_blank">{copy.government} ↗</a></div>
        </div></details>
        <Link className="button button--secondary" href={`/${locale}/contact?topic=developer&developer=${developer.slug}`}>{copy.enquire}</Link>
        <span className="visually-hidden">{developer.enquiry_types[0] ? enquiryLabels[developer.enquiry_types[0]] : ""}</span>
      </article>)}
    </div>
  </div>;
}
