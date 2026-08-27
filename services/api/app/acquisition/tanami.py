"""Reusable, bounded Tanami Project acquisition boundary.

Only owner-approved exact Project URLs or an explicitly approved city listing
enter this adapter. It may follow a small set of same-project document links,
but it never follows related-project cards.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.acquisition.adapters import adapter_for, official_url_matches_project
from app.acquisition.contracts import (
    FetchResult,
    ManifestCandidate,
    NormalizedEvidence,
    SourceFetcher,
)
from app.acquisition.parser import clean, normalize_evidence, normalize_name, parse_html
from app.acquisition.reconciliation import reconcile_candidate_quality, source_disagreement
from app.acquisition.security import BatchCachingFetcher, SecureFetcher, host_is_allowed
from app.acquisition.tanami_context import (
    contextual_tables,
    payment_variants,
    select_unambiguous_plan,
    summary_facts,
)
from app.config import Settings, get_settings
from app.models import (
    AreaAlias,
    AreaCommunity,
    Developer,
    DeveloperTranslation,
    DeveloperVerificationStatus,
    EditorialApprovalStatus,
    ImportReviewStatus,
    MediaRightsStatus,
    ProjectImportBatch,
    ProjectImportCandidate,
    ProjectImportEditorialDraft,
    ProjectImportMedia,
    ProjectMediaCategory,
    ProjectProcessingStatus,
    ProjectSourceSnapshot,
    ProjectSourceType,
    PublicationStatus,
    UAEEmirate,
    User,
)
from app.storage import PrivateStorage

TANAMI_ADAPTER_KEY = "tanami-explicit-project-list"
TANAMI_ADAPTER_VERSION = "2.1"
TANAMI_DOCUMENT_DOMAINS = ("tanamiproperties.com",)
TANAMI_MEDIA_DOMAINS = ("tanamiproperties.com", "manage.tanamiproperties.com")
SHARJAH_LISTING_URL = "https://www.tanamiproperties.com/Offplan-Projects-in-Sharjah"
TANAMI_CITY_PROJECT_ENDPOINT = (
    "https://www.tanamiproperties.com/CityProjectlist.aspx/GetProjectListbyCity"
)
SHARJAH_CITY_ID = "114"
CITY_PAGE_ROWS = 10
MAX_CITY_LISTING_PAGES = 25
SHARJAH_AREA_AR = {
    "Al Mamsha Raseel": "الممشى رسيل",
    "Al Mamzar": "الممزر",
    "Al Zahia": "الزاهية",
    "Aljada": "الجادة",
    "Maryam Island": "جزيرة مريم",
    "Masaar": "مسار",
    "Masaar 2": "مسار 2",
    "Masaar 3": "مسار 3",
    "Naseej District": "حي نسيج",
    "Sharjah": "الشارقة",
    "Sharjah Waterfront City": "مدينة الشارقة للواجهات المائية",
    "Tilal City": "مدينة تلال",
}
SHARJAH_DEVELOPER_AR = {
    "ARADA Developer": "أرادَ",
    "Ajmal Makan": "أجمل مكان",
    "Alef Group": "مجموعة ألف",
    "Diamond Developer": "دايموند ديفلوبرز",
    "Eagle Hills": "إيجل هيلز",
    "Emaar Properties": "إعمار العقارية",
    "IFA Hotel & Resorts": "إيفا للفنادق والمنتجعات",
    "Mada'in Properties": "مدائن العقارية",
    "Majid Al Futtaim": "ماجد الفطيم",
    "Sharjah Holding": "الشارقة القابضة",
    "Shoumous Properties": "شموس العقارية",
    "Shurooq": "شروق",
    "Tiger Group": "مجموعة تايجر",
    "Tilal Properties": "تلال العقارية",
}
AMENITY_AR = {
    "Swimming pool": "مسبح",
    "Gym": "صالة رياضية",
    "Spa": "منتجع صحي",
    "Children's play area": "منطقة لعب للأطفال",
    "Clubhouse": "نادي اجتماعي",
    "Cinema": "سينما",
    "Beach access": "وصول إلى الشاطئ",
    "Landscaped gardens": "حدائق منسقة",
    "Parking": "مواقف سيارات",
    "Concierge": "خدمة الكونسيرج",
    "Security": "خدمات أمن",
}
PROJECT_PATH = re.compile(r"^/Projects/([A-Za-z0-9][A-Za-z0-9-]*)$")
SAME_PROJECT_SECTIONS = frozenset(
    {
        "amenities",
        "features",
        "floor-plan",
        "floor-plans",
        "gallery",
        "location",
        "master-plan",
        "overview",
        "payment-plan",
    }
)
REJECTED_CONTENT_TOKENS = frozenset(
    {
        "agent",
        "amenitiesicon",
        "avatar",
        "contact",
        "connectivity/",
        "currency",
        "bitcoin",
        "favicon",
        "facebook",
        "icon",
        "instagram",
        "linkedin",
        "logo",
        "placeholder",
        "projects/images/fpimage/",
        "projects/img/",
        "qr",
        "related",
        "snapchat",
        "social",
        "spinner",
        "slider1",
        "tiktok",
        "tracking",
        "twitter",
        "whatsapp",
        "/x.",
        "youtube",
        "content/images/slider",
    }
)

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".avif")
SAME_PROJECT_SECTION_KEYS = frozenset(value.replace("-", "") for value in SAME_PROJECT_SECTIONS)


@dataclass(frozen=True)
class TanamiIdentity:
    project_name: str
    developer_name: str | None
    area_name: str | None


@dataclass(frozen=True)
class TanamiDocumentSet:
    primary_url: str
    results: tuple[FetchResult, ...]
    normalized: NormalizedEvidence
    identity: TanamiIdentity
    media: tuple[tuple[str, ProjectMediaCategory], ...]


@dataclass(frozen=True)
class MediaDiscovery:
    media: tuple[tuple[str, ProjectMediaCategory], ...]
    excluded_count: int
    duplicate_count: int
    visible_gallery_count: int


@dataclass(frozen=True)
class TanamiCityDiscovery:
    urls: tuple[str, ...]
    projects: tuple[TanamiListingProject, ...]
    total_reported: int
    rows_seen: int
    pages_fetched: int
    duplicate_count: int
    listing_content_hash: str
    retrieved_at: datetime


@dataclass(frozen=True)
class TanamiListingProject:
    url: str
    project_name: str
    developer_name: str
    area_name: str


class _HiddenInputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "input":
            return
        values = dict(attrs)
        identifier = values.get("id")
        value = values.get("value")
        if identifier and value is not None:
            self.values[identifier] = value


def _city_listing_payload(page: int) -> dict[str, object]:
    return {
        "iPageIndex": str(page),
        "iPageRows": str(CITY_PAGE_ROWS),
        "strSearch": "",
        "strOrderBy": "",
        "strMinPrice": "",
        "strMaxPrice": "",
        "strCity": SHARJAH_CITY_ID,
        "strCommunity": "",
        "strPropertyType": "",
        "strProjectStage": "",
        "strDevelopers": "",
        "strAccommodation": "",
        "strHandover": "",
        "strMinSize": "",
        "strMaxSize": "",
        "strDPMinPrice": "",
        "strDPMaxPrice": "",
    }


async def discover_sharjah_project_urls(
    *, fetcher: SecureFetcher | None = None
) -> TanamiCityDiscovery:
    """Enumerate every exact Project URL from the bounded Sharjah listing."""
    source_fetcher = fetcher or SecureFetcher()
    landing = await asyncio.to_thread(
        source_fetcher.fetch, SHARJAH_LISTING_URL, TANAMI_DOCUMENT_DOMAINS
    )
    if not landing.ok or landing.content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError(landing.error_message or "The Sharjah Project listing was unavailable.")
    parser = _HiddenInputParser()
    parser.feed(landing.body.decode("utf-8", errors="replace"))
    if parser.values.get("hdnCity") != SHARJAH_CITY_ID:
        raise ValueError("The approved listing no longer resolves to the locked Sharjah city ID.")
    try:
        rows_per_page = int(parser.values["hdnProjPageRows"])
        total = int(parser.values["hdnProjRecordCount"])
    except (KeyError, ValueError) as exc:
        raise ValueError("The Sharjah listing did not expose bounded pagination metadata.") from exc
    if rows_per_page != CITY_PAGE_ROWS or total < 1:
        raise ValueError("The Sharjah listing pagination contract changed unexpectedly.")
    page_count = math.ceil(total / rows_per_page)
    if page_count > MAX_CITY_LISTING_PAGES:
        raise ValueError("The Sharjah listing exceeds the approved bounded pagination limit.")
    rows_seen = 0
    discovered: list[TanamiListingProject] = []
    reported_totals: set[int] = set()
    for page in range(1, page_count + 1):
        response = await asyncio.to_thread(
            source_fetcher.post_json,
            TANAMI_CITY_PROJECT_ENDPOINT,
            TANAMI_DOCUMENT_DOMAINS,
            _city_listing_payload(page),
            referer=SHARJAH_LISTING_URL,
        )
        if not response.ok or response.content_type not in {
            "application/json",
            "application/ld+json",
        }:
            raise ValueError(
                response.error_message or f"Sharjah listing page {page} was unavailable."
            )
        try:
            envelope = json.loads(response.body)
            payload = envelope["d"]
            records = payload["lstprojlist"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Sharjah listing page {page} returned an invalid payload.") from exc
        if not isinstance(records, list) or not records:
            raise ValueError(f"Sharjah listing page {page} returned no Project records.")
        if len(records) > rows_per_page:
            raise ValueError(f"Sharjah listing page {page} exceeded its row limit.")
        for record in records:
            if not isinstance(record, dict) or not all(
                isinstance(record.get(key), str)
                for key in ("ProjURL", "ProjName", "DevName", "ComName")
            ):
                raise ValueError(f"Sharjah listing page {page} exposed an invalid Project URL.")
            discovered.append(
                TanamiListingProject(
                    url=urljoin(SHARJAH_LISTING_URL, str(record["ProjURL"])),
                    project_name=clean(str(record["ProjName"])),
                    developer_name=clean(str(record["DevName"])),
                    area_name=clean(str(record["ComName"])),
                )
            )
            try:
                reported_totals.add(int(record["ProjCount"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("A Sharjah listing row omitted its catalogue total.") from exc
        rows_seen += len(records)
    if reported_totals != {total} or rows_seen != total:
        raise ValueError("Sharjah listing totals changed during bounded pagination.")
    normalized = normalize_project_urls([item.url for item in discovered])
    projects_by_url = {item.url: item for item in discovered}
    if len(projects_by_url) != len(normalized):
        raise ValueError("The Sharjah listing contains duplicate exact Project URLs.")
    return TanamiCityDiscovery(
        urls=normalized,
        projects=tuple(projects_by_url[url] for url in normalized),
        total_reported=total,
        rows_seen=rows_seen,
        pages_fetched=page_count,
        duplicate_count=rows_seen - len(normalized),
        listing_content_hash=hashlib.sha256(landing.body).hexdigest(),
        retrieved_at=landing.retrieved_at,
    )


def normalize_project_urls(urls: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Validate and deterministically deduplicate explicit Tanami Project URLs."""
    if not urls:
        raise ValueError("At least one owner-approved Tanami Project URL is required.")
    normalized: dict[str, None] = {}
    for value in urls:
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or parsed.query
            or parsed.fragment
            or not host_is_allowed(parsed.hostname, TANAMI_DOCUMENT_DOMAINS)
            or not PROJECT_PATH.fullmatch(parsed.path.rstrip("/"))
        ):
            raise ValueError(
                "Every input must be an exact credential-free HTTPS Tanami Project URL."
            )
        canonical = urlunsplit(
            ("https", "www.tanamiproperties.com", parsed.path.rstrip("/"), "", "")
        )
        normalized[canonical] = None
    return tuple(sorted(normalized))


def same_project_urls(primary_url: str, body: bytes) -> tuple[str, ...]:
    """Return only bounded same-project documents linked by the exact Project page."""
    primary = normalize_project_urls([primary_url])[0]
    primary_path = urlsplit(primary).path
    parsed = parse_html(body, primary)
    accepted: set[str] = set()
    for value in parsed.links:
        split = urlsplit(value)
        path = split.path.rstrip("/")
        if (
            split.scheme != "https"
            or not split.hostname
            or not host_is_allowed(split.hostname, TANAMI_DOCUMENT_DOMAINS)
            or split.query
            or path == primary_path
            or not (path.startswith(f"{primary_path}/") or path.startswith(f"{primary_path}-"))
        ):
            continue
        remainder = path[len(primary_path) :].lstrip("/-").casefold()
        section_key = remainder.replace("-", "")
        if section_key in SAME_PROJECT_SECTION_KEYS:
            accepted.add(urlunsplit(("https", "www.tanamiproperties.com", path, "", "")))
    return tuple(sorted(accepted))


async def acquire_project_documents(
    url: str,
    *,
    fetcher: SourceFetcher | None = None,
) -> TanamiDocumentSet:
    """Fetch one exact Project and its explicitly linked same-project documents."""
    primary_url = normalize_project_urls([url])[0]
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    primary = await asyncio.to_thread(source_fetcher.fetch, primary_url, TANAMI_DOCUMENT_DOMAINS)
    if not primary.ok or primary.content_type not in {"text/html", "application/xhtml+xml"}:
        raise ValueError(primary.error_message or "The exact Tanami Project page was unavailable.")
    results = [primary]
    for linked_url in same_project_urls(primary_url, primary.body):
        result = await asyncio.to_thread(source_fetcher.fetch, linked_url, TANAMI_DOCUMENT_DOMAINS)
        if result.ok and result.content_type in {"text/html", "application/xhtml+xml"}:
            results.append(result)
    identity = extract_identity(primary)
    manifest = ManifestCandidate(
        row_id=1,
        project_name=identity.project_name,
        developer=identity.developer_name or "Developer not confirmed",
        area=identity.area_name or "Area not confirmed",
    )
    combined = _combined_normalized(results, manifest)
    media = exact_project_media(primary_url, tuple(results))
    return TanamiDocumentSet(primary_url, tuple(results), combined, identity, media)


def extract_identity(result: FetchResult) -> TanamiIdentity:
    page = parse_html(result.body, result.url)
    breadcrumb_name, breadcrumb_developer, breadcrumb_area = _breadcrumb_identity(result.body)
    project_name = breadcrumb_name or next((value for value in page.headings if value), page.title)
    if not project_name:
        raise ValueError("The exact Tanami page did not expose a Project identity.")
    project_name = re.split(r"\s+[|–—]\s+", project_name, maxsplit=1)[0].strip()
    developer = breadcrumb_developer or _label_value(page.text, ("developer", "developed by"))
    area = breadcrumb_area or _label_value(page.text, ("area", "location", "community"))
    return TanamiIdentity(project_name, developer, area)


class _JsonLdIdentityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.collecting = False
        self.parts: list[str] = []
        self.payloads: list[object] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and (dict(attrs).get("type") or "").casefold() == "application/ld+json":
            self.collecting = True
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.collecting:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "script" or not self.collecting:
            return
        try:
            self.payloads.append(json.loads("".join(self.parts)))
        except (json.JSONDecodeError, ValueError):
            pass
        self.collecting = False
        self.parts = []


def _breadcrumb_identity(body: bytes) -> tuple[str | None, str | None, str | None]:
    parser = _JsonLdIdentityParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    stack = list(parser.payloads)
    while stack:
        value = stack.pop()
        if isinstance(value, list):
            stack.extend(value)
            continue
        if not isinstance(value, dict):
            continue
        if value.get("@type") != "BreadcrumbList":
            stack.extend(value.values())
            continue
        project = developer = area = None
        items = value.get("itemListElement")
        if not isinstance(items, list):
            continue
        for entry in items:
            item = entry.get("item") if isinstance(entry, dict) else None
            if not isinstance(item, dict):
                continue
            name = clean(str(item.get("name") or "")) or None
            item_type = str(item.get("@type") or "").casefold()
            if item_type == "brand":
                developer = name
            elif item_type == "place":
                area = name
            elif item_type in {"house", "apartment", "product", "residence"}:
                project = name
        if project or developer or area:
            return project, developer, area
    return None, None, None


def _label_value(text: str, labels: tuple[str, ...]) -> str | None:
    next_label = (
        "Developer|Developed by|Area|Location|Community|Property Type|Bedrooms|Handover|"
        "Payment Plan"
    )
    for label in labels:
        match = re.search(
            rf"\b{re.escape(label)}\s*[:\-]\s*([^|•\n]{{2,100}}?)"
            rf"(?=\s+(?:{next_label})\s*[:\-]|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            return clean(match.group(1)).rstrip(".,")
    return None


def _combined_normalized(
    results: list[FetchResult], manifest: ManifestCandidate
) -> NormalizedEvidence:
    normalized = [normalize_evidence(parse_html(item.body, item.url), manifest) for item in results]
    structured = [_tanami_structured_facts(result) for result in results]
    extracted: dict[str, object] = {}
    proposal: dict[str, object] = {}
    conflicts: list[str] = []
    disagreement_evidence: list[dict[str, object]] = []
    media: set[str] = set()
    for item in normalized:
        for key, value in item.source_extracted.items():
            if value not in (None, [], {}, "") and key not in extracted:
                extracted[key] = value
                proposal[key] = value
        # Tanami uses SEO-expanded headings and short marketing names on different
        # views of the same exact Project URL. Preserve those titles in evidence,
        # but do not misclassify cosmetic identity variants as source conflicts.
        conflicts.extend(
            conflict
            for conflict in item.conflicts
            if not conflict.startswith("Official source name differs:")
        )
        media.update(item.media_urls)
    for structured_item in structured:
        for key, value in structured_item.items():
            if value not in (None, [], {}, "") and key not in extracted:
                extracted[key] = value
                proposal[key] = value
    # Explicit summary cells outrank keyword matches in surrounding prose.
    summary = summary_facts(contextual_tables(results[0].body)) if results else {}
    extracted.update(summary)
    proposal.update(summary)
    variants = [
        {**plan, "source_url": result.url}
        for result in results
        for plan in payment_variants(contextual_tables(result.body))
    ]
    if variants:
        extracted["payment_plan_variants"] = variants
        selected_plan = select_unambiguous_plan(variants)
        if selected_plan:
            selected_plan["requires_review"] = True
        extracted["payment_plan"] = selected_plan
        proposal["payment_plan"] = selected_plan
    scoped_payment_urls = set()
    for result in results:
        offers = payment_variants(contextual_tables(result.body))
        bookings = {
            milestone["percentage"]
            for offer in offers
            for milestone in offer["milestones"]
            if milestone["stage"] == "booking"
        }
        if (
            len(offers) > 1
            and all(offer["is_complete"] for offer in offers)
            and proposal.get("down_payment_percentage") in bookings
        ):
            scoped_payment_urls.add(result.url)
    for key in (
        "handover_quarter",
        "handover_year",
        "availability_status",
        "construction_status",
        "down_payment_percentage",
    ):
        observations = [
            (result, item, structured_item)
            for result, item, structured_item in zip(results, normalized, structured, strict=True)
            if not (key == "down_payment_percentage" and result.url in scoped_payment_urls)
        ]
        # A down payment inside a labelled offer is not a contradictory
        # Project-wide value. Keep every offer privately for applicability review.
        values = [
            value
            for _, item, structured_item in observations
            for value in (item.source_extracted.get(key), structured_item.get(key))
        ]
        disagreement = source_disagreement(key, values)
        if disagreement:
            conflicts.append(disagreement)
            retained: list[dict[str, object]] = []
            for result, normalized_item, structured_item in observations:
                for value in (
                    normalized_item.source_extracted.get(key),
                    structured_item.get(key),
                ):
                    if value in (None, "", [], {}) or value == "not-confirmed":
                        continue
                    evidence_item = {"value": value, "source_url": result.url}
                    if evidence_item not in retained:
                        retained.append(evidence_item)
            disagreement_evidence.append(
                {
                    "field": key,
                    "sources": retained,
                    "requires_human_review": True,
                }
            )
    if disagreement_evidence:
        extracted["_source_disagreement_evidence"] = disagreement_evidence
    extracted.setdefault("project_name", manifest.project_name)
    proposal.setdefault("project_name", manifest.project_name)
    missing = tuple(
        key
        for key in (
            "developer",
            "area",
            "property_types",
            "unit_types",
            "bedrooms",
            "size_min",
            "size_max",
            "down_payment_percentage",
            "handover_quarter",
            "handover_year",
            "payment_plan",
            "availability_status",
            "construction_status",
            "amenities",
        )
        if proposal.get(key) in (None, [], {}, "")
    )
    return NormalizedEvidence(
        source_extracted=extracted,
        normalized_proposal=proposal,
        missing_fields=missing,
        conflicts=tuple(dict.fromkeys(conflicts)),
        media_urls=tuple(sorted(media)),
    )


def _tanami_structured_facts(result: FetchResult) -> dict[str, object]:
    source = result.body.decode("utf-8", errors="replace")
    text = parse_html(result.body, result.url).text
    facts: dict[str, object] = {}

    unit_values = re.findall(r"Unit\s*type\s*:\s*(.{1,140}?)\s+Size\s*:", text, re.IGNORECASE)
    if unit_values:
        facts["unit_types"] = list(dict.fromkeys(clean(value) for value in unit_values))

    ranges: list[dict[str, object]] = []
    minimum_sizes: list[float] = []
    maximum_sizes: list[float] = []
    for low, high in re.findall(
        r"Size\s*:\s*([\d,.]+)\s+to\s+([\d,.]+)\s+Sq\s*Ft", text, re.IGNORECASE
    ):
        minimum = float(low.replace(",", ""))
        maximum = float(high.replace(",", ""))
        minimum_sizes.append(minimum)
        maximum_sizes.append(maximum)
        ranges.append(
            {
                "minimum": minimum,
                "maximum": maximum,
                "unit": "sqft",
            }
        )
    if ranges:
        facts["size_ranges"] = ranges
        facts["size_min"] = min(minimum_sizes)
        facts["size_max"] = max(maximum_sizes)
        facts["size_unit"] = "sqft"

    down_payment = re.search(r"Down\s+Payment\s*:\s*(\d{1,3}(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if down_payment:
        facts["down_payment_percentage"] = float(down_payment.group(1))

    amenities = []
    for value in re.findall(
        r"class=['\"][^'\"]*\bfeatures\b[^'\"]*['\"][\s\S]{0,900}?"
        r"<h3[^>]*>([\s\S]*?)</h3>",
        source,
        re.IGNORECASE,
    ):
        label = clean(html.unescape(re.sub(r"<[^>]+>", " ", value)))
        if label and label.casefold() not in {"feature & amenities", "features & amenities"}:
            amenities.append(label)
    if amenities:
        facts["amenities"] = list(dict.fromkeys(amenities))

    lowered_url = result.url.casefold()
    facts["overview_evidence_present"] = bool(
        re.search(r"<h3[^>]*>\s*<span>\s*Overview\s*</span>", source, re.IGNORECASE)
    )
    if "floorplans" in lowered_url:
        facts["floor_plans_present"] = True
    if "masterplan" in lowered_url:
        facts["master_plan_present"] = True
    if lowered_url.endswith("-location"):
        facts["location_map_present"] = True
    if re.search(r"\bRas\s+Al\s+Khaimah\b", text, re.IGNORECASE):
        facts["emirate"] = "RAS_AL_KHAIMAH"
    return facts


class _ContextualMediaParser(HTMLParser):
    def __init__(self, base_url: str, primary_path: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.primary_path = primary_path
        self.anchor_stack: list[str | None] = []
        self.media: dict[str, int] = {}
        self.duplicate_count = 0
        self.script_type: str | None = None
        self.script_parts: list[str] = []

    def _add(self, value: str | None, score: int = 0) -> None:
        if not value:
            return
        absolute = urljoin(self.base_url, value.strip())
        if absolute in self.media:
            self.duplicate_count += 1
        self.media[absolute] = max(score, self.media.get(absolute, score))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a":
            href = values.get("href")
            linked = urljoin(self.base_url, href) if href else None
            self.anchor_stack.append(linked)
            if linked and urlsplit(linked).path.casefold().endswith(IMAGE_SUFFIXES):
                self._add(linked, 60)
        if tag == "script":
            self.script_type = values.get("type")
            self.script_parts = []
        style = values.get("style") or ""
        for match in re.finditer(r"url\((?:['\"])?([^)'\"]+)", style, re.IGNORECASE):
            self._add(match.group(1), 10)
        if tag not in {"img", "source"}:
            return
        linked = next((item for item in reversed(self.anchor_stack) if item), None)
        if linked:
            linked_path = urlsplit(linked).path.rstrip("/")
            if linked_path.startswith("/Projects/") and linked_path != self.primary_path:
                return
        for attribute, score in (
            ("src", 0),
            ("data-src", 25),
            ("data-lazy-src", 25),
            ("data-lazy", 25),
            ("data-original", 40),
            ("data-echo", 35),
        ):
            self._add(values.get(attribute), score)
        for attribute in ("srcset", "data-srcset"):
            for url, width in _srcset_candidates(values.get(attribute)):
                self._add(url, 20 + width)

    def handle_data(self, data: str) -> None:
        if self.script_type != "application/ld+json":
            return
        self.script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchor_stack:
            self.anchor_stack.pop()
        if tag == "script" and self.script_type == "application/ld+json":
            text = "".join(self.script_parts).replace("\\/", "/")
            if self.primary_path in text:
                for match in re.finditer(
                    r"https://[^\s\"']+?(?:\.jpg|\.jpeg|\.png|\.webp|\.avif)(?:\?[^\s\"']*)?",
                    text,
                    re.IGNORECASE,
                ):
                    self._add(match.group(0), 5)
            self.script_type = None
            self.script_parts = []


def _srcset_candidates(value: str | None) -> tuple[tuple[str, int], ...]:
    if not value:
        return ()
    candidates: list[tuple[str, int]] = []
    for item in value.split(","):
        parts = item.strip().split()
        if not parts:
            continue
        descriptor = parts[-1]
        width = (
            int(descriptor[:-1]) if descriptor.endswith("w") and descriptor[:-1].isdigit() else 0
        )
        candidates.append((parts[0], width))
    return tuple(candidates)


def exact_project_media(
    primary_url: str, results: tuple[FetchResult, ...]
) -> tuple[tuple[str, ProjectMediaCategory], ...]:
    """Collect media embedded in exact-project documents, excluding related-card assets."""
    return discover_exact_project_media(primary_url, results).media


def discover_exact_project_media(
    primary_url: str, results: tuple[FetchResult, ...]
) -> MediaDiscovery:
    """Collect the best exact-project variants and bounded discovery diagnostics."""
    primary_path = urlsplit(primary_url).path.rstrip("/")
    selected: dict[str, tuple[str, ProjectMediaCategory, int]] = {}
    excluded: set[str] = set()
    duplicate_count = 0
    visible_gallery: set[str] = set()
    for result in results:
        parser = _ContextualMediaParser(result.url, primary_path)
        parser.feed(result.body.decode("utf-8", errors="replace"))
        duplicate_count += parser.duplicate_count
        section = urlsplit(result.url).path.rstrip("/").rsplit("/", 1)[-1].casefold()
        for url, parser_score in parser.media.items():
            split = urlsplit(url)
            path = split.path.casefold()
            if (
                split.scheme != "https"
                or not split.hostname
                or not host_is_allowed(split.hostname, TANAMI_MEDIA_DOMAINS)
                or not path.endswith(IMAGE_SUFFIXES)
                or any(token in path for token in REJECTED_CONTENT_TOKENS)
            ):
                excluded.add(url)
                continue
            category = _media_category(path, section)
            if "/gallery/" in path and "/floor_image/" not in path:
                visible_gallery.add(_media_identity(url))
            identity = _media_identity(url)
            score = parser_score + _variant_score(path)
            previous = selected.get(identity)
            if (
                previous is None
                or score > previous[2]
                or (
                    previous[1] == ProjectMediaCategory.GALLERY
                    and category != ProjectMediaCategory.GALLERY
                    and url == previous[0]
                )
            ):
                if previous is not None:
                    duplicate_count += 1
                selected[identity] = (url, category, score)
            else:
                duplicate_count += 1
    media = tuple(sorted((url, category) for url, category, _ in selected.values()))
    return MediaDiscovery(media, len(excluded), duplicate_count, len(visible_gallery))


def _media_identity(url: str) -> str:
    split = urlsplit(url)
    path = re.sub(r"/(?:thumb|large|original)/", "/{variant}/", split.path, flags=re.I)
    return urlunsplit(
        (split.scheme.casefold(), split.netloc.casefold(), path.casefold(), split.query, "")
    )


def _variant_score(path: str) -> int:
    if "/original/" in path:
        return 3000
    if "/large/" in path:
        return 2000
    if "/thumb/" in path:
        return -1000
    return 1000


def _media_category(path: str, section: str) -> ProjectMediaCategory:
    if "/banner/" in path or any(token in path for token in ("cover", "hero")):
        return ProjectMediaCategory.COVER
    if "floor_image" in path:
        return ProjectMediaCategory.FLOOR_PLAN
    if "layoutplan" in path or "master-plan" in path:
        return ProjectMediaCategory.MASTER_PLAN
    if "location_map" in path:
        return ProjectMediaCategory.LOCATION_MAP
    if "project_index" in path:
        return ProjectMediaCategory.GALLERY
    value = f"{path} {section}"
    if "floor" in value:
        return ProjectMediaCategory.FLOOR_PLAN
    if "master" in value:
        return ProjectMediaCategory.MASTER_PLAN
    if "location" in value or "map" in value:
        return ProjectMediaCategory.LOCATION_MAP
    if "amenit" in value or "feature" in value:
        return ProjectMediaCategory.AMENITIES
    if "interior" in value:
        return ProjectMediaCategory.INTERIOR
    if "exterior" in value or "facade" in value:
        return ProjectMediaCategory.EXTERIOR
    return ProjectMediaCategory.GALLERY


async def acquire_explicit_batch(
    db: AsyncSession,
    settings: Settings,
    urls: list[str] | tuple[str, ...],
    *,
    fetcher: SourceFetcher | None = None,
    batch_name: str | None = None,
) -> ProjectImportBatch:
    """Acquire an idempotent review batch from an explicit approved URL list."""
    approved_urls = normalize_project_urls(urls)
    digest = hashlib.sha256(json.dumps(approved_urls, separators=(",", ":")).encode()).hexdigest()
    batch = await db.scalar(
        select(ProjectImportBatch)
        .where(ProjectImportBatch.manifest_hash == digest)
        .execution_options(populate_existing=True)
        .options(
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.evidence
            ),
            selectinload(ProjectImportBatch.candidates).selectinload(
                ProjectImportCandidate.staged_media
            ),
        )
    )
    if batch is None:
        batch = ProjectImportBatch(
            name=batch_name or f"Tanami explicit Project batch {digest[:12]}",
            source_reference="explicit-owner-approved-url-list",
            manifest_hash=digest,
            adapter_version=TANAMI_ADAPTER_VERSION,
            total_count=len(approved_urls),
            started_at=datetime.now(UTC),
            candidates=[],
        )
        db.add(batch)
        await db.flush()
    existing = {item.manifest_row_id: item for item in batch.candidates}
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    storage = PrivateStorage(settings)
    for row_id, url in enumerate(approved_urls, start=1):
        documents = await acquire_project_documents(url, fetcher=source_fetcher)
        candidate = existing.get(row_id)
        if candidate is None:
            candidate = ProjectImportCandidate(
                batch_id=batch.id,
                manifest_row_id=row_id,
                raw_source_payload={},
                owner_manifest_values={"approved_project_url": url},
                normalized_project_name=documents.identity.project_name,
                content_hash=hashlib.sha256(url.encode()).hexdigest(),
                review_status=ImportReviewStatus.DISCOVERED,
                processing_status=ProjectProcessingStatus.RAW,
                evidence=[],
                staged_media=[],
                changes=[],
            )
            batch.candidates.append(candidate)
            await db.flush()
            existing[row_id] = candidate
        elif candidate.owner_manifest_values.get("approved_project_url") != url:
            raise ValueError("An existing explicit batch row has a different approved URL.")
        await _update_candidate(db, storage, candidate, documents, source_fetcher)
        await db.commit()
    batch.completed_at = datetime.now(UTC)
    batch.clean_count = 0
    batch.needs_review_count = len(approved_urls)
    batch.failed_count = 0
    await db.commit()
    return batch


async def finalize_sharjah_private_drafts(
    db: AsyncSession,
    batch: ProjectImportBatch,
    *,
    fetcher: SourceFetcher | None = None,
) -> dict[str, object]:
    """Create exact Draft identities, bilingual review copy and private Projects."""
    from app.acquisition.service import match_developer_identity
    from app.import_review import (
        _create_draft,
        draft_eligibility_errors,
        sync_linked_draft_from_candidate,
    )

    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    storage = PrivateStorage(get_settings())
    ambiguous_media_ids = _ambiguous_cross_candidate_media_ids(batch)
    if ambiguous_media_ids:
        from app.acquisition.media_intake import _remove_media_output

        for candidate in batch.candidates:
            for media in candidate.staged_media:
                if media.id in ambiguous_media_ids:
                    _remove_media_output(
                        storage,
                        media,
                        "Identical media was shared across multiple Project candidates.",
                    )
                    media.stage_status = "rejected-unrelated"
                    media.rights_status = MediaRightsStatus.REJECTED
            reconcile_candidate_quality(candidate)
    actor_id = await db.scalar(
        select(User.id).where(User.is_active.is_(True)).order_by(User.created_at)
    )
    if not isinstance(actor_id, UUID):
        raise ValueError("An active Admin user is required to attribute private Draft creation.")
    developers_created = 0
    areas_created = 0
    overviews_created = 0
    drafts_created = 0
    drafts_reused = 0
    unresolved: list[dict[str, object]] = []
    for candidate in batch.candidates:
        source_developer = candidate.owner_manifest_values.get("source_developer")
        source_area = candidate.owner_manifest_values.get("source_area")
        if isinstance(source_developer, str) and source_developer:
            candidate.proposed_developer_id = await match_developer_identity(db, source_developer)
            if not candidate.proposed_developer_id:
                official = adapter_for(source_developer)
                if official:
                    verification = await asyncio.to_thread(
                        source_fetcher.fetch, official.base_url, official.allowed_domains
                    )
                    candidate.acquisition_summary = {
                        **candidate.acquisition_summary,
                        "developer_identity_check": {
                            "official_url": official.base_url,
                            "status": verification.status,
                            "error_code": verification.error_code,
                            "retrieved_at": verification.retrieved_at.isoformat(),
                        },
                    }
                    slug = _canonical_slug(official.key)
                    if await db.scalar(select(Developer.id).where(Developer.slug == slug)):
                        raise ValueError(
                            f"Developer slug collision requires review: {source_developer}."
                        )
                    developer = Developer(
                        slug=slug,
                        legal_name=None,
                        source_name=source_developer,
                        internal_aliases=list(dict.fromkeys([source_developer, *official.aliases])),
                        primary_emirate=UAEEmirate.SHARJAH.value,
                        other_presence=[],
                        selected_projects=[],
                        official_website=official.base_url,
                        source_url=(official.base_url if verification.ok else SHARJAH_LISTING_URL),
                        additional_source_urls=list(
                            dict.fromkeys(
                                [
                                    SHARJAH_LISTING_URL,
                                    official.base_url,
                                ]
                            )
                        ),
                        verification_date=verification.retrieved_at.date(),
                        verification_status=DeveloperVerificationStatus.PENDING,
                        enquiry_types=[],
                        featured=False,
                        display_order=0,
                        status=PublicationStatus.DRAFT,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                    developer.translations = [
                        DeveloperTranslation(
                            locale="en",
                            name=source_developer,
                            description=(
                                "Developer identity retained from the exact Sharjah listing "
                                "and configured Developer-controlled source for private review."
                            ),
                            focus="Sharjah Project identity review.",
                            verification_note=(
                                "Draft identity; publication requires Admin review."
                            ),
                        ),
                        DeveloperTranslation(
                            locale="ar",
                            name=SHARJAH_DEVELOPER_AR.get(source_developer, source_developer),
                            description=(
                                "هوية مطور محفوظة من قائمة الشارقة المطابقة ومصدر المطور "
                                "المحدد لأغراض المراجعة الداخلية."
                            ),
                            focus="مراجعة هوية مشاريع الشارقة.",
                            verification_note="هوية مسودة؛ يتطلب النشر مراجعة الإدارة.",
                        ),
                    ]
                    db.add(developer)
                    await db.flush()
                    candidate.proposed_developer_id = developer.id
                    developers_created += 1
        if isinstance(source_area, str) and source_area:
            candidate.proposed_area_id = await _match_area(db, source_area)
            if not candidate.proposed_area_id:
                if source_area not in SHARJAH_AREA_AR:
                    unresolved.append(
                        {
                            "candidate_id": str(candidate.id),
                            "reason": f"Unverified Sharjah Area identity: {source_area}",
                        }
                    )
                else:
                    slug = _canonical_slug(source_area)
                    if await db.scalar(select(AreaCommunity.id).where(AreaCommunity.slug == slug)):
                        raise ValueError(f"Area slug collision requires review: {source_area}.")
                    area = AreaCommunity(
                        slug=slug,
                        name_en=source_area,
                        name_ar=SHARJAH_AREA_AR[source_area],
                        emirate=UAEEmirate.SHARJAH,
                        status=PublicationStatus.DRAFT,
                    )
                    area.aliases = [
                        AreaAlias(
                            locale="en",
                            alias=source_area,
                            normalized_alias=normalize_name(source_area),
                        )
                    ]
                    db.add(area)
                    await db.flush()
                    candidate.proposed_area_id = area.id
                    areas_created += 1
        if candidate.editorial_draft is None and candidate.normalized_project_name:
            developer_en = str(source_developer or "the source-listed developer")
            area_en = str(source_area or "Sharjah")
            developer_ar = SHARJAH_DEVELOPER_AR.get(developer_en, developer_en)
            area_ar = SHARJAH_AREA_AR.get(area_en, "الشارقة")
            candidate.editorial_draft = ProjectImportEditorialDraft(
                candidate_id=candidate.id,
                overview_en=(
                    f"{candidate.normalized_project_name} is a real estate Project in "
                    f"{area_en}, Sharjah, associated with {developer_en}. This private "
                    "bilingual draft reflects only the source-grounded identity and location "
                    "evidence currently retained; unconfirmed details remain under review."
                ),
                overview_ar=(
                    f"يُعد {candidate.normalized_project_name} مشروعًا عقاريًا في {area_ar} "
                    f"بإمارة الشارقة، ويرتبط بالمطور {developer_ar}. تعكس هذه المسودة الخاصة "
                    "ثنائية اللغة فقط بيانات الهوية والموقع المدعومة بالمصادر المحفوظة حاليًا، "
                    "وتظل التفاصيل غير المؤكدة قيد المراجعة."
                ),
                source_version=candidate.content_hash,
                generated_at=datetime.now(UTC),
                approval_status=EditorialApprovalStatus.NEEDS_REVIEW,
                origin="source-grounded-template",
                fact_input_version="normalized-facts-v1",
                fact_input_hash=hashlib.sha256(
                    json.dumps(
                        candidate.normalized_payload or {},
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest(),
                candidate_version=candidate.review_version,
                import_correlation_id=f"sharjah:{batch.manifest_hash[:16]}",
            )
            overviews_created += 1
        reconcile_candidate_quality(candidate)
        await db.flush()
        if candidate.linked_project_id:
            await sync_linked_draft_from_candidate(db, candidate)
            drafts_reused += 1
            continue
        problems = draft_eligibility_errors(candidate)
        if problems:
            unresolved.append(
                {
                    "candidate_id": str(candidate.id),
                    "project": candidate.normalized_project_name,
                    "reason": "; ".join(problems),
                }
            )
            continue
        project = await _create_draft(db, candidate, actor_id)
        candidate.linked_project_id = project.id
        candidate.review_status = ImportReviewStatus.MERGED
        drafts_created += 1
    await db.commit()
    return {
        "developers_created": developers_created,
        "areas_created": areas_created,
        "overviews_created": overviews_created,
        "drafts_created": drafts_created,
        "drafts_reused": drafts_reused,
        "unresolved": unresolved,
    }


def _ambiguous_cross_candidate_media_ids(
    batch: ProjectImportBatch,
) -> set[UUID]:
    """Reject raster evidence reused by more than one exact Project candidate."""
    grouped: dict[tuple[str, str], list[tuple[UUID, UUID]]] = {}
    for candidate in batch.candidates:
        for media in candidate.staged_media:
            if media.stage_status != "downloaded":
                continue
            grouped.setdefault(("url", media.source_url), []).append((candidate.id, media.id))
            if media.sha256:
                grouped.setdefault(("sha256", media.sha256), []).append((candidate.id, media.id))
    rejected: set[UUID] = set()
    for references in grouped.values():
        if len({candidate_id for candidate_id, _media_id in references}) > 1:
            rejected.update(media_id for _candidate_id, media_id in references)
    return rejected


def _canonical_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if not slug:
        raise ValueError("A verified canonical identity could not produce a stable slug.")
    return slug


async def _update_candidate(
    db: AsyncSession,
    storage: PrivateStorage,
    candidate: ProjectImportCandidate,
    documents: TanamiDocumentSet,
    fetcher: SourceFetcher,
) -> None:
    previous = candidate.normalized_payload or {}
    prior_source_urls = list(candidate.source_urls)
    for result in documents.results:
        await _store_snapshot(
            db, storage, candidate, result, ProjectSourceType.APPROVED_SECONDARY_SOURCE
        )
    identity = documents.identity
    proposal = dict(documents.normalized.normalized_proposal)
    retained_prior_evidence: list[dict[str, object]] = []
    for field_name in (
        "property_types",
        "unit_types",
        "bedrooms",
        "size_min",
        "size_max",
        "size_unit",
        "down_payment_percentage",
        "down_payment_source_value",
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "payment_plan",
        "availability_status",
        "construction_status",
        "amenities",
        "localized_unit_types",
        "localized_amenities",
    ):
        current = proposal.get(field_name)
        retained = previous.get(field_name)
        current_missing = current in (None, "", [], {}) or current == "not-confirmed"
        retained_confirmed = retained not in (None, "", [], {}) and retained != "not-confirmed"
        if current_missing and retained_confirmed:
            proposal[field_name] = retained
            retained_prior_evidence.append(
                {
                    "field": field_name,
                    "source_urls": prior_source_urls,
                    "reason": "Retained stored source evidence omitted by the latest response.",
                }
            )
    human_conflicts: list[str] = []
    for field_name in candidate.human_edited_fields:
        if field_name in previous and previous.get(field_name) != proposal.get(field_name):
            proposal[field_name] = previous[field_name]
            human_conflicts.append(f"Human-edited field preserved during refresh: {field_name}.")
    candidate.owner_manifest_values = {
        "approved_project_url": documents.primary_url,
        "source_project_name": identity.project_name,
        "source_developer": identity.developer_name,
        "source_area": identity.area_name,
    }
    candidate.adapter_key = TANAMI_ADAPTER_KEY
    candidate.adapter_version = TANAMI_ADAPTER_VERSION
    candidate.normalized_project_name = identity.project_name
    candidate.raw_source_payload = {
        "source_extracted": documents.normalized.source_extracted,
        "document_count": len(documents.results),
    }
    candidate.source_urls = [item.url for item in documents.results]
    candidate.extracted_at = max(item.retrieved_at for item in documents.results)
    candidate.last_verified_at = candidate.extracted_at
    candidate.content_hash = hashlib.sha256(
        "".join(hashlib.sha256(item.body).hexdigest() for item in documents.results).encode()
    ).hexdigest()
    conflicts = [*documents.normalized.conflicts, *human_conflicts]
    source_disagreements = documents.normalized.source_extracted.get(
        "_source_disagreement_evidence", []
    )
    official_fact_evidence: list[dict[str, object]] = (
        list(source_disagreements) if isinstance(source_disagreements, list) else []
    )
    retained_media_urls = {url for url, _category in documents.media}
    official_status = "not-resolved"
    candidate.official_source_url = None
    if identity.developer_name:
        official = adapter_for(identity.developer_name)
        if official:
            manifest = ManifestCandidate(
                candidate.manifest_row_id,
                identity.project_name,
                identity.developer_name,
                identity.area_name or "Area not confirmed",
            )
            discovery = await asyncio.to_thread(official.discover, manifest, fetcher)
            if discovery.source_url and discovery.match_kind == "deterministic":
                result, evidence = await asyncio.to_thread(
                    official.acquire,
                    manifest,
                    discovery,
                    fetcher,
                )
                if (
                    result.ok
                    and evidence
                    and official_url_matches_project(manifest.project_name, result.url)
                ):
                    await _store_snapshot(
                        db,
                        storage,
                        candidate,
                        result,
                        ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
                    )
                    candidate.official_source_url = result.url
                    candidate.source_urls = list(
                        dict.fromkeys([*candidate.source_urls, result.url])
                    )
                    await _stage_media(
                        db,
                        candidate,
                        tuple(
                            (url, _media_category(urlsplit(url).path.casefold(), "official"))
                            for url in evidence.media_urls
                        ),
                    )
                    retained_media_urls.update(evidence.media_urls)
                    official_page = parse_html(result.body, result.url)
                    for brochure_url in (
                        value
                        for value in official_page.links
                        if urlsplit(value).path.casefold().endswith(".pdf")
                    ):
                        brochure = await asyncio.to_thread(
                            fetcher.fetch, brochure_url, official.allowed_domains
                        )
                        if brochure.ok:
                            await _store_snapshot(
                                db,
                                storage,
                                candidate,
                                brochure,
                                ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
                            )
                            candidate.source_urls = list(
                                dict.fromkeys([*candidate.source_urls, brochure.url])
                            )
                    for localized_url in discovery.localized_urls:
                        if localized_url == result.url:
                            continue
                        localized = await asyncio.to_thread(
                            fetcher.fetch, localized_url, official.allowed_domains
                        )
                        if localized.ok and official_url_matches_project(
                            manifest.project_name, localized.url
                        ):
                            await _store_snapshot(
                                db,
                                storage,
                                candidate,
                                localized,
                                ProjectSourceType.OFFICIAL_DEVELOPER_PAGE,
                            )
                            candidate.source_urls = list(
                                dict.fromkeys([*candidate.source_urls, localized.url])
                            )
                            await _stage_media(
                                db,
                                candidate,
                                tuple(
                                    (
                                        url,
                                        _media_category(urlsplit(url).path.casefold(), "official"),
                                    )
                                    for url in parse_html(localized.body, localized.url).media_urls
                                ),
                            )
                            retained_media_urls.update(
                                parse_html(localized.body, localized.url).media_urls
                            )
                    official_status = "corroborated"
                    _merge_official_evidence(
                        proposal,
                        evidence.normalized_proposal,
                        conflicts,
                        official_fact_evidence,
                        result.url,
                    )
                elif result.ok:
                    official_status = "redirect-mismatch-needs-review"
                else:
                    official_status = "source-unavailable"
            elif discovery.suggested_url:
                official_status = "fuzzy-suggestion-needs-review"
            else:
                official_status = "source-not-found"
            if official.canonical_developer_slug:
                from app.acquisition.service import match_developer_identity

                candidate.proposed_developer_id = await match_developer_identity(
                    db, official.canonical_developer_slug
                )
        else:
            official_status = "alias-not-registered"
    if identity.area_name:
        candidate.proposed_area_id = await _match_area(db, identity.area_name)
    media_warning = None
    if len(documents.media) < 2:
        media_warning = (
            "Insufficient exact-project media was discovered; retain the candidate for review."
        )
    candidate.validation_errors = [
        {"field": field, "code": "missing_source_evidence"}
        for field in documents.normalized.missing_fields
    ]
    if official_status != "corroborated":
        candidate.validation_errors.append(
            {
                "field": "official_developer_source",
                "code": "official_source_not_found",
                "message": "Official Developer corroboration requires review or recovery.",
            }
        )
    candidate.conflict_reasons = list(dict.fromkeys(conflicts))
    candidate.acquisition_summary = {
        "source_status": "acquired",
        "official_developer_status": official_status,
        "document_count": len(documents.results),
        "media_discovered": len(documents.media),
        "media_warning": media_warning,
        "official_fact_evidence": official_fact_evidence,
        "retained_prior_evidence": retained_prior_evidence,
        "publication": "not-permitted",
    }
    candidate.normalized_payload = dict(proposal)
    candidate.review_status = ImportReviewStatus.NEEDS_REVIEW
    candidate.processing_status = ProjectProcessingStatus.NEEDS_REVIEW
    await _stage_media(db, candidate, documents.media)
    # Imported lazily because media_intake imports this adapter's domain constants.
    from app.acquisition.media_intake import _remove_media_output

    for media in candidate.staged_media:
        hostname = urlsplit(media.source_url).hostname or ""
        if host_is_allowed(hostname, TANAMI_MEDIA_DOMAINS):
            continue
        if media.source_url not in retained_media_urls:
            _remove_media_output(
                storage,
                media,
                "Media was not retained by an exact Project-specific official source.",
            )
            media.stage_status = "rejected-unrelated"
            media.rights_status = MediaRightsStatus.REJECTED
    reconcile_candidate_quality(candidate)


def _merge_official_evidence(
    proposal: dict[str, object],
    official: dict[str, object],
    conflicts: list[str],
    evidence_log: list[dict[str, object]],
    source_url: str,
) -> None:
    for field in (
        "property_types",
        "bedrooms",
        "handover_quarter",
        "handover_year",
        "original_handover_value",
        "availability_status",
        "construction_status",
        "size_min",
        "size_max",
        "size_unit",
        "down_payment_percentage",
        "payment_plan",
        "amenities",
    ):
        value = official.get(field)
        if value in (None, "", [], {}) or value == "not-confirmed":
            continue
        current = proposal.get(field)
        if field in {"property_types", "bedrooms", "amenities"} and isinstance(value, list):
            merged = list(dict.fromkeys([*(current if isinstance(current, list) else []), *value]))
            if merged != current:
                proposal[field] = merged
                evidence_log.append({"field": field, "value": value, "source_url": source_url})
                if field == "amenities":
                    proposal["localized_amenities"] = [
                        {"label_en": label, "label_ar": AMENITY_AR[label]}
                        for label in merged
                        if label in AMENITY_AR
                    ]
            continue
        if field == "original_handover_value":
            if current in (None, ""):
                proposal[field] = value
            continue
        if field == "payment_plan" and isinstance(value, dict):
            official_milestones = value.get("milestones") or []
            current_milestones = (
                current.get("milestones") or [] if isinstance(current, dict) else []
            )
            if not official_milestones:
                continue
            if not current_milestones:
                proposal[field] = value
                evidence_log.append({"field": field, "value": value, "source_url": source_url})
                continue
        if current in (None, "", [], {}) or current == "not-confirmed":
            proposal[field] = value
            evidence_log.append({"field": field, "value": value, "source_url": source_url})
            continue
        disagreement = source_disagreement(field, (current, value))
        if disagreement:
            conflicts.append(disagreement)
            evidence_log.append(
                {
                    "field": field,
                    "retained_value": current,
                    "official_value": value,
                    "source_url": source_url,
                    "requires_human_review": True,
                }
            )


async def refresh_explicit_candidate(
    db: AsyncSession,
    settings: Settings,
    candidate_id: UUID,
    *,
    fetcher: SourceFetcher | None = None,
) -> ProjectImportCandidate:
    """Refresh one existing explicit-list candidate without changing its identity."""
    candidate = await db.scalar(
        select(ProjectImportCandidate)
        .where(ProjectImportCandidate.id == candidate_id)
        .options(
            selectinload(ProjectImportCandidate.evidence),
            selectinload(ProjectImportCandidate.staged_media),
            selectinload(ProjectImportCandidate.editorial_draft),
        )
    )
    if not candidate or candidate.adapter_key != TANAMI_ADAPTER_KEY:
        raise ValueError("Only an existing reusable Tanami candidate may use this refresh.")
    value = candidate.owner_manifest_values.get("approved_project_url")
    if not isinstance(value, str):
        raise ValueError("The candidate has no retained owner-approved Project URL.")
    source_fetcher = fetcher or BatchCachingFetcher(SecureFetcher())
    linked_draft = candidate.linked_project_id is not None
    documents = await acquire_project_documents(value, fetcher=source_fetcher)
    await _update_candidate(db, PrivateStorage(settings), candidate, documents, source_fetcher)
    if linked_draft:
        candidate.review_status = ImportReviewStatus.MERGED
    candidate.human_review_completed = False
    candidate.review_version += 1
    await db.commit()
    return candidate


async def _store_snapshot(
    db: AsyncSession,
    storage: PrivateStorage,
    candidate: ProjectImportCandidate,
    result: FetchResult,
    source_type: ProjectSourceType,
    *,
    rendered: bool = False,
) -> None:
    digest = hashlib.sha256(result.body).hexdigest()
    existing = await db.scalar(
        select(ProjectSourceSnapshot).where(
            ProjectSourceSnapshot.candidate_id == candidate.id,
            ProjectSourceSnapshot.source_url == result.url,
            ProjectSourceSnapshot.content_hash == digest,
        )
    )
    if existing:
        return
    stored = await storage.save_acquisition_snapshot(result.body, result.content_type)
    db.add(
        ProjectSourceSnapshot(
            candidate_id=candidate.id,
            source_url=result.url,
            source_type=source_type,
            http_status=result.status,
            retrieved_at=result.retrieved_at,
            adapter_key=TANAMI_ADAPTER_KEY,
            adapter_version="tanami-rendered-context-v1" if rendered else TANAMI_ADAPTER_VERSION,
            content_type=result.content_type,
            size_bytes=len(result.body),
            etag=result.etag,
            last_modified=result.last_modified,
            content_hash=digest,
            storage_key=stored.storage_key,
            outcome="rendered" if rendered else "extracted",
        )
    )


async def _stage_media(
    db: AsyncSession,
    candidate: ProjectImportCandidate,
    media: tuple[tuple[str, ProjectMediaCategory], ...],
) -> None:
    existing = {item.source_url: item for item in candidate.staged_media}
    eligible = tuple((url, category) for url, category in media if _is_https_raster_candidate(url))
    for order, (url, category) in enumerate(eligible):
        item = existing.get(url)
        if item:
            item.category = category
            item.last_seen_at = datetime.now(UTC)
            continue
        item = ProjectImportMedia(
            candidate_id=candidate.id,
            category=category,
            source_url=url,
            rights_status=MediaRightsStatus.PENDING,
            stage_status="reference-only",
            display_order=order,
            last_seen_at=datetime.now(UTC),
        )
        db.add(item)
        candidate.staged_media.append(item)
        existing[url] = item


def _is_https_raster_candidate(url: str) -> bool:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        return False
    if parts.path.casefold().endswith(IMAGE_SUFFIXES):
        return True
    if parts.path.rstrip("/").casefold().endswith("/image"):
        return any(
            value.casefold().endswith(IMAGE_SUFFIXES)
            for value in parse_qs(parts.query).get("url", [])
        )
    return False


async def _match_area(db: AsyncSession, name: str) -> UUID | None:
    direct = await db.scalar(
        select(AreaCommunity.id).where(func.lower(AreaCommunity.name_en) == name.casefold())
    )
    if direct:
        return direct if isinstance(direct, UUID) else None
    result = await db.scalar(
        select(AreaAlias.area_id).where(AreaAlias.normalized_alias == normalize_name(name))
    )
    return result if isinstance(result, UUID) else None
