import Image from "next/image";
import Link from "next/link";
import type { CSSProperties, ReactNode } from "react";

import type { Locale } from "../../lib/home-copy";
import { HomeHeroShinyEyebrow } from "../motion/home-hero-shiny-eyebrow";
import { HomeHeroTypedDescription } from "../motion/home-hero-typed-description";
import { Reveal } from "../motion/reveal";
import { heroImages, type HeroImageKey } from "./hero-images";
import styles from "./page-hero.module.css";

type HeroAction = Readonly<{ label: string; href: string }>;
type PageHeroProps = Readonly<{
  locale: Locale;
  image: HeroImageKey;
  eyebrow: string;
  title: string;
  description: string;
  primary: HeroAction;
  secondary?: HeroAction;
  note?: ReactNode;
}>;

// Homepage motion is reused directly; its markup, styles and timings stay intact.
export function PageHero({ locale, image, eyebrow, title, description, primary, secondary, note }: PageHeroProps) {
  const asset = heroImages[image];
  const artDirection = {
    "--hero-focus": asset.desktop,
    "--hero-focus-mobile": asset.mobile,
    "--hero-focus-rtl": asset.rtl,
    "--hero-focus-rtl-mobile": asset.rtlMobile,
  } as CSSProperties;

  return (
    <section aria-labelledby="page-hero-title" className={styles.hero} data-page-hero={image} style={artDirection}>
      <div className={styles.media}>
        <Image alt={asset[locale]} className={styles.image} fill preload sizes="100vw" src={`/images/home-premium/${asset.file}`} />
        <div aria-hidden="true" className={styles.shade} />
      </div>
      <div className={styles.inner}>
        <Reveal className={styles.copy} distance={18}>
          <p className={styles.eyebrow}>{locale === "en" ? <HomeHeroShinyEyebrow text={eyebrow} /> : eyebrow}</p>
          <h1 id="page-hero-title">{title}</h1>
          <HomeHeroTypedDescription key={`${locale}:${description}`} locale={locale} text={description} />
          <div className={styles.actions}>
            <Link className="button button--primary animated-gold-border" href={primary.href}>{primary.label}</Link>
            {secondary ? <Link className={`button button--secondary ${styles.secondary}`} href={secondary.href}>{secondary.label}</Link> : null}
          </div>
        </Reveal>
        {note ? <aside className={styles.note}>{note}</aside> : null}
      </div>
    </section>
  );
}
