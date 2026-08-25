"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import type { HeaderCopy, Locale } from "../../lib/home-copy";
import { isNavigationHrefActive } from "../../lib/navigation";
import { siteCopy } from "../../lib/site-copy";

export function SiteFooter({ copy, locale }: Readonly<{ copy: HeaderCopy; locale: Locale }>) {
  const pathname = usePathname();
  const router = useRouter();
  const common = siteCopy[locale].common;
  const contactNavigationLabel = locale === "ar" ? "التواصل" : "Contact";
  const groups = [
    { heading: locale === "ar" ? "اكتشف" : "Discover", links: [
      { href: `/${locale}/properties`, label: copy.properties },
      { href: `/${locale}/off-plan`, label: copy.offPlan },
      { href: `/${locale}/communities`, label: copy.communities },
      { href: `/${locale}/developers`, label: copy.developers },
    ] },
    { heading: locale === "ar" ? "المصادر" : "Resources", links: [
      { href: `/${locale}/insights`, label: copy.insights },
    ] },
    { heading: locale === "ar" ? "الشركة" : "Company", links: [
      { href: `/${locale}/about`, label: copy.about },
      { href: `/${locale}/careers`, label: copy.careers },
      { href: `/${locale}/contact`, label: contactNavigationLabel },
    ] },
  ];

  function isActive(href: string) {
    return isNavigationHrefActive(pathname, href);
  }

  function switchLocale(nextLocale: Locale) {
    const segments = pathname.split("/").filter(Boolean);
    const suffix = segments.slice(1).join("/");
    const nextPath = `/${nextLocale}${suffix ? `/${suffix}` : ""}`;
    const currentQuery = new URLSearchParams(window.location.search);
    const safeQuery = new URLSearchParams();

    if (suffix === "properties") {
      for (const key of ["location", "type", "purpose"]) {
        const value = currentQuery.get(key);
        if (value) {
          safeQuery.set(key, value);
        }
      }
    }

    if (suffix === "contact" && currentQuery.get("topic") === "developer") {
      const developer = currentQuery.get("developer");
      if (developer && /^[a-z0-9-]+$/.test(developer)) {
        safeQuery.set("topic", "developer");
        safeQuery.set("developer", developer);
      }
    }

    const query = safeQuery.toString();
    router.push(`${nextPath}${query ? `?${query}` : ""}`);
  }

  function resetCurrentRoute(event: React.MouseEvent<HTMLAnchorElement>, href: string) {
    if (pathname === href) {
      event.preventDefault();
      window.scrollTo({ top: 0 });
    }
  }

  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__identity">
          <span>ALIYAS</span>
          <p>{common.footerLabel}</p>
          <small>{common.footerDescription}</small>
        </div>
        <div aria-label={common.footerNavigation} className="site-footer__groups" role="group">
          {groups.map((group) => <nav aria-label={group.heading} className="site-footer__navigation" key={group.heading}>
            <strong>{group.heading}</strong>
            {group.links.map((item) => <Link aria-current={isActive(item.href) ? "page" : undefined} href={item.href} key={item.href} onClick={(event) => resetCurrentRoute(event, item.href)}>{item.label}</Link>)}
          </nav>)}
        </div>
        <nav aria-label={common.language} className="site-footer__languages">
          <Link
            aria-current={locale === "en" ? "page" : undefined}
            href={pathname.replace(/^\/(en|ar)/, "/en")}
            hrefLang="en"
            onClick={(event) => {
              event.preventDefault();
              switchLocale("en");
            }}
          >
            EN
          </Link>
          <Link
            aria-current={locale === "ar" ? "page" : undefined}
            href={pathname.replace(/^\/(en|ar)/, "/ar")}
            hrefLang="ar"
            onClick={(event) => {
              event.preventDefault();
              switchLocale("ar");
            }}
          >
            العربية
          </Link>
        </nav>
      </div>
    </footer>
  );
}
