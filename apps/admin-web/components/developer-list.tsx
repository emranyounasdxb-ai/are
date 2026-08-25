"use client";

import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Plus, Search, Star } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { EmptyState } from "./admin-ui";
import { api, PUBLIC_WEB_URL, type PageResponse, type ResourceRecord } from "../lib/api";
import { resolveResourceListState } from "../lib/resource-list-state";

const emirates = ["Abu Dhabi", "Ajman", "Dubai", "Fujairah", "Ras Al Khaimah", "Sharjah", "Umm Al Quwain"];

export function DeveloperList() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [emirate, setEmirate] = useState("");
  const [featured, setFeatured] = useState("");
  const params = new URLSearchParams({ page_size: "100" });
  if (search) params.set("search", search);
  if (status) params.set("status", status);
  if (emirate) params.set("emirate", emirate);
  if (featured) params.set("featured", featured);
  const query = useQuery({ queryKey: ["developers", search, status, emirate, featured], queryFn: () => api<PageResponse<ResourceRecord>>(`/admin/developers?${params}`) });
  const countsQuery = useQuery({ queryKey: ["developer-counts"], queryFn: () => api<PageResponse<ResourceRecord>>("/admin/developers?page_size=100") });
  const counts = { published: 0, draft: 0, archived: 0 };
  countsQuery.data?.items.forEach((item) => { const key = item.status as keyof typeof counts; if (key in counts) counts[key] += 1; });
  const filtered = Boolean(search || status || emirate || featured);
  const listState = resolveResourceListState(countsQuery.data?.meta.total, query.data?.items.length, filtered);
  const hasRecords = listState === "populated" || listState === "filtered-empty";
  const initialEmpty = listState === "initial-empty";
  const filteredEmpty = listState === "filtered-empty";
  const resetFilters = () => { setSearch(""); setStatus(""); setEmirate(""); setFeatured(""); };
  const createAction = <Link className="primary-button" href="/developers/new"><Plus aria-hidden size={17}/>Add Developer</Link>;

  return <section className="developer-list-page">
    <header className="developer-list-header"><div><p className="eyebrow">Developer directory</p><h1>Developers</h1><p>Manage verified bilingual developer records and publication state.</p></div>{hasRecords ? createAction : null}</header>
    <div className="developer-counts" aria-label="Developer publication counts"><div><strong>{countsQuery.isLoading ? "—" : counts.published}</strong><span>Published</span></div><div><strong>{countsQuery.isLoading ? "—" : counts.draft}</strong><span>Draft</span></div><div><strong>{countsQuery.isLoading ? "—" : counts.archived}</strong><span>Archived</span></div></div>
    <div className="developer-toolbar">
      <label className="search-control"><span>Search</span><div><Search aria-hidden size={16}/><input onChange={(event) => setSearch(event.target.value)} placeholder="Name or slug" type="search" value={search}/></div></label>
      <label><span>Status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{["draft", "published", "archived"].map((item) => <option key={item}>{item}</option>)}</select></label>
      <label><span>Primary emirate</span><select onChange={(event) => setEmirate(event.target.value)} value={emirate}><option value="">All emirates</option>{emirates.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label><span>Featured</span><select onChange={(event) => setFeatured(event.target.value)} value={featured}><option value="">All records</option><option value="true">Featured</option><option value="false">Not featured</option></select></label>
    </div>
    {query.isLoading || countsQuery.isLoading ? <div className="panel-state">Loading developers…</div> : query.error ? <div className="panel-state form-error" role="alert">{query.error.message}</div> : countsQuery.error ? <div className="panel-state form-error" role="alert">{countsQuery.error.message}</div> : !query.data?.items.length ? <div className="table-wrap"><EmptyState action={initialEmpty ? createAction : filteredEmpty ? <button className="primary-button" onClick={resetFilters} type="button">Reset filters</button> : undefined} description={filteredEmpty ? "Adjust or reset the filters to see other records." : "Create a verified developer record when approved data is available."} filtered={filteredEmpty} title={filteredEmpty ? "No developers match these filters" : "No developers yet"}/></div> : <div className="table-wrap developer-table"><table><thead><tr><th>Developer</th><th>Primary emirate</th><th>Verified</th><th>Publication</th><th>Featured</th><th><span className="visually-hidden">Actions</span></th></tr></thead><tbody>{query.data.items.map((item) => {
      const translations = item.translations as Record<string, Record<string, unknown>>;
      const itemStatus = String(item.status);
      return <tr key={item.id}><td><strong>{String(translations.en?.name ?? item.slug)}</strong><code dir="ltr">{String(item.slug)}</code></td><td>{String(item.primary_emirate)}</td><td><time dateTime={String(item.verification_date)}>{String(item.verification_date)}</time></td><td><span className={`status-chip status-chip--${itemStatus}`}>{itemStatus}</span></td><td>{item.featured ? <span className="featured-indicator"><Star aria-hidden fill="currentColor" size={14}/>Featured</span> : <span className="muted-value">—</span>}</td><td><div className="row-actions"><Link className="table-link" href={`/developers/${item.id}`}>Edit</Link>{itemStatus === "published" ? <a className="table-link" href={`${PUBLIC_WEB_URL}/en/developers#${item.slug}`} rel="noreferrer" target="_blank">View website<ExternalLink aria-hidden size={14}/></a> : null}</div></td></tr>;
    })}</tbody></table></div>}
  </section>;
}
