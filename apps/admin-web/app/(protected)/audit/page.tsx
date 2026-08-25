"use client";

import { useQuery } from "@tanstack/react-query";
import { Check, Copy, Search } from "lucide-react";
import { useState } from "react";

import { AdminPageHeader, DataTableShell, EmptyState, FilterToolbar, InlineFeedback, LoadingState, StatusBadge } from "../../../components/admin-ui";
import { api, type PageResponse } from "../../../lib/api";

type Audit = { id: string; action: string; entity_type: string; entity_id: string | null; occurred_at: string; outcome: string; request_correlation_id: string };
const readableAction = (action: string) => action.split(".").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" · ");

export default function AuditPage() {
  const [action, setAction] = useState(""); const [copied, setCopied] = useState("");
  const query = useQuery({ queryKey: ["audit", action], queryFn: () => api<PageResponse<Audit>>(`/admin/audit?page_size=100${action ? `&action=${encodeURIComponent(action)}` : ""}`) });
  const total = query.data?.meta.total ?? 0;
  return <section><AdminPageHeader description="Review immutable security and operational events without exposing private payloads." eyebrow="Security" title="Audit Log"/>
    <FilterToolbar filtered={Boolean(action)} onReset={() => setAction("")} resultLabel={`${total} ${total === 1 ? "event" : "events"}`}><label className="search-control"><span>Action</span><div><Search aria-hidden size={16}/><input onChange={(event) => setAction(event.target.value)} placeholder="Filter by action" type="search" value={action}/></div></label></FilterToolbar>
    {query.isLoading ? <LoadingState label="Loading audit events…"/> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : !query.data?.items.length ? <DataTableShell label="Audit results"><EmptyState description={action ? "Reset the action filter to see other events." : "Security and operational events will appear here."} filtered={Boolean(action)} title={action ? "No events match this filter" : "No audit events yet"}/></DataTableShell> : <DataTableShell label="Audit results"><table><thead><tr><th>Time</th><th>Action</th><th>Entity</th><th>Outcome</th><th>Correlation ID</th></tr></thead><tbody>{query.data.items.map((item) => <tr key={item.id}><td><time dateTime={item.occurred_at}>{new Date(item.occurred_at).toLocaleString()}</time></td><td><strong title={item.action}>{readableAction(item.action)}</strong><code className="raw-action">{item.action}</code></td><td>{item.entity_type}{item.entity_id ? ` · ${item.entity_id.slice(0, 8)}` : ""}</td><td><StatusBadge status={item.outcome}/></td><td><div className="copy-value"><code title={item.request_correlation_id}>{item.request_correlation_id}</code><button aria-label="Copy correlation ID" onClick={async () => { await navigator.clipboard.writeText(item.request_correlation_id); setCopied(item.id); }} type="button">{copied === item.id ? <Check aria-hidden size={15}/> : <Copy aria-hidden size={15}/>}</button></div></td></tr>)}</tbody></table></DataTableShell>}
  </section>;
}
