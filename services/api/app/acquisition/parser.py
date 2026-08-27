from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from app.acquisition.contracts import ManifestCandidate, NormalizedEvidence, ParsedEvidence

SPACE = re.compile(r"\s+")
ARABIC = re.compile(r"[\u0600-\u06ff]")
HANDOVER = re.compile(
    r"\b(Q[1-4])\s*[,\-/ ]*\s*(20\d{2})\b|\b(20\d{2})\s*[,\-/ ]*\s*(Q[1-4])\b", re.I
)
BEDROOM = re.compile(r"\b(studio|[1-6]\+?)\s*(?:bed|bedroom)s?\b", re.I)
PERCENTAGE = re.compile(r"\b(100|\d{1,2}(?:\.\d+)?)\s*%")
PROPERTY_TYPES = {
    "apartment": ("apartment", "apartments"),
    "villa": ("villa", "villas"),
    "townhouse": ("townhouse", "townhouses"),
    "penthouse": ("penthouse", "penthouses"),
    "duplex": ("duplex", "duplexes"),
    "mansion": ("mansion", "mansions"),
    "residential-plot": ("residential plot", "residential plots"),
}
AMENITIES = {
    "Swimming pool": ("swimming pool", "infinity pool"),
    "Gym": ("gym", "fitness centre", "fitness center"),
    "Spa": ("spa",),
    "Children's play area": ("children's play area", "kids play area", "children play area"),
    "Clubhouse": ("clubhouse",),
    "Cinema": ("cinema",),
    "Beach access": ("beach access", "private beach"),
    "Landscaped gardens": ("landscaped gardens", "landscape gardens"),
    "Parking": ("parking",),
    "Concierge": ("concierge",),
    "Security": ("24-hour security", "24/7 security"),
}


class EvidenceHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.text_parts: list[str] = []
        self.links: set[str] = set()
        self.media: set[str] = set()
        self._ignored = 0
        self._title = False
        self._heading = False
        self._heading_parts: list[str] = []
        self._json_ld = False
        self._json_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"script", "style", "noscript", "template", "select", "nav", "footer"}:
            if tag == "script" and (values.get("type") or "").lower() == "application/ld+json":
                self._json_ld = True
                self._json_parts = []
            else:
                self._ignored += 1
        if tag == "title":
            self._title = True
        if tag in {"h1", "h2"}:
            self._heading = True
            self._heading_parts = []
        href = values.get("href")
        if href:
            self.links.add(urljoin(self.base_url, href))
        for key in (
            "src",
            "data-src",
            "data-lazy-src",
            "data-background-image",
            "data-bg",
        ):
            value = values.get(key)
            if value:
                self.media.add(urljoin(self.base_url, value))
        srcset = values.get("srcset") or values.get("data-srcset")
        if srcset:
            for candidate in srcset.split(","):
                value = candidate.strip().split()[0] if candidate.strip() else ""
                if value:
                    self.media.add(urljoin(self.base_url, value))
        meta_key = values.get("property") or values.get("name")
        if tag == "meta" and meta_key in {"og:image", "og:video", "twitter:image"}:
            value = values.get("content")
            if value:
                self.media.add(urljoin(self.base_url, value))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "template", "select", "nav", "footer"}:
            if tag == "script" and self._json_ld:
                self._consume_json_ld()
                self._json_ld = False
            elif self._ignored:
                self._ignored -= 1
        if tag == "title":
            self._title = False
        if tag in {"h1", "h2"} and self._heading:
            value = clean(" ".join(self._heading_parts))
            if value:
                self.headings.append(value)
            self._heading = False

    def handle_data(self, data: str) -> None:
        if self._json_ld:
            self._json_parts.append(data)
            return
        if self._ignored:
            return
        value = clean(data)
        if not value:
            return
        self.text_parts.append(value)
        if self._title:
            self.title_parts.append(value)
        if self._heading:
            self._heading_parts.append(value)

    def _consume_json_ld(self) -> None:
        try:
            payload = json.loads("".join(self._json_parts))
        except (json.JSONDecodeError, ValueError):
            return
        stack = [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key, value in item.items():
                    if key in {"name", "description", "addressLocality"} and isinstance(value, str):
                        self.text_parts.append(clean(value))
                    elif key in {"image", "contentUrl", "thumbnailUrl"} and isinstance(value, str):
                        self.media.add(urljoin(self.base_url, value))
                    else:
                        stack.append(value)
            elif isinstance(item, list):
                stack.extend(item)


def parse_html(body: bytes, source_url: str) -> ParsedEvidence:
    parser = EvidenceHTMLParser(source_url)
    parser.feed(body.decode("utf-8", errors="replace"))
    text = clean(" ".join(parser.text_parts))
    return ParsedEvidence(
        title=clean(" ".join(parser.title_parts)) or None,
        headings=tuple(dict.fromkeys(parser.headings)),
        text=text[:250_000],
        links=tuple(sorted(parser.links)),
        media_urls=tuple(sorted(parser.media)),
        has_arabic=bool(ARABIC.search(text)),
    )


def normalize_evidence(
    parsed: ParsedEvidence, candidate: ManifestCandidate, *, discovery_conflict: str | None = None
) -> NormalizedEvidence:
    # Tanami appends other developments after this explicit catalogue heading.
    # Those cards are discovery links, not facts about the current Project.
    text = re.split(
        r"\b(?:More|Other|Related) Projects(?: of)?\b", parsed.text, maxsplit=1, flags=re.I
    )[0]
    lowered = text.casefold()
    headings = [value for value in parsed.headings if value]
    extracted_name = next(
        (value for value in headings if name_similarity(value, candidate.project_name) >= 0.6),
        parsed.title,
    )
    conflicts: list[str] = []
    if discovery_conflict:
        conflicts.append(discovery_conflict)
    if extracted_name and names_genuinely_disagree(candidate.project_name, extracted_name):
        conflicts.append(
            "Official source name differs: "
            f"manifest '{candidate.project_name}' versus source '{extracted_name}'."
        )
    developer = candidate.developer if candidate.developer.casefold() in lowered else None
    area = candidate.area if candidate.area.casefold() in lowered else None
    property_types = [
        key
        for key, variants in PROPERTY_TYPES.items()
        if any(re.search(rf"\b{re.escape(value)}\b", lowered) for value in variants)
    ]
    bedrooms = list(dict.fromkeys(match.group(1).lower() for match in BEDROOM.finditer(text)))
    if re.search(r"\bstudios?\b", lowered) and "studio" not in bedrooms:
        bedrooms.insert(0, "studio")
    handover_match = HANDOVER.search(text)
    handover_quarter = None
    handover_year = None
    original_handover = None
    if handover_match:
        handover_quarter = (handover_match.group(1) or handover_match.group(4)).upper()
        handover_year = int(handover_match.group(2) or handover_match.group(3))
        original_handover = handover_match.group(0)
    availability = explicit_availability(lowered)
    construction = explicit_construction(lowered)
    payment = payment_plan(text)
    size_min, size_max, size_unit = explicit_size_range(text)
    down_payment = explicit_down_payment(text)
    amenities = explicit_amenities(lowered)
    source_extracted: dict[str, object] = {
        "project_name": extracted_name,
        "developer": developer,
        "area": area,
        "property_types": property_types,
        "bedrooms": bedrooms,
        "handover_quarter": handover_quarter,
        "handover_year": handover_year,
        "original_handover_value": original_handover,
        "payment_plan": payment,
        "availability_status": availability,
        "construction_status": construction,
        "size_min": size_min,
        "size_max": size_max,
        "size_unit": size_unit,
        "down_payment_percentage": down_payment,
        "amenities": amenities,
        "arabic_content_available": parsed.has_arabic,
    }
    missing = tuple(
        key
        for key, value in source_extracted.items()
        if key != "arabic_content_available" and value in (None, [], {})
    )
    return NormalizedEvidence(
        source_extracted=source_extracted,
        normalized_proposal=dict(source_extracted),
        missing_fields=missing,
        conflicts=tuple(conflicts),
        media_urls=parsed.media_urls,
    )


def normalize_name(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def names_genuinely_disagree(manifest_name: str, source_name: str) -> bool:
    ignored = {
        "amenities",
        "and",
        "at",
        "by",
        "features",
        "floor",
        "location",
        "map",
        "master",
        "payment",
        "plan",
        "plans",
        "summary",
        "the",
        "developer",
        "development",
        "properties",
        "property",
        "rak",
    }
    synonyms = {
        "residences": "residence",
        "townhome": "townhouse",
        "townhomes": "townhouse",
        "townhouses": "townhouse",
    }
    manifest = {
        synonyms.get(token, token)
        for token in normalize_name(manifest_name).split()
        if token not in ignored
    }
    source = {
        synonyms.get(token, token)
        for token in normalize_name(source_name).split()
        if token not in ignored
    }
    if not manifest or not source:
        return False
    return not (manifest <= source or source <= manifest)


def name_similarity(left: str, right: str) -> float:
    left_tokens = set(normalize_name(left).split())
    right_tokens = set(normalize_name(right).split())
    if not left_tokens or not right_tokens:
        return 0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def explicit_availability(text: str) -> str | None:
    if re.search(r"\bsold[ -]?out\b", text):
        return "sold-out"
    if re.search(r"\blimited availability\b|\blimited units? available\b", text):
        return "limited-availability"
    # An enquiry CTA is also present on completed/sold-out developments and
    # cannot establish a commercial availability state.
    if re.search(r"\bcoming soon\b", text):
        return "coming-soon"
    if re.search(r"\bavailable now\b|\bcurrently available\b", text):
        return "available"
    return None


def explicit_construction(text: str) -> str | None:
    for pattern, value in (
        (r"\bnear completion\b", "near-completion"),
        (r"\bunder construction\b", "under-construction"),
        (r"\bconstruction completed\b|\bready for handover\b", "completed"),
        (r"\bpre[ -]?launch\b", "pre-launch"),
        (r"\bnow launched\b|\bnew launch\b", "launched"),
        (r"\bon hold\b", "on-hold"),
    ):
        if re.search(pattern, text):
            return value
    return None


def explicit_size_range(text: str) -> tuple[float | None, float | None, str | None]:
    ranges = re.findall(
        r"\b([\d,]{3,10}(?:\.\d+)?)\s*"
        r"(?:(?:sq\.?\s*ft|sqft|square feet)\s*)?"
        r"(?:to|[-–])\s*([\d,]{3,10}(?:\.\d+)?)"
        r"\s*(?:sq\.?\s*ft|sqft|square feet)\b",
        text,
        flags=re.IGNORECASE,
    )
    if ranges:
        values = [
            (float(low.replace(",", "")), float(high.replace(",", ""))) for low, high in ranges
        ]
        return min(value[0] for value in values), max(value[1] for value in values), "sqft"
    single = re.findall(
        r"\b(?:from|starting from)\s+([\d,]{3,10}(?:\.\d+)?)\s*"
        r"(?:sq\.?\s*ft|sqft|square feet)\b",
        text,
        flags=re.IGNORECASE,
    )
    if single:
        minimum = min(float(value.replace(",", "")) for value in single)
        return minimum, None, "sqft"
    return None, None, None


def explicit_down_payment(text: str) -> float | None:
    for pattern in (
        r"\b(100|\d{1,2}(?:\.\d+)?)\s*%\s*(?:initial\s+)?down payment\b",
        r"\bdown payment\s*(?:of|:|-)?\s*(100|\d{1,2}(?:\.\d+)?)\s*%",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def explicit_amenities(lowered_text: str) -> list[str]:
    if "amenit" not in lowered_text and "facilit" not in lowered_text:
        return []
    return [
        label
        for label, variants in AMENITIES.items()
        if any(re.search(rf"\b{re.escape(value)}\b", lowered_text) for value in variants)
    ]


def payment_plan(text: str) -> dict[str, object] | None:
    lowered = text.casefold()
    index = lowered.find("payment plan")
    if index < 0:
        return None
    raw = clean(text[index : index + 700])
    matches = list(PERCENTAGE.finditer(raw))
    percentages = [float(match.group(1)) for match in matches]
    milestones = []
    for sequence, match in enumerate(matches):
        context_end = (
            matches[sequence + 1].start() if sequence + 1 < len(matches) else match.end() + 100
        )
        context = raw[match.start() : min(len(raw), context_end)]
        milestones.append(
            {
                "sequence": sequence,
                "stage": _payment_stage(context.casefold()),
                "percentage": float(match.group(1)),
                "source_value": clean(context),
            }
        )
    return {
        "raw_source_text": raw,
        "percentages": percentages,
        "milestones": milestones,
        "is_complete": bool(percentages) and sum(percentages) == 100,
        "requires_review": bool(percentages) and sum(percentages) != 100,
    }


def _payment_stage(context: str) -> str:
    if "post-handover" in context or "post handover" in context:
        return "post-handover"
    if "booking" in context or "reservation" in context:
        return "booking"
    if "during construction" in context or "construction" in context:
        return "during-construction"
    if "handover" in context or "completion" in context:
        return "handover"
    return "other"


def clean(value: str) -> str:
    return SPACE.sub(" ", value).strip()
