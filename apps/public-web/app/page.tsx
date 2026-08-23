import type { Metadata } from "next";

import { Reveal } from "../components/motion/reveal";
import { SiteHeader } from "../components/navigation/site-header";
import { DiscoverySearch } from "../components/search/discovery-search";

export const metadata: Metadata = {
  title: "ALIYAS Real Estate | UAE Property Discovery",
  description:
    "Explore properties, communities and opportunities across the UAE with ALIYAS Real Estate.",
};

const discoveryCards = [
  {
    className: "discovery-card--buy",
    eyebrow: "01 / Buy",
    href: "#search",
    linkLabel: "Explore buying",
    text: "Explore a considered path to finding your next home or investment.",
    title: "Buy",
  },
  {
    className: "discovery-card--rent",
    eyebrow: "02 / Rent",
    href: "#search",
    linkLabel: "Explore renting",
    text: "Find a place that fits the way you want to live across the UAE.",
    title: "Rent",
  },
  {
    className: "discovery-card--off-plan",
    eyebrow: "03 / Off-Plan",
    href: "#search",
    linkLabel: "Explore off-plan",
    text: "Discover the questions that matter before exploring a new project.",
    title: "Off-Plan",
  },
] as const;

export default function HomePage() {
  return (
    <div id="top">
      <SiteHeader />

      <main id="main-content">
        <section aria-labelledby="hero-title" className="hero-section">
          <div className="hero-orbit hero-orbit--one" aria-hidden="true" />
          <div className="hero-orbit hero-orbit--two" aria-hidden="true" />

          <div className="hero-shell">
            <div className="hero-grid">
              <div className="hero-copy">
                <Reveal className="hero-eyebrow" delay={0.04} distance={10}>
                  <span aria-hidden="true" />
                  <p>UAE REAL ESTATE, REIMAGINED</p>
                </Reveal>

                <Reveal delay={0.1} distance={20}>
                  <h1 id="hero-title">Discover Exceptional Living Across the UAE</h1>
                </Reveal>

                <Reveal delay={0.18} distance={18}>
                  <p className="hero-description">
                    Explore properties, communities and opportunities designed around the way you
                    want to live and invest.
                  </p>
                </Reveal>

                <Reveal className="hero-actions" delay={0.26} distance={16}>
                  <a className="button button--primary" href="#search">
                    Explore Properties
                    <span aria-hidden="true">↗</span>
                  </a>
                  <a className="button button--secondary" href="#approach">
                    Discover How It Works
                  </a>
                </Reveal>

                <Reveal className="hero-coordinate" delay={0.32} distance={10}>
                  <span>English preview</span>
                  <span aria-hidden="true" />
                  <span>UAE</span>
                  <small>Local review</small>
                </Reveal>
              </div>

              <Reveal className="hero-visual-wrap" delay={0.16} distance={28}>
                <div className="architectural-scene">
                  <div className="scene-glow" aria-hidden="true" />
                  <div className="scene-grid" aria-hidden="true" />
                  <div className="scene-sun" aria-hidden="true" />
                  <div className="scene-tower scene-tower--rear" aria-hidden="true" />
                  <div className="scene-tower scene-tower--main" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </div>
                  <div className="scene-tower scene-tower--front" aria-hidden="true" />
                  <div className="scene-plinth" aria-hidden="true" />
                  <div className="scene-frame" aria-hidden="true">
                    <span>ARE / 01</span>
                  </div>
                  <div className="scene-caption">
                    <span>Conceptual architectural study</span>
                    <p>Replaceable preview composition — no property is represented.</p>
                  </div>
                </div>
              </Reveal>
            </div>

            <Reveal className="search-panel" delay={0.32} distance={22}>
              <div className="search-panel__heading" id="search">
                <div>
                  <span>Property discovery</span>
                  <h2>Begin with what matters to you</h2>
                </div>
                <p>01 — 03</p>
              </div>
              <DiscoverySearch />
            </Reveal>
          </div>
        </section>

        <section aria-labelledby="discovery-title" className="discovery-section" id="discovery">
          <div className="section-intro" id="approach">
            <Reveal className="section-kicker" distance={10}>
              <span>Three ways to begin</span>
              <span>ALIYAS discovery</span>
            </Reveal>
            <Reveal delay={0.08}>
              <h2 id="discovery-title">A clearer first step into UAE real estate.</h2>
            </Reveal>
            <Reveal delay={0.14}>
              <p>
                Choose the journey that matches your intent. Live results will follow only when
                approved property data is connected.
              </p>
            </Reveal>
          </div>

          <div className="discovery-grid">
            {discoveryCards.map((card, index) => (
              <Reveal delay={0.08 * index} key={card.title}>
                <article
                  className={`discovery-card ${card.className}`}
                  id={card.title === "Off-Plan" ? "off-plan" : undefined}
                >
                  <div className="discovery-card__visual" aria-hidden="true">
                    <span className="discovery-card__plane discovery-card__plane--one" />
                    <span className="discovery-card__plane discovery-card__plane--two" />
                    <span className="discovery-card__line" />
                  </div>
                  <div className="discovery-card__content">
                    <p>{card.eyebrow}</p>
                    <h3>{card.title}</h3>
                    <span>{card.text}</span>
                    <a href={card.href}>
                      {card.linkLabel}
                      <span aria-hidden="true">↗</span>
                    </a>
                  </div>
                </article>
              </Reveal>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
