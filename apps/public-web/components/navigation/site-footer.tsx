"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import type { HeaderCopy, Locale } from "../../lib/home-copy";
import { siteCopy } from "../../lib/site-copy";

export function SiteFooter({ copy, locale }: Readonly<{ copy: HeaderCopy; locale: Locale }>) {
  const pathname = usePathname();
  const router = useRouter();
  const common = siteCopy[locale].common;
  const navigation = [
    { href: `/${locale}`, label: copy.home },
    { href: `/${locale}/properties`, label: copy.properties },
    { href: `/${locale}/communities`, label: copy.communities },
    { href: `/${locale}/off-plan`, label: copy.offPlan },
    { href: `/${locale}/about`, label: copy.about },
    { href: `/${locale}/contact`, label: copy.contact },
  ];

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
        <nav aria-label={common.footerNavigation} className="site-footer__navigation">
          {navigation.map((item) => (
            <Link
              aria-current={pathname === item.href ? "page" : undefined}
              href={item.href}
              key={item.href}
              onClick={(event) => resetCurrentRoute(event, item.href)}
            >
              {item.label}
            </Link>
          ))}
        </nav>
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
