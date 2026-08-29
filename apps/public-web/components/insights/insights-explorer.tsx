"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { Locale } from "../../lib/home-copy";
import { localizedDisplayText, normalizeArabicUserFacingText } from "../../lib/arabic-localization";
import type { InsightArticle, InsightCategory, VerifiedUpdate } from "../../lib/insights-data";

type Filter = "all" | InsightCategory | "news";

export function InsightsExplorer({ articles, locale, updates }: Readonly<{
  articles: ReadonlyArray<InsightArticle>;
  locale: Locale;
  updates: ReadonlyArray<VerifiedUpdate>;
}>) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const copy = locale === "ar" ? {
    all: "الكل", guides: "أدلة", market: "رؤى السوق", news: "أخبار موثقة", search: "ابحث في الرؤى", placeholder: "ابحث بعنوان أو موضوع", reset: "إعادة الضبط", empty: "لا توجد نتائج مطابقة. جرّب عبارة أو فئة أخرى.", read: "اقرأ المقال", source: "المصدر الرسمي", updated: "آخر تحديث",
  } : {
    all: "All", guides: "Guides", market: "Market insights", news: "Verified news", search: "Search insights", placeholder: "Search by title or topic", reset: "Reset", empty: "No matching results. Try another phrase or category.", read: "Read article", source: "Official source", updated: "Last updated",
  };
  const normalizedQuery = query.trim().toLocaleLowerCase(locale === "ar" ? "ar" : "en");
  const visibleArticles = useMemo(() => articles.filter((article) => {
    const content = article.content[locale];
    const matchesFilter = filter === "all" || filter === article.category;
    return matchesFilter && (!normalizedQuery || `${content.title} ${content.introduction}`.toLocaleLowerCase(locale).includes(normalizedQuery));
  }), [articles, filter, locale, normalizedQuery]);
  const visibleUpdates = useMemo(() => updates.filter((update) => {
    const matchesFilter = filter === "all" || filter === "news";
    return matchesFilter && (!normalizedQuery || `${update.title[locale]} ${update.summary[locale]} ${update.sourceName}`.toLocaleLowerCase(locale).includes(normalizedQuery));
  }), [filter, locale, normalizedQuery, updates]);
  const hasResults = visibleArticles.length + visibleUpdates.length > 0;

  function reset() { setFilter("all"); setQuery(""); }

  return (
    <div className="insights-explorer">
      <div className="directory-controls">
        <label><span>{copy.search}</span><input onChange={(event) => setQuery(event.target.value)} placeholder={copy.placeholder} type="search" value={query} /></label>
        <div aria-label={locale === "ar" ? "تصفية المحتوى" : "Filter content"} className="filter-tabs" role="group">
          {([['all', copy.all], ['guides', copy.guides], ['market-insights', copy.market], ['news', copy.news]] as const).map(([value, label]) => (
            <button aria-pressed={filter === value} key={value} onClick={() => setFilter(value)} type="button">{label}</button>
          ))}
        </div>
        <button className="reset-button" disabled={filter === "all" && !query} onClick={reset} type="button">{copy.reset}</button>
      </div>
      <p aria-live="polite" className="results-status">{hasResults ? `${localizedDisplayText((visibleArticles.length + visibleUpdates.length).toString(), locale)} ${locale === "ar" ? "نتيجة" : "results"}` : copy.empty}</p>
      {hasResults ? <div className="insight-card-grid">
        {visibleArticles.map((article) => {
          const content = article.content[locale];
          return <article className="insight-card" key={article.slug}>
            <div><span>{content.categoryLabel}</span><time dateTime={article.updated}>{copy.updated}: {localizedDisplayText(article.updated, locale)}</time></div>
            <h3>{content.title}</h3><p>{content.introduction}</p>
            <Link href={`/${locale}/insights/${article.slug}`}>{copy.read}</Link>
          </article>;
        })}
        {visibleUpdates.map((update) => <article className="insight-card insight-card--news" key={update.id}>
          <div><span>{copy.news}</span><time dateTime={update.published}>{localizedDisplayText(update.published, locale)}</time></div>
          <h3>{locale === "ar" ? normalizeArabicUserFacingText(update.title[locale]) : update.title[locale]}</h3><p>{locale === "ar" ? normalizeArabicUserFacingText(update.summary[locale]) : update.summary[locale]}</p><small>{locale === "ar" ? "المصدر الرسمي" : update.sourceName} · {copy.updated} {localizedDisplayText(update.verified, locale)}</small>
          <a href={update.sourceUrl} rel="noreferrer" target="_blank">{copy.source}<span aria-hidden="true">↗</span></a>
        </article>)}
      </div> : null}
    </div>
  );
}
