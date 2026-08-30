"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AdminPageHeader, FormSection, InlineFeedback, StickyFormActions, StatusBadge } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink } from "./navigation-guard";
import { api } from "../lib/api";

type Alias = { alias: string; locale: "en" | "ar" | null };
type AreaRecord = { id: string; slug: string; name_en: string; name_ar: string; emirate: string; status: string; aliases: Alias[]; workflow: { content_version: string; workflow_status: string; referenced_project_count: number; blockers: string[] } };
const emirates = ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"];

export function AreaEditor({ id }: Readonly<{ id: string }>) {
  const query = useQuery({ queryKey: ["area", id], queryFn: () => api<AreaRecord>(`/admin/areas/${id}`) });
  if (query.isLoading) return <p>Loading Area…</p>;
  if (query.error || !query.data) return <InlineFeedback tone="error">{query.error?.message ?? "Area not found."}</InlineFeedback>;
  return <AreaEditorForm id={id} key={query.data.workflow.content_version} record={query.data}/>;
}

function AreaEditorForm({ id, record }: Readonly<{ id: string; record: AreaRecord }>) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [values, setValues] = useState({ slug: record.slug, name_en: record.name_en, name_ar: record.name_ar, emirate: record.emirate, aliases_en: record.aliases.filter((item) => item.locale === "en").map((item) => item.alias).join("\n"), aliases_ar: record.aliases.filter((item) => item.locale === "ar").map((item) => item.alias).join("\n"), aliases_other: record.aliases.filter((item) => item.locale === null).map((item) => item.alias).join("\n") });
  const [notice, setNotice] = useState("");
  const mutation = useMutation({
    mutationFn: () => api<AreaRecord>(`/admin/areas/${id}`, { method: "PUT", body: JSON.stringify({ slug: values.slug, name_en: values.name_en, name_ar: values.name_ar, emirate: values.emirate, aliases: [[values.aliases_en, "en"], [values.aliases_ar, "ar"], [values.aliases_other, null]].flatMap(([text, locale]) => String(text).split("\n").map((alias) => alias.trim()).filter(Boolean).map((alias) => ({ alias, locale }))), expected_content_version: record.workflow.content_version }) }, user?.csrf_token),
    onSuccess: async (record) => { setNotice("Area saved. Any earlier review receipt is now stale until this version is reviewed."); queryClient.setQueryData(["area", id], record); await queryClient.invalidateQueries({ queryKey: ["areas"] }); },
  });
  return <section><AdminPageHeader eyebrow="Canonical Area" title={record.name_en} description="Edit identity and bilingual labels. Publication transitions remain explicit on the Areas workspace." back={<GuardedLink className="back-link" href="/areas">Back to Areas</GuardedLink>} action={<div className="status-cluster"><StatusBadge status={record.workflow.workflow_status}/><StatusBadge status={record.status}/></div>}/>{notice ? <InlineFeedback tone="success">{notice}</InlineFeedback> : null}{mutation.error ? <InlineFeedback tone="error">{mutation.error.message}</InlineFeedback> : null}<form className="editor-form" onSubmit={(event) => { event.preventDefault(); mutation.mutate(); }}><FormSection id="area-identity" title="Area identity and bilingual labels" description={`${record.workflow.referenced_project_count} target Project(s) reference this immutable Area ID.`}><div className="form-grid"><label>Stable slug<input required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" value={values.slug} onChange={(event) => setValues((current) => ({ ...current, slug: event.target.value }))}/></label><label>Emirate<select required value={values.emirate} onChange={(event) => setValues((current) => ({ ...current, emirate: event.target.value }))}>{emirates.map((item) => <option key={item}>{item}</option>)}</select></label><label>English name<input required value={values.name_en} onChange={(event) => setValues((current) => ({ ...current, name_en: event.target.value }))}/></label><label dir="rtl">الاسم العربي<input required value={values.name_ar} onChange={(event) => setValues((current) => ({ ...current, name_ar: event.target.value }))}/></label><label>English aliases<textarea rows={5} value={values.aliases_en} onChange={(event) => setValues((current) => ({ ...current, aliases_en: event.target.value }))}/></label><label dir="rtl">الأسماء العربية البديلة<textarea rows={5} value={values.aliases_ar} onChange={(event) => setValues((current) => ({ ...current, aliases_ar: event.target.value }))}/></label><label className="wide">Locale-neutral aliases<textarea rows={4} value={values.aliases_other} onChange={(event) => setValues((current) => ({ ...current, aliases_other: event.target.value }))}/></label></div></FormSection><StickyFormActions state={`Version ${record.workflow.content_version.slice(0, 12)}`} help={record.workflow.blockers.length ? record.workflow.blockers.join("; ") : "No current eligibility blockers."}><GuardedLink className="secondary-button" href="/areas">Cancel</GuardedLink><button className="action-button" disabled={mutation.isPending || record.status !== "draft"} type="submit">{mutation.isPending ? "Saving…" : "Save Area"}</button></StickyFormActions></form></section>;
}
