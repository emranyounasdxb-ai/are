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
    aliases: tuple[str, ...] = ()

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
            return DiscoveryResult(
                exact,
                "deterministic",
                failures=tuple(failures),
                localized_urls=_localized_exact_urls(candidate.project_name, urls, exact),
            )
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
    exact: list[str] = []
    fuzzy: list[tuple[float, str]] = []
    for url in urls:
        path = normalize_name(urlsplit(url).path.replace("-", " "))
        if not path or any(value in path for value in ("privacy", "terms", "career", "news")):
            continue
        if official_url_matches_project(project_name, url):
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


def _localized_exact_urls(project_name: str, urls: set[str], primary: str) -> tuple[str, ...]:
    """Keep at most one exact English and one exact Arabic official Project URL."""
    matches = [url for url in urls if official_url_matches_project(project_name, url)]
    english = sorted(
        (url for url in matches if "/ar/" not in urlsplit(url).path.casefold()),
        key=lambda value: (len(urlsplit(value).path), value),
    )
    arabic = sorted(
        (url for url in matches if "/ar/" in urlsplit(url).path.casefold()),
        key=lambda value: (len(urlsplit(value).path), value),
    )
    return tuple(dict.fromkeys([primary, *(english[:1]), *(arabic[:1])]))


def official_url_matches_project(project_name: str, url: str) -> bool:
    """Require every meaningful Project token, including phase numbers, in the URL."""
    project_identity = re.split(r"\s+by\s+", project_name, maxsplit=1, flags=re.IGNORECASE)[0]
    target_tokens = normalize_name(project_identity).split()
    important = {
        value
        for value in target_tokens
        if value not in STOP_TOKENS and (len(value) > 2 or value.isdigit())
    }
    path = normalize_name(urlsplit(url).path.replace("-", " "))
    path_tokens = set(path.split())
    excluded_sections = {"blog", "career", "media", "news", "press", "privacy", "terms"}
    return bool(important) and not (path_tokens & excluded_sections) and important <= path_tokens


OFFICIAL_ADAPTERS = (
    OfficialSiteAdapter(
        "arada",
        "ARADA Developer",
        "https://www.arada.com/en/properties/",
        ("arada.com",),
        None,
        ("/en/properties/",),
        aliases=("Arada", "ARADA"),
    ),
    OfficialSiteAdapter(
        "ajmal-makan",
        "Ajmal Makan",
        "https://ajmalmakan.com/",
        ("ajmalmakan.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "alef-group",
        "Alef Group",
        "https://www.alefgroup.ae/",
        ("alefgroup.ae",),
        None,
        ("/", "/projects/"),
    ),
    OfficialSiteAdapter(
        "diamond-developers",
        "Diamond Developer",
        "https://www.sharjahsustainablecity.ae/",
        ("sharjahsustainablecity.ae",),
        None,
        ("/",),
        aliases=("Diamond Developers",),
    ),
    OfficialSiteAdapter(
        "eagle-hills",
        "Eagle Hills",
        "https://eaglehills.com/eagle-hills-uae-projects/",
        ("eaglehills.com",),
        None,
        ("/eagle-hills-uae-projects/", "/our-projects/"),
    ),
    OfficialSiteAdapter(
        "ifa-hotels-resorts",
        "IFA Hotel & Resorts",
        "https://www.ifahotelsresorts.com/en",
        ("ifahotelsresorts.com",),
        None,
        ("/en",),
        aliases=("IFA Hotels & Resorts",),
    ),
    OfficialSiteAdapter(
        "madain-properties",
        "Mada'in Properties",
        "https://madain.com/",
        ("madain.com",),
        None,
        ("/",),
        aliases=("Mada’in Properties",),
    ),
    OfficialSiteAdapter(
        "majid-al-futtaim",
        "Majid Al Futtaim",
        "https://communities.majidalfuttaim.com/en",
        ("majidalfuttaim.com",),
        None,
        ("/en",),
    ),
    OfficialSiteAdapter(
        "sharjah-holding",
        "Sharjah Holding",
        "https://sharjahholding.ae/",
        ("sharjahholding.ae",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "shoumous-properties",
        "Shoumous Properties",
        "https://www.shoumous.com/",
        ("shoumous.com",),
        None,
        ("/", "/the-community/"),
    ),
    OfficialSiteAdapter(
        "shurooq",
        "Shurooq",
        "https://shurooq.gov.ae/",
        ("shurooq.gov.ae",),
        None,
        ("/", "/portfolio/"),
    ),
    OfficialSiteAdapter(
        "tiger-group",
        "Tiger Group",
        "https://www.tigergroup.ae/Home/",
        ("tigergroup.ae",),
        None,
        ("/Home/", "/Projects/SearchProjects"),
    ),
    OfficialSiteAdapter(
        "tilal-properties",
        "Tilal Properties",
        "https://www.tilalproperties.com/",
        ("tilalproperties.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "emaar",
        "Emaar",
        "https://properties.emaar.com/en/",
        ("emaar.com",),
        "emaar-properties",
        ("/en/properties/",),
        aliases=("Emaar Properties",),
    ),
    OfficialSiteAdapter(
        "sobha",
        "Sobha Realty",
        "https://sobharealty.com/",
        ("sobharealty.com",),
        "sobha-realty",
        ("/properties/",),
        aliases=("Sobha Group", "Sobha", "شوبا العقارية", "مجموعة شوبا"),
    ),
    OfficialSiteAdapter(
        "damac",
        "DAMAC",
        "https://www.damacproperties.com/",
        ("damacproperties.com",),
        "damac-properties",
        ("/en/projects/",),
        aliases=("Damac Properties",),
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
        aliases=("Ellington Properties",),
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
        aliases=("Aldar Properties",),
    ),
    OfficialSiteAdapter(
        "rak-properties",
        "RAK Properties",
        "https://www.rakproperties.ae/our-properties/",
        ("rakproperties.ae",),
        None,
        ("/our-properties/",),
    ),
    OfficialSiteAdapter(
        "al-hamra",
        "Al Hamra Group",
        "https://alhamra.ae/en/",
        ("alhamra.ae",),
        None,
        ("/en/",),
        aliases=("Al Hamra",),
    ),
    OfficialSiteAdapter(
        "bnw",
        "BnW Developments",
        "https://bnw.ae/en/projects/",
        ("bnw.ae", "bnwdevelopments.ae", "bnw-projects.com"),
        None,
        ("/en/projects/",),
    ),
    OfficialSiteAdapter(
        "cledor",
        "Cledor Development",
        "https://cledor.com/",
        ("cledor.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "lapis",
        "Lapis Properties",
        "https://lapisproperties.com/",
        ("lapisproperties.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "dubai-investments",
        "Dubai Investments",
        "https://dirc.ae/",
        ("dirc.ae", "dubaiinvestments.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "ardee",
        "Ardee Developments",
        "https://www.ardee.ae/",
        ("ardee.ae",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "topero",
        "Topero Properties",
        "https://fortunebayresidences.com/",
        ("fortunebayresidences.com", "toperoproperties.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "mira",
        "Mira Developments",
        "https://www.miradevelopments.ae/",
        ("miradevelopments.ae", "mira-coral-bay.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "range-rak",
        "Range RAK Development",
        "https://rangerak.ae/",
        ("rangerak.ae", "rangedevelopmentsgroup.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "wow-resorts",
        "Wow Resorts",
        "https://www.wowresorts.com/",
        ("wowresorts.com", "jwalmarjanisland.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "the-luxe",
        "The Luxe Developers",
        "https://theluxedevelopers.ae/",
        ("theluxedevelopers.ae",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "arte",
        "ARTE Developments",
        "https://lamer-byeliesaab.com/",
        ("lamer-byeliesaab.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "major",
        "Major Developers",
        "https://majordevelopers.com/",
        ("majordevelopers.com", "majordevelopments.ae"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "marjan",
        "Marjan Developer",
        "https://marjan.ae/",
        ("marjan.ae",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "source-of-fate",
        "Source of Fate Properties",
        "https://www.sourceoffate.com/",
        ("sourceoffate.com", "sof-miraggio.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "durar",
        "Durar Properties",
        "https://www.durargroup.com/",
        ("durargroup.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "deca",
        "Deca Properties",
        "https://deca-properties.com/",
        ("deca-properties.com",),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "lacasa-living",
        "Lacasa Living",
        "https://lacasaliving.ae/",
        ("lacasaliving.ae",),
        None,
        ("/ola-residences/",),
    ),
    OfficialSiteAdapter(
        "pantheon",
        "Pantheon Development",
        "https://pantheondevelopment.ae/",
        ("pantheondevelopment.ae",),
        None,
        ("/projects/",),
    ),
    OfficialSiteAdapter(
        "richmind",
        "Richmind Development",
        "https://richmind.com/projects/",
        ("richmind.com", "oystra.richmind.com"),
        None,
        ("/projects/",),
    ),
    OfficialSiteAdapter(
        "tissoli",
        "Tissoli luxury Developments",
        "https://www.tissoli.com/properties/",
        ("tissoli.com", "palazzo-tissoli.com"),
        None,
        ("/properties/",),
    ),
    OfficialSiteAdapter(
        "uniestate",
        "Uniestate Properties",
        "https://uniestate.com/project/playa-viva/",
        ("uniestate.com",),
        None,
        ("/project/playa-viva/",),
        aliases=("Uniestate Properties",),
    ),
    OfficialSiteAdapter(
        "wow-red",
        "Wow Red",
        "https://www.wowred.ae/",
        ("wowred.ae", "wowresorts.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "dar-global",
        "Dar Global",
        "https://darglobal.co.uk/",
        ("darglobal.co.uk", "the-astera.com"),
        None,
        ("/",),
    ),
    OfficialSiteAdapter(
        "almal",
        "Almal Real Estate",
        "https://almal-investments.com/",
        ("almal-investments.com",),
        None,
        ("/",),
    ),
)


def _adapter_registry() -> dict[str, OfficialSiteAdapter]:
    registry: dict[str, OfficialSiteAdapter] = {}
    for item in OFFICIAL_ADAPTERS:
        for identity in (item.developer_name, item.key, *item.aliases):
            normalized = normalize_name(identity)
            existing = registry.get(normalized)
            if existing is not None and existing != item:
                raise RuntimeError(f"Duplicate official Developer alias: {identity}.")
            registry[normalized] = item
    return registry


ADAPTERS = _adapter_registry()


def adapter_for(developer: str) -> OfficialSiteAdapter | None:
    """Resolve only an exact approved Developer name or private alias."""
    return ADAPTERS.get(normalize_name(developer))
