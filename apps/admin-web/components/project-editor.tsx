"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, ArrowLeft, Eye, Plus, Save, Send, Trash2, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { api, type PageResponse, type ResourceRecord } from "../lib/api";
import { AdminPageHeader, ErrorSummary, FormSection, InlineFeedback, LanguageTabs, LoadingState, StatusBadge, StickyFormActions } from "./admin-ui";
import { useAuth } from "./auth-provider";
import { GuardedLink } from "./navigation-guard";
import { ProjectApprovalReview } from "./project-approval-review";
type Translation = {
    official_name: string;
    short_summary: string;
    full_description: string;
    seo_title: string;
    seo_description: string;
};
type Source = {
    id?: string;
    source_url: string;
    source_type: string;
    is_official: boolean;
    retrieved_at: string;
    last_checked_at: string;
    content_hash: string;
    source_title: string;
    source_developer_domain: string;
    is_active: boolean;
};
type Media = {
    id?: string;
    category: string;
    source_url: string;
    rights_status: string;
    alt_en: string;
    alt_ar: string;
    display_order: number;
    verified_at: string;
    has_upload?: boolean;
    association_status?: string | null;
};
type Milestone = {
    sequence: number;
    stage: string;
    label_en: string;
    label_ar: string;
    percentage: string;
    due_trigger: string;
    source_value: string;
};
type BilingualItem = {
    label_en: string;
    label_ar: string;
    display_order: number;
};
type NearbyPlace = {
    name_en: string;
    name_ar: string;
    distance_value: string;
    distance_unit: string;
    travel_time_minutes: string;
    display_order: number;
};
type Values = {
    slug: string;
    emirate: string;
    developer_id: string;
    area_id: string;
    status: string;
    workflow_status: string;
    availability_status: string;
    construction_status: string;
    handover_quarter: string;
    handover_year: string;
    original_handover_value: string;
    size_min: string;
    size_max: string;
    size_unit: string;
    down_payment_percentage: string;
    down_payment_source_value: string;
    latitude: string;
    longitude: string;
    last_verified_at: string;
    priority: string;
    featured: boolean;
    display_order: number;
    internal_notes: string;
    property_types: string[];
    bedroom_options: string[];
    unit_types: BilingualItem[];
    amenities: BilingualItem[];
    nearby_places: NearbyPlace[];
    translations: {
        en: Translation;
        ar: Translation;
    };
    sources: Source[];
    payment_raw: string;
    payment_source_index: number;
    payment_complete: boolean;
    payment_verified_at: string;
    milestones: Milestone[];
    media: Media[];
};
type OptionRecord = ResourceRecord & {
    translations?: Record<string, {
        name?: string;
    }>;
    name_en?: string;
    emirate?: string;
};
type ProjectRecord = ResourceRecord & Partial<Values> & {
    translations?: Record<string, Translation>;
    sources?: Source[];
    media?: Media[];
    payment_plan?: {
        raw_source_text?: string;
        source_id?: string;
        is_complete?: boolean;
        verified_at?: string;
        milestones?: Milestone[];
    } | null;
};
type RevisionRecord = { id: string; revision_number: number; status: string; change_summary: string; field_diff: Record<string, unknown>; created_at: string };
const emptyTranslation = (): Translation => ({ official_name: "", short_summary: "", full_description: "", seo_title: "", seo_description: "" });
const emptySource = (): Source => ({ source_url: "", source_type: "OWNER_MANIFEST", is_official: false, retrieved_at: "", last_checked_at: "", content_hash: "", source_title: "", source_developer_domain: "", is_active: true });
const emptyMedia = (): Media => ({ category: "cover", source_url: "", rights_status: "pending", alt_en: "", alt_ar: "", display_order: 0, verified_at: "" });
const initialValues = (): Values => ({ slug: "", emirate: "", developer_id: "", area_id: "", status: "draft", workflow_status: "draft", availability_status: "", construction_status: "not-confirmed", handover_quarter: "", handover_year: "", original_handover_value: "", size_min: "", size_max: "", size_unit: "", down_payment_percentage: "", down_payment_source_value: "", latitude: "", longitude: "", last_verified_at: "", priority: "", featured: false, display_order: 0, internal_notes: "", property_types: [], bedroom_options: [], unit_types: [], amenities: [], nearby_places: [], translations: { en: emptyTranslation(), ar: emptyTranslation() }, sources: [], payment_raw: "", payment_source_index: 0, payment_complete: false, payment_verified_at: "", milestones: [], media: [] });
export function ProjectEditor({ id }: Readonly<{
    id?: string;
}>) {
    const { user } = useAuth();
    const router = useRouter();
    const queryClient = useQueryClient();
    const errorRef = useRef<HTMLDivElement>(null);
    const [locale, setLocale] = useState<"en" | "ar">("en");
    const [values, setValues] = useState(initialValues);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const record = useQuery({ queryKey: ["project", id], queryFn: async () => { const data = await api<ProjectRecord>(`/admin/projects/${id}`); setValues(recordValues(data)); return data; }, enabled: Boolean(id) });
    const developers = useQuery({ queryKey: ["project-developers"], queryFn: () => api<PageResponse<OptionRecord>>("/admin/developers?page_size=100") });
    const areas = useQuery({ queryKey: ["project-areas"], queryFn: () => api<PageResponse<OptionRecord>>("/admin/areas") });
    const set = <K extends keyof Values>(key: K, value: Values[K]) => setValues((current) => ({ ...current, [key]: value }));
    const setTranslation = (key: keyof Translation, value: string) => setValues((current) => ({ ...current, translations: { ...current.translations, [locale]: { ...current.translations[locale], [key]: value } } }));
    const payload = (status: string) => ({ slug: values.slug, emirate: values.emirate, developer_id: values.developer_id, area_id: values.area_id, status, workflow_status: values.workflow_status, availability_status: values.availability_status || null, construction_status: values.construction_status, handover_quarter: values.handover_quarter || null, handover_year: numberOrNull(values.handover_year), original_handover_value: values.original_handover_value || null, size_min: numberOrNull(values.size_min), size_max: numberOrNull(values.size_max), size_unit: values.size_unit || null, down_payment_percentage: numberOrNull(values.down_payment_percentage), down_payment_source_value: values.down_payment_source_value || null, latitude: numberOrNull(values.latitude), longitude: numberOrNull(values.longitude), last_verified_at: iso(values.last_verified_at), priority: values.priority || null, featured: values.featured, display_order: Number(values.display_order), internal_notes: values.internal_notes || null, property_types: values.property_types, bedroom_options: values.bedroom_options, unit_types: values.unit_types.map((item) => ({ ...item, label_ar: item.label_ar || null })), amenities: values.amenities.map((item) => ({ ...item, label_ar: item.label_ar || null })), nearby_places: values.nearby_places.map((item) => ({ ...item, name_ar: item.name_ar || null, distance_value: numberOrNull(item.distance_value), distance_unit: item.distance_unit || null, travel_time_minutes: numberOrNull(item.travel_time_minutes) })), translations: Object.fromEntries(Object.entries(values.translations).filter(([, item]) => item.official_name && item.short_summary && item.full_description && item.seo_title && item.seo_description)), sources: values.sources.filter((source) => source.source_url).map((source) => ({ source_url: source.source_url, source_type: source.source_type, is_official: source.is_official, retrieved_at: iso(source.retrieved_at), last_checked_at: iso(source.last_checked_at), content_hash: source.content_hash, source_title: source.source_title || null, source_developer_domain: source.source_developer_domain || null, is_active: source.is_active })), payment_plan: values.payment_raw ? { raw_source_text: values.payment_raw, source_index: values.payment_source_index, is_complete: values.payment_complete, verified_at: iso(values.payment_verified_at), milestones: values.milestones.map((item) => ({ ...item, percentage: item.percentage === "" ? null : Number(item.percentage), label_ar: item.label_ar || null, due_trigger: item.due_trigger || null })) } : null, media: values.media.filter((item) => item.source_url).map((item) => ({ id: item.id, category: item.category, source_url: item.source_url, rights_status: item.rights_status, alt_en: item.alt_en || null, alt_ar: item.alt_ar || null, display_order: item.display_order, verified_at: iso(item.verified_at) })) });
    async function save(status: string) { setBusy(true); setError(""); setNotice(""); try {
        if (id && values.status === "published" && status !== "archived") {
            const revision = await api<RevisionRecord>(`/admin/projects/${id}/revisions`, { method: "POST", body: JSON.stringify({ project: payload("published"), media_snapshot: values.media.map((item) => ({ id: item.id, category: item.category, rights_status: item.rights_status, alt_en: item.alt_en, alt_ar: item.alt_ar, display_order: item.display_order })), field_diff: { human_edits_preserved: true }, change_summary: "Admin editor draft changes" }) }, user?.csrf_token);
            setNotice(`Draft Revision ${revision.revision_number} created. The live version is unchanged.`);
            await queryClient.invalidateQueries({ queryKey: ["project-revisions", id] });
            return;
        }
        const saved = await api<ProjectRecord>(id ? `/admin/projects/${id}` : "/admin/projects", { method: id ? "PUT" : "POST", body: JSON.stringify(payload(status)) }, user?.csrf_token);
        queryClient.setQueryData(["project", saved.id], saved);
        setValues(recordValues(saved));
        await queryClient.invalidateQueries({ queryKey: ["project-approval", saved.id] });
        setNotice(status === "published" ? "Project published." : status === "archived" ? "Project archived." : "Draft saved.");
        if (!id)
            router.replace(`/projects/${saved.id}`);
    }
    catch (caught) {
        setError(caught instanceof Error ? caught.message : "The Project could not be saved.");
        requestAnimationFrame(() => errorRef.current?.focus());
    }
    finally {
        setBusy(false);
    } }
    async function upload(mediaId: string, file?: File) { if (!file || !id)
        return; setBusy(true); try {
        const body = new FormData();
        body.append("image", file);
        const saved = await api<ProjectRecord>(`/admin/projects/${id}/media/${mediaId}`, { method: "POST", body }, user?.csrf_token);
        queryClient.setQueryData(["project", id], saved);
        setValues(recordValues(saved));
        await queryClient.invalidateQueries({ queryKey: ["project-approval", id] });
        setNotice("Project media uploaded and sanitized.");
    }
    catch (caught) {
        setError(caught instanceof Error ? caught.message : "Upload failed.");
    }
    finally {
        setBusy(false);
    } }
    async function supersedePrivateMedia(mediaId: string) { if (!id)
        return; setBusy(true); setError(""); try {
        const saved = await api<ProjectRecord>(`/admin/projects/${id}/media/${mediaId}/supersede-private`, { method: "POST" }, user?.csrf_token);
        queryClient.setQueryData(["project", id], saved);
        setValues(recordValues(saved));
        await queryClient.invalidateQueries({ queryKey: ["project-approval", id] });
        setNotice("Superseded fallback archived privately. The original file was preserved.");
    }
    catch (caught) {
        setError(caught instanceof Error ? caught.message : "The media association could not be archived.");
        requestAnimationFrame(() => errorRef.current?.focus());
    }
    finally {
        setBusy(false);
    } }
    async function transition(action: "submit-review", message: string) { if (!id)
        return; setBusy(true); setError(""); try {
        const saved = await api<ProjectRecord>(`/admin/projects/${id}/${action}`, { method: "POST" }, user?.csrf_token);
        setValues(recordValues(saved));
        queryClient.setQueryData(["project", id], saved);
        setNotice(message);
    }
    catch (caught) {
        setError(caught instanceof Error ? caught.message : "Workflow action failed.");
        requestAnimationFrame(() => errorRef.current?.focus());
    }
    finally {
        setBusy(false);
    } }
    if (id && record.isLoading)
        return <LoadingState label="Loading Project…"/>;
    if (record.error)
        return <InlineFeedback tone="error">{record.error.message}</InlineFeedback>;
    const noAreas = !areas.isLoading && !(areas.data?.items.length);
    const englishComplete = complete(values.translations.en);
    const arabicComplete = complete(values.translations.ar);
    return <section><AdminPageHeader back={<GuardedLink className="back-link" href="/projects"><ArrowLeft aria-hidden size={16}/>Back to Projects</GuardedLink>} description="Projects are canonical Off-Plan developments. Prices are intentionally not part of this record." eyebrow="Off-Plan CMS" title={id ? "Review Project" : "New Project"} action={<div className="status-cluster"><StatusBadge status={values.status}/><StatusBadge status={values.workflow_status}/></div>}/><form className="editor-form" onSubmit={(event) => { event.preventDefault(); void save("draft"); }}><ErrorSummary focusRef={errorRef} message={error}/>{notice ? <InlineFeedback tone="success">{notice}</InlineFeedback> : null}{noAreas ? <InlineFeedback tone="info">No canonical Areas exist. ARE-PRJ-02 must verify and create an Area before a Project can be saved.</InlineFeedback> : null}<FormSection id="identity" title="1. Identity and workflow"><div className="form-grid"><label>Stable slug<input required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" value={values.slug} onChange={(event) => set("slug", event.target.value)}/></label><label>Publication status<input disabled value={values.status}/></label><label>Workflow status<input disabled value={human(values.workflow_status)}/></label><label>Display order<input min="0" type="number" value={values.display_order} onChange={(event) => set("display_order", Number(event.target.value))}/></label><label className="check"><input checked={values.featured} onChange={(event) => set("featured", event.target.checked)} type="checkbox"/>Featured</label></div></FormSection><FormSection id="relations" title="2. Developer, Emirate and Area"><div className="form-grid"><label>Canonical Developer<select required value={values.developer_id} onChange={(event) => set("developer_id", event.target.value)}><option value="">Select Developer</option>{developers.data?.items.map((item) => <option key={item.id} value={item.id}>{item.translations?.en?.name ?? item.slug}</option>)}</select></label><label>Emirate<select required value={values.emirate} onChange={(event) => { const next = event.target.value; setValues((current) => ({ ...current, emirate: next, area_id: areas.data?.items.find((item) => item.id === current.area_id)?.emirate === next ? current.area_id : "" })); }}><option value="">Select Emirate</option>{["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"].map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label>Canonical Area/Community<select required value={values.area_id} onChange={(event) => { const area = areas.data?.items.find((item) => item.id === event.target.value); setValues((current) => ({ ...current, area_id: event.target.value, emirate: area?.emirate ?? current.emirate })); }}><option value="">Select verified Area</option>{areas.data?.items.filter((item) => !values.emirate || item.emirate === values.emirate).map((item) => <option key={item.id} value={item.id}>{item.name_en}</option>)}</select></label></div></FormSection><FormSection id="content" title="3–4. English and Arabic content" description="Project names are never translated or transliterated automatically."><LanguageTabs active={locale} arabicComplete={arabicComplete} englishComplete={englishComplete} label="Project content language" onChange={setLocale}><div className="form-grid"><label>Official Project Name<input dir={locale === "ar" ? "rtl" : "ltr"} value={values.translations[locale].official_name} onChange={(event) => setTranslation("official_name", event.target.value)}/></label><label className="wide">Short summary<textarea rows={3} value={values.translations[locale].short_summary} onChange={(event) => setTranslation("short_summary", event.target.value)}/></label><label className="wide">Full description<textarea rows={6} value={values.translations[locale].full_description} onChange={(event) => setTranslation("full_description", event.target.value)}/></label><label>SEO title<input value={values.translations[locale].seo_title} onChange={(event) => setTranslation("seo_title", event.target.value)}/></label><label>SEO description<textarea rows={3} value={values.translations[locale].seo_description} onChange={(event) => setTranslation("seo_description", event.target.value)}/></label></div></LanguageTabs></FormSection><FormSection id="inventory" title="5. Property types and bedrooms"><Checkboxes label="Property types" options={["apartment", "villa", "townhouse", "penthouse", "duplex", "mansion", "residential-plot", "other"]} selected={values.property_types} onChange={(selected) => set("property_types", selected)}/><Checkboxes label="Bedroom options" options={["studio", "1", "2", "3", "4", "5", "6+"]} selected={values.bedroom_options} onChange={(selected) => set("bedroom_options", selected)}/></FormSection><RepeaterSection label="Unit types" values={values.unit_types} onChange={(items) => set("unit_types", items)}/><RepeaterSection label="Amenities" values={values.amenities} onChange={(items) => set("amenities", items)}/><SizeLocationSection values={values} set={set}/><NearbyPlaces values={values.nearby_places} onChange={(items) => set("nearby_places", items)}/><FormSection id="handover" title="7. Handover"><div className="form-grid"><label>Quarter<select value={values.handover_quarter} onChange={(event) => set("handover_quarter", event.target.value)}><option value="">Not confirmed</option>{["Q1", "Q2", "Q3", "Q4"].map((item) => <option key={item}>{item}</option>)}</select></label><label>Year<input min="2000" max="2200" type="number" value={values.handover_year} onChange={(event) => set("handover_year", event.target.value)}/></label><label className="wide">Original source value<input value={values.original_handover_value} onChange={(event) => set("original_handover_value", event.target.value)}/></label></div></FormSection><PaymentSection values={values} set={set}/><DownPaymentSection values={values} set={set}/><FormSection id="status" title="10. Availability and construction"><div className="form-grid"><label>Availability<select value={values.availability_status} onChange={(event) => set("availability_status", event.target.value)}><option value="">Not Confirmed</option>{["available", "limited-availability", "sold-out", "coming-soon"].map((item) => <option key={item} value={item}>{human(item)}</option>)}</select></label><label>Construction<select value={values.construction_status} onChange={(event) => set("construction_status", event.target.value)}>{["pre-launch", "launched", "under-construction", "near-completion", "completed", "on-hold", "not-confirmed"].map((item) => <option key={item} value={item}>{human(item)}</option>)}</select></label></div></FormSection><SourceSection values={values} set={set}/><MediaSection busy={busy} id={id} onSupersede={supersedePrivateMedia} onUpload={upload} values={values} set={set}/><FormSection id="priority" title="12. Internal priority and notes" description="ARE Priority and internal notes never enter the Public API."><div className="form-grid"><label>ARE Priority<select required value={values.priority} onChange={(event) => set("priority", event.target.value)}><option value="">Select manually</option><option value="A">A — Homepage/high focus</option><option value="B">B — Standard visibility</option><option value="C">C — Reference</option></select></label><label>Last Verified<input type="datetime-local" value={values.last_verified_at} onChange={(event) => set("last_verified_at", event.target.value)}/></label><label className="wide">Internal notes<textarea rows={4} value={values.internal_notes} onChange={(event) => set("internal_notes", event.target.value)}/></label></div></FormSection><div id="preview"><StickyFormActions help="Publication requires bilingual content, authoritative sources, a published Area/Developer and approved uploaded cover." state={id ? "Canonical Project record" : "Not saved yet"}>{id ? <GuardedLink className="secondary-button" href={`/projects/${id}/view`}><Eye aria-hidden size={16}/>View</GuardedLink> : null}{id ? <GuardedLink className="secondary-button" href={`/projects/${id}/preview`}><Eye aria-hidden size={16}/>Preview</GuardedLink> : null}<GuardedLink className="secondary-button" href="/projects">Cancel</GuardedLink><button className="action-button" disabled={busy || noAreas} type="submit"><Save aria-hidden size={16}/>Save Draft</button><button className="action-button" disabled={busy || !id || values.workflow_status !== "draft"} onClick={() => void transition("submit-review", "Project submitted for review.")} type="button"><Send aria-hidden size={16}/>Submit for Review</button>{id && values.status !== "archived" ? <button className="action-button action-button--archive" disabled={busy} onClick={() => void save("archived")} type="button"><Archive aria-hidden size={16}/>Archive</button> : null}</StickyFormActions></div></form>{id ? <ProjectApprovalReview id={id} status={values.status} workflow={values.workflow_status} onApproved={() => { void record.refetch(); }}/> : null}</section>;
}
function RepeaterSection({ label, values, onChange }: Readonly<{
    label: string;
    values: BilingualItem[];
    onChange: (values: BilingualItem[]) => void;
}>) {
    const update = (index: number, key: keyof BilingualItem, value: string | number) => onChange(values.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item));
    return <FormSection id={label.toLowerCase().replace(" ", "-")} title={label}><div className="block-list-heading"><strong>{label}</strong><button onClick={() => onChange([...values, { label_en: "", label_ar: "", display_order: values.length }])} type="button"><Plus aria-hidden size={15}/>Add {label.toLowerCase().replace(/s$/, "")}</button></div>{values.map((item, index) => <div className="content-block" key={`${label}-${index}`}><div className="form-grid"><label>English label<input value={item.label_en} onChange={(event) => update(index, "label_en", event.target.value)}/></label><label>Arabic label<input dir="rtl" value={item.label_ar} onChange={(event) => update(index, "label_ar", event.target.value)}/></label><label>Display order<input min="0" type="number" value={item.display_order} onChange={(event) => update(index, "display_order", Number(event.target.value))}/></label></div><button onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))} type="button"><Trash2 aria-hidden size={15}/>Remove</button></div>)}</FormSection>;
}
function SizeLocationSection({ values, set }: Readonly<{
    values: Values;
    set: <K extends keyof Values>(key: K, value: Values[K]) => void;
}>) {
    return <FormSection id="size-location" title="6. Size range and location"><div className="form-grid"><label>Minimum size<input min="0" step="0.01" type="number" value={values.size_min} onChange={(event) => set("size_min", event.target.value)}/></label><label>Maximum size<input min="0" step="0.01" type="number" value={values.size_max} onChange={(event) => set("size_max", event.target.value)}/></label><label>Size unit<select value={values.size_unit} onChange={(event) => set("size_unit", event.target.value)}><option value="">Not confirmed</option><option value="sqft">Square feet</option><option value="sqm">Square metres</option></select></label><label>Latitude<input min="-90" max="90" step="0.000001" type="number" value={values.latitude} onChange={(event) => set("latitude", event.target.value)}/></label><label>Longitude<input min="-180" max="180" step="0.000001" type="number" value={values.longitude} onChange={(event) => set("longitude", event.target.value)}/></label></div></FormSection>;
}
function NearbyPlaces({ values, onChange }: Readonly<{
    values: NearbyPlace[];
    onChange: (values: NearbyPlace[]) => void;
}>) {
    const update = (index: number, key: keyof NearbyPlace, value: string | number) => onChange(values.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item));
    return <FormSection id="nearby-places" title="Nearby places"><div className="block-list-heading"><strong>Nearby places</strong><button onClick={() => onChange([...values, { name_en: "", name_ar: "", distance_value: "", distance_unit: "", travel_time_minutes: "", display_order: values.length }])} type="button"><Plus aria-hidden size={15}/>Add place</button></div>{values.map((item, index) => <div className="content-block" key={`place-${index}`}><div className="form-grid"><label>English name<input value={item.name_en} onChange={(event) => update(index, "name_en", event.target.value)}/></label><label>Arabic name<input dir="rtl" value={item.name_ar} onChange={(event) => update(index, "name_ar", event.target.value)}/></label><label>Distance<input min="0" step="0.01" type="number" value={item.distance_value} onChange={(event) => update(index, "distance_value", event.target.value)}/></label><label>Distance unit<select value={item.distance_unit} onChange={(event) => update(index, "distance_unit", event.target.value)}><option value="">Not confirmed</option><option value="km">km</option><option value="m">m</option></select></label><label>Travel time (minutes)<input min="0" type="number" value={item.travel_time_minutes} onChange={(event) => update(index, "travel_time_minutes", event.target.value)}/></label></div><button onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))} type="button"><Trash2 aria-hidden size={15}/>Remove place</button></div>)}</FormSection>;
}
function DownPaymentSection({ values, set }: Readonly<{
    values: Values;
    set: <K extends keyof Values>(key: K, value: Values[K]) => void;
}>) {
    return <FormSection id="down-payment" title="9. Down payment" description="Store only source-grounded values; never infer a missing percentage."><div className="form-grid"><label>Normalized percentage<input min="0" max="100" step="0.01" type="number" value={values.down_payment_percentage} onChange={(event) => set("down_payment_percentage", event.target.value)}/></label><label className="wide">Original source wording<input value={values.down_payment_source_value} onChange={(event) => set("down_payment_source_value", event.target.value)}/></label></div></FormSection>;
}
function PaymentSection({ values, set }: Readonly<{
    values: Values;
    set: <K extends keyof Values>(key: K, value: Values[K]) => void;
}>) { const update = (index: number, key: keyof Milestone, value: string | number) => set("milestones", values.milestones.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item)); return <FormSection id="payment" title="7. Payment plan" description="Preserve source wording. Never infer a missing percentage or Arabic label."><div className="form-grid"><label className="wide">Raw source wording<textarea rows={3} value={values.payment_raw} onChange={(event) => set("payment_raw", event.target.value)}/></label><label>Source row index<input min="0" type="number" value={values.payment_source_index} onChange={(event) => set("payment_source_index", Number(event.target.value))}/></label><label>Verified at<input type="datetime-local" value={values.payment_verified_at} onChange={(event) => set("payment_verified_at", event.target.value)}/></label><label className="check"><input checked={values.payment_complete} onChange={(event) => set("payment_complete", event.target.checked)} type="checkbox"/>Plan is complete</label></div><div className="block-list"><div className="block-list-heading"><strong>Ordered milestones</strong><button onClick={() => set("milestones", [...values.milestones, { sequence: values.milestones.length + 1, stage: "other", label_en: "", label_ar: "", percentage: "", due_trigger: "", source_value: "" }])} type="button"><Plus aria-hidden size={15}/>Add milestone</button></div>{values.milestones.map((item, index) => <div className="content-block" key={`milestone-${index}`}><div className="form-grid"><label>Sequence<input min="0" type="number" value={item.sequence} onChange={(event) => update(index, "sequence", Number(event.target.value))}/></label><label>Stage<select value={item.stage} onChange={(event) => update(index, "stage", event.target.value)}>{["booking", "during-construction", "handover", "post-handover", "other"].map((stage) => <option key={stage} value={stage}>{human(stage)}</option>)}</select></label><label>English label<input value={item.label_en} onChange={(event) => update(index, "label_en", event.target.value)}/></label><label>Arabic label<input dir="rtl" value={item.label_ar} onChange={(event) => update(index, "label_ar", event.target.value)}/></label><label>Percentage<input min="0" max="100" step="0.01" type="number" value={item.percentage} onChange={(event) => update(index, "percentage", event.target.value)}/></label><label>Timing/event<input value={item.due_trigger} onChange={(event) => update(index, "due_trigger", event.target.value)}/></label><label className="wide">Original source value<input value={item.source_value} onChange={(event) => update(index, "source_value", event.target.value)}/></label></div><button onClick={() => set("milestones", values.milestones.filter((_, itemIndex) => itemIndex !== index))} type="button"><Trash2 aria-hidden size={15}/>Remove milestone</button></div>)}</div></FormSection>; }
function SourceSection({ values, set }: Readonly<{
    values: Values;
    set: <K extends keyof Values>(key: K, value: Values[K]) => void;
}>) { const update = (index: number, key: keyof Source, value: string | boolean) => set("sources", values.sources.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item)); const types = ["OWNER_MANIFEST", "DLD_PROJECT_STATUS", "OFFICIAL_DEVELOPER_PAGE", "OFFICIAL_DEVELOPER_BROCHURE", "OFFICIAL_MASTER_COMMUNITY_PAGE", "OWNER_SUPPLIED_DOCUMENT", "OWNER_APPROVED_PARTNER_FEED", "APPROVED_SECONDARY_SOURCE"]; return <FormSection id="sources" title="9. Sources and verification" description="Lower-authority sources cannot silently override official evidence."><div className="block-list-heading"><strong>Evidence sources</strong><button onClick={() => set("sources", [...values.sources, emptySource()])} type="button"><Plus aria-hidden size={15}/>Add source</button></div>{values.sources.map((source, index) => <div className="content-block" key={`source-${index}`}><div className="form-grid"><label>Source type<select value={source.source_type} onChange={(event) => update(index, "source_type", event.target.value)}>{types.map((item) => <option key={item}>{item}</option>)}</select></label><label>Source URL<input dir="ltr" type="url" value={source.source_url} onChange={(event) => update(index, "source_url", event.target.value)}/></label><label>Retrieved<input type="datetime-local" value={source.retrieved_at} onChange={(event) => update(index, "retrieved_at", event.target.value)}/></label><label>Last checked<input type="datetime-local" value={source.last_checked_at} onChange={(event) => update(index, "last_checked_at", event.target.value)}/></label><label className="wide">SHA-256 content hash<input dir="ltr" maxLength={64} value={source.content_hash} onChange={(event) => update(index, "content_hash", event.target.value)}/></label><label>Source title<input value={source.source_title} onChange={(event) => update(index, "source_title", event.target.value)}/></label><label>Developer/domain<input value={source.source_developer_domain} onChange={(event) => update(index, "source_developer_domain", event.target.value)}/></label><label className="check"><input checked={source.is_official} onChange={(event) => update(index, "is_official", event.target.checked)} type="checkbox"/>Official classification</label><label className="check"><input checked={source.is_active} onChange={(event) => update(index, "is_active", event.target.checked)} type="checkbox"/>Source active</label></div><button onClick={() => set("sources", values.sources.filter((_, itemIndex) => itemIndex !== index))} type="button"><Trash2 aria-hidden size={15}/>Remove source</button></div>)}</FormSection>; }
function MediaSection({ values, set, id, busy, onUpload, onSupersede }: Readonly<{
    values: Values;
    set: <K extends keyof Values>(key: K, value: Values[K]) => void;
    id?: string;
    busy: boolean;
    onUpload: (mediaId: string, file?: File) => Promise<void>;
    onSupersede: (mediaId: string) => Promise<void>;
}>) { const update = (index: number, key: keyof Media, value: string | number) => set("media", values.media.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item)); const categories = ["cover", "gallery", "exterior", "interior", "amenities", "floor-plan", "master-plan", "location-map", "construction", "video-reference"]; return <FormSection id="media" title="10. Media" description="No Project may publish without an uploaded approved cover and bilingual alternative text."><div className="block-list-heading"><strong>Project media</strong><button onClick={() => set("media", [...values.media, emptyMedia()])} type="button"><Plus aria-hidden size={15}/>Add media</button></div>{values.media.map((media, index) => <div className="content-block" key={media.id ?? `media-${index}`}><div className="form-grid"><label>Category<select value={media.category} onChange={(event) => update(index, "category", event.target.value)}>{categories.map((item) => <option key={item} value={item}>{human(item)}</option>)}</select></label><label>Rights status<select value={media.rights_status} onChange={(event) => update(index, "rights_status", event.target.value)}><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option></select></label><label className="wide">Provenance/source URL<input dir="ltr" type="url" value={media.source_url} onChange={(event) => update(index, "source_url", event.target.value)}/></label><label>English alt text<input value={media.alt_en} onChange={(event) => update(index, "alt_en", event.target.value)}/></label><label>Arabic alt text<input dir="rtl" value={media.alt_ar} onChange={(event) => update(index, "alt_ar", event.target.value)}/></label><label>Display order<input min="0" type="number" value={media.display_order} onChange={(event) => update(index, "display_order", Number(event.target.value))}/></label><label>Verified at<input type="datetime-local" value={media.verified_at} onChange={(event) => update(index, "verified_at", event.target.value)}/></label>{id && media.id ? <label>Upload JPEG, PNG or WebP<span className="secondary-button"><Upload aria-hidden size={15}/>{media.has_upload ? "Replace file" : "Upload file"}</span><input className="visually-hidden" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={(event) => void onUpload(media.id!, event.target.files?.[0])} type="file"/></label> : <p>Save the Draft before uploading a file.</p>}</div>{media.id && media.association_status !== "superseded-private" && media.rights_status !== "approved" && media.source_url.startsWith("owner-approved:aliyas-neutral-cover-temporary-private-preview-") ? <button disabled={busy} onClick={() => void onSupersede(media.id!)} type="button"><Archive aria-hidden size={15}/>Supersede private association</button> : <button onClick={() => set("media", values.media.filter((_, itemIndex) => itemIndex !== index))} type="button"><Trash2 aria-hidden size={15}/>Remove metadata</button>}</div>)}</FormSection>; }
function Checkboxes({ label, options, selected, onChange }: Readonly<{
    label: string;
    options: string[];
    selected: string[];
    onChange: (selected: string[]) => void;
}>) { return <div className="field-group"><span className="field-label">{label}</span><div className="check-grid">{options.map((item) => <label className="check" key={item}><input checked={selected.includes(item)} onChange={(event) => onChange(event.target.checked ? [...selected, item] : selected.filter((value) => value !== item))} type="checkbox"/>{human(item)}</label>)}</div></div>; }
function recordValues(record: ProjectRecord): Values {
    const plan = record.payment_plan;
    const base = initialValues();
    return {
        ...base,
        ...record,
        status: record.status ?? "draft",
        workflow_status: record.workflow_status ?? "draft",
        availability_status: record.availability_status ?? "",
        handover_quarter: record.handover_quarter ?? "",
        size_unit: record.size_unit ?? "",
        original_handover_value: record.original_handover_value ?? "",
        down_payment_source_value: record.down_payment_source_value ?? "",
        internal_notes: record.internal_notes ?? "",
        priority: record.priority ?? "",
        handover_year: stringValue(record.handover_year),
        size_min: stringValue(record.size_min),
        size_max: stringValue(record.size_max),
        down_payment_percentage: stringValue(record.down_payment_percentage),
        latitude: stringValue(record.latitude),
        longitude: stringValue(record.longitude),
        last_verified_at: localDateTime(record.last_verified_at),
        unit_types: record.unit_types ?? [],
        amenities: record.amenities ?? [],
        nearby_places: record.nearby_places?.map((item) => ({ ...item, distance_value: stringValue(item.distance_value), travel_time_minutes: stringValue(item.travel_time_minutes) })) ?? [],
        translations: { en: record.translations?.en ?? emptyTranslation(), ar: record.translations?.ar ?? emptyTranslation() },
        sources: record.sources?.map((item) => ({ ...item, source_title: item.source_title ?? "", source_developer_domain: item.source_developer_domain ?? "", retrieved_at: localDateTime(item.retrieved_at), last_checked_at: localDateTime(item.last_checked_at) })) ?? [],
        media: record.media?.map((item) => ({ id: item.id, category: item.category, source_url: item.source_url, rights_status: item.rights_status, alt_en: item.alt_en ?? "", alt_ar: item.alt_ar ?? "", display_order: item.display_order, verified_at: localDateTime(item.verified_at), has_upload: item.has_upload })) ?? [],
        payment_raw: plan?.raw_source_text ?? "",
        payment_source_index: Math.max(0, (record.sources ?? []).findIndex((source) => source.id === plan?.source_id)),
        payment_complete: Boolean(plan?.is_complete),
        payment_verified_at: localDateTime(plan?.verified_at),
        milestones: plan?.milestones?.map((item) => ({ ...item, percentage: item.percentage == null ? "" : String(item.percentage) })) ?? [],
    };
}
function complete(value: Translation) { return Object.values(value).every((item) => item.trim().length >= 2); }
function human(value: string) { return value.split("-").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" "); }
function iso(value?: string | null) { return value ? new Date(value).toISOString() : null; }
function localDateTime(value?: string | null) { return value ? new Date(value).toISOString().slice(0, 16) : ""; }
function numberOrNull(value?: string | number | null) { return value === "" || value == null ? null : Number(value); }
function stringValue(value?: string | number | null) { return value == null ? "" : String(value); }
