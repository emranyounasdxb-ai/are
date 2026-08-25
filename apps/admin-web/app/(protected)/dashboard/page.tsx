"use client";

import { useQuery } from "@tanstack/react-query";
import { BriefcaseBusiness, Building2, Factory, FileSearch, FileText, FolderKanban, Inbox, Plus, Users } from "lucide-react";
import Link from "next/link";

import { AdminPageHeader, InlineFeedback, LoadingState, MetricCard } from "../../../components/admin-ui";
import { api } from "../../../lib/api";

const modules = [
  ["properties", "Properties", "/properties", Building2], ["developers", "Developers", "/developers", Factory],
  ["projects", "Projects", "/projects", FolderKanban], ["project_candidates", "Project candidates", "/project-imports", FileSearch],
  ["insights", "Insights", "/insights", FileText], ["jobs", "Jobs", "/careers/jobs", BriefcaseBusiness],
  ["enquiries", "Enquiries", "/enquiries", Inbox], ["applications", "Applications", "/careers/applications", Users],
] as const;

export default function DashboardPage() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Record<string, number>>("/admin/dashboard") });
  return <section><AdminPageHeader eyebrow="Overview" title="Dashboard" description="Live overview of your content and enquiries."/>
    {query.isLoading ? <LoadingState label="Loading workspace overview…"/> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : <div className="metric-grid">{modules.map(([key, label, href, Icon]) => <MetricCard href={href} icon={Icon} key={key} label={label} value={query.data?.[key] ?? 0}/>)}</div>}
    <section className="quick-actions" aria-labelledby="quick-actions-title"><div><p className="eyebrow">Create</p><h2 id="quick-actions-title">Quick actions</h2></div><div><Link href="/properties/new"><Plus aria-hidden size={16}/>Add Property</Link><Link href="/projects/new"><Plus aria-hidden size={16}/>Add Project</Link><Link href="/developers/new"><Plus aria-hidden size={16}/>Add Developer</Link><Link href="/insights/new"><Plus aria-hidden size={16}/>Create Insight</Link><Link href="/careers/jobs/new"><Plus aria-hidden size={16}/>Add Job</Link></div></section>
  </section>;
}
