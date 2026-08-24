"use client";

import { useEffect, useState } from "react";
import { useAuth } from "./auth-provider";
import { API_URL, api } from "../lib/api";

type RecordData = Record<string, unknown> & { id: string; reference_code: string; status: string; internal_note?: string; file?: { original_filename: string; verified_format: string; size_bytes: number } };

export function SubmissionDetail({ id, kind }: Readonly<{ id: string; kind: "enquiries" | "applications" }>) {
  const { user } = useAuth(); const [record, setRecord] = useState<RecordData>(); const [status, setStatus] = useState(""); const [note, setNote] = useState(""); const [message, setMessage] = useState("");
  useEffect(() => { api<RecordData>(`/admin/${kind}/${id}`).then((data) => { setRecord(data); setStatus(data.status); setNote(data.internal_note ?? ""); }); }, [id, kind]);
  if (!record) return <p aria-live="polite">Loading secure record…</p>;
  const fileName = record.file?.original_filename ?? "cv";
  const statuses = kind === "enquiries" ? ["new", "in-review", "contacted", "qualified", "closed", "spam"] : ["new", "reviewed", "shortlisted", "interview", "selected", "rejected"];
  async function save() { const updated = await api<RecordData>(`/admin/${kind}/${id}`, { method: "PUT", body: JSON.stringify({ status, internal_note: note || null }) }, user?.csrf_token); setRecord(updated); setMessage("Saved and recorded in the audit log."); }
  async function download() { const response = await fetch(`${API_URL}/admin/applications/${id}/cv`, { credentials: "include" }); if (!response.ok) { setMessage("CV download failed."); return; } const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = fileName; anchor.click(); URL.revokeObjectURL(url); }
  const privateKeys = new Set(["id", "internal_note", "file"]);
  return <section><header className="page-heading"><div><p className="eyebrow">Secure record</p><h1>{record.reference_code}</h1></div></header><dl className="detail-grid">{Object.entries(record).filter(([key]) => !privateKeys.has(key)).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value ?? "—")}</dd></div>)}</dl>
    {record.file ? <div className="panel"><h2>Private CV</h2><p>{record.file.original_filename} · {record.file.verified_format.toUpperCase()} · {(record.file.size_bytes / 1024).toFixed(1)} KB</p><button onClick={download} type="button">Download CV</button></div> : null}
    <div className="panel"><h2>Review</h2><label>Status<select onChange={(event) => setStatus(event.target.value)} value={status}>{statuses.map((value) => <option key={value}>{value}</option>)}</select></label><label>Internal note<textarea onChange={(event) => setNote(event.target.value)} rows={6} value={note}/></label><button onClick={save} type="button">Save review</button><p aria-live="polite">{message}</p></div></section>;
}
