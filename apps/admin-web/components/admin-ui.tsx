"use client";

import { AlertCircle, CheckCircle2, CircleDot, Inbox, LoaderCircle, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { type ReactNode, useEffect, useRef } from "react";

export function AdminPageHeader({ eyebrow, title, description, action, back }: Readonly<{ eyebrow: string; title: string; description?: string; action?: ReactNode; back?: ReactNode }>) {
  return <header className="admin-page-header"><div>{back}<p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description ? <p className="page-description">{description}</p> : null}</div>{action ? <div className="page-header-action">{action}</div> : null}</header>;
}

export function MetricCard({ href, label, value, icon: Icon }: Readonly<{ href: string; label: string; value: number | string; icon: LucideIcon }>) {
  return <Link className="metric-card" href={href}><span className="metric-icon"><Icon aria-hidden size={18}/></span><span>{label}</span><strong>{value}</strong></Link>;
}

export function FilterToolbar({ children, resultLabel, onReset, filtered }: Readonly<{ children: ReactNode; resultLabel?: string; onReset?: () => void; filtered?: boolean }>) {
  return <section className="filter-toolbar" aria-label="Filters"><div className="filter-fields">{children}</div>{resultLabel || onReset ? <div className="filter-meta">{resultLabel ? <span aria-live="polite">{resultLabel}</span> : null}{onReset ? <button disabled={!filtered} onClick={onReset} type="button">Reset filters</button> : null}</div> : null}</section>;
}

export function EmptyState({ title, description, action, filtered = false }: Readonly<{ title: string; description: string; action?: ReactNode; filtered?: boolean }>) {
  return <div className="empty-state"><span className="empty-state-icon">{filtered ? <CircleDot aria-hidden size={20}/> : <Inbox aria-hidden size={20}/>}</span><div><h2>{title}</h2><p>{description}</p></div>{action}</div>;
}

export function StatusBadge({ status }: Readonly<{ status: string }>) {
  const normalized = status.toLowerCase().replaceAll("_", "-");
  const label = normalized.split("-").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
  return <span className={`status-badge status-badge--${normalized}`}>{label}</span>;
}

export function DataTableShell({ children, label }: Readonly<{ children: ReactNode; label: string }>) {
  return <div className="data-table-shell" role="region" aria-label={label} tabIndex={0}>{children}</div>;
}

export function FormSection({ id, title, description, children }: Readonly<{ id: string; title: string; description?: string; children: ReactNode }>) {
  return <fieldset className="form-section" id={id}><legend>{title}</legend>{description ? <p className="section-guidance">{description}</p> : null}{children}</fieldset>;
}

export function LanguageTabs({ active, onChange, englishComplete, arabicComplete, label, children }: Readonly<{ active: "en" | "ar"; onChange: (locale: "en" | "ar") => void; englishComplete: boolean; arabicComplete: boolean; label: string; children: ReactNode }>) {
  return <><div className="locale-tabs" role="tablist" aria-label={label}><button aria-selected={active === "en"} onClick={() => onChange("en")} role="tab" type="button">English <span className={`completion${englishComplete ? " complete" : ""}`}>{englishComplete ? "Complete" : "Incomplete"}</span></button><button aria-selected={active === "ar"} onClick={() => onChange("ar")} role="tab" type="button">العربية <span className={`completion${arabicComplete ? " complete" : ""}`}>{arabicComplete ? "مكتمل" : "غير مكتمل"}</span></button></div><div className={`locale-panel locale-panel--${active}`} dir={active === "ar" ? "rtl" : "ltr"} role="tabpanel">{children}</div></>;
}

export function StickyFormActions({ state, help, children }: Readonly<{ state: string; help: string; children: ReactNode }>) {
  return <div className="sticky-actions"><div><strong>{state}</strong><span>{help}</span></div><div className="command-actions">{children}</div></div>;
}

export function ErrorSummary({ title = "Review the form before continuing.", message, children, focusRef }: Readonly<{ title?: string; message?: string; children?: ReactNode; focusRef?: React.RefObject<HTMLDivElement | null> }>) {
  if (!message && !children) return null;
  return <div className="error-summary" ref={focusRef} role="alert" tabIndex={-1}><strong>{title}</strong>{message ? <p>{message}</p> : null}{children}</div>;
}

export function ConfirmationDialog({ open, title, description, confirmLabel, onCancel, onConfirm }: Readonly<{ open: boolean; title: string; description: string; confirmLabel: string; onCancel: () => void; onConfirm: () => void }>) {
  const cancelRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement as HTMLElement | null; cancelRef.current?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { onCancel(); return; }
      if (event.key !== "Tab") return;
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>('button:not([disabled]),a[href]');
      if (!focusable?.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keydown);
    return () => { document.removeEventListener("keydown", keydown); previousFocus?.focus(); };
  }, [onCancel, open]);
  if (!open) return null;
  return <div className="dialog-backdrop" onMouseDown={(event) => { if (event.currentTarget === event.target) onCancel(); }}><div aria-describedby="confirmation-description" aria-labelledby="confirmation-title" aria-modal="true" className="confirmation-dialog" ref={dialogRef} role="alertdialog"><h2 id="confirmation-title">{title}</h2><p id="confirmation-description">{description}</p><div><button ref={cancelRef} onClick={onCancel} type="button">Cancel</button><button className="danger-button" onClick={onConfirm} type="button">{confirmLabel}</button></div></div></div>;
}

export function LoadingState({ label = "Loading…" }: Readonly<{ label?: string }>) {
  return <div className="loading-state" aria-live="polite"><LoaderCircle aria-hidden className="spin" size={20}/>{label}</div>;
}

export function InlineFeedback({ tone, children }: Readonly<{ tone: "success" | "error" | "info" | "warning"; children: ReactNode }>) {
  const Icon = tone === "success" ? CheckCircle2 : tone === "error" || tone === "warning" ? AlertCircle : CircleDot;
  return <div className={`inline-feedback inline-feedback--${tone}`} role={tone === "error" ? "alert" : "status"}><Icon aria-hidden size={18}/>{children}</div>;
}
