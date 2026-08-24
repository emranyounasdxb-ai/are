"use client";
import { useQuery } from "@tanstack/react-query";
import { api, type PageResponse } from "../../../lib/api";
type Audit = { id: string; action: string; entity_type: string; entity_id: string | null; occurred_at: string; outcome: string; request_correlation_id: string };
export default function AuditPage() {
  const query = useQuery({ queryKey: ["audit"], queryFn: () => api<PageResponse<Audit>>("/admin/audit?page_size=100") });
  return <section><div className="page-heading"><div><p className="eyebrow">Security and operations</p><h1>Audit log</h1><p>Immutable summaries without secrets or submitted content.</p></div></div>{query.isLoading ? <div className="panel-state">Loading audit entries…</div> : query.error ? <div className="panel-state form-error">{query.error.message}</div> : !query.data?.items.length ? <div className="panel-state">No audit entries yet.</div> : <div className="table-wrap"><table><thead><tr><th>Time</th><th>Action</th><th>Entity</th><th>Outcome</th><th>Correlation ID</th></tr></thead><tbody>{query.data.items.map((item) => <tr key={item.id}><td>{new Date(item.occurred_at).toLocaleString()}</td><td><strong>{item.action}</strong></td><td>{item.entity_type}{item.entity_id ? ` · ${item.entity_id.slice(0, 8)}` : ""}</td><td>{item.outcome}</td><td><code>{item.request_correlation_id}</code></td></tr>)}</tbody></table></div>}</section>;
}
