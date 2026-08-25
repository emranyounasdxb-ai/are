"use client";

import { BriefcaseBusiness, Building2, Factory, FileText, Gauge, Inbox, LogOut, Menu, ScrollText, Users, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { useAuth } from "./auth-provider";
import { AdminBrandLogo } from "./admin-brand-logo";
import { GuardedLink, NavigationGuardProvider, useNavigationGuard } from "./navigation-guard";

const links = [
  ["/dashboard", "Dashboard", Gauge], ["/properties", "Properties", Building2],
  ["/developers", "Developers", Factory],
  ["/insights", "Insights", FileText], ["/careers/jobs", "Career jobs", BriefcaseBusiness],
  ["/enquiries", "Enquiries", Inbox], ["/careers/applications", "Applications", Users],
  ["/audit", "Audit log", ScrollText],
] as const;

export function AdminShell({ children }: Readonly<{ children: ReactNode }>) {
  return <NavigationGuardProvider><AdminShellContent>{children}</AdminShellContent></NavigationGuardProvider>;
}

function AdminShellContent({ children }: Readonly<{ children: ReactNode }>) {
  const { user, loading, logout } = useAuth();
  const { confirmDiscard } = useNavigationGuard();
  const router = useRouter();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (!loading && !user) router.replace(`/login?returnTo=${encodeURIComponent(pathname)}`); }, [loading, pathname, router, user]);
  useEffect(() => {
    if (!menuOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const drawer = drawerRef.current;
    const focusable = drawer?.querySelectorAll<HTMLElement>('a[href],button:not([disabled])');
    focusable?.[0]?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setMenuOpen(false); menuButtonRef.current?.focus(); return; }
      if (event.key !== "Tab" || !focusable?.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", keydown);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener("keydown", keydown); };
  }, [menuOpen]);
  if (loading || !user) return <main className="center-state" aria-live="polite">Checking secure session…</main>;
  const navigation = <nav aria-label="Admin modules">{links.map(([href, label, Icon]) => <GuardedLink aria-current={pathname.startsWith(href) ? "page" : undefined} href={href} key={href} onNavigate={() => setMenuOpen(false)}><Icon aria-hidden size={17}/><span>{label}</span></GuardedLink>)}</nav>;
  const doLogout = async () => { if (!confirmDiscard()) return; await logout(); router.replace("/login"); };
  return <div className="admin-layout"><header className="admin-topbar"><GuardedLink aria-label="ALIYAS Real Estate Admin dashboard" className="admin-brand" href="/dashboard"><AdminBrandLogo className="admin-brand-mark"/></GuardedLink><div className="desktop-nav">{navigation}</div><div className="admin-utilities"><div className="admin-user"><strong>{user.display_name}</strong></div><button className="logout-button" onClick={doLogout} type="button"><LogOut aria-hidden size={16}/><span>Logout</span></button><button aria-controls="admin-drawer" aria-expanded={menuOpen} aria-label="Open Admin menu" className="menu-button" onClick={() => setMenuOpen(true)} ref={menuButtonRef} type="button"><Menu aria-hidden size={20}/></button></div></header>{menuOpen ? <div className="drawer-backdrop" onMouseDown={(event) => { if (event.currentTarget === event.target) { setMenuOpen(false); menuButtonRef.current?.focus(); } }}><div className="admin-drawer" id="admin-drawer" ref={drawerRef}><div className="drawer-header"><div className="drawer-brand"><AdminBrandLogo className="admin-brand-mark"/></div><button aria-label="Close Admin menu" onClick={() => { setMenuOpen(false); menuButtonRef.current?.focus(); }} type="button"><X aria-hidden size={20}/></button></div>{navigation}<div className="drawer-user"><strong>{user.display_name}</strong><button onClick={doLogout} type="button"><LogOut aria-hidden size={16}/>Logout</button></div></div></div> : null}<main id="main-content" className="admin-main">{children}</main></div>;
}
