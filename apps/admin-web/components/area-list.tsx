"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";

import { AdminPageHeader, ConfirmationDialog, DataTableShell, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { api, type PageResponse } from "../lib/api";

type AreaWorkflow = { content_version: string; workflow_status: string; referenced_project_count: number; blockers: string[]; receipt: { current: boolean } | null };
type AreaRecord = { id: string; slug: string; name_en: string; name_ar: string; emirate: string; status: string; workflow: AreaWorkflow };
type Action = "submit-review" | "approve" | "publish";

const actionLabels: Record<Action, string> = {
  "submit-review": "Submit for Review",
  approve: "Approve current versions",
  publish: "Publish Areas",
};

export function AreaList() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [pending, setPending] = useState<Action | null>(null);
  const [notice, setNotice] = useState("");
  const query = useQuery({ queryKey: ["areas"], queryFn: () => api<PageResponse<AreaRecord>>("/admin/areas") });
  const referenced = useMemo(() => query.data?.items.filter((item) => item.workflow.referenced_project_count > 0) ?? [], [query.data]);
  const selectedRecords = referenced.filter((item) => selected[item.id]);
  const selectionState = new Set(selectedRecords.map((item) => item.workflow.workflow_status));
  const expectedState: Record<Action, string> = { "submit-review": "draft", approve: "in_review", publish: "approved" };
  const canRun = (action: Action) => selectedRecords.length > 0 && selectedRecords.length <= 50 && selectionState.size === 1 && selectionState.has(expectedState[action]) && selectedRecords.every((item) => item.workflow.blockers.length === 0);
  const mutation = useMutation({
    mutationFn: (action: Action) => api<{ affected_count: number; correlation_id: string; message: string }>("/admin/areas/bulk-workflow", {
      method: "POST",
      body: JSON.stringify({
        action,
        area_ids: selectedRecords.map((item) => item.id),
        expected_content_versions: Object.fromEntries(selectedRecords.map((item) => [item.id, item.workflow.content_version])),
        idempotency_key: crypto.randomUUID(),
        confirmation: { "submit-review": "SUBMIT", approve: "APPROVE", publish: "PUBLISH" }[action],
      }),
    }, user?.csrf_token),
    onSuccess: async (result) => {
      setPending(null);
      setNotice(`${result.message} Audit correlation: ${result.correlation_id}`);
      await queryClient.invalidateQueries({ queryKey: ["areas"] });
    },
  });
  const allSelected = referenced.length > 0 && referenced.every((item) => selected[item.id]);

  return <section>
    <AdminPageHeader eyebrow="Off-Plan CMS" title="Areas" description="Review and publish the canonical Areas referenced by RAK and Sharjah Projects."/>
    {notice ? <InlineFeedback tone="success">{notice}</InlineFeedback> : null}
    {mutation.error ? <InlineFeedback tone="error">{mutation.error.message}</InlineFeedback> : null}
    {query.isLoading ? <LoadingState label="Loading Areas…"/> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : <>
      <div className="bulk-toolbar" role="region" aria-label="Area publication workflow"><strong>{selectedRecords.length} selected · {referenced.length} referenced</strong><button disabled={!user?.permissions.includes("project.update") || !canRun("submit-review")} onClick={() => setPending("submit-review")} type="button">Submit for Review<small>Current bilingual Area version</small></button><button disabled={!user?.permissions.includes("project.publish") || !canRun("approve")} onClick={() => setPending("approve")} type="button">Approve<small>Creates content-bound receipts</small></button><button disabled={!user?.permissions.includes("project.publish") || !canRun("publish")} onClick={() => setPending("publish")} type="button">Publish<small>Explicit local confirmation</small></button></div>
      <DataTableShell label="Canonical Areas"><table><thead><tr><th><input aria-label="Select all referenced Areas" checked={allSelected} onChange={(event) => setSelected(Object.fromEntries(referenced.map((item) => [item.id, event.target.checked])))} type="checkbox"/></th><th>Area</th><th>Arabic</th><th>Emirate</th><th>Projects</th><th>Workflow</th><th>Publication</th><th>Blockers</th><th>Action</th></tr></thead><tbody>{query.data?.items.map((item) => <tr key={item.id}><td><input aria-label={`Select ${item.name_en}`} checked={Boolean(selected[item.id])} disabled={item.workflow.referenced_project_count === 0} onChange={(event) => setSelected((current) => ({ ...current, [item.id]: event.target.checked }))} type="checkbox"/></td><td><strong>{item.name_en}</strong><code dir="ltr">{item.id}</code></td><td dir="rtl">{item.name_ar}</td><td>{item.emirate}</td><td>{item.workflow.referenced_project_count}</td><td><StatusBadge status={item.workflow.workflow_status}/></td><td><StatusBadge status={item.status}/></td><td>{item.workflow.blockers.length ? item.workflow.blockers.join("; ") : "None"}</td><td><Link className="table-link" href={`/areas/${item.id}`}>Edit/review</Link></td></tr>)}</tbody></table></DataTableShell>
    </>}
    <ConfirmationDialog open={Boolean(pending)} title={pending ? `Confirm ${actionLabels[pending]}` : "Confirm Area action"} description={`Apply this transition atomically to ${selectedRecords.length} exact Area record(s). Any stale or ineligible Area will stop the entire request.`} confirmLabel={pending ? actionLabels[pending] : "Confirm"} onCancel={() => setPending(null)} onConfirm={() => { if (pending) mutation.mutate(pending); }}/>
  </section>;
}
