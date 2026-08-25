"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, RefreshCw, SearchCheck } from "lucide-react";

import { api, type PageResponse } from "../lib/api";
import {
  AdminPageHeader,
  DataTableShell,
  EmptyState,
  InlineFeedback,
  LoadingState,
  StatusBadge,
} from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink } from "./navigation-guard";

type Diagnostic = {
  id: string;
  item_id: string;
  stage: string;
  error_code: string;
  explanation: string;
  affected_reference?: string | null;
  retryable: boolean;
  attempt_count: number;
  next_retry_at?: string | null;
  last_successful_stage?: string | null;
  suggested_resolution: string;
  resolution_status: string;
  resolution_note?: string | null;
  correlation_id: string;
  latest_occurred_at: string;
};

type ProcessingItem = {
  id: string;
  candidate_id: string;
  ordinal: number;
  status: string;
  current_stage?: string | null;
  completed_stages: string[];
  attempt_count: number;
  next_retry_at?: string | null;
  result_summary: Record<string, unknown>;
  diagnostics: Diagnostic[];
};

type ProcessingJob = {
  id: string;
  batch_id: string;
  requested_action: string;
  selection_mode: string;
  selected_record_ids: string[];
  status: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  total_count: number;
  queued_count: number;
  processing_count: number;
  succeeded_count: number;
  failed_count: number;
  skipped_count: number;
  progress_percent: number;
  cancellation_requested: boolean;
  correlation_id: string;
  items?: ProcessingItem[];
};

export function ProcessingJobList() {
  const query = useQuery({
    queryKey: ["project-processing-jobs"],
    queryFn: () => api<PageResponse<ProcessingJob>>("/admin/project-processing-jobs"),
    refetchInterval: 5000,
  });
  return (
    <section>
      <AdminPageHeader
        description="Monitor durable Project preparation jobs. Ready to Post remains separate from publication."
        eyebrow="Off-Plan Operations"
        title="Processing Jobs"
      />
      {query.isLoading ? (
        <LoadingState label="Loading processing jobs…" />
      ) : query.error ? (
        <InlineFeedback tone="error">{query.error.message}</InlineFeedback>
      ) : !query.data?.items.length ? (
        <DataTableShell label="Processing jobs">
          <EmptyState
            description="No preparation job exists. Start one from a Project import batch."
            title="No processing jobs"
          />
        </DataTableShell>
      ) : (
        <DataTableShell label="Processing jobs">
          <table>
            <thead><tr><th>Created</th><th>Selection</th><th>Status</th><th>Progress</th><th>Results</th><th>Action</th></tr></thead>
            <tbody>{query.data.items.map((job) => (
              <tr key={job.id}>
                <td>{date(job.created_at)}</td>
                <td>{humanize(job.selection_mode)} · {job.total_count}</td>
                <td><StatusBadge status={job.status} /></td>
                <td>{job.progress_percent}%</td>
                <td>{job.succeeded_count} passed · {job.failed_count} failed</td>
                <td><GuardedLink className="table-link" href={`/project-processing/${job.id}`}>View job</GuardedLink></td>
              </tr>
            ))}</tbody>
          </table>
        </DataTableShell>
      )}
    </section>
  );
}

export function ProcessingJobDetail({ id }: Readonly<{ id: string }>) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["project-processing-job", id],
    queryFn: () => api<ProcessingJob>(`/admin/project-processing-jobs/${id}`),
    refetchInterval: 3000,
  });
  const retry = useMutation({
    mutationFn: (itemIds?: string[]) => api<ProcessingJob>(
      `/admin/project-processing-jobs/${id}/retry`,
      { method: "POST", body: JSON.stringify({ item_ids: itemIds ?? null }) },
      user?.csrf_token,
    ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["project-processing-job", id] }),
  });
  const cancel = useMutation({
    mutationFn: () => api<ProcessingJob>(
      `/admin/project-processing-jobs/${id}/cancel`,
      { method: "POST" },
      user?.csrf_token,
    ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["project-processing-job", id] }),
  });
  if (query.isLoading) return <LoadingState label="Loading processing job…" />;
  if (query.error) return <InlineFeedback tone="error">{query.error.message}</InlineFeedback>;
  if (!query.data) return null;
  const job = query.data;
  const failed = job.items?.filter((item) => item.status === "failed") ?? [];
  const running = ["queued", "running"].includes(job.status);
  return (
    <section>
      <AdminPageHeader
        back={<GuardedLink className="back-link" href="/project-processing"><ArrowLeft aria-hidden size={16} />Back to jobs</GuardedLink>}
        description={`${humanize(job.selection_mode)} selection · immutable snapshot of ${job.total_count} candidate(s)`}
        eyebrow="Processing Job"
        title={job.id}
        action={<StatusBadge status={job.status} />}
      />
      {(retry.error || cancel.error) ? <InlineFeedback tone="error">{retry.error?.message ?? cancel.error?.message}</InlineFeedback> : null}
      <section className="panel processing-summary">
        <div><span>Progress</span><strong>{job.progress_percent}%</strong></div>
        <div><span>Queued</span><strong>{job.queued_count}</strong></div>
        <div><span>Processing</span><strong>{job.processing_count}</strong></div>
        <div><span>Succeeded</span><strong>{job.succeeded_count}</strong></div>
        <div><span>Failed</span><strong>{job.failed_count}</strong></div>
        <div><span>Skipped</span><strong>{job.skipped_count}</strong></div>
      </section>
      <div className="row-actions">
        {failed.length ? <button className="secondary-button" disabled={retry.isPending} onClick={() => retry.mutate()} type="button"><RefreshCw aria-hidden size={15} />Retry eligible failures</button> : null}
        {running ? <button className="action-button action-button--archive" disabled={cancel.isPending} onClick={() => cancel.mutate()} type="button">Cancel between records</button> : null}
        <button className="secondary-button" onClick={() => downloadSummary(job)} type="button">Download operational summary</button>
      </div>
      <DataTableShell label="Per-record processing results">
        <table>
          <thead><tr><th>Record</th><th>Status</th><th>Stage</th><th>Completed</th><th>Attempts</th><th>Diagnostic</th><th>Action</th></tr></thead>
          <tbody>{job.items?.map((item) => {
            const diagnostic = item.diagnostics.at(-1);
            return <tr key={item.id}><td>#{item.ordinal}</td><td><StatusBadge status={item.status} /></td><td>{humanize(item.current_stage ?? "waiting")}</td><td>{item.completed_stages.length}/15</td><td>{item.attempt_count}</td><td>{diagnostic?.explanation ?? "—"}</td><td>{item.status === "failed" && diagnostic?.retryable ? <button className="table-link" disabled={retry.isPending} onClick={() => retry.mutate([item.id])} type="button">Retry stage</button> : "—"}</td></tr>;
          })}</tbody>
        </table>
      </DataTableShell>
      <details className="panel technical-details"><summary>Authenticated technical references</summary><dl className="detail-grid"><Detail label="Correlation ID" value={job.correlation_id} /><Detail label="Requested action" value={job.requested_action} /><Detail label="Started" value={date(job.started_at)} /><Detail label="Completed" value={date(job.completed_at)} /></dl></details>
    </section>
  );
}

export function ProjectRecoveryQueue() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({ stage: "", code: "", kind: "", status: "" });
  const [notes, setNotes] = useState<Record<string, string>>({});
  const params = useMemo(() => {
    const value = new URLSearchParams();
    if (filters.stage) value.set("stage", filters.stage);
    if (filters.code) value.set("error_code", filters.code);
    if (filters.kind) value.set("retryable", filters.kind);
    if (filters.status) value.set("resolution_status", filters.status);
    return value.toString();
  }, [filters]);
  const query = useQuery({
    queryKey: ["project-recovery", params],
    queryFn: () => api<PageResponse<Diagnostic>>(`/admin/project-recovery${params ? `?${params}` : ""}`),
  });
  const action = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => api<Diagnostic>(
      `/admin/project-recovery/${id}/actions`,
      { method: "POST", body: JSON.stringify({ action: name, note: notes[id] }) },
      user?.csrf_token,
    ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["project-recovery"] }),
  });
  return (
    <section>
      <AdminPageHeader
        description="Review sanitized diagnostics and rerun only eligible failed stages. Recovery never publishes or invents facts."
        eyebrow="Off-Plan Operations"
        title="Recovery Queue"
      />
      <div className="resource-filters import-filters">
        <label>Error stage<input value={filters.stage} onChange={(event) => setFilters((current) => ({ ...current, stage: event.target.value }))} /></label>
        <label>Error code<input value={filters.code} onChange={(event) => setFilters((current) => ({ ...current, code: event.target.value }))} /></label>
        <label>Recovery type<select value={filters.kind} onChange={(event) => setFilters((current) => ({ ...current, kind: event.target.value }))}><option value="">All</option><option value="true">Retryable</option><option value="false">Human required</option></select></label>
        <label>Resolution<select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}><option value="">All</option><option value="open">Open</option><option value="human-input-required">Human input required</option><option value="resolved">Resolved</option><option value="rejected">Rejected</option></select></label>
        <button className="secondary-button" onClick={() => setFilters({ stage: "", code: "", kind: "", status: "" })} type="button">Reset filters</button>
      </div>
      {action.error ? <InlineFeedback tone="error">{action.error.message}</InlineFeedback> : null}
      {query.isLoading ? <LoadingState label="Loading recovery diagnostics…" /> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : !query.data?.items.length ? <DataTableShell label="Recovery diagnostics"><EmptyState description="No diagnostic matches the current filters." title="Recovery queue is clear" /></DataTableShell> : <div className="recovery-list">{query.data.items.map((item) => <article className="panel" key={item.id}><div className="recovery-heading"><AlertTriangle aria-hidden size={18} /><div><h2>{humanize(item.error_code)}</h2><p>{humanize(item.stage)} · attempt {item.attempt_count}</p></div><StatusBadge status={item.resolution_status} /></div><p>{item.explanation}</p><p><strong>Suggested resolution:</strong> {item.suggested_resolution}</p><label>Required operator note<textarea rows={2} value={notes[item.id] ?? ""} onChange={(event) => setNotes((current) => ({ ...current, [item.id]: event.target.value }))} /></label><div className="row-actions"><button className="secondary-button" disabled={(notes[item.id]?.trim().length ?? 0) < 3 || action.isPending} onClick={() => action.mutate({ id: item.id, name: "diagnose-ai" })} type="button"><SearchCheck aria-hidden size={15} />Diagnose with AI boundary</button>{item.retryable ? <button className="secondary-button" disabled={(notes[item.id]?.trim().length ?? 0) < 3 || action.isPending} onClick={() => action.mutate({ id: item.id, name: "apply-safe-correction" })} type="button">Apply safe correction and rerun</button> : null}<button className="secondary-button" disabled={(notes[item.id]?.trim().length ?? 0) < 3 || action.isPending} onClick={() => action.mutate({ id: item.id, name: "mark-human-input-required" })} type="button">Human input required</button><button className="action-button action-button--archive" disabled={(notes[item.id]?.trim().length ?? 0) < 3 || action.isPending} onClick={() => action.mutate({ id: item.id, name: "reject" })} type="button">Reject</button></div><details className="technical-details"><summary>Diagnostic references</summary><dl className="detail-grid"><Detail label="Affected item" value={item.affected_reference ?? "—"} /><Detail label="Last successful stage" value={item.last_successful_stage ?? "None"} /><Detail label="Next retry" value={date(item.next_retry_at)} /><Detail label="Correlation ID" value={item.correlation_id} /></dl></details></article>)}</div>}
    </section>
  );
}

function downloadSummary(job: ProcessingJob) {
  const safe = {
    job_id: job.id,
    status: job.status,
    selection_mode: job.selection_mode,
    total: job.total_count,
    succeeded: job.succeeded_count,
    failed: job.failed_count,
    skipped: job.skipped_count,
    items: job.items?.map((item) => ({
      ordinal: item.ordinal,
      status: item.status,
      stage: item.current_stage,
      error_code: item.diagnostics.at(-1)?.error_code,
    })),
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(safe, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `project-processing-${job.id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function Detail({ label, value }: Readonly<{ label: string; value: string }>) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}

function date(value?: string | null) {
  return value ? new Date(value).toLocaleString("en-AE") : "—";
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
