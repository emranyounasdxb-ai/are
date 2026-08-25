"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, Download, Save } from "lucide-react";
import { useAuth } from "./auth-provider";
import { AdminPageHeader, InlineFeedback, LoadingState, StatusBadge } from "./admin-ui";
import { GuardedLink } from "./navigation-guard";
import { API_URL, api } from "../lib/api";

type RecordData = Record<string, unknown> & { id: string; reference_code: string; status: string; internal_note?: string; file?: { original_filename: string; verified_format: string; size_bytes: number } };

export function SubmissionDetail({ id, kind }: Readonly<{ id: string; kind: "enquiries" | "applications" }>) {
  const { user } = useAuth(); const [record, setRecord] = useState<RecordData>(); const [status, setStatus] = useState(""); const [note, setNote] = useState(""); const [message, setMessage] = useState("");
  useEffect(() => { api<RecordData>(`/admin/${kind}/${id}`).then((data) => { setRecord(data); setStatus(data.status); setNote(data.internal_note ?? ""); }); }, [id, kind]);
  if (!record) return <LoadingState label="Loading secure record…"/>;
  const fileName = record.file?.original_filename ?? "cv";
  const statuses = kind === "enquiries" ? ["new", "in-review", "contacted", "qualified", "closed", "spam"] : ["new", "reviewed", "shortlisted", "interview", "selected", "rejected"];
  async function save() { const updated = await api<RecordData>(`/admin/${kind}/${id}`, { method: "PUT", body: JSON.stringify({ status, internal_note: note || null }) }, user?.csrf_token); setRecord(updated); setMessage("Saved and recorded in the audit log."); }
  async function download() { const response = await fetch(`${API_URL}/admin/applications/${id}/cv`, { credentials: "include" }); if (!response.ok) { setMessage("CV download failed."); return; } const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = fileName; anchor.click(); URL.revokeObjectURL(url); }
  const privateKeys = new Set(["id", "internal_note", "file"]);
  const back = kind === "enquiries" ? "/enquiries" : "/careers/applications";
  return <section><AdminPageHeader back={<GuardedLink className="back-link" href={back}><ArrowLeft aria-hidden size={16}/>Back to inbox</GuardedLink>} description="Sensitive submission details are available only to authorized Admin users." eyebrow="Secure record" title={record.reference_code} action={<StatusBadge status={record.status}/>}/><div className="submission-detail-layout"><dl className="detail-grid">{Object.entries(record).filter(([key]) => !privateKeys.has(key)).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value ?? "—")}</dd></div>)}</dl><aside>{record.file ? <div className="panel"><h2>Private CV</h2><p>{record.file.original_filename} · {record.file.verified_format.toUpperCase()} · {(record.file.size_bytes / 1024).toFixed(1)} KB</p><button onClick={download} type="button"><Download aria-hidden size={16}/>Download CV</button></div> : null}<div className="panel"><h2>Review</h2><label>Status<select onChange={(event) => setStatus(event.target.value)} value={status}>{statuses.map((value) => <option key={value}>{value}</option>)}</select></label><label>Internal note<textarea onChange={(event) => setNote(event.target.value)} rows={6} value={note}/></label><button onClick={save} type="button"><Save aria-hidden size={16}/>Save review</button>{message ? <InlineFeedback tone={message.includes("failed") ? "error" : "success"}>{message}</InlineFeedback> : null}</div></aside></div></section>;
}
