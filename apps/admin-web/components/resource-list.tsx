"use client";

import { useQuery } from "@tanstack/react-query";
import { flexRender, tableFeatures, useTable, type ColumnDef } from "@tanstack/react-table";
import { BriefcaseBusiness, Building2, FileText, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { AdminPageHeader, DataTableShell, EmptyState, FilterToolbar, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { api, type PageResponse, type ResourceRecord } from "../lib/api";

const features = tableFeatures({});
const config = {
  properties: { singular: "property", description: "Manage bilingual property records and publication state.", action: "Add Property", icon: Building2 },
  insights: { singular: "insight", description: "Create and publish trustworthy bilingual editorial content.", action: "Create Insight", icon: FileText },
  jobs: { singular: "job", description: "Manage bilingual career vacancies and their availability.", action: "Add Job", icon: BriefcaseBusiness },
} as const;

export function ResourceList({ resource, title, newHref }: Readonly<{ resource: "properties" | "insights" | "jobs"; title: string; newHref: string }>) {
  const [search, setSearch] = useState(""); const [status, setStatus] = useState("");
  const path = resource === "jobs" ? "/admin/jobs" : `/admin/${resource}`;
  const base = resource === "jobs" ? "/careers/jobs" : `/${resource}`;
  const query = useQuery({ queryKey: [resource, search, status], queryFn: () => api<PageResponse<ResourceRecord>>(`${path}?page_size=100&search=${encodeURIComponent(search)}${status ? `&status=${status}` : ""}`) });
  const allQuery = useQuery({ queryKey: [resource, "all-counts"], queryFn: () => api<PageResponse<ResourceRecord>>(`${path}?page_size=100`) });
  const columns = useMemo<ColumnDef<typeof features, ResourceRecord>[]>(() => [
    { accessorKey: "slug", header: "Record", cell: (info) => <strong title={String(info.getValue())}>{String(info.getValue())}</strong> },
    { accessorKey: "status", header: "Status", cell: (info) => <StatusBadge status={String(info.getValue())}/> },
    { accessorKey: "updated_at", header: "Updated", cell: (info) => info.getValue() ? <time dateTime={String(info.getValue())}>{new Date(String(info.getValue())).toLocaleString()}</time> : "—" },
    { id: "actions", header: "", cell: ({ row }) => <Link className="table-link" href={`${base}/${row.original.id}`}>Edit</Link> },
  ], [base]);
  const table = useTable({ features, columns, data: query.data?.items ?? [] });
  const statuses = resource === "jobs" ? ["draft", "open", "closed", "archived"] : ["draft", "published", "archived"];
  const itemConfig = config[resource]; const filtered = Boolean(search || status); const total = query.data?.meta.total ?? 0;
  const counts = statuses.map((value) => [value, allQuery.data?.items.filter((item) => item.status === value).length ?? 0] as const);
  return <section><AdminPageHeader action={<Link className="primary-button" href={newHref}><Plus aria-hidden size={16}/>{itemConfig.action}</Link>} description={itemConfig.description} eyebrow="Content operations" title={title}/>
    <div className="status-summary" aria-label={`${title} status summary`}>{counts.map(([label, count]) => <div key={label}><strong>{allQuery.isLoading ? "—" : count}</strong><span>{label}</span></div>)}</div>
    <FilterToolbar filtered={filtered} onReset={() => { setSearch(""); setStatus(""); }} resultLabel={`${total} ${total === 1 ? itemConfig.singular : resource}`}><label className="search-control"><span>Search</span><div><Search aria-hidden size={16}/><input onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${resource} by slug${resource === "properties" ? " or community" : ""}`} type="search" value={search}/></div></label><label><span>Status</span><select onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label></FilterToolbar>
    {query.isLoading ? <LoadingState label={`Loading ${resource}…`}/> : query.error ? <InlineFeedback tone="error">{query.error.message}</InlineFeedback> : !query.data?.items.length ? <DataTableShell label={`${title} results`}><EmptyState action={!filtered ? <Link className="primary-button" href={newHref}>{itemConfig.action}</Link> : undefined} description={filtered ? "Adjust or reset the filters to see other records." : `Create the first approved ${itemConfig.singular} when real content is available.`} filtered={filtered} title={filtered ? `No ${resource} match these filters` : `No ${resource} yet`}/></DataTableShell> : <DataTableShell label={`${title} results`}><table><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id}>{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id}>{row.getAllCells().map((cell) => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></DataTableShell>}
  </section>;
}
