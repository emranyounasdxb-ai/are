"use client";

import { useEffect, useState } from "react";

import TextType from "../TextType";

const playedDescriptions = new Set<string>();

type DescriptionMode = "animate" | "pending" | "static";

export function HomeHeroTypedDescription({
  locale,
  text,
}: Readonly<{ locale: "ar" | "en"; text: string }>) {
  const [mode, setMode] = useState<DescriptionMode>("pending");

  useEffect(() => {
    const descriptionKey = `${locale}:${text}`;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    const animationFrame = window.requestAnimationFrame(() => {
      if (reducedMotion.matches || playedDescriptions.has(descriptionKey)) {
        setMode("static");
      } else {
        playedDescriptions.add(descriptionKey);
        setMode("animate");
      }
    });

    const respectReducedMotion = (event: MediaQueryListEvent) => {
      if (event.matches) setMode("static");
    };

    reducedMotion.addEventListener("change", respectReducedMotion);
    return () => {
      window.cancelAnimationFrame(animationFrame);
      reducedMotion.removeEventListener("change", respectReducedMotion);
    };
  }, [locale, text]);

  return (
    <span className="premium-home__hero-description" dir={locale === "ar" ? "rtl" : "ltr"}>
      <span className="visually-hidden">{text}</span>
      <span aria-hidden="true" className="premium-home__hero-description-measure">
        {text}
      </span>
      <span aria-hidden="true" className="premium-home__hero-description-visual">
        {mode === "animate" ? (
          <TextType
            as="span"
            className="premium-home__hero-description-type"
            cursorCharacter="|"
            loop={false}
            pauseDuration={1500}
            showCursor
            text={[text]}
            typingSpeed={55}
          />
        ) : mode === "static" ? (
          text
        ) : null}
      </span>
      <noscript>
        <span aria-hidden="true">{text}</span>
      </noscript>
    </span>
  );
}
