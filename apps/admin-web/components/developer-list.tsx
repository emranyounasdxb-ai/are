"use client";

import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { api, type PageResponse, type ResourceRecord } from "../lib/api";

const emirates = ["Dubai", "Abu Dhabi", "Ras Al Khaimah"];

export function DeveloperList() {
  const [search, setSearch] = useState(""); const [status, setStatus] = useState("");
  const [emirate, setEmirate] = useState(""); const [featured, setFeatured] = useState("");
  const params = new URLSearchParams({ page_size: "100" });
  if (search) params.set("search", search); if (status) params.set("status", status);
  if (emirate) params.set("emirate", emirate); if (featured) params.set("featured", featured);
  const query = useQuery({ queryKey: ["developers", search, status, emirate, featured], queryFn: () => api<PageResponse<ResourceRecord>>(`/admin/developers?${params}`) });
  return <section><div className="page-heading"><div><p className="eyebrow">Canonical data</p><h1>Developers</h1><p>{query.data?.meta.total ?? 0} database records</p></div><Link className="primary-button" href="/developers/new"><Plus aria-hidden size={17}/>New developer</Link></div>
    <div className="toolbar"><label>Search<input onChange={(event) => setSearch(event.target.value)} placeholder="Name or slug" type="search" value={search}/></label><label>Status<select onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{["draft", "published", "archived"].map((item) => <option key={item}>{item}</option>)}</select></label><label>Primary emirate<select onChange={(event) => setEmirate(event.target.value)} value={emirate}><option value="">All emirates</option>{emirates.map((item) => <option key={item}>{item}</option>)}</select></label><label>Featured<select onChange={(event) => setFeatured(event.target.value)} value={featured}><option value="">All</option><option value="true">Featured</option><option value="false">Not featured</option></select></label></div>
    {query.isLoading ? <div className="panel-state">Loading developers…</div> : query.error ? <div className="panel-state form-error" role="alert">{query.error.message}</div> : !query.data?.items.length ? <div className="panel-state"><h2>No developers found</h2><p>Adjust the filters or create an approved developer record.</p></div> : <div className="table-wrap"><table><thead><tr><th>Name</th><th>Primary emirate</th><th>Status</th><th>Featured</th><th>Updated</th><th/></tr></thead><tbody>{query.data.items.map((item) => { const translations = item.translations as Record<string, Record<string, unknown>>; return <tr key={item.id}><td><strong>{String(translations.en?.name ?? item.slug)}</strong><br/><small>{String(item.slug)}</small></td><td>{String(item.primary_emirate)}</td><td><span className="status-chip">{String(item.status)}</span></td><td>{item.featured ? "Yes" : "No"}</td><td>{item.updated_at ? new Date(item.updated_at).toLocaleString() : "—"}</td><td><Link className="table-link" href={`/developers/${item.id}`}>Edit</Link></td></tr>; })}</tbody></table></div>}
  </section>;
}
