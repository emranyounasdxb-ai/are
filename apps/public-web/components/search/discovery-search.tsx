"use client";

import { useState } from "react";

const purposes = ["Buy", "Rent", "Off-Plan"] as const;

export function DiscoverySearch() {
  const [purpose, setPurpose] = useState<(typeof purposes)[number]>("Buy");
  const [message, setMessage] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(
      "Search preview ready. Live property search will be connected with approved property data.",
    );
  }

  return (
    <form aria-describedby="search-preview-note search-result-message" onSubmit={handleSubmit}>
      <div className="search-panel__grid">
        <label className="search-field">
          <span>Location</span>
          <select defaultValue="">
            <option disabled value="">
              Choose a location
            </option>
            <option value="uae">Across the UAE</option>
            <option value="dubai">Dubai</option>
            <option value="ajman">Ajman</option>
          </select>
        </label>

        <label className="search-field">
          <span>Property Type</span>
          <select defaultValue="">
            <option disabled value="">
              Choose a property type
            </option>
            <option value="apartment">Apartment</option>
            <option value="villa">Villa</option>
            <option value="townhouse">Townhouse</option>
            <option value="commercial">Commercial</option>
          </select>
        </label>

        <fieldset className="purpose-field">
          <legend>Purpose</legend>
          <input name="purpose" type="hidden" value={purpose} />
          <div className="purpose-field__options">
            {purposes.map((item) => (
              <button
                aria-pressed={purpose === item}
                key={item}
                onClick={() => {
                  setPurpose(item);
                  setMessage("");
                }}
                type="button"
              >
                {item}
              </button>
            ))}
          </div>
        </fieldset>

        <button className="search-submit" type="submit">
          <span>Search</span>
          <span aria-hidden="true">↗</span>
        </button>
      </div>

      <div className="search-panel__feedback">
        <p id="search-preview-note">Preview only — no live inventory is queried.</p>
        <p aria-live="polite" id="search-result-message" role="status">
          {message}
        </p>
      </div>
    </form>
  );
}
