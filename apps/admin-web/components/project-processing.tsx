"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";

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

type ProcessingItem = {
  id: string;
  candidate_id: string;
  ordinal: number;
  status: string;
  current_stage?: string | null;
  completed_stages: string[];
  attempt_count: number;
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
      {cancel.error ? <InlineFeedback tone="error">{cancel.error.message}</InlineFeedback> : null}
      <section className="panel processing-summary">
        <div><span>Progress</span><strong>{job.progress_percent}%</strong></div>
        <div><span>Queued</span><strong>{job.queued_count}</strong></div>
        <div><span>Processing</span><strong>{job.processing_count}</strong></div>
        <div><span>Succeeded</span><strong>{job.succeeded_count}</strong></div>
        <div><span>Failed</span><strong>{job.failed_count}</strong></div>
        <div><span>Skipped</span><strong>{job.skipped_count}</strong></div>
      </section>
      <div className="row-actions">
        {running ? <button className="action-button action-button--archive" disabled={cancel.isPending} onClick={() => cancel.mutate()} type="button">Cancel between records</button> : null}
        <button className="secondary-button" onClick={() => downloadSummary(job)} type="button">Download operational summary</button>
      </div>
      <DataTableShell label="Per-record processing results">
        <table>
          <thead><tr><th>Record</th><th>Status</th><th>Stage</th><th>Completed</th><th>Attempts</th></tr></thead>
          <tbody>{job.items?.map((item) => <tr key={item.id}><td>#{item.ordinal}</td><td><StatusBadge status={item.status} /></td><td>{humanize(item.current_stage ?? "waiting")}</td><td>{item.completed_stages.length}/15</td><td>{item.attempt_count}</td></tr>)}</tbody>
        </table>
      </DataTableShell>
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
    })),
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(safe, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `project-processing-${job.id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function date(value?: string | null) {
  return value ? new Date(value).toLocaleString("en-AE") : "—";
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
