"use client";

import Image from "next/image";
import { ChevronLeft, ChevronRight, Expand, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { Locale } from "../../lib/home-copy";

export type ProjectPresentationMedia = {
  id: string;
  category: string;
  thumbnailUrl: string;
  fullUrl: string;
  alt: string;
  width: number;
  height: number;
};

type MediaCategory = {
  id: "floor-plan" | "master-plan" | "location-map" | "gallery";
  label: string;
  items: ProjectPresentationMedia[];
};

const copy = {
  en: {
    close: "Close full-size viewer",
    next: "Next image",
    previous: "Previous image",
    open: "Open full-size image",
    position: (current: number, total: number) => `Image ${current} of ${total}`,
  },
  ar: {
    close: "إغلاق عارض الصورة بالحجم الكامل",
    next: "الصورة التالية",
    previous: "الصورة السابقة",
    open: "فتح الصورة بالحجم الكامل",
    position: (current: number, total: number) => `الصورة ${current} من ${total}`,
  },
} as const;

export function ProjectMediaViewer({
  categories,
  locale,
}: Readonly<{ categories: MediaCategory[]; locale: Locale }>) {
  const [activeCategory, setActiveCategory] = useState(categories[0]?.id);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const t = copy[locale];
  const category = categories.find((item) => item.id === activeCategory) ?? categories[0];
  const activeItem = activeIndex == null ? null : category?.items[activeIndex];

  useEffect(() => {
    if (!activeItem) return;
    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setActiveIndex(null);
      if (event.key === "ArrowRight") {
        setActiveIndex((current) => current == null ? null : (current + 1) % category.items.length);
      }
      if (event.key === "ArrowLeft") {
        setActiveIndex((current) => current == null ? null : (current - 1 + category.items.length) % category.items.length);
      }
      if (event.key === "Tab") {
        const dialog = closeRef.current?.closest<HTMLElement>("[role='dialog']");
        const controls = dialog?.querySelectorAll<HTMLElement>("button:not([disabled])");
        if (!controls?.length) return;
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);
    closeRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
      triggerRef.current?.focus();
    };
  }, [activeItem, category.items.length]);

  if (!category) return null;

  function open(index: number, trigger: HTMLButtonElement) {
    triggerRef.current = trigger;
    setActiveIndex(index);
  }

  function move(delta: number) {
    setActiveIndex((current) => current == null ? null : (current + delta + category.items.length) % category.items.length);
  }

  return <div className="project-media-viewer">
    <div aria-label={locale === "ar" ? "فئات وسائط المشروع" : "Project media categories"} className="project-media-viewer__tabs" role="tablist">
      {categories.map((item) => <button
        aria-controls={`project-media-panel-${item.id}`}
        aria-selected={item.id === category.id}
        id={`project-media-tab-${item.id}`}
        key={item.id}
        onClick={() => {
          setActiveCategory(item.id);
          setActiveIndex(null);
        }}
        role="tab"
        type="button"
      >{item.label}<span>{item.items.length}</span></button>)}
    </div>

    <div aria-labelledby={`project-media-tab-${category.id}`} className="project-media-viewer__grid" id={`project-media-panel-${category.id}`} role="tabpanel">
      {category.items.map((item, index) => <figure key={item.id}>
        <button aria-label={`${t.open}: ${item.alt}`} onClick={(event) => open(index, event.currentTarget)} type="button">
          <span className="project-media-viewer__image">
            <Image
              alt={item.alt}
              height={item.height}
              loading="lazy"
              sizes="(max-width: 767px) calc(100vw - 32px), (max-width: 1200px) 50vw, 620px"
              src={item.thumbnailUrl}
              unoptimized
              width={item.width}
            />
          </span>
          <span className="project-media-viewer__caption"><span>{item.alt}</span><Expand aria-hidden size={18}/></span>
        </button>
      </figure>)}
    </div>

    {activeItem ? <div aria-label={activeItem.alt} aria-modal="true" className="project-media-lightbox" role="dialog">
      <button aria-label={t.close} className="project-media-lightbox__close" onClick={() => setActiveIndex(null)} ref={closeRef} type="button"><X aria-hidden size={24}/></button>
      {category.items.length > 1 ? <button aria-label={t.previous} className="project-media-lightbox__previous" onClick={() => move(-1)} type="button"><ChevronLeft aria-hidden className="directional-icon" size={28}/></button> : null}
      <figure>
        <div className="project-media-lightbox__image">
          <Image alt={activeItem.alt} height={activeItem.height} priority sizes="95vw" src={activeItem.fullUrl} unoptimized width={activeItem.width}/>
        </div>
        <figcaption><span>{activeItem.alt}</span><small>{t.position((activeIndex ?? 0) + 1, category.items.length)}</small></figcaption>
      </figure>
      {category.items.length > 1 ? <button aria-label={t.next} className="project-media-lightbox__next" onClick={() => move(1)} type="button"><ChevronRight aria-hidden className="directional-icon" size={28}/></button> : null}
    </div> : null}
  </div>;
}
