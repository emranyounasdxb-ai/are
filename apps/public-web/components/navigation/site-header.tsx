"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { LogIn } from "lucide-react";
import { Suspense, useEffect, useRef, useState } from "react";

import type { HeaderCopy, Locale } from "../../lib/home-copy";
import { isNavigationHrefActive } from "../../lib/navigation";
import GradientText from "../GradientText";

type SiteHeaderProps = Readonly<{
  copy: HeaderCopy;
  locale: Locale;
}>;

type NavigationItem = Readonly<{
  href: string;
  label: string;
}>;

function ConsultGradientLabel({ children }: Readonly<{ children: string }>) {
  return (
    <GradientText
      animationSpeed={5}
      className="header-consult-gradient"
      colors={["#B89245", "#F4D995", "#FFF3C4", "#D4B675", "#B89245"]}
      showBorder={false}
    >
      {children}
    </GradientText>
  );
}

function NavigationLink({
  item,
  onClick,
  pathname,
}: Readonly<{
  item: NavigationItem;
  onClick: (event: React.MouseEvent<HTMLAnchorElement>) => void;
  pathname: string;
}>) {
  const searchParams = useSearchParams();
  const query = searchParams.toString();
  const isActive = isNavigationHrefActive(`${pathname}${query ? `?${query}` : ""}`, item.href);

  return (
    <Link aria-current={isActive ? "page" : undefined} href={item.href} onClick={onClick}>
      <span>{item.label}</span>
    </Link>
  );
}

function NavigationLinkFallback({ item, pathname }: Readonly<{ item: NavigationItem; pathname: string }>) {
  const isActive = isNavigationHrefActive(pathname, item.href);

  return (
    <Link aria-current={isActive ? "page" : undefined} href={item.href}>
      <span>{item.label}</span>
    </Link>
  );
}

export function SiteHeader({ copy, locale }: SiteHeaderProps) {
  const adminUrl = process.env.NEXT_PUBLIC_ARE_ADMIN_URL ?? "http://127.0.0.1:50002";
  const adminAccessibleLabel = locale === "ar" ? "تسجيل دخول الإدارة" : "Admin login";
  const [isOpen, setIsOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuPanelRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const router = useRouter();
  const directNavigation: ReadonlyArray<NavigationItem> = [
    { href: `/${locale}/properties?purpose=buy`, label: copy.buy },
    { href: `/${locale}/properties?purpose=rent`, label: copy.rent },
    { href: `/${locale}/off-plan`, label: copy.offPlan },
    { href: `/${locale}/developers`, label: copy.developers },
    { href: `/${locale}/communities`, label: copy.communities },
    { href: `/${locale}/insights`, label: copy.insights },
    { href: `/${locale}/careers`, label: copy.careers },
  ];
  const mobileNavigation = directNavigation;

  function isActive(href: string) {
    return isNavigationHrefActive(pathname, href);
  }

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const menuButton = menuButtonRef.current;
    const panel = menuPanelRef.current;
    const main = document.getElementById("main-content");
    const header = document.querySelector<HTMLElement>(".site-header");
    const focusableSelector =
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    document.body.style.overflow = "hidden";
    main?.setAttribute("inert", "");
    header?.setAttribute("inert", "");
    panel?.querySelector<HTMLElement>(focusableSelector)?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setIsOpen(false);
        return;
      }

      if (event.key !== "Tab" || !panel) {
        return;
      }

      const focusable = Array.from(panel.querySelectorAll<HTMLElement>(focusableSelector));
      const first = focusable.at(0);
      const last = focusable.at(-1);

      if (!first || !last) {
        return;
      }

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    function handleResize() {
      if (window.innerWidth >= 1200) {
        setIsOpen(false);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    window.addEventListener("resize", handleResize);

    return () => {
      document.body.style.overflow = previousOverflow;
      main?.removeAttribute("inert");
      header?.removeAttribute("inert");
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("resize", handleResize);
      menuButton?.focus();
    };
  }, [isOpen]);

  function closeMenu() {
    setIsOpen(false);
  }

  function resetCurrentRoute(event: React.MouseEvent<HTMLAnchorElement>, href: string) {
    if (pathname === href) {
      event.preventDefault();
      window.scrollTo({ top: 0 });
    }
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
    closeMenu();
  }

  return (
    <>
      <a className="skip-link" href="#main-content">
        {copy.skipLink}
      </a>
      <header className="site-header">
        <div className="site-header__inner">
          <Link
            aria-label="ALIYAS Real Estate"
            className="brand-mark"
            href={`/${locale}`}
            onClick={(event) => resetCurrentRoute(event, `/${locale}`)}
          >
            <span className="brand-mark__plate">
              <Image
                alt="ALIYAS Real Estate logo"
                fetchPriority="high"
                height={2885}
                loading="eager"
                sizes="(max-width: 900px) 60px, 70px"
                src="/brand/aliyas-real-estate-logo.png"
                width={2885}
              />
            </span>
          </Link>

          <nav aria-label={copy.navigation} className="desktop-navigation">
            {directNavigation.map((item) => (
              <Suspense fallback={<NavigationLinkFallback item={item} pathname={pathname} />} key={item.href}>
                <NavigationLink
                  item={item}
                  onClick={(event) => resetCurrentRoute(event, item.href)}
                  pathname={pathname}
                />
              </Suspense>
            ))}
          </nav>

          <div className="site-header__actions">
            <Link
              aria-current={isActive(`/${locale}/contact`) ? "page" : undefined}
              className="header-cta"
              href={`/${locale}/contact`}
            >
              <ConsultGradientLabel>{copy.contact}</ConsultGradientLabel>
            </Link>
            <nav aria-label={copy.language} className="locale-control">
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
            <a
              aria-label={adminAccessibleLabel}
              className="admin-login-link"
              href={adminUrl}
              title={adminAccessibleLabel}
            >
              <LogIn aria-hidden="true" size={15} strokeWidth={1.75} />
            </a>
            <button
              aria-controls={isOpen ? "mobile-navigation" : undefined}
              aria-expanded={isOpen}
              aria-label={isOpen ? copy.closeMenu : copy.openMenu}
              className="menu-button"
              onClick={() => setIsOpen((open) => !open)}
              ref={menuButtonRef}
              type="button"
            >
              <span aria-hidden="true" />
              <span aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      {isOpen ? (
        <div className="mobile-menu-backdrop" onMouseDown={closeMenu}>
          <div
            aria-labelledby="mobile-navigation-title"
            aria-modal="true"
            className="mobile-menu"
            id="mobile-navigation"
            onMouseDown={(event) => event.stopPropagation()}
            ref={menuPanelRef}
            role="dialog"
          >
            <div className="mobile-menu__topline">
              <span id="mobile-navigation-title">{copy.menu}</span>
              <button aria-label={copy.closeMenu} onClick={closeMenu} type="button">
                {locale === "ar" ? "إغلاق" : "Close"}
              </button>
            </div>
            <nav aria-label={copy.navigation}>
              {mobileNavigation.map((item) => (
                <Suspense fallback={<NavigationLinkFallback item={item} pathname={pathname} />} key={item.href}>
                  <NavigationLink
                    item={item}
                    onClick={(event) => {
                      resetCurrentRoute(event, item.href);
                      closeMenu();
                    }}
                    pathname={pathname}
                  />
                </Suspense>
              ))}
            </nav>
            <div className="mobile-menu__footer">
              <p>{copy.activeLanguage}</p>
              <span>{copy.menuDescription}</span>
              <div className="mobile-menu__utilities">
                <Link
                  aria-current={isActive(`/${locale}/contact`) ? "page" : undefined}
                  className="mobile-enquire-link"
                  href={`/${locale}/contact`}
                  onClick={closeMenu}
                >
                  <ConsultGradientLabel>{copy.contact}</ConsultGradientLabel>
                </Link>
                <nav aria-label={copy.language} className="mobile-menu__locales">
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
                <a
                  aria-label={adminAccessibleLabel}
                  className="mobile-admin-login"
                  href={adminUrl}
                  onClick={closeMenu}
                  title={adminAccessibleLabel}
                >
                  <LogIn aria-hidden="true" size={15} strokeWidth={1.75} />
                </a>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
