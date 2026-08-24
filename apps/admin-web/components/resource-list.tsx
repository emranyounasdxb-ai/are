"use client";

import { useQuery } from "@tanstack/react-query";
import { flexRender, tableFeatures, useTable, type ColumnDef } from "@tanstack/react-table";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { api, type PageResponse, type ResourceRecord } from "../lib/api";

const features = tableFeatures({});

export function ResourceList({ resource, title, newHref }: Readonly<{ resource: "properties" | "insights" | "jobs"; title: string; newHref: string }>) {
  const [search, setSearch] = useState(""); const [status, setStatus] = useState("");
  const path = resource === "jobs" ? "/admin/jobs" : `/admin/${resource}`;
  const base = resource === "jobs" ? "/careers/jobs" : `/${resource}`;
  const query = useQuery({ queryKey: [resource, search, status], queryFn: () => api<PageResponse<ResourceRecord>>(`${path}?page_size=100&search=${encodeURIComponent(search)}${status ? `&status=${status}` : ""}`) });
  const columns = useMemo<ColumnDef<typeof features, ResourceRecord>[]>(() => [
    { accessorKey: "slug", header: "Slug", cell: (info) => <strong>{String(info.getValue())}</strong> },
    { accessorKey: "status", header: "Status", cell: (info) => <span className="status-chip">{String(info.getValue())}</span> },
    { accessorKey: "updated_at", header: "Updated", cell: (info) => info.getValue() ? new Date(String(info.getValue())).toLocaleString() : "—" },
    { id: "actions", header: "", cell: ({ row }) => <Link className="table-link" href={`${base}/${row.original.id}`}>Edit</Link> },
  ], [base]);
  const table = useTable({ features, columns, data: query.data?.items ?? [] });
  const statuses = resource === "jobs" ? ["draft", "open", "closed", "archived"] : ["draft", "published", "archived"];
  return <section><div className="page-heading"><div><p className="eyebrow">Content operations</p><h1>{title}</h1><p>{query.data?.meta.total ?? 0} real database records</p></div><Link className="primary-button" href={newHref}><Plus aria-hidden size={17}/>New record</Link></div>
    <div className="toolbar"><label>Search<input onChange={(event) => setSearch(event.target.value)} placeholder="Search records" value={search}/></label><label>Status<select onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label></div>
    {query.isLoading ? <div className="panel-state">Loading records…</div> : query.error ? <div className="panel-state form-error" role="alert">{query.error.message}</div> : !query.data?.items.length ? <div className="panel-state"><h2>No records yet</h2><p>Create an approved record when real content is available.</p></div> : <div className="table-wrap"><table><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id}>{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id}>{row.getAllCells().map((cell) => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></div>}
  </section>;
}
