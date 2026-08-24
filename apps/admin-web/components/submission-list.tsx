"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type PageResponse } from "../lib/api";

type Item = { id: string; reference_code: string; status: string; created_at: string; name?: string; applicant_name?: string; email: string };
type Job = { id: string; slug: string };

export function SubmissionList({ kind }: Readonly<{ kind: "enquiries" | "applications" }>) {
  const [items, setItems] = useState<Item[]>([]); const [jobs, setJobs] = useState<Job[]>([]); const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [dateFrom, setDateFrom] = useState(""); const [dateTo, setDateTo] = useState(""); const [context, setContext] = useState(""); const [error, setError] = useState("");
  useEffect(() => { if (kind === "applications") api<PageResponse<Job>>("/admin/jobs?page_size=100").then((data) => setJobs(data.items)); }, [kind]);
  useEffect(() => { const query = new URLSearchParams(); if (search) query.set("search", search); if (status) query.set("status", status); if (dateFrom) query.set("date_from", new Date(`${dateFrom}T00:00:00Z`).toISOString()); if (dateTo) query.set("date_to", new Date(`${dateTo}T23:59:59Z`).toISOString()); if (context) query.set(kind === "enquiries" ? "enquiry_type" : "job_opening_id", context); api<PageResponse<Item>>(`/admin/${kind}?${query}`).then((data) => { setItems(data.items); setError(""); }).catch((reason: Error) => setError(reason.message)); }, [context, dateFrom, dateTo, kind, search, status]);
  const statuses = kind === "enquiries" ? ["new", "in-review", "contacted", "qualified", "closed", "spam"] : ["new", "reviewed", "shortlisted", "interview", "selected", "rejected"];
  return <section><header className="page-heading"><div><p className="eyebrow">Inbox</p><h1>{kind === "enquiries" ? "Enquiries" : "Career applications"}</h1></div></header>
    <div className="toolbar"><label>Search<input onChange={(event) => setSearch(event.target.value)} type="search" value={search}/></label><label>Status<select onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All</option>{statuses.map((value) => <option key={value}>{value}</option>)}</select></label>{kind === "enquiries" ? <label>Enquiry type<input onChange={(event) => setContext(event.target.value)} value={context}/></label> : <label>Job<select onChange={(event) => setContext(event.target.value)} value={context}><option value="">All / general</option>{jobs.map((job) => <option key={job.id} value={job.id}>{job.slug}</option>)}</select></label>}<label>From<input onChange={(event) => setDateFrom(event.target.value)} type="date" value={dateFrom}/></label><label>To<input onChange={(event) => setDateTo(event.target.value)} type="date" value={dateTo}/></label></div>
    {error ? <p role="alert">{error}</p> : null}<div className="table-wrap"><table><thead><tr><th>Reference</th><th>Name</th><th>Email</th><th>Status</th><th>Received</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><Link href={kind === "enquiries" ? `/enquiries/${item.id}` : `/careers/applications/${item.id}`}>{item.reference_code}</Link></td><td>{item.name ?? item.applicant_name}</td><td>{item.email}</td><td>{item.status}</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>
  </section>;
}
