"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { FormSection, InlineFeedback } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink } from "./navigation-guard";

type Review = {
  content_version: string;
  blockers: string[];
  media: Array<{ sha256: string | null; category: string; source_url: string }>;
  receipt: null | { reviewer: string; reviewed_at: string; content_version: string; current: boolean };
};
const labels = {
  facts: "Facts, official sources, freshness and payment-plan applicability",
  english: "English editorial content",
  arabic: "Arabic editorial content and RTL",
  media_rights: "Documented Cover/Gallery reuse permission (scraping is not permission)",
  seo: "English and Arabic SEO titles and descriptions",
  disclaimer: "Displayed disclaimer and required source/asset limitations",
  preview: "Both private EN/AR previews checked",
};

export function ProjectApprovalReview({ id, status, workflow, onApproved }: Readonly<{
  id: string; status: string; workflow: string; onApproved: () => void;
}>) {
  const { user } = useAuth();
  const cache = useQueryClient();
  const review = useQuery({ queryKey: ["project-approval", id, workflow], queryFn: () => api<Review>(`/admin/projects/${id}/approval-review`) });
  type Checks = Record<string, { confirmed: boolean; evidence_reference: string }>;
  type Permissions = Record<string, string>;
  const [draft, setDraft] = useState<{ version: string; checks: Checks; permissions: Permissions }>({ version: "", checks: {}, permissions: {} });
  const version = review.data?.content_version ?? "";
  const checks = draft.version === version ? draft.checks : {};
  const permissions = draft.version === version ? draft.permissions : {};
  function setChecks(update: (current: Checks) => Checks) {
    setDraft((current) => ({ version, checks: update(current.version === version ? current.checks : {}), permissions: current.version === version ? current.permissions : {} }));
  }
  function setPermissions(update: (current: Permissions) => Permissions) {
    setDraft((current) => ({ version, permissions: update(current.version === version ? current.permissions : {}), checks: current.version === version ? current.checks : {} }));
  }
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [failed, setFailed] = useState(false);
  async function approve() {
    if (!review.data) return;
    setBusy(true); setMessage("");
    try {
      await api(`/admin/projects/${id}/approve`, { method: "POST", body: JSON.stringify({ content_version: review.data.content_version, checks, media_permissions: permissions }) }, user?.csrf_token);
      setFailed(false); setMessage("Review recorded. The Project remains private and unpublished.");
      await cache.invalidateQueries({ queryKey: ["project", id] });
      await review.refetch(); onApproved();
    } catch (error) { setFailed(true); setMessage(error instanceof Error ? error.message : "Review could not be recorded."); }
    finally { setBusy(false); }
  }
  return <div className="editor-form"><FormSection id="approval-review" title="Publication review" description="Save changes first, then submit for review. Approval records the signed-in reviewer, time and exact content version; it never publishes.">
    {review.error ? <InlineFeedback tone="error">{review.error.message}</InlineFeedback> : null}
    {review.data ? <>
      <p>Review version: <code>{review.data.content_version.slice(0, 12)}</code></p>
      {review.data.receipt ? <p>Last review: {review.data.receipt.reviewer} · {new Date(review.data.receipt.reviewed_at).toLocaleString("en-AE")} · {review.data.receipt.current ? "Current version" : "Stale — review required"}</p> : <p>No complete approval receipt has been recorded.</p>}
      <GuardedLink className="secondary-button" href={`/projects/${id}/preview`}>Open private EN/AR preview</GuardedLink>
      {review.data.blockers.length ? <InlineFeedback tone="info"><ul>{review.data.blockers.map((item) => <li key={item}>{item}</li>)}</ul></InlineFeedback> : null}
      <details><summary>Review checklist and private evidence references</summary>
        <div className="form-grid">{Object.entries(labels).map(([key, label]) => <div className="content-block" key={key}>
          <label className="check"><input type="checkbox" checked={checks[key]?.confirmed ?? false} onChange={(event) => setChecks((current) => ({ ...current, [key]: { evidence_reference: current[key]?.evidence_reference ?? "", confirmed: event.target.checked } }))}/>{label}</label>
          <label>Private evidence / review reference<input value={checks[key]?.evidence_reference ?? ""} onChange={(event) => setChecks((current) => ({ ...current, [key]: { confirmed: current[key]?.confirmed ?? false, evidence_reference: event.target.value } }))}/></label>
        </div>)}</div>
        <p>For each exact image, reference a Developer permission, permitted media kit or licence, including permitted channels, attribution and expiry. Do not use the source URL as a substitute for permission.</p>
        {review.data.media.filter((item) => item.sha256).map((item) => <label key={item.sha256}> {item.category} · checksum {item.sha256?.slice(0, 12)}<input value={permissions[item.sha256!] ?? ""} onChange={(event) => setPermissions((current) => ({ ...current, [item.sha256!]: event.target.value }))}/></label>)}
      </details>
      {status === "draft" && workflow === "in-review" && user?.permissions.includes("project.publish") ? <button className="primary-button" type="button" disabled={busy || review.data.blockers.length > 0 || Object.keys(labels).some((key) => !checks[key]?.confirmed || (checks[key]?.evidence_reference.trim().length ?? 0) < 12) || review.data.media.some((item) => !item.sha256 || (permissions[item.sha256]?.trim().length ?? 0) < 12)} onClick={() => void approve()}>{busy ? "Recording review…" : "Approve reviewed version"}</button> : null}
    </> : !review.error ? <p>Loading review requirements…</p> : null}
    {message ? <InlineFeedback tone={failed ? "error" : "success"}>{message}</InlineFeedback> : null}
  </FormSection></div>;
}
