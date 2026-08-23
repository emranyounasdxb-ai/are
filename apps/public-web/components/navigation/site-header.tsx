"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";

const navigation = [
  { href: "#top", label: "Home" },
  { href: "#search", label: "Properties" },
  { href: "#discovery", label: "Communities" },
  { href: "#off-plan", label: "Off-Plan" },
  { href: "#approach", label: "About" },
] as const;

export function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuPanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const menuButton = menuButtonRef.current;
    const panel = menuPanelRef.current;
    const focusableSelector =
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    document.body.style.overflow = "hidden";
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
      if (window.innerWidth > 900) {
        setIsOpen(false);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    window.addEventListener("resize", handleResize);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("resize", handleResize);
      menuButton?.focus();
    };
  }, [isOpen]);

  function closeMenu() {
    setIsOpen(false);
  }

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="site-header">
        <div className="site-header__inner">
          <a aria-label="ALIYAS Real Estate home" className="brand-mark" href="#top">
            <span className="brand-mark__plate">
              <Image
                alt="ALIYAS Real Estate logo"
                fetchPriority="high"
                height={2885}
                loading="eager"
                src="/brand/aliyas-real-estate-logo.png"
                width={2885}
              />
            </span>
          </a>

          <nav aria-label="Primary navigation" className="desktop-navigation">
            {navigation.map((item) => (
              <a href={item.href} key={item.href}>
                {item.label}
              </a>
            ))}
          </nav>

          <div className="site-header__actions">
            <div aria-label="Language" className="locale-control">
              <span aria-current="true">EN</span>
              <button
                aria-label="Arabic preview is not available in this phase"
                disabled
                title="Arabic preview will follow in an approved locale phase"
                type="button"
              >
                العربية
              </button>
            </div>
            <a className="header-cta" href="#search">
              Start discovering
            </a>
            <button
              aria-controls="mobile-navigation"
              aria-expanded={isOpen}
              aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
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
            aria-label="Mobile navigation"
            aria-modal="true"
            className="mobile-menu"
            id="mobile-navigation"
            onMouseDown={(event) => event.stopPropagation()}
            ref={menuPanelRef}
            role="dialog"
          >
            <div className="mobile-menu__topline">
              <span>Navigation</span>
              <button aria-label="Close navigation menu" onClick={closeMenu} type="button">
                Close
              </button>
            </div>
            <nav aria-label="Mobile primary navigation">
              {navigation.map((item, index) => (
                <a href={item.href} key={item.href} onClick={closeMenu}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {item.label}
                </a>
              ))}
            </nav>
            <div className="mobile-menu__footer">
              <p>English preview</p>
              <span>Arabic navigation will follow its approved locale implementation.</span>
              <a href="#search" onClick={closeMenu}>
                Explore property discovery
              </a>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
