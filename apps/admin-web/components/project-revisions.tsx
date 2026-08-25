"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

import { api, type PageResponse } from "../lib/api";
import { AdminPageHeader, DataTableShell, EmptyState, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink } from "./navigation-guard";

type Revision = {
  id: string;
  revision_number: number;
  status: string;
  field_diff: Record<string, unknown>;
  media_snapshot: Array<Record<string, unknown>>;
  change_summary?: string | null;
  created_at: string;
};

export function ProjectRevisions({ projectId }: Readonly<{ projectId: string }>) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["project-revisions", projectId], queryFn: () => api<PageResponse<Revision>>(`/admin/projects/${projectId}/revisions`) });
  const transition = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) => api<Revision>(`/admin/projects/${projectId}/revisions/${id}/${action}`, { method: "POST", body: JSON.stringify({ note: `Admin ${action} confirmation` }) }, user?.csrf_token),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["project-revisions", projectId] }),
  });
  if (query.isLoading) return <LoadingState label="Loading Project revisions…" />;
  if (query.error) return <InlineFeedback tone="error">{query.error.message}</InlineFeedback>;
  return <section><AdminPageHeader back={<GuardedLink className="back-link" href={`/projects/${projectId}/view`}><ArrowLeft aria-hidden size={16}/>Back to Project</GuardedLink>} description="The active Published version stays public until an approved revision is activated atomically." eyebrow="Published Project" title="Revision workflow"/>{transition.error ? <InlineFeedback tone="error">{transition.error.message}</InlineFeedback> : null}{!query.data?.items.length ? <DataTableShell label="Project revisions"><EmptyState description="Save changes from the Project editor to create the first private Draft Revision." title="No revisions"/></DataTableShell> : <DataTableShell label="Project revisions"><table><thead><tr><th>Revision</th><th>Status</th><th>Summary</th><th>Field changes</th><th>Media changes</th><th>Created</th><th>Actions</th></tr></thead><tbody>{query.data.items.map((revision) => <tr key={revision.id}><td>#{revision.revision_number}</td><td><StatusBadge status={revision.status}/></td><td>{revision.change_summary ?? "—"}</td><td>{Object.keys(revision.field_diff).length}</td><td>{revision.media_snapshot.length}</td><td>{new Date(revision.created_at).toLocaleString("en-AE")}</td><td><div className="row-actions">{revision.status === "draft" ? <button className="table-link" disabled={transition.isPending} onClick={() => transition.mutate({ id: revision.id, action: "submit" })} type="button">Submit</button> : null}{revision.status === "in-review" ? <button className="table-link" disabled={transition.isPending} onClick={() => transition.mutate({ id: revision.id, action: "approve" })} type="button">Approve</button> : null}{revision.status === "approved" ? <button className="table-link" disabled={transition.isPending} onClick={() => transition.mutate({ id: revision.id, action: "activate" })} type="button">Activate</button> : null}{revision.status === "superseded" ? <button className="table-link" disabled={transition.isPending} onClick={() => transition.mutate({ id: revision.id, action: "rollback" })} type="button">Rollback</button> : null}{revision.status === "active" ? "Current live version" : null}</div></td></tr>)}</tbody></table></DataTableShell>}<details className="panel technical-details"><summary>Revision safety rules</summary><p>Review field and media differences before approval. Activation is atomic, retains the previous approved version and never exposes internal sources or ARE Priority through Public output.</p></details></section>;
}
