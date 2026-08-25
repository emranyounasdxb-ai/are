from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

from app.acquisition.contracts import (
    DiscoveryResult,
    FetchResult,
    ManifestCandidate,
    NormalizedEvidence,
    SourceFetcher,
)
from app.acquisition.parser import name_similarity, normalize_evidence, normalize_name, parse_html
from app.acquisition.security import host_is_allowed

ADAPTER_VERSION = "1.0"
STOP_TOKENS = {"at", "by", "the", "phase", "tower", "and"}


@dataclass(frozen=True)
class OfficialSiteAdapter:
    key: str
    developer_name: str
    base_url: str
    allowed_domains: tuple[str, ...]
    canonical_developer_slug: str | None = None
    catalog_paths: tuple[str, ...] = ()
    version: str = ADAPTER_VERSION

    def discover(self, candidate: ManifestCandidate, fetcher: SourceFetcher) -> DiscoveryResult:
        failures: list[str] = []
        urls: set[str] = set()
        origin = f"{urlsplit(self.base_url).scheme}://{urlsplit(self.base_url).netloc}"
        for path in ("/sitemap.xml", "/sitemap_index.xml"):
            result = fetcher.fetch(urljoin(origin, path), self.allowed_domains)
            if result.ok:
                urls.update(_sitemap_urls(result.body, origin, self.allowed_domains, fetcher))
            elif result.error_code:
                failures.append(f"{path}:{result.error_code}")
        for path in self.catalog_paths or ("/",):
            result = fetcher.fetch(urljoin(origin, path), self.allowed_domains)
            if result.ok and result.content_type in {"text/html", "application/xhtml+xml"}:
                parsed = parse_html(result.body, result.url)
                urls.update(
                    value
                    for value in parsed.links
                    if urlsplit(value).hostname
                    and host_is_allowed(urlsplit(value).hostname or "", self.allowed_domains)
                )
            elif result.error_code:
                failures.append(f"{path}:{result.error_code}")
        exact, suggested = _best_url(candidate.project_name, urls)
        if exact:
            return DiscoveryResult(exact, "deterministic", failures=tuple(failures))
        if suggested:
            return DiscoveryResult(
                suggested,
                "fuzzy-suggestion",
                suggested_url=suggested,
                conflict_reason=(
                    "Official URL was a fuzzy suggestion and requires human name review."
                ),
                failures=tuple(failures),
            )
        return DiscoveryResult(None, "not-found", failures=tuple(failures))

    def acquire(
        self, candidate: ManifestCandidate, discovery: DiscoveryResult, fetcher: SourceFetcher
    ) -> tuple[FetchResult, NormalizedEvidence | None]:
        if not discovery.source_url:
            return (
                FetchResult(
                    url=self.base_url,
                    status=None,
                    retrieved_at=datetime.now(UTC),
                    error_code="official_source_not_found",
                    error_message="No matching public official URL was discovered.",
                ),
                None,
            )
        result = fetcher.fetch(discovery.source_url, self.allowed_domains)
        if not result.ok or result.content_type not in {"text/html", "application/xhtml+xml"}:
            return result, None
        parsed = parse_html(result.body, result.url)
        return result, normalize_evidence(
            parsed, candidate, discovery_conflict=discovery.conflict_reason
        )


def _sitemap_urls(
    body: bytes,
    origin: str,
    allowed_domains: tuple[str, ...],
    fetcher: SourceFetcher,
) -> set[str]:
    found = _xml_locations(body)
    urls: set[str] = set()
    nested = [value for value in found if value.lower().endswith(".xml")][:12]
    urls.update(value for value in found if value not in nested)
    for value in nested:
        if not urlsplit(value).hostname or not host_is_allowed(
            urlsplit(value).hostname or "", allowed_domains
        ):
            continue
        result = fetcher.fetch(urljoin(origin, value), allowed_domains)
        if result.ok and result.content_type in {"application/xml", "text/xml"}:
            urls.update(_xml_locations(result.body))
    return urls


def _xml_locations(body: bytes) -> set[str]:
    if len(body) > 8 * 1024 * 1024:
        return set()
    text = body.decode("utf-8", errors="replace")
    return {
        html.unescape(value.strip())
        for value in re.findall(r"<loc\b[^>]*>([^<]+)</loc>", text, flags=re.IGNORECASE)
    }


def _best_url(project_name: str, urls: set[str]) -> tuple[str | None, str | None]:
    target = normalize_name(project_name)
    important = {value for value in target.split() if value not in STOP_TOKENS and len(value) > 2}
    exact: list[str] = []
    fuzzy: list[tuple[float, str]] = []
    for url in urls:
        path = normalize_name(urlsplit(url).path.replace("-", " "))
        if not path or any(value in path for value in ("privacy", "terms", "career", "news")):
            continue
        tokens = set(path.split())
        if target in path or (important and important <= tokens):
            exact.append(url)
            continue
        score = name_similarity(path, project_name)
        if score >= 0.5:
            fuzzy.append((score, url))
    if exact:
        return sorted(exact, key=lambda value: (len(urlsplit(value).path), value))[0], None
    if fuzzy:
        return None, sorted(fuzzy, key=lambda value: (-value[0], len(value[1])))[0][1]
    return None, None


ADAPTERS = {
    item.developer_name.casefold(): item
    for item in (
        OfficialSiteAdapter(
            "emaar",
            "Emaar",
            "https://properties.emaar.com/en/",
            ("emaar.com",),
            "emaar-properties",
            ("/en/properties/",),
        ),
        OfficialSiteAdapter(
            "sobha",
            "Sobha Realty",
            "https://sobharealty.com/",
            ("sobharealty.com",),
            "sobha-realty",
            ("/properties/",),
        ),
        OfficialSiteAdapter(
            "damac",
            "DAMAC",
            "https://www.damacproperties.com/",
            ("damacproperties.com",),
            "damac-properties",
            ("/en/projects/",),
        ),
        OfficialSiteAdapter(
            "binghatti",
            "Binghatti",
            "https://www.binghatti.com/",
            ("binghatti.com",),
            "binghatti",
            ("/projects/",),
        ),
        OfficialSiteAdapter(
            "ellington",
            "Ellington",
            "https://ellingtonproperties.ae/en/",
            ("ellingtonproperties.ae",),
            None,
            ("/en/properties",),
        ),
        OfficialSiteAdapter(
            "meraas", "Meraas", "https://meraas.com/", ("meraas.com",), "meraas", ("/en/projects",)
        ),
        OfficialSiteAdapter(
            "beyond",
            "Beyond",
            "https://beyonddevelopments.ae/",
            ("beyonddevelopments.ae",),
            None,
            ("/projects/",),
        ),
        OfficialSiteAdapter(
            "expo-city",
            "Expo City Dubai",
            "https://www.expocitydubai.com/en/expo-living/",
            ("expocitydubai.com",),
            None,
            ("/en/expo-living/",),
        ),
        OfficialSiteAdapter(
            "nakheel",
            "Nakheel",
            "https://www.nakheel.com/",
            ("nakheel.com",),
            "nakheel",
            ("/en/our-projects",),
        ),
        OfficialSiteAdapter(
            "danube",
            "Danube",
            "https://danubeproperties.com/",
            ("danubeproperties.com",),
            "danube-properties",
            ("/projects/",),
        ),
        OfficialSiteAdapter(
            "azizi",
            "Azizi",
            "https://www.azizidevelopments.com/",
            ("azizidevelopments.com",),
            "azizi-developments",
            ("/projects",),
        ),
        OfficialSiteAdapter(
            "bold",
            "Bold",
            "https://bolddeveloper.com/",
            ("bolddeveloper.com",),
            None,
            ("/projects/",),
        ),
        OfficialSiteAdapter(
            "zaya",
            "Zaya",
            "https://www.zaya.com/projects",
            ("zaya.com", "lunaya.com"),
            None,
            ("/projects",),
        ),
        OfficialSiteAdapter(
            "mr-eight",
            "Mr Eight",
            "https://www.mr8uae.com/",
            ("mr8uae.com", "mr8.ae"),
            None,
            ("/projects",),
        ),
        OfficialSiteAdapter(
            "reportage",
            "Reportage",
            "https://reportagegroup.com/",
            ("reportagegroup.com", "reportageuae.com"),
            "reportage-properties",
            ("/projects/",),
        ),
        OfficialSiteAdapter(
            "aldar",
            "Aldar",
            "https://www.aldar.com/",
            ("aldar.com",),
            "aldar-properties",
            ("/en/explore-aldar/properties",),
        ),
    )
}


def adapter_for(developer: str) -> OfficialSiteAdapter | None:
    return ADAPTERS.get(developer.casefold())
