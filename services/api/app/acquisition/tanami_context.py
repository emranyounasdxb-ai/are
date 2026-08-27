"""Project-scoped table evidence; never flatten alternative offers into one plan."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

from app.acquisition.parser import HANDOVER, PROPERTY_TYPES, clean, explicit_size_range


@dataclass(frozen=True)
class ContextTable:
    heading: str
    rows: list[list[str]]


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[ContextTable] = []
        self.stack: list[tuple[str, bool]] = []
        self.heading = ""
        self.heading_parts: list[str] | None = None
        self.rows: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.table_heading = ""
        self.finished = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        blocked = (
            any(item[1] for item in self.stack)
            or tag in {"nav", "aside", "footer", "script", "style", "select"}
            or attrs_map.get("id") == "enq"
            or "modal" in (attrs_map.get("class") or "").split()
        )
        if tag not in {"br", "img", "hr", "input", "meta", "link", "source"}:
            self.stack.append((tag, blocked))
        if blocked or self.finished or not any(item[0] == "main" for item in self.stack):
            return
        if tag in {"h2", "h3", "h4"}:
            self.heading_parts = []
        elif tag == "table":
            self.rows, self.table_heading = [], self.heading
        elif tag == "tr" and self.rows is not None:
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.finished or any(item[1] for item in self.stack):
            return
        if self.heading_parts is not None:
            self.heading_parts.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        blocked = any(item[1] for item in self.stack)
        if not blocked and not self.finished:
            if tag in {"h2", "h3", "h4"} and self.heading_parts is not None:
                self.heading = clean(" ".join(self.heading_parts))
                self.heading_parts = None
                self.finished = bool(
                    re.search(r"more projects|related projects|other projects", self.heading, re.I)
                )
            elif tag in {"td", "th"} and self.cell is not None and self.row is not None:
                self.row.append(clean(" ".join(self.cell)))
                self.cell = None
            elif tag == "tr" and self.row is not None and self.rows is not None:
                self.rows.append(self.row)
                self.row = None
            elif tag == "table" and self.rows is not None:
                self.tables.append(ContextTable(self.table_heading, self.rows))
                self.rows = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def contextual_tables(body: bytes) -> list[ContextTable]:
    parser = _TableParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    return parser.tables


def payment_variants(tables: list[ContextTable]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    for table in tables:
        payment_column: int | None = None
        option = table.heading
        phase = ""
        milestones: list[dict[str, Any]] = []

        def finish(option: str, milestones: list[dict[str, Any]]) -> None:
            if not milestones:
                return
            percentages = [item["percentage"] for item in milestones]
            complete = abs(sum(percentages) - 100) < 0.001
            variants.append(
                {
                    "applicability": option,
                    "raw_source_text": option
                    + " | "
                    + " | ".join(item["source_value"] for item in milestones),
                    "milestones": list(milestones),
                    "percentages": percentages,
                    "is_complete": complete,
                    "requires_review": not complete,
                }
            )

        for row in table.rows:
            cells = [clean(value) for value in row]
            if not any(cells):
                continue
            if len(cells) == 1:
                if re.match(r"option\b", cells[0], re.I):
                    finish(option, milestones)
                    milestones = []
                    option = table.heading + " — " + cells[0]
                    phase = ""
                elif re.search(r"(?:after|post).*handover", cells[0], re.I):
                    phase = "post-handover"
                continue
            header = next(
                (
                    i
                    for i, value in enumerate(cells)
                    if re.fullmatch(r"payment(?:\s*\(%?\))?", value, re.I)
                ),
                None,
            )
            if header is not None and any(
                re.search(r"milestone|installment", c, re.I) for c in cells
            ):
                payment_column = header
                continue
            if payment_column is None or payment_column >= len(cells):
                continue
            match = re.fullmatch(r"(100|\d{1,2}(?:\.\d+)?)\s*%", cells[payment_column])
            if not match:
                continue
            label = " | ".join(cells)
            lowered = label.casefold()
            stage = phase or "other"
            if "post" in lowered and "handover" in lowered:
                stage = "post-handover"
            elif "down payment" in lowered or "booking" in lowered or "reservation" in lowered:
                stage = "booking"
            elif "handover" in lowered or "completion" in lowered:
                stage = "handover"
            elif "construction" in lowered:
                stage = "during-construction"
            milestones.append(
                {
                    "sequence": len(milestones) + 1,
                    "stage": stage,
                    "percentage": float(match.group(1)),
                    "source_value": label,
                }
            )
        finish(option, milestones)
    return variants


def select_unambiguous_plan(variants: list[dict[str, Any]]) -> dict[str, Any] | None:
    """A unit-specific or alternative offer is evidence, not a Project-wide default."""
    if len(variants) != 1:
        return None
    plan = variants[0]
    if re.search(
        r"\b(?:option|bedroom|resident|villa|townhouse|apartment)\b", plan["applicability"], re.I
    ):
        return None
    return plan if plan["is_complete"] else None


def summary_facts(tables: list[ContextTable]) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for table in tables:
        for row in table.rows:
            if len(row) != 2:
                continue
            label, value = row
            key = clean(label).casefold().rstrip(":")
            if key == "property type":
                current = {"property_type": value}
                groups.append(current)
            elif key == "unit type" and current:
                current["unit_type"] = value
            elif key == "size" and current:
                current["source_size"] = value
                low, high, unit = explicit_size_range(value.replace("SQ. FT.", "sqft"))
                if low is not None and high is not None:
                    current.update(minimum=low, maximum=high, unit=unit)
            elif key == "handover":
                match = HANDOVER.search(value)
                if match:
                    facts.update(
                        handover_quarter=(match.group(1) or match.group(4)).upper(),
                        handover_year=int(match.group(2) or match.group(3)),
                        original_handover_value=value,
                    )
                elif re.fullmatch(r"20\d{2}", value):
                    facts.update(handover_year=int(value), original_handover_value=value)
            elif key == "down payment":
                match = re.fullmatch(r"(100|\d{1,2}(?:\.\d+)?)\s*%", value)
                if match:
                    facts["down_payment_percentage"] = float(match.group(1))
    if groups:
        facts["unit_summary_evidence"] = groups
        property_types: set[str] = set()
        bedrooms: set[str] = set()
        unit_types: list[str] = []
        for group in groups:
            for canonical, aliases in PROPERTY_TYPES.items():
                if group["property_type"].casefold() in aliases:
                    property_types.add(canonical)
            value = str(group.get("unit_type", ""))
            if re.search(r"\b(?:studio|bedrooms?|br)\b", value, re.I):
                unit_types.append(value)
                if re.search(r"\bstudio", value, re.I):
                    bedrooms.add("studio")
                # Only the explicit unit cell, never floor-plan icons or unit IDs.
                for low, high in re.findall(r"\b(\d)\s*(?:to|[-–])\s*(\d)\b", value):
                    if int(low) <= int(high):
                        bedrooms.update(str(n) for n in range(int(low), int(high) + 1))
                bedrooms.update(re.findall(r"\b([1-9])(?=\s*(?:,|&|bed|br))", value, re.I))
        if property_types:
            facts["property_types"] = sorted(property_types)
        if bedrooms:
            facts["bedrooms"] = sorted(
                {"6+" if b.isdigit() and int(b) >= 6 else b for b in bedrooms}
            )
        if unit_types:
            facts["unit_types"] = list(dict.fromkeys(unit_types))
        sizes = [group for group in groups if group.get("minimum") is not None]
        if sizes and len(sizes) == len(groups):
            facts.update(
                size_min=min(g["minimum"] for g in sizes),
                size_max=max(g["maximum"] for g in sizes),
                size_unit="sqft",
            )
    return facts


def floor_unit_facts(tables: list[ContextTable]) -> dict[str, Any]:
    """Use only explicitly labelled unit rows, never plan IDs or nearby-project cards."""
    groups = []
    for table in tables:
        header: list[str] = []
        for row in table.rows:
            if "Unit Type" in row and "Sizes" in row and "Type" in row:
                header = row
                continue
            if not header or len(row) != len(header):
                continue
            values = dict(zip(header, row, strict=True))
            if values.get("Category") not in {"Unit Plan", "Unit"}:
                continue
            groups.extend(
                [
                    ["Property Type", values["Type"]],
                    ["Unit Type", values["Unit Type"]],
                    ["Size", values["Sizes"]],
                ]
            )
    return summary_facts([ContextTable("Exact unit table", groups)])
