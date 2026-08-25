"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Search } from "lucide-react";
import { AdminPageHeader, DataTableShell, EmptyState, FilterToolbar, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { api, type PageResponse } from "../lib/api";

type Item = { id: string; reference_code: string; status: string; created_at: string; name?: string; applicant_name?: string; email: string };
type Job = { id: string; slug: string };

export function SubmissionList({ kind }: Readonly<{ kind: "enquiries" | "applications" }>) {
  const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [dateFrom, setDateFrom] = useState(""); const [dateTo, setDateTo] = useState(""); const [context, setContext] = useState("");
  const params = new URLSearchParams(); if (search) params.set("search", search); if (status) params.set("status", status); if (dateFrom) params.set("date_from", new Date(`${dateFrom}T00:00:00Z`).toISOString()); if (dateTo) params.set("date_to", new Date(`${dateTo}T23:59:59Z`).toISOString()); if (context) params.set(kind === "enquiries" ? "enquiry_type" : "job_opening_id", context);
  const query = useQuery({ queryKey: [kind, search, status, dateFrom, dateTo, context], queryFn: () => api<PageResponse<Item>>(`/admin/${kind}?${params}`) });
  const jobsQuery = useQuery({ queryKey: ["jobs", "submission-filter"], queryFn: () => api<PageResponse<Job>>("/admin/jobs?page_size=100"), enabled: kind === "applications" });
  const items = query.data?.items ?? []; const jobs = jobsQuery.data?.items ?? [];
  const statuses = kind === "enquiries" ? ["new", "in-review", "contacted", "qualified", "closed", "spam"] : ["new", "reviewed", "shortlisted", "interview", "selected", "rejected"];
  const title = kind === "enquiries" ? "Enquiries" : "Career Applications"; const filtered = Boolean(search || status || dateFrom || dateTo || context);
  const reset = () => { setSearch(""); setStatus(""); setDateFrom(""); setDateTo(""); setContext(""); };
  return <section><AdminPageHeader description={kind === "enquiries" ? "Review and progress customer enquiries securely." : "Review submitted applications and private CVs securely."} eyebrow="Inbox" title={title}/>
    <FilterToolbar filtered={filtered} onReset={reset} resultLabel={`${items.length} ${items.length === 1 ? "result" : "results"}`}><label className="search-control"><span>Search</span><div><Search aria-hidden size={16}/><input onChange={(event) => setSearch(event.target.value)} placeholder={kind === "enquiries" ? "Reference, name or email" : "Reference, applicant or email"} type="search" value={search}/></div></label><label><span>Status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{statuses.map((value) => <option key={value}>{value}</option>)}</select></label>{kind === "enquiries" ? <label><span>Enquiry type</span><input onChange={(event) => setContext(event.target.value)} placeholder="All types" value={context}/></label> : <label><span>Job</span><select onChange={(event) => setContext(event.target.value)} value={context}><option value="">All / general</option>{jobs.map((job) => <option key={job.id} value={job.id}>{job.slug}</option>)}</select></label>}<label><span>From</span><input onChange={(event) => setDateFrom(event.target.value)} type="date" value={dateFrom}/></label><label><span>To</span><input onChange={(event) => setDateTo(event.target.value)} type="date" value={dateTo}/></label></FilterToolbar>
    {query.isLoading ? <LoadingState label={`Loading ${title.toLowerCase()}…`}/> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : !items.length ? <DataTableShell label={`${title} results`}><EmptyState description={filtered ? "Adjust or reset the filters to see other submissions." : "New secure submissions will appear here."} filtered={filtered} title={filtered ? "No submissions match these filters" : `No ${title.toLowerCase()} yet`}/></DataTableShell> : <DataTableShell label={`${title} results`}><table><thead><tr><th>Reference</th><th>Name</th><th>Email</th><th>Status</th><th>Received</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><Link className="table-link" href={kind === "enquiries" ? `/enquiries/${item.id}` : `/careers/applications/${item.id}`}>{item.reference_code}</Link></td><td>{item.name ?? item.applicant_name}</td><td>{item.email}</td><td><StatusBadge status={item.status}/></td><td><time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></td></tr>)}</tbody></table></DataTableShell>}
  </section>;
}
