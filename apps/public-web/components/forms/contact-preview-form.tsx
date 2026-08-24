"use client";

import { useState } from "react";

import { siteCopy } from "../../lib/site-copy";
import type { Locale } from "../../lib/home-copy";

export function ContactPreviewForm({ locale }: Readonly<{ locale: Locale }>) {
  const copy = siteCopy[locale].contact;
  const [message, setMessage] = useState("");
  const [state, setState] = useState<"idle" | "error" | "success">("idle");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    const email = String(form.get("email") ?? "").trim();
    const enquiryType = String(form.get("enquiryType") ?? "").trim();
    const enquiry = String(form.get("message") ?? "").trim();
    const emailIsValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    if (!name || !emailIsValid || !enquiryType || enquiry.length < 10) {
      setMessage(copy.validation);
      setState("error");
      return;
    }

    setMessage(copy.success);
    setState("success");
  }

  return (
    <form
      aria-describedby="contact-preview-note contact-form-feedback"
      className="contact-form"
      noValidate
      onSubmit={handleSubmit}
    >
      <label>
        <span>{copy.enquiryTypeLabel}</span>
        <select aria-invalid={state === "error"} defaultValue="" name="enquiryType" required>
          <option disabled value="">{copy.enquiryTypeLabel}</option>
          {copy.enquiryTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
      </label>
      <label>
        <span>{copy.nameLabel}</span>
        <input
          aria-invalid={state === "error"}
          autoComplete="name"
          name="name"
          placeholder={copy.namePlaceholder}
          required
        />
      </label>
      <label>
        <span>{copy.emailLabel}</span>
        <input
          autoComplete="email"
          aria-invalid={state === "error"}
          inputMode="email"
          name="email"
          placeholder={copy.emailPlaceholder}
          required
          type="email"
        />
      </label>
      <label>
        <span>{copy.messageLabel}</span>
        <textarea
          aria-invalid={state === "error"}
          name="message"
          placeholder={copy.messagePlaceholder}
          required
          rows={6}
        />
      </label>
      <p className="contact-form__note" id="contact-preview-note">{copy.previewNote}</p>
      <button className="button button--primary" type="submit">
        {copy.submit}
        <span aria-hidden="true" className="directional-icon">↗</span>
      </button>
      <p
        aria-live="polite"
        className="contact-form__feedback"
        data-state={state}
        id="contact-form-feedback"
        role={state === "error" ? "alert" : "status"}
      >
        {message}
      </p>
    </form>
  );
}
