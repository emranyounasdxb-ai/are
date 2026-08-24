"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Locale, Purpose, SearchCopy } from "../../lib/home-copy";

type DiscoverySearchProps = Readonly<{
  copy: SearchCopy;
  initialLocation?: string;
  initialPurpose: Purpose;
  initialPropertyType?: string;
  locale: Locale;
  purposes?: ReadonlyArray<Purpose>;
}>;

export function DiscoverySearch({
  copy,
  initialLocation = "",
  initialPurpose,
  initialPropertyType = "",
  locale,
  purposes = ["buy", "rent", "off-plan"],
}: DiscoverySearchProps) {
  const router = useRouter();
  const [location, setLocation] = useState(initialLocation);
  const [message, setMessage] = useState("");
  const [messageState, setMessageState] = useState<"idle" | "error" | "success">("idle");
  const [propertyType, setPropertyType] = useState(initialPropertyType);
  const [purpose, setPurpose] = useState<Purpose>(initialPurpose);
  const showLocationError = messageState === "error" && !location;
  const showPropertyTypeError = messageState === "error" && !propertyType;

  function resetMessage() {
    setMessage("");
    setMessageState("idle");
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!location || !propertyType) {
      setMessage(copy.validationMessage);
      setMessageState("error");
      return;
    }

    const query = new URLSearchParams({ location, purpose, type: propertyType });
    router.push(`/${locale}/properties?${query.toString()}`);
  }

  return (
    <form
      aria-describedby="search-preview-note search-result-message"
      noValidate
      onSubmit={handleSubmit}
    >
      <div className="search-panel__grid">
        <label className="search-field">
          <span>{copy.locationLabel}</span>
          <select
            aria-invalid={showLocationError}
            onChange={(event) => {
              setLocation(event.target.value);
              resetMessage();
            }}
            required
            value={location}
          >
            <option disabled value="">
              {copy.locationPlaceholder}
            </option>
            {copy.locations.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="search-field">
          <span>{copy.propertyTypeLabel}</span>
          <select
            aria-invalid={showPropertyTypeError}
            onChange={(event) => {
              setPropertyType(event.target.value);
              resetMessage();
            }}
            required
            value={propertyType}
          >
            <option disabled value="">
              {copy.propertyTypePlaceholder}
            </option>
            {copy.propertyTypes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="purpose-field">
          <legend>{copy.purposeLabel}</legend>
          <input name="purpose" type="hidden" value={purpose} />
          <div className="purpose-field__options">
            {purposes.map((item) => (
              <button
                aria-pressed={purpose === item}
                key={item}
                onClick={() => {
                  setPurpose(item);
                  resetMessage();
                }}
                type="button"
              >
                {copy.purposes[item]}
              </button>
            ))}
          </div>
        </fieldset>

        <button className="search-submit" type="submit">
          <span>{copy.searchButton}</span>
          <span aria-hidden="true" className="directional-icon">
            →
          </span>
        </button>
      </div>

      <div className="search-panel__feedback">
        <p id="search-preview-note">{copy.previewNote}</p>
        <p
          aria-live="polite"
          data-state={messageState}
          id="search-result-message"
          role={messageState === "error" ? "alert" : "status"}
        >
          {message}
        </p>
      </div>
    </form>
  );
}
