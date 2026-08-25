"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, ArrowLeft, Check, ExternalLink, Plus, Save, Send, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { type FieldErrors, useForm, useWatch } from "react-hook-form";

import { api, PUBLIC_WEB_URL, type ResourceRecord } from "../lib/api";
import { ConfirmationDialog, StatusBadge } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink, useNavigationGuard } from "./navigation-guard";

const emirates = ["Abu Dhabi", "Ajman", "Dubai", "Fujairah", "Ras Al Khaimah", "Sharjah", "Umm Al Quwain"] as const;
const enquiryOptions = [["new-booking", "New booking"], ["primary-sale", "Primary sale"], ["resale", "Resale"]] as const;

type Values = {
  slug: string; primaryEmirate: string; otherPresence: string[]; selectedProjects: string[];
  officialWebsite: string; sourceUrl: string; additionalSourceUrls: string[]; verificationDate: string;
  enquiryTypes: string[]; featured: boolean; displayOrder: string; nameEn: string; nameAr: string;
  descriptionEn: string; descriptionAr: string; focusEn: string; focusAr: string; noteEn: string; noteAr: string;
};

const empty: Values = {
  slug: "", primaryEmirate: "Dubai", otherPresence: [], selectedProjects: [""], officialWebsite: "",
  sourceUrl: "", additionalSourceUrls: [""], verificationDate: "", enquiryTypes: enquiryOptions.map(([token]) => token),
  featured: false, displayOrder: "0", nameEn: "", nameAr: "", descriptionEn: "", descriptionAr: "",
  focusEn: "", focusAr: "", noteEn: "", noteAr: "",
};
const requiredMessage = "Required by the Developer data contract.";
const cleanList = (values: string[]) => values.map((item) => item.trim()).filter(Boolean);
const slugify = (value: string) => value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
const complete = (values: Array<string | undefined>) => values.every((value) => Boolean(value?.trim()));
const validWebUrl = (value: string) => !value || /^https?:\/\/[^\s]+$/i.test(value) || "Enter a complete http:// or https:// URL.";

function recordValues(data: ResourceRecord): Values {
  const translations = data.translations as Record<string, Record<string, unknown>>;
  const projects = (data.selected_projects as string[] | undefined) ?? [];
  const sources = (data.additional_source_urls as string[] | undefined) ?? [];
  return {
    slug: String(data.slug ?? ""), primaryEmirate: String(data.primary_emirate ?? "Dubai"),
    otherPresence: (data.other_presence as string[] | undefined) ?? [], selectedProjects: projects.length ? projects : [""],
    officialWebsite: String(data.official_website ?? ""), sourceUrl: String(data.source_url ?? ""),
    additionalSourceUrls: sources.length ? sources : [""], verificationDate: String(data.verification_date ?? ""),
    enquiryTypes: (data.enquiry_types as string[] | undefined) ?? [], featured: Boolean(data.featured),
    displayOrder: String(data.display_order ?? 0), nameEn: String(translations.en?.name ?? ""),
    nameAr: String(translations.ar?.name ?? ""), descriptionEn: String(translations.en?.description ?? ""),
    descriptionAr: String(translations.ar?.description ?? ""), focusEn: String(translations.en?.focus ?? ""),
    focusAr: String(translations.ar?.focus ?? ""), noteEn: String(translations.en?.verification_note ?? ""),
    noteAr: String(translations.ar?.verification_note ?? ""),
  };
}

function FieldError({ message }: Readonly<{ message?: string }>) {
  return message ? <small className="field-error">{message}</small> : null;
}

export function DeveloperEditor({ id }: Readonly<{ id?: string }>) {
  const { user } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setBlocked } = useNavigationGuard();
  const [notice, setNotice] = useState("");
  const [activeLocale, setActiveLocale] = useState<"en" | "ar">("en");
  const [slugEdited, setSlugEdited] = useState(Boolean(id));
  const [pendingAction, setPendingAction] = useState<"draft" | "published" | "archived" | null>(null);
  const [confirmArchive, setConfirmArchive] = useState(false);
  const errorSummaryRef = useRef<HTMLDivElement>(null);
  const record = useQuery({ queryKey: ["developer", id], queryFn: () => api<ResourceRecord>(`/admin/developers/${id}`), enabled: Boolean(id) });
  const { register, handleSubmit, reset, setError, clearErrors, setFocus, setValue, control, formState: { errors, isDirty } } = useForm<Values>({ defaultValues: empty });
  const values = useWatch({ control });
  const status = String(record.data?.status ?? "draft");
  const busy = pendingAction !== null;
  const englishComplete = complete([values.nameEn, values.descriptionEn, values.focusEn, values.noteEn]);
  const arabicComplete = complete([values.nameAr, values.descriptionAr, values.focusAr, values.noteAr]);

  useEffect(() => { if (record.data) reset(recordValues(record.data)); }, [record.data, reset]);
  useEffect(() => { setBlocked(isDirty); return () => setBlocked(false); }, [isDirty, setBlocked]);
  useEffect(() => {
    if (!isDirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [isDirty]);
  useEffect(() => {
    if (id || slugEdited) return;
    setValue("slug", slugify(values.nameEn ?? ""), { shouldDirty: Boolean(values.nameEn) });
  }, [id, setValue, slugEdited, values.nameEn]);

  async function save(formValues: Values, nextStatus: "draft" | "published" | "archived") {
    setNotice(""); clearErrors("root"); setPendingAction(nextStatus);
    const payload = {
      slug: formValues.slug, primary_emirate: formValues.primaryEmirate,
      other_presence: formValues.otherPresence.filter((item) => item !== formValues.primaryEmirate),
      selected_projects: cleanList(formValues.selectedProjects), official_website: formValues.officialWebsite,
      source_url: formValues.sourceUrl, additional_source_urls: cleanList(formValues.additionalSourceUrls),
      verification_date: formValues.verificationDate, enquiry_types: formValues.enquiryTypes,
      featured: formValues.featured, display_order: Number(formValues.displayOrder), status: nextStatus,
      translations: {
        en: { name: formValues.nameEn, description: formValues.descriptionEn, focus: formValues.focusEn, verification_note: formValues.noteEn },
        ar: { name: formValues.nameAr, description: formValues.descriptionAr, focus: formValues.focusAr, verification_note: formValues.noteAr },
      },
    };
    try {
      const saved = await api<ResourceRecord>(id ? `/admin/developers/${id}` : "/admin/developers", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) }, user?.csrf_token);
      await Promise.all([queryClient.invalidateQueries({ queryKey: ["developers"] }), queryClient.invalidateQueries({ queryKey: ["developer-counts"] })]);
      if (id) queryClient.setQueryData(["developer", id], saved);
      reset(recordValues(saved));
      setBlocked(false);
      setNotice(nextStatus === "published" ? "Developer published successfully." : nextStatus === "archived" ? "Developer archived." : "Draft saved successfully.");
      if (!id) router.replace(`/developers/${saved.id}`);
    } catch (reason) {
      setError("root", { message: reason instanceof Error ? reason.message : "The developer could not be saved." });
      requestAnimationFrame(() => errorSummaryRef.current?.focus());
    } finally { setPendingAction(null); }
  }

  function invalid(invalidFields: FieldErrors<Values>) {
    const names = Object.keys(invalidFields) as Array<keyof Values>;
    const firstArabic = names.find((name) => String(name).endsWith("Ar"));
    if (firstArabic) setActiveLocale("ar");
    requestAnimationFrame(() => { errorSummaryRef.current?.focus(); if (firstArabic ?? names[0]) setFocus(firstArabic ?? names[0]); });
  }
  const submit = (nextStatus: "draft" | "published" | "archived") => handleSubmit((formValues) => save(formValues, nextStatus), invalid);
  const addItem = (field: "selectedProjects" | "additionalSourceUrls") => setValue(field, [...(values[field] ?? []), ""], { shouldDirty: true });
  const removeItem = (field: "selectedProjects" | "additionalSourceUrls", index: number) => {
    const next = (values[field] ?? []).filter((_, itemIndex) => itemIndex !== index);
    setValue(field, next.length ? next : [""], { shouldDirty: true, shouldValidate: true });
  };

  if (id && record.isLoading) return <div className="panel-state">Loading developer…</div>;
  if (record.error) return <div className="panel-state form-error" role="alert">{record.error.message}</div>;

  const errorEntries = Object.entries(errors).filter(([name]) => name !== "root") as Array<[keyof Values, { message?: string }]>;
  return <section className="developer-editor-page">
    <header className="developer-editor-header">
      <div><GuardedLink className="back-link" href="/developers"><ArrowLeft aria-hidden size={16}/>Back to Developers</GuardedLink><div className="developer-title-row"><h1>{id ? "Edit Developer" : "New Developer"}</h1><span className={`status-chip status-chip--${status}`}>{status}</span></div><p>Drafts remain private. Complete both languages and provenance before publishing.</p></div>
      {status === "published" ? <a className="secondary-button" href={`${PUBLIC_WEB_URL}/en/developers#${record.data?.slug}`} rel="noreferrer" target="_blank">View on website<ExternalLink aria-hidden size={16}/></a> : null}
    </header>

    <form className="editor-form developer-editor-form" noValidate onSubmit={(event) => void submit("draft")(event)}><div className="editor-workspace"><nav className="editor-step-rail" aria-label="Developer form sections"><a href="#developer-identity"><span>1</span>Identity</a><a href="#developer-content"><span>2</span>Content</a><a href="#developer-provenance"><span>3</span>Provenance</a><a href="#developer-review"><span>4</span>Review</a></nav><div className="editor-main">
      {(errors.root?.message || errorEntries.length) ? <div className="error-summary" ref={errorSummaryRef} role="alert" tabIndex={-1}><strong>Review the form before continuing.</strong>{errors.root?.message ? <p>{errors.root.message}</p> : null}{errorEntries.length ? <ul>{errorEntries.map(([name, error]) => <li key={name}><button onClick={() => { if (String(name).endsWith("Ar")) setActiveLocale("ar"); else if (String(name).endsWith("En")) setActiveLocale("en"); requestAnimationFrame(() => setFocus(name)); }} type="button">{error.message ?? `${name} is invalid.`}</button></li>)}</ul> : null}</div> : null}
      {notice ? <div className="form-success" role="status"><Check aria-hidden size={18}/>{notice}</div> : null}

      <fieldset className="form-section" id="developer-identity"><legend>1. Identity and publication</legend><p className="section-guidance">Identity fields are required by the current data contract. Optional relationship fields may remain empty in a Draft.</p><div className="form-grid">
        <label>English official name<span className="field-hint">Used to suggest the initial stable slug.</span><input autoComplete="organization" {...register("nameEn", { required: requiredMessage, minLength: { value: 2, message: "English official name must be at least 2 characters." } })}/><FieldError message={errors.nameEn?.message}/></label>
        <label>Stable slug<span className="field-hint">Lowercase letters, numbers and hyphens only.</span><input dir="ltr" {...register("slug", { required: requiredMessage, pattern: { value: /^[a-z0-9]+(?:-[a-z0-9]+)*$/, message: "Use a lowercase hyphenated slug." }, onChange: () => setSlugEdited(true) })}/><FieldError message={errors.slug?.message}/></label>
        <div className="path-preview wide"><span>Public path preview</span><code dir="ltr">/en/developers#{values.slug || "developer-slug"}</code></div>
        <label>Primary emirate<select {...register("primaryEmirate", { required: requiredMessage })}>{emirates.map((emirate) => <option key={emirate}>{emirate}</option>)}</select></label>
        <div className="field-group"><span className="field-label">Other market presence <em>Optional</em></span><span className="field-hint">The primary emirate is excluded automatically.</span><div className="check-grid">{emirates.filter((emirate) => emirate !== values.primaryEmirate).map((emirate) => <label className="check" key={emirate}><input checked={(values.otherPresence ?? []).includes(emirate)} onChange={(event) => setValue("otherPresence", event.target.checked ? [...(values.otherPresence ?? []), emirate] : (values.otherPresence ?? []).filter((item) => item !== emirate), { shouldDirty: true })} type="checkbox"/>{emirate}</label>)}</div></div>
        <Repeater errors={errors} field="selectedProjects" label="Notable projects" values={values.selectedProjects ?? [""]} register={register} onAdd={() => addItem("selectedProjects")} onRemove={(index) => removeItem("selectedProjects", index)} />
        <label className="check help-check"><input type="checkbox" {...register("featured")}/><span><strong>Featured</strong><small>Highlights this record in approved curated views; it does not publish it.</small></span></label>
        <label>Display order<span className="field-hint">Lower numbers appear first. Preserve the approved sequence for existing records.</span><input dir="ltr" min="0" max="10000" type="number" {...register("displayOrder", { required: requiredMessage, min: { value: 0, message: "Display order cannot be negative." } })}/><FieldError message={errors.displayOrder?.message}/></label>
      </div></fieldset>

      <fieldset className="form-section bilingual-section" id="developer-content"><legend>2. Bilingual content</legend><p className="section-guidance">Both language panels must be complete before publication. Drafts remain private while editorial review continues.</p>
        <div className="locale-tabs" role="tablist" aria-label="Developer content language"><button aria-controls="developer-panel-en" aria-selected={activeLocale === "en"} id="developer-tab-en" onClick={() => setActiveLocale("en")} role="tab" type="button">English <span className={`completion${englishComplete ? " complete" : ""}`}>{englishComplete ? "Complete" : "Incomplete"}</span></button><button aria-controls="developer-panel-ar" aria-selected={activeLocale === "ar"} id="developer-tab-ar" onClick={() => setActiveLocale("ar")} role="tab" type="button">العربية <span className={`completion${arabicComplete ? " complete" : ""}`}>{arabicComplete ? "مكتمل" : "غير مكتمل"}</span></button></div>
        <div aria-labelledby={`developer-tab-${activeLocale}`} className={`locale-panel locale-panel--${activeLocale}`} dir={activeLocale === "ar" ? "rtl" : "ltr"} id={`developer-panel-${activeLocale}`} role="tabpanel">{activeLocale === "en" ? <EnglishFields register={register} errors={errors}/> : <ArabicFields register={register} errors={errors}/>}</div>
      </fieldset>

      <fieldset className="form-section" id="developer-provenance"><legend>3. Provenance and verification</legend><p className="section-guidance">Official provenance and a verification date are required before publication. URLs and technical values remain left-to-right.</p><div className="form-grid">
        <label>Official website<input dir="ltr" inputMode="url" type="url" {...register("officialWebsite", { required: requiredMessage, validate: validWebUrl })}/><FieldError message={errors.officialWebsite?.message}/></label>
        <label>Primary source URL<input dir="ltr" inputMode="url" type="url" {...register("sourceUrl", { required: requiredMessage, validate: validWebUrl })}/><FieldError message={errors.sourceUrl?.message}/></label>
        <label>Verification date<input dir="ltr" type="date" {...register("verificationDate", { required: requiredMessage })}/><FieldError message={errors.verificationDate?.message}/></label>
        <div className="field-group"><span className="field-label">Enquiry types</span><div className="check-grid">{enquiryOptions.map(([token, label]) => <label className="check" key={token}><input type="checkbox" value={token} {...register("enquiryTypes")}/>{label}</label>)}</div></div>
        <Repeater errors={errors} field="additionalSourceUrls" label="Additional official source URLs" values={values.additionalSourceUrls ?? [""]} register={register} onAdd={() => addItem("additionalSourceUrls")} onRemove={(index) => removeItem("additionalSourceUrls", index)} urls />
      </div></fieldset>

      <div className="sticky-actions" id="developer-review"><div><strong>{isDirty ? "Unsaved changes" : id ? "No unsaved changes" : "Not saved yet"}</strong><span>{status === "published" ? "Publishing updates the live directory." : "Save privately or publish when complete."}</span></div><div className="developer-actions"><button className="action-button" disabled={busy} type="submit"><Save aria-hidden size={17}/>{pendingAction === "draft" ? "Saving…" : "Save Draft"}</button><button className="action-button action-button--publish" disabled={busy} onClick={() => void submit("published")()} type="button"><Send aria-hidden size={17}/>{pendingAction === "published" ? "Publishing…" : "Publish"}</button>{id && status !== "archived" ? <button className="action-button action-button--archive" disabled={busy} onClick={() => setConfirmArchive(true)} type="button"><Archive aria-hidden size={17}/>{pendingAction === "archived" ? "Archiving…" : "Archive"}</button> : null}</div></div></div><aside className="editor-context"><p className="eyebrow">Record summary</p><dl><div><dt>Status</dt><dd><StatusBadge status={status}/></dd></div><div><dt>English</dt><dd>{englishComplete ? "Complete" : "Incomplete"}</dd></div><div><dt>Arabic</dt><dd>{arabicComplete ? "Complete" : "Incomplete"}</dd></div><div><dt>Provenance</dt><dd>{complete([values.officialWebsite, values.sourceUrl, values.verificationDate]) ? "Complete" : "Incomplete"}</dd></div><div><dt>Slug</dt><dd><code dir="ltr">{values.slug || "Not set"}</code></dd></div><div><dt>Featured</dt><dd>{values.featured ? "Yes" : "No"}</dd></div></dl></aside></div></form><ConfirmationDialog confirmLabel="Archive developer" description="The developer will no longer appear on the public website." onCancel={() => setConfirmArchive(false)} onConfirm={() => { setConfirmArchive(false); void submit("archived")(); }} open={confirmArchive} title="Archive this developer?"/>
  </section>;
}

type FormProps = { register: ReturnType<typeof useForm<Values>>["register"]; errors: FieldErrors<Values> };
function EnglishFields({ register, errors }: Readonly<FormProps>) {
  return <div className="form-grid"><p className="wide locale-note">The English official name is managed in Identity and publication so it can safely generate the initial slug.</p><label>Development focus<input dir="ltr" {...register("focusEn", { required: requiredMessage, minLength: { value: 2, message: "English development focus is required." } })}/><FieldError message={errors.focusEn?.message}/></label><label className="wide">Description<textarea dir="ltr" rows={5} {...register("descriptionEn", { required: requiredMessage, minLength: { value: 10, message: "English description must be at least 10 characters." } })}/><FieldError message={errors.descriptionEn?.message}/></label><label className="wide">Verification note<textarea dir="ltr" rows={3} {...register("noteEn", { required: requiredMessage, minLength: { value: 10, message: "English verification note must be at least 10 characters." } })}/><FieldError message={errors.noteEn?.message}/></label></div>;
}
function ArabicFields({ register, errors }: Readonly<FormProps>) {
  return <div className="form-grid"><label>الاسم الرسمي<input dir="rtl" {...register("nameAr", { required: "الاسم العربي مطلوب للنشر.", minLength: { value: 2, message: "يجب أن يتكون الاسم العربي من حرفين على الأقل." } })}/><FieldError message={errors.nameAr?.message}/></label><label>مجال التطوير<input dir="rtl" {...register("focusAr", { required: "مجال التطوير باللغة العربية مطلوب للنشر.", minLength: { value: 2, message: "مجال التطوير باللغة العربية مطلوب." } })}/><FieldError message={errors.focusAr?.message}/></label><label className="wide">الوصف<textarea dir="rtl" rows={5} {...register("descriptionAr", { required: "الوصف العربي مطلوب للنشر.", minLength: { value: 10, message: "يجب أن يتكون الوصف العربي من 10 أحرف على الأقل." } })}/><FieldError message={errors.descriptionAr?.message}/></label><label className="wide">ملاحظة التحقق<textarea dir="rtl" rows={3} {...register("noteAr", { required: "ملاحظة التحقق باللغة العربية مطلوبة للنشر.", minLength: { value: 10, message: "يجب أن تتكون ملاحظة التحقق من 10 أحرف على الأقل." } })}/><FieldError message={errors.noteAr?.message}/></label></div>;
}
type RepeaterProps = { field: "selectedProjects" | "additionalSourceUrls"; label: string; values: string[]; register: ReturnType<typeof useForm<Values>>["register"]; errors: FieldErrors<Values>; onAdd: () => void; onRemove: (index: number) => void; urls?: boolean };
function Repeater({ field, label, values, register, errors, onAdd, onRemove, urls }: Readonly<RepeaterProps>) {
  const rowErrors = errors[field] as Array<{ message?: string } | undefined> | undefined;
  return <div className="wide field-group"><span className="field-label">{label} <em>Optional</em></span>{field === "selectedProjects" ? <span className="field-hint">Identity references only; this does not assert inventory or availability.</span> : null}<div className="repeater">{values.map((_, index) => <div key={`${field}-${index}`}><div className="repeater-row"><input aria-invalid={Boolean(rowErrors?.[index])} aria-label={`${label} ${index + 1}`} dir={urls ? "ltr" : undefined} inputMode={urls ? "url" : undefined} type={urls ? "url" : "text"} {...register(`${field}.${index}`, urls ? { validate: validWebUrl } : undefined)}/><button aria-label={`Remove ${label.toLowerCase()} ${index + 1}`} onClick={() => onRemove(index)} type="button"><Trash2 aria-hidden size={16}/></button></div><FieldError message={rowErrors?.[index]?.message}/></div>)}<button className="add-row-button" onClick={onAdd} type="button"><Plus aria-hidden size={16}/>Add {field === "selectedProjects" ? "project" : "source URL"}</button></div></div>;
}
