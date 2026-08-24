"use client";

import { BriefcaseBusiness, Building2, Factory, FileText, Gauge, Inbox, LogOut, ScrollText, Users } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "./auth-provider";
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
  useEffect(() => { if (!loading && !user) router.replace(`/login?returnTo=${encodeURIComponent(pathname)}`); }, [loading, pathname, router, user]);
  if (loading || !user) return <main className="center-state" aria-live="polite">Checking secure session…</main>;
  return <div className="admin-layout">
    <aside className="admin-sidebar">
      <GuardedLink className="admin-brand" href="/dashboard"><span>ARE</span><strong>Admin</strong></GuardedLink>
      <nav aria-label="Admin navigation">{links.map(([href, label, Icon]) => <GuardedLink aria-current={pathname.startsWith(href) ? "page" : undefined} href={href} key={href}><Icon aria-hidden size={18}/>{label}</GuardedLink>)}</nav>
    </aside>
    <div className="admin-workspace">
      <header className="admin-header"><div><strong>{user.display_name}</strong><span>{user.roles.join(", ")}</span></div><button onClick={async () => { if (!confirmDiscard()) return; await logout(); router.replace("/login"); }} type="button"><LogOut aria-hidden size={17}/>Logout</button></header>
      <main id="main-content" className="admin-main">{children}</main>
    </div>
  </div>;
}
