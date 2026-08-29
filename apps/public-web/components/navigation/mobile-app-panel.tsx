import Image from "next/image";

import { footerStackCopy } from "../../lib/footer-copy";
import type { Locale } from "../../lib/home-copy";
import { mobileStoreTargets } from "../../lib/mobile-app-links";

export function MobileAppPanel({ locale }: Readonly<{ locale: Locale }>) {
  const copy = footerStackCopy[locale].app;
  const storeLabels = locale === "ar"
    ? { ios: "متجر تطبيقات آبل", android: "متجر غوغل بلاي" }
    : { ios: "App Store", android: "Google Play" };

  return (
    <section aria-labelledby="mobile-app-heading" className="mobile-app-panel">
      <div aria-hidden="true" className="mobile-app-panel__pattern" />
      <div className="mobile-app-panel__copy">
        <p>{copy.eyebrow}</p>
        <h2 id="mobile-app-heading">{copy.heading}</h2>
        <span>{copy.text}</span>
        <div aria-label={copy.plannedLabel} className="mobile-app-panel__planned" role="list">
          {copy.plannedItems.map((item) => <small key={item} role="listitem">{item}</small>)}
        </div>
        <div aria-label={copy.comingSoon} className="mobile-app-panel__stores" role="group">
          {mobileStoreTargets.map((target) => target.url ? (
            <a href={target.url} key={target.platform} rel="noreferrer" target="_blank">
              <span>{storeLabels[target.platform]}</span>
            </a>
          ) : (
            <button aria-label={`${storeLabels[target.platform]} — ${copy.comingSoon}`} disabled key={target.platform} type="button">
              <span>{storeLabels[target.platform]}</span>
              <small>{copy.comingSoon}</small>
            </button>
          ))}
        </div>
      </div>
      <div aria-label={copy.deviceLabel} className="mobile-app-panel__devices" role="img">
        <div className="mobile-app-panel__device mobile-app-panel__device--rear" />
        <div className="mobile-app-panel__device mobile-app-panel__device--front">
          <span className="mobile-app-panel__speaker" />
          <Image alt="" height={2885} sizes="120px" src="/brand/aliyas-real-estate-logo.png" width={2885} />
          <small>{locale === "ar" ? "علياس" : "ALIYAS"}</small>
        </div>
      </div>
    </section>
  );
}
