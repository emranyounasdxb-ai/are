"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Edit3 } from "lucide-react";

import { api, type ResourceRecord } from "../lib/api";
import { AdminPageHeader, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { GuardedLink } from "./navigation-guard";

type Translation = { official_name?: string; short_summary?: string; full_description?: string };
type ProjectRecord = ResourceRecord & {
  emirate?: string;
  workflow_status?: string;
  translations?: Record<string, Translation>;
  developer?: { slug?: string };
  area?: { name_en?: string; name_ar?: string };
  availability_status?: string;
  construction_status?: string;
  handover_quarter?: string | null;
  handover_year?: number | null;
  original_handover_value?: string | null;
  property_types?: string[];
  bedroom_options?: string[];
  unit_types?: Array<{ label_en?: string; label_ar?: string }>;
  size_min?: string | number | null;
  size_max?: string | number | null;
  size_unit?: string | null;
  down_payment_percentage?: string | number | null;
  amenities?: Array<{ label_en?: string; label_ar?: string }>;
  nearby_places?: Array<{ name_en?: string; name_ar?: string; distance_value?: string | number | null; distance_unit?: string | null; travel_time_minutes?: number | null }>;
  payment_plan?: { milestones?: Array<{ label_en?: string; percentage?: string | number | null }> } | null;
  media?: Array<{ category?: string; rights_status?: string; has_upload?: boolean }>;
  sources?: Array<{ source_type?: string; source_title?: string | null; last_checked_at?: string }>;
  last_verified_at?: string | null;
  priority?: string | null;
};

export function ProjectView({ id }: Readonly<{ id: string }>) {
  const project = useQuery({ queryKey: ["project", id], queryFn: () => api<ProjectRecord>(`/admin/projects/${id}`) });
  if (project.isLoading) return <LoadingState label="Loading Project…"/>;
  if (project.error || !project.data) return <InlineFeedback tone="error">{project.error?.message ?? "Project not found."}</InlineFeedback>;
  const record = project.data;
  const en = record.translations?.en ?? {};
  return <section>
    <AdminPageHeader back={<GuardedLink className="back-link" href="/projects"><ArrowLeft aria-hidden size={16}/>Back to Projects</GuardedLink>} eyebrow="Project record" title={en.official_name ?? record.slug ?? "Project"} description="Read-only canonical Project details." action={<div className="status-cluster"><StatusBadge status={record.status ?? "draft"}/><StatusBadge status={record.workflow_status ?? "draft"}/></div>}/>
    <div className="detail-grid"><Detail title="Developer" value={record.developer?.slug}/><Detail title="Area" value={record.area?.name_en}/><Detail title="Emirate" value={record.emirate}/><Detail title="Availability" value={record.availability_status}/><Detail title="Construction" value={record.construction_status}/><Detail title="Handover" value={[record.handover_quarter, record.handover_year].filter(Boolean).join(" ") || record.original_handover_value}/><Detail title="Property types" value={record.property_types?.join(", ")}/><Detail title="Unit types" value={record.unit_types?.map((item) => item.label_en).filter(Boolean).join(", ")}/><Detail title="Bedrooms" value={record.bedroom_options?.join(", ")}/><Detail title="Size range" value={record.size_min || record.size_max ? `${record.size_min ?? "—"}–${record.size_max ?? "—"} ${record.size_unit ?? ""}` : undefined}/><Detail title="Down payment" value={record.down_payment_percentage == null ? undefined : `${record.down_payment_percentage}%`}/><Detail title="Amenities" value={record.amenities?.map((item) => item.label_en).filter(Boolean).join(", ")}/><Detail title="Nearby places" value={record.nearby_places?.map((item) => item.name_en).filter(Boolean).join(", ")}/><Detail title="Payment milestones" value={record.payment_plan?.milestones?.length ? String(record.payment_plan.milestones.length) : undefined}/><Detail title="Gallery and floor plans" value={record.media?.length ? `${record.media.length} media records` : undefined}/><Detail title="Last Verified" value={record.last_verified_at ? new Date(record.last_verified_at).toLocaleString("en-AE") : undefined}/><Detail title="ARE Priority" value={record.priority ?? undefined}/><Detail title="Internal sources" value={record.sources?.length ? `${record.sources.length} source-history records` : undefined}/></div>
    <article className="content-block"><h2>Overview</h2><p>{en.short_summary || "No English summary supplied."}</p>{en.full_description ? <p>{en.full_description}</p> : null}</article>
    <div className="sticky-actions"><GuardedLink className="primary-button" href={`/projects/${id}`}><Edit3 aria-hidden size={16}/>Edit Project</GuardedLink>{record.status === "published" ? <GuardedLink className="secondary-button" href={`/projects/${id}/revisions`}>Revision workflow</GuardedLink> : null}<GuardedLink className="secondary-button" href={`/projects/${id}/preview`}>Preview public-safe fields</GuardedLink></div>
  </section>;
}

function Detail({ title, value }: Readonly<{ title: string; value?: string | null }>) {
  return <div className="content-block"><small>{title}</small><strong>{value || "Not confirmed"}</strong></div>;
}
