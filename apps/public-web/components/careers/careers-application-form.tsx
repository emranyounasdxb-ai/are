"use client";

import { useRef, useState } from "react";

import { careerInterests, careersCopy, experienceRanges } from "../../lib/careers-data";
import type { Locale } from "../../lib/home-copy";

type FieldName = "fullName" | "email" | "phone" | "location" | "interest" | "experience" | "coverMessage" | "cv" | "linkedin" | "portfolio" | "languages" | "currentTitle" | "acknowledge";
type Errors = Partial<Record<FieldName, string>>;

const maximumFileSize = 5 * 1024 * 1024;
const permittedFileTypes: Readonly<Record<string, ReadonlyArray<string>>> = {
  pdf: ["application/pdf"],
  doc: ["application/msword"],
  docx: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
};

function isValidUrl(value: string) {
  if (!value) return true;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function validateFile(file: File | undefined, locale: Locale) {
  const copy = careersCopy[locale].form;
  if (!file) return copy.errors.cvRequired;
  if (file.size > maximumFileSize) return copy.errors.cvSize;
  const extension = file.name.toLocaleLowerCase("en").split(".").pop() ?? "";
  const permittedMimes = permittedFileTypes[extension];
  if (!permittedMimes || (file.type && !permittedMimes.includes(file.type))) return copy.errors.cvType;
  return undefined;
}

export function CareersApplicationForm({ jobSlug, locale }: Readonly<{ jobSlug?: string; locale: Locale }>) {
  const copy = careersCopy[locale].form;
  const formRef = useRef<HTMLFormElement>(null);
  const idempotencyRef = useRef<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [errors, setErrors] = useState<Errors>({});
  const [selectedFile, setSelectedFile] = useState<File>();
  const [result, setResult] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function focusField(field: FieldName) {
    const control = formRef.current?.elements.namedItem(field);
    if (control instanceof HTMLElement) {
      control.focus();
      control.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function clearFieldError(field: string) {
    if (!(field in errors)) return;
    setErrors((current) => {
      const next = { ...current };
      delete next[field as FieldName];
      return next;
    });
    setResult("");
  }

  function handleFile(file: File | undefined) {
    setSelectedFile(file);
    const error = validateFile(file, locale);
    setErrors((current) => ({ ...current, cv: error }));
    setResult("");
  }

  function removeFile() {
    setSelectedFile(undefined);
    if (fileRef.current) fileRef.current.value = "";
    setErrors((current) => {
      const next = { ...current };
      delete next.cv;
      return next;
    });
    setResult("");
    fileRef.current?.focus();
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const value = (name: FieldName) => String(form.get(name) ?? "").trim();
    const next: Errors = {};
    const email = value("email");
    const phone = value("phone");
    const linkedin = value("linkedin");
    const portfolio = value("portfolio");

    if (value("fullName").length < 2) next.fullName = copy.errors.fullName;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = copy.errors.email;
    if (!/^[0-9+().\s-]{7,25}$/.test(phone) || phone.replace(/\D/g, "").length < 7) next.phone = copy.errors.phone;
    if (value("location").length < 2) next.location = copy.errors.location;
    if (!value("interest")) next.interest = copy.errors.interest;
    if (!value("experience")) next.experience = copy.errors.experience;
    if (value("coverMessage").length < 30) next.coverMessage = copy.errors.coverMessage;
    const fileError = validateFile(selectedFile, locale);
    if (fileError) next.cv = fileError;
    if (!isValidUrl(linkedin)) next.linkedin = copy.errors.linkedin;
    if (!isValidUrl(portfolio)) next.portfolio = copy.errors.portfolio;
    if (!form.get("acknowledge")) next.acknowledge = copy.errors.acknowledge;

    setErrors(next);
    setResult("");
    const firstInvalid = Object.keys(next)[0] as FieldName | undefined;
    if (firstInvalid) {
      requestAnimationFrame(() => focusField(firstInvalid));
      return;
    }
    setSubmitting(true);
    try {
      form.set("applicant_name", value("fullName"));
      form.set("current_location", value("location"));
      form.set("context_label", `${value("interest")} | ${value("experience")}`);
      form.set("cover_note", value("coverMessage"));
      form.set("linkedin_url", linkedin);
      form.set("portfolio_url", portfolio);
      form.set("locale", locale);
      form.set("acknowledgement_consent", "true");
      form.set("marketing_consent", form.get("marketingConsent") ? "true" : "false");
      form.set("website", "");
      if (jobSlug) form.set("job_slug", jobSlug);
      if (selectedFile) form.set("cv", selectedFile);
      idempotencyRef.current ??= crypto.randomUUID();
      const response = await fetch(`${process.env.NEXT_PUBLIC_ARE_API_URL ?? "http://127.0.0.1:50003/api/v1"}/public/applications`, { method: "POST", headers: { "Idempotency-Key": idempotencyRef.current }, body: form });
      const body = await response.json() as { reference_id?: string };
      if (!response.ok || !body.reference_id) throw new Error();
      setResult(`${locale === "ar" ? "تم استلام طلبك. الرقم المرجعي" : "Your application was received. Reference"}: ${body.reference_id}`);
      idempotencyRef.current = null;
      setErrors({});
    } catch {
      setResult(locale === "ar" ? "تعذر إرسال طلبك. يرجى المحاولة مرة أخرى." : "We could not submit your application. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function resetForm() {
    formRef.current?.reset();
    if (fileRef.current) fileRef.current.value = "";
    setSelectedFile(undefined);
    setErrors({});
    setResult("");
    formRef.current?.querySelector<HTMLElement>("input")?.focus();
  }

  function describedBy(field: FieldName, hint?: string) {
    return [hint, errors[field] ? `${field}-error` : undefined].filter(Boolean).join(" ") || undefined;
  }

  const marker = <small className="career-form__marker">{copy.required}</small>;
  const optional = <small className="career-form__marker">{copy.optional}</small>;

  return (
    <form className="career-form" noValidate onInput={(event) => clearFieldError((event.target as HTMLInputElement).name)} onSubmit={handleSubmit} ref={formRef}>
      {Object.keys(errors).length ? <div aria-labelledby="career-error-summary-title" className="career-form__error-summary" role="alert"><h3 id="career-error-summary-title">{copy.summaryTitle}</h3><p>{copy.summaryIntro}</p><ul>{Object.entries(errors).map(([field, message]) => <li key={field}><button onClick={() => focusField(field as FieldName)} type="button">{message}</button></li>)}</ul></div> : null}

      <div className="career-form__grid">
        <Field error={errors.fullName} label={copy.fullName} marker={marker} name="fullName"><input aria-describedby={describedBy("fullName")} aria-invalid={Boolean(errors.fullName)} autoComplete="name" id="fullName" name="fullName" required /></Field>
        <Field error={errors.email} label={copy.email} marker={marker} name="email"><input aria-describedby={describedBy("email")} aria-invalid={Boolean(errors.email)} autoComplete="email" dir="ltr" id="email" inputMode="email" name="email" required type="email" /></Field>
        <Field error={errors.phone} label={copy.phone} marker={marker} name="phone"><input aria-describedby={describedBy("phone")} aria-invalid={Boolean(errors.phone)} autoComplete="tel" dir="ltr" id="phone" inputMode="tel" name="phone" required type="tel" /></Field>
        <Field error={errors.location} label={copy.location} marker={marker} name="location"><input aria-describedby={describedBy("location")} aria-invalid={Boolean(errors.location)} autoComplete="address-level2" id="location" name="location" required /></Field>
        <Field error={errors.interest} label={copy.interest} marker={marker} name="interest"><select aria-describedby={describedBy("interest")} aria-invalid={Boolean(errors.interest)} defaultValue="" id="interest" name="interest" required><option disabled value="">{copy.select}</option>{careerInterests.map((interest) => <option key={interest.value} value={interest.value}>{interest.label[locale]}</option>)}</select></Field>
        <Field error={errors.experience} label={copy.experience} marker={marker} name="experience"><select aria-describedby={describedBy("experience")} aria-invalid={Boolean(errors.experience)} defaultValue="" id="experience" name="experience" required><option disabled value="">{copy.select}</option>{experienceRanges.map((range) => <option key={range.value} value={range.value}>{range.label[locale]}</option>)}</select></Field>
        <Field error={errors.currentTitle} label={copy.currentTitle} marker={optional} name="currentTitle"><input aria-describedby={describedBy("currentTitle")} aria-invalid={Boolean(errors.currentTitle)} autoComplete="organization-title" id="currentTitle" name="currentTitle" /></Field>
        <Field error={errors.languages} label={copy.languages} marker={optional} name="languages"><input aria-describedby={describedBy("languages")} aria-invalid={Boolean(errors.languages)} id="languages" name="languages" /></Field>
        <Field error={errors.linkedin} label={copy.linkedin} marker={optional} name="linkedin"><input aria-describedby={describedBy("linkedin")} aria-invalid={Boolean(errors.linkedin)} autoComplete="url" dir="ltr" id="linkedin" inputMode="url" name="linkedin" type="url" /></Field>
        <Field error={errors.portfolio} label={copy.portfolio} marker={optional} name="portfolio"><input aria-describedby={describedBy("portfolio")} aria-invalid={Boolean(errors.portfolio)} autoComplete="url" dir="ltr" id="portfolio" inputMode="url" name="portfolio" type="url" /></Field>
        <Field className="career-form__wide" error={errors.coverMessage} label={copy.coverMessage} marker={marker} name="coverMessage"><textarea aria-describedby={describedBy("coverMessage")} aria-invalid={Boolean(errors.coverMessage)} id="coverMessage" name="coverMessage" required rows={7} /></Field>
        <div className="career-form__field career-form__wide"><div className="career-form__label"><label htmlFor="cv">{copy.cv}</label>{marker}</div><input accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" aria-describedby={describedBy("cv", "cv-hint")} aria-invalid={Boolean(errors.cv)} id="cv" name="cv" onChange={(event) => handleFile(event.target.files?.[0])} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); event.currentTarget.click(); } }} ref={fileRef} required type="file" /><p className="career-form__hint" id="cv-hint">{copy.fileHint} {copy.localFileNote}</p>{errors.cv ? <p className="career-form__error" id="cv-error">{errors.cv}</p> : null}{selectedFile ? <div className="career-form__file"><span><strong>{copy.selectedFile}:</strong> <bdi>{selectedFile.name}</bdi> ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span><button onClick={removeFile} type="button">{copy.removeFile}</button></div> : null}</div>
      </div>

      <div className="career-form__acknowledgement"><input aria-describedby={describedBy("acknowledge")} aria-invalid={Boolean(errors.acknowledge)} id="acknowledge" name="acknowledge" onKeyDown={(event) => { if (event.key === " ") { event.preventDefault(); event.currentTarget.click(); } }} required type="checkbox" /><label htmlFor="acknowledge">{copy.acknowledge}</label>{errors.acknowledge ? <p className="career-form__error" id="acknowledge-error">{errors.acknowledge}</p> : null}</div>
      <div className="career-form__acknowledgement"><input id="marketingConsent" name="marketingConsent" type="checkbox"/><label htmlFor="marketingConsent">{locale === "ar" ? "أرغب في تلقي تحديثات التوظيف والتسويق (اختياري)." : "I would like recruitment and marketing updates (optional)."}</label></div>
      <p className="career-form__hint">{locale === "ar" ? "سيتم تخزين سيرتك الذاتية بشكل خاص واستخدامها لمراجعة طلبك." : "Your CV is stored privately and used to review your application."}</p>
      <div className="career-form__actions"><button className="button button--primary animated-gold-border" disabled={submitting} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); formRef.current?.requestSubmit(); } }} type="submit">{copy.submit}</button><button className="career-form__reset" onClick={resetForm} type="button">{copy.reset}</button></div>
      <p aria-live="polite" className="career-form__result" role="status">{result}</p>
    </form>
  );
}

function Field({ children, className, error, label, marker, name }: Readonly<{ children: React.ReactNode; className?: string; error?: string; label: string; marker: React.ReactNode; name: FieldName }>) {
  return <div className={`career-form__field ${className ?? ""}`}><div className="career-form__label"><label htmlFor={name}>{label}</label>{marker}</div>{children}{error ? <p className="career-form__error" id={`${name}-error`}>{error}</p> : null}</div>;
}
