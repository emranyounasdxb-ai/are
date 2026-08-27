"use client";

import { useEffect, useId, useRef, useState } from "react";

export type PublicSelectOption = Readonly<{
  label: string;
  value: string;
}>;

type PublicSelectProps = Readonly<{
  invalid?: boolean;
  label: string;
  onChange: (value: string) => void;
  options: ReadonlyArray<PublicSelectOption>;
  placeholder: string;
  required?: boolean;
  value: string;
}>;

export function PublicSelect({
  invalid = false,
  label,
  onChange,
  options,
  placeholder,
  required = false,
  value,
}: PublicSelectProps) {
  const instanceId = useId();
  const labelId = `${instanceId}-label`;
  const listboxId = `${instanceId}-listbox`;
  const valueId = `${instanceId}-value`;
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [menuMaxHeight, setMenuMaxHeight] = useState(256);
  const [placement, setPlacement] = useState<"bottom" | "top">("bottom");
  const selectedIndex = options.findIndex((option) => option.value === value);
  const selectedOption = selectedIndex >= 0 ? options[selectedIndex] : undefined;

  useEffect(() => {
    function handleOutsidePointer(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("pointerdown", handleOutsidePointer);
    return () => document.removeEventListener("pointerdown", handleOutsidePointer);
  }, []);

  function optionId(index: number) {
    return `${instanceId}-option-${index}`;
  }

  function openList(preferredIndex?: number) {
    const trigger = triggerRef.current;
    if (trigger) {
      const bounds = trigger.getBoundingClientRect();
      const menuGap = 7;
      const viewportInset = 16;
      const spaceAbove = Math.max(0, bounds.top - menuGap - viewportInset);
      const spaceBelow = Math.max(0, window.innerHeight - bounds.bottom - menuGap - viewportInset);
      const expectedHeight = Math.min(options.length * 46 + 12, 256);
      const isMobile = window.matchMedia("(max-width: 700px)").matches;
      const nextPlacement = isMobile && spaceAbove < expectedHeight && spaceBelow > spaceAbove ? "bottom" : "top";
      const availableHeight = nextPlacement === "top" ? spaceAbove : spaceBelow;

      setPlacement(nextPlacement);
      setMenuMaxHeight(Math.min(256, availableHeight));
    }

    setActiveIndex(preferredIndex ?? (selectedIndex >= 0 ? selectedIndex : 0));
    setIsOpen(true);
  }

  function closeList({ restoreFocus = false } = {}) {
    setIsOpen(false);
    if (restoreFocus) {
      window.requestAnimationFrame(() => triggerRef.current?.focus());
    }
  }

  function selectOption(index: number) {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    closeList({ restoreFocus: true });
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;

      if (!isOpen) {
        const initialIndex = selectedIndex >= 0 ? selectedIndex : direction > 0 ? 0 : options.length - 1;
        openList(initialIndex);
        return;
      }

      setActiveIndex((current) => Math.max(0, Math.min(options.length - 1, current + direction)));
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      if (!isOpen) return;
      event.preventDefault();
      setActiveIndex(event.key === "Home" ? 0 : options.length - 1);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (isOpen) selectOption(activeIndex);
      else openList();
      return;
    }

    if (event.key === "Escape" && isOpen) {
      event.preventDefault();
      event.stopPropagation();
      closeList({ restoreFocus: true });
      return;
    }

    if (event.key === "Tab" && isOpen) closeList();
  }

  return (
    <div className="search-field public-select" data-placement={placement} ref={rootRef}>
      <span id={labelId}>{label}</span>
      <div className="public-select__control">
        <button
          aria-activedescendant={isOpen ? optionId(activeIndex) : undefined}
          aria-autocomplete="none"
          aria-controls={listboxId}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-invalid={invalid}
          aria-labelledby={`${labelId} ${valueId}`}
          aria-required={required}
          className="public-select__trigger"
          onClick={() => (isOpen ? closeList({ restoreFocus: true }) : openList())}
          onKeyDown={handleKeyDown}
          ref={triggerRef}
          role="combobox"
          type="button"
        >
          <span className="public-select__value" data-placeholder={!selectedOption} id={valueId}>
            {selectedOption?.label ?? placeholder}
          </span>
          <span aria-hidden="true" className="public-select__chevron">
            ▾
          </span>
        </button>

        {isOpen ? (
          <ul
            aria-labelledby={labelId}
            className="public-select__listbox"
            id={listboxId}
            role="listbox"
            style={{ maxHeight: menuMaxHeight }}
          >
            {options.map((option, index) => {
              const isSelected = option.value === value;
              return (
                <li
                  aria-selected={isSelected}
                  className="public-select__option"
                  data-active={activeIndex === index}
                  data-selected={isSelected}
                  id={optionId(index)}
                  key={option.value}
                  onClick={() => selectOption(index)}
                  onPointerDown={(event) => event.preventDefault()}
                  onPointerEnter={() => setActiveIndex(index)}
                  role="option"
                >
                  {option.label}
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
