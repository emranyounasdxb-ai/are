"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useRef } from "react";
import {
  domAnimation,
  LazyMotion,
  MotionConfig,
  useReducedMotion,
  useScroll,
  useTransform,
} from "motion/react";
import * as m from "motion/react-m";

const revealSelector = [
  "main > section",
  "main > header",
  ".article-hero",
  ".article-body > section",
  ".site-footer__identity",
  ".site-footer__groups",
  ".site-footer__languages",
].join(",");

function MotionDocument({ children }: Readonly<{ children: ReactNode }>) {
  const pathname = usePathname();
  const rootRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const progressScale = useTransform(scrollYProgress, [0, 1], [0, 1]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const sections = Array.from(root.querySelectorAll<HTMLElement>(revealSelector));
    sections.forEach((section) => section.classList.add("motion-section"));
    const hero = root.querySelector<HTMLElement>("main > section, main > header, .article-hero");

    if (reduceMotion) {
      sections.forEach((section) => section.classList.add("motion-section--visible"));
      return;
    }

    const heroFrame = window.requestAnimationFrame(() => {
      hero?.classList.add("motion-section--visible");
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("motion-section--visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -15%", threshold: 0.16 },
    );

    sections.forEach((section) => observer.observe(section));
    return () => {
      window.cancelAnimationFrame(heroFrame);
      observer.disconnect();
    };
  }, [pathname, reduceMotion]);

  return (
    <>
      <m.div
        aria-hidden="true"
        className="page-progress"
        style={{ scaleX: reduceMotion ? 0 : progressScale }}
      />
      <div className="motion-document" ref={rootRef}>
        {children}
      </div>
    </>
  );
}

export function MotionProvider({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <MotionConfig reducedMotion="user">
      <LazyMotion features={domAnimation} strict>
        <MotionDocument>{children}</MotionDocument>
      </LazyMotion>
    </MotionConfig>
  );
}
