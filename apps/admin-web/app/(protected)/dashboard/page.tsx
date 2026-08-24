"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
export default function DashboardPage() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Record<string, number>>("/admin/dashboard") });
  return <section><div className="page-heading"><div><p className="eyebrow">Authenticated workspace</p><h1>Dashboard</h1><p>Live counts from PostgreSQL. No placeholder statistics.</p></div></div>{query.isLoading ? <div className="panel-state">Loading counts…</div> : query.error ? <div className="panel-state form-error">{query.error.message}</div> : <div className="metric-grid">{Object.entries(query.data ?? {}).map(([name, count]) => <article key={name}><span>{name}</span><strong>{count}</strong></article>)}</div>}</section>;
}
