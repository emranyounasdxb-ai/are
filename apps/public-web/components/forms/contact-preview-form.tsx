"use client";

import { useRef, useState } from "react";
import type { Locale } from "../../lib/home-copy";
import { siteCopy } from "../../lib/site-copy";

const API_URL = process.env.NEXT_PUBLIC_ARE_API_URL ?? "http://127.0.0.1:50003/api/v1";

export function ContactPreviewForm({ initialEnquiryType, locale, selectedDeveloper, selectedEnquiryLabel }: Readonly<{ initialEnquiryType?: string; locale: Locale; selectedDeveloper?: string; selectedEnquiryLabel?: string }>) {
  const copy = siteCopy[locale].contact;
  const formRef = useRef<HTMLFormElement>(null);
  const idempotencyRef = useRef<string | null>(null);
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [state, setState] = useState<"idle" | "error" | "submitting" | "success">("idle");
  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    const value = (name: string) => String(form.get(name) ?? "").trim();
    const issues: Array<{ field: string; message: string }> = [];
    if (value("name").length < 2) issues.push({ field: "name", message: locale === "ar" ? "أدخل اسمك." : "Enter your name." });
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value("email"))) issues.push({ field: "email", message: locale === "ar" ? "أدخل بريداً إلكترونياً صالحاً." : "Enter a valid email address." });
    if (!/^[+0-9 ()-]{7,48}$/.test(value("phone")) || value("phone").replace(/\D/g, "").length < 7) issues.push({ field: "phone", message: locale === "ar" ? "أدخل رقم هاتف صالحاً." : "Enter a valid phone number." });
    if (!value("enquiryType")) issues.push({ field: "enquiryType", message: locale === "ar" ? "اختر نوع الاستفسار." : "Choose an enquiry type." });
    if (value("message").length < 10) issues.push({ field: "message", message: locale === "ar" ? "اكتب رسالة لا تقل عن ١٠ أحرف." : "Write a message of at least 10 characters." });
    if (!form.get("contactConsent")) issues.push({ field: "contactConsent", message: locale === "ar" ? "أكد موافقتك على معالجة الاستفسار." : "Confirm consent to process the enquiry." });
    if (issues.length) {
      setErrors(issues.map((item) => item.message)); setMessage(copy.validation); setState("error");
      const field = issues[0].field;
      (formRef.current?.elements.namedItem(field) as HTMLElement | null)?.focus(); return;
    }
    setErrors([]);
    setState("submitting"); setMessage(locale === "ar" ? "جارٍ إرسال طلبك…" : "Sending your request…");
    try {
      idempotencyRef.current ??= crypto.randomUUID();
      const response = await fetch(`${API_URL}/public/enquiries`, { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyRef.current }, body: JSON.stringify({ enquiry_type: form.get("enquiryType"), name: form.get("name"), email: form.get("email"), phone: form.get("phone"), message: form.get("message"), selected_developer: selectedDeveloper, locale, preferred_contact_method: form.get("preferredContact"), contact_consent: true, marketing_consent: Boolean(form.get("marketingConsent")), attribution: { referrer: document.referrer.slice(0, 300) }, website: form.get("website") }) });
      const body = await response.json() as { reference_id?: string };
      if (!response.ok || !body.reference_id) throw new Error();
      setMessage(`${copy.success} ${locale === "ar" ? "الرقم المرجعي" : "Reference"}: ${body.reference_id}`); setState("success"); setErrors([]); formRef.current?.reset(); idempotencyRef.current = null;
    } catch { setMessage(locale === "ar" ? "تعذر إرسال طلبك. يرجى المحاولة مرة أخرى." : "We could not send your request. Please try again."); setState("error"); }
  }
  return <form aria-describedby="contact-form-feedback" className="contact-form" noValidate onSubmit={handleSubmit} ref={formRef}>
    <input aria-hidden="true" autoComplete="off" className="honeypot" name="website" tabIndex={-1}/>
    {errors.length ? <div className="career-form__error-summary" role="alert"><strong>{locale === "ar" ? "يرجى مراجعة الحقول التالية" : "Please review these fields"}</strong><ul>{errors.map((error) => <li key={error}>{error}</li>)}</ul></div> : null}
    <label><span>{copy.enquiryTypeLabel}</span><select defaultValue={initialEnquiryType ?? ""} name="enquiryType" required><option disabled value="">{copy.enquiryTypeLabel}</option>{copy.enquiryTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}{initialEnquiryType && !copy.enquiryTypes.some((item) => item.value === initialEnquiryType) ? <option value={initialEnquiryType}>{selectedEnquiryLabel ?? initialEnquiryType}</option> : null}</select></label>
    {selectedDeveloper ? <div className="contact-form__selection"><span>{locale === "ar" ? "المطور المحدد" : "Selected developer"}</span><strong dir="ltr">{selectedDeveloper}</strong></div> : null}
    <label><span>{copy.nameLabel}</span><input autoComplete="name" name="name" required/></label>
    <label><span>{copy.emailLabel}</span><input autoComplete="email" dir="ltr" inputMode="email" name="email" required type="email"/></label>
    <label><span>{locale === "ar" ? "رقم الهاتف" : "Phone number"}</span><input autoComplete="tel" dir="ltr" inputMode="tel" name="phone" required type="tel"/></label>
    <label><span>{locale === "ar" ? "طريقة التواصل المفضلة" : "Preferred contact method"}</span><select defaultValue="email" name="preferredContact"><option value="email">{locale === "ar" ? "بريد إلكتروني" : "Email"}</option><option value="phone">{locale === "ar" ? "هاتف" : "Phone"}</option><option value="whatsapp">{locale === "ar" ? "واتساب" : "WhatsApp"}</option></select></label>
    <label><span>{copy.messageLabel}</span><textarea name="message" placeholder={copy.messagePlaceholder} required rows={6}/></label>
    <label className="contact-form__consent"><input name="contactConsent" required type="checkbox"/><span>{locale === "ar" ? "أوافق على معالجة بياناتي للرد على هذا الطلب." : "I agree to the processing of my data to respond to this request."}</span></label>
    <label className="contact-form__consent"><input name="marketingConsent" type="checkbox"/><span>{locale === "ar" ? "أرغب في تلقي تحديثات تسويقية (اختياري)." : "I would like to receive marketing updates (optional)."}</span></label>
    <p className="contact-form__note">{locale === "ar" ? "تُستخدم بياناتك لإدارة طلبك وفق إشعار الخصوصية." : "Your data is used to manage your request under the privacy notice."}</p>
    <button className="button button--primary animated-gold-border" disabled={state === "submitting"} type="submit">{copy.submit}<span aria-hidden="true" className="directional-icon">→</span></button>
    <p aria-live="polite" className="contact-form__feedback" data-state={state} id="contact-form-feedback" role={state === "error" ? "alert" : "status"}>{message}</p>
  </form>;
}
