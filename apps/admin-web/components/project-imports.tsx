"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, CircleX, GitMerge, ListChecks, SearchCheck } from "lucide-react";

import { api, type PageResponse } from "../lib/api";
import { AdminPageHeader, DataTableShell, EmptyState, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink } from "./navigation-guard";

type ImportBatch = {
  id: string;
  name: string;
  source_reference: string;
  started_at?: string | null;
  completed_at?: string | null;
  total_count: number;
  clean_count: number;
  needs_review_count: number;
  failed_count: number;
};

type Candidate = {
  id: string;
  owner_manifest_values: Record<string, unknown>;
  raw_source_payload: Record<string, unknown>;
  normalized_payload: Record<string, unknown> | null;
  normalized_project_name?: string | null;
  proposed_developer_id?: string | null;
  proposed_area_id?: string | null;
  official_source_url?: string | null;
  source_urls: string[];
  extracted_at?: string | null;
  content_hash: string;
  match_result: Record<string, unknown> | null;
  validation_errors: unknown[];
  conflict_reasons: unknown[];
  review_status: string;
  linked_project_id?: string | null;
};

type ImportBatchDetail = ImportBatch & { candidates: Candidate[] };

export function ProjectImportList() {
  const query = useQuery({ queryKey: ["project-imports"], queryFn: () => api<PageResponse<ImportBatch>>("/admin/project-imports") });
  return <section><AdminPageHeader description="Review staged evidence before any candidate can become a canonical Project. This queue never publishes automatically." eyebrow="Off-Plan CMS" title="Project Imports"/>{query.isLoading ? <LoadingState label="Loading import batches…"/> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : !query.data?.items.length ? <DataTableShell label="Project import batches"><EmptyState description="No import batch exists. The owner manifest is retained as an inert intake file for ARE-PRJ-02 and has not entered the database." title="No Project imports yet"/></DataTableShell> : <DataTableShell label="Project import batches"><table><thead><tr><th>Batch</th><th>Source reference</th><th>Total</th><th>Clean</th><th>Needs Review</th><th>Failed</th><th>Started</th><th>Actions</th></tr></thead><tbody>{query.data.items.map((batch) => <tr key={batch.id}><td><strong>{batch.name}</strong></td><td>{batch.source_reference}</td><td>{batch.total_count}</td><td>{batch.clean_count}</td><td>{batch.needs_review_count}</td><td>{batch.failed_count}</td><td>{date(batch.started_at)}</td><td><GuardedLink className="table-link" href={`/project-imports/${batch.id}`}><SearchCheck aria-hidden size={15}/>Review batch</GuardedLink></td></tr>)}</tbody></table></DataTableShell>}</section>;
}

export function ProjectImportDetail({ id }: Readonly<{ id: string }>) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["project-import", id], queryFn: () => api<ImportBatchDetail>(`/admin/project-imports/${id}`) });
  const review = useMutation({ mutationFn: ({ candidateId, status }: { candidateId: string; status: string }) => api<Candidate>(`/admin/project-imports/candidates/${candidateId}`, { method: "PUT", body: JSON.stringify({ review_status: status }) }, user?.csrf_token), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["project-import", id] }) });
  if (query.isLoading) return <LoadingState label="Loading import review…"/>;
  if (query.error) return <InlineFeedback tone="error">{query.error.message}</InlineFeedback>;
  if (!query.data) return null;
  const batch = query.data;
  return <section><AdminPageHeader back={<GuardedLink className="back-link" href="/project-imports"><ArrowLeft aria-hidden size={16}/>Back to Project Imports</GuardedLink>} description={batch.source_reference} eyebrow="Import Review Queue" title={batch.name}/><div className="status-summary" aria-label="Batch summary"><Summary label="Total" value={batch.total_count}/><Summary label="Clean" value={batch.clean_count}/><Summary label="Needs review" value={batch.needs_review_count}/><Summary label="Failed" value={batch.failed_count}/></div>{review.error ? <InlineFeedback tone="error">{review.error.message}</InlineFeedback> : null}{!batch.candidates.length ? <DataTableShell label="Import candidates"><EmptyState description="This batch contains no staged candidates." title="No candidates"/></DataTableShell> : <div className="import-candidate-list">{batch.candidates.map((candidate) => <article className="panel import-candidate" key={candidate.id}><header><div><p className="eyebrow">Candidate {candidate.id}</p><h2>{candidateName(candidate)}</h2></div><StatusBadge status={candidate.review_status}/></header><dl className="detail-grid"><Detail label="Normalized name" value={candidate.normalized_project_name ?? "Unresolved"}/><Detail label="Proposed Developer" value={candidate.proposed_developer_id ?? "Unresolved"}/><Detail label="Proposed Area" value={candidate.proposed_area_id ?? "Unresolved"}/><Detail label="Official source" value={candidate.official_source_url ?? "Unresolved"}/><Detail label="Content hash" value={candidate.content_hash}/><Detail label="Extracted" value={date(candidate.extracted_at)}/><Detail label="Source URLs" value={candidate.source_urls.join(", ") || "None"}/><Detail label="Linked Project" value={candidate.linked_project_id ?? "Not linked"}/><Detail label="Match result" value={json(candidate.match_result)}/><Detail label="Validation errors" value={json(candidate.validation_errors)}/><Detail label="Conflict reasons" value={json(candidate.conflict_reasons)}/></dl><details><summary>Owner manifest values</summary><pre>{json(candidate.owner_manifest_values)}</pre></details><details><summary>Normalized proposed payload</summary><pre>{json(candidate.normalized_payload)}</pre></details><details><summary>Raw source payload (authenticated review only)</summary><pre>{json(candidate.raw_source_payload)}</pre></details><div className="row-actions"><button disabled={review.isPending} onClick={() => review.mutate({ candidateId: candidate.id, status: "ready-for-approval" })} type="button"><ListChecks aria-hidden size={15}/>Ready for approval</button><button disabled={review.isPending} onClick={() => review.mutate({ candidateId: candidate.id, status: "approved" })} type="button"><Check aria-hidden size={15}/>Approve</button><button disabled={review.isPending} onClick={() => review.mutate({ candidateId: candidate.id, status: "rejected" })} type="button"><CircleX aria-hidden size={15}/>Reject</button>{candidate.linked_project_id ? <button disabled={review.isPending} onClick={() => review.mutate({ candidateId: candidate.id, status: "merged" })} type="button"><GitMerge aria-hidden size={15}/>Mark merged</button> : null}</div></article>)}</div>}</section>;
}

function Summary({ label, value }: Readonly<{ label: string; value: number }>) { return <div><strong>{value}</strong><span>{label}</span></div>; }
function Detail({ label, value }: Readonly<{ label: string; value: string }>) { return <div><dt>{label}</dt><dd>{value}</dd></div>; }
function candidateName(candidate: Candidate) { const value = candidate.owner_manifest_values.owner_project_name ?? candidate.normalized_payload?.project_name; return typeof value === "string" && value ? value : "Unnamed candidate"; }
function date(value?: string | null) { return value ? new Date(value).toLocaleString("en-AE") : "—"; }
function json(value: unknown) { return JSON.stringify(value, null, 2); }
