"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AdminPageHeader, InlineFeedback, LoadingState } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { api, type ResourceRecord } from "../lib/api";

type Values = { display_name: string; phone: string; google_business_url: string; google_rating: string; google_review_count: string; snapshot_verified_at: string; office_address: string; status: string };
const fromRecord = (data: ResourceRecord): Values => ({ display_name: String(data.display_name ?? ""), phone: String(data.phone ?? ""), google_business_url: String(data.google_business_url ?? ""), google_rating: String(data.google_rating ?? ""), google_review_count: String(data.google_review_count ?? ""), snapshot_verified_at: String(data.snapshot_verified_at ?? ""), office_address: String(data.office_address ?? ""), status: String(data.status ?? "draft") });

export function TrustProfileEditor() {
  const query = useQuery({ queryKey: ["trust-profile"], queryFn: () => api<ResourceRecord>("/admin/trust-profile") });
  if (query.isLoading) return <LoadingState label="Loading trust profile…"/>;
  if (query.error) return <InlineFeedback tone="error">{query.error.message}</InlineFeedback>;
  if (!query.data) return <InlineFeedback tone="error">Trust profile not found.</InlineFeedback>;
  return <TrustProfileForm initial={fromRecord(query.data)}/>;
}

function TrustProfileForm({ initial }: Readonly<{ initial: Values }>) {
  const { user } = useAuth(); const queryClient = useQueryClient(); const [values, setValues] = useState(initial); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState("");
  const update = (key: keyof Values, value: string) => setValues((current) => ({ ...current, [key]: value }));
  async function save(event: React.FormEvent) { event.preventDefault(); setBusy(true); setNotice(""); try { await api("/admin/trust-profile", { method: "PUT", body: JSON.stringify({ ...values, google_rating: Number(values.google_rating), google_review_count: Number(values.google_review_count) }) }, user?.csrf_token); await queryClient.invalidateQueries({ queryKey: ["trust-profile"] }); setNotice("Verified business snapshot saved and audited."); } catch (error) { setNotice(error instanceof Error ? error.message : "The snapshot could not be saved."); } finally { setBusy(false); } }
  return <section><AdminPageHeader description="Maintain the timestamped public-safe Google Business snapshot. Values are not live." eyebrow="Verified business data" title="Trust profile"/><form className="editor-form" onSubmit={(event) => void save(event)}><fieldset className="form-section"><legend>Business identity and source</legend><div className="form-grid"><label>Display name<input required value={values.display_name} onChange={(e) => update("display_name", e.target.value)}/></label><label>WhatsApp / phone<input required dir="ltr" value={values.phone} onChange={(e) => update("phone", e.target.value)}/></label><label className="wide">Google Business source URL<input required dir="ltr" type="url" value={values.google_business_url} onChange={(e) => update("google_business_url", e.target.value)}/></label><label>Rating snapshot<input required max="5" min="0" step="0.1" type="number" value={values.google_rating} onChange={(e) => update("google_rating", e.target.value)}/></label><label>Review-count snapshot<input required min="0" type="number" value={values.google_review_count} onChange={(e) => update("google_review_count", e.target.value)}/></label><label>Snapshot verification date<input required type="date" value={values.snapshot_verified_at} onChange={(e) => update("snapshot_verified_at", e.target.value)}/></label><label>Status<select value={values.status} onChange={(e) => update("status", e.target.value)}><option value="draft">Draft</option><option value="published">Published</option><option value="archived">Archived</option></select></label><label className="wide">Exact Google Business address<input required value={values.office_address} onChange={(e) => update("office_address", e.target.value)}/></label></div></fieldset><button className="action-button action-button--publish" disabled={busy} type="submit">{busy ? "Saving…" : "Save trust profile"}</button>{notice ? <InlineFeedback tone={notice.includes("could not") ? "error" : "success"}>{notice}</InlineFeedback> : null}</form></section>;
}
