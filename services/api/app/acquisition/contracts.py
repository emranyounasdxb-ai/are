from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class ManifestCandidate:
    row_id: int
    project_name: str
    developer: str
    area: str


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int | None
    retrieved_at: datetime
    content_type: str | None = None
    body: bytes = b""
    etag: str | None = None
    last_modified: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300 and bool(self.body)


@dataclass(frozen=True)
class DiscoveryResult:
    source_url: str | None
    match_kind: str
    suggested_url: str | None = None
    conflict_reason: str | None = None
    failures: tuple[str, ...] = ()
    localized_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedEvidence:
    title: str | None
    headings: tuple[str, ...]
    text: str
    links: tuple[str, ...]
    media_urls: tuple[str, ...]
    has_arabic: bool


@dataclass(frozen=True)
class NormalizedEvidence:
    source_extracted: dict[str, object]
    normalized_proposal: dict[str, object]
    missing_fields: tuple[str, ...]
    conflicts: tuple[str, ...]
    media_urls: tuple[str, ...] = field(default_factory=tuple)


class SourceFetcher(Protocol):
    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult: ...


class SourceAdapter(Protocol):
    key: str
    version: str
    developer_name: str
    canonical_developer_slug: str | None
    allowed_domains: tuple[str, ...]

    def discover(self, candidate: ManifestCandidate, fetcher: SourceFetcher) -> DiscoveryResult: ...

    def acquire(
        self, candidate: ManifestCandidate, discovery: DiscoveryResult, fetcher: SourceFetcher
    ) -> tuple[FetchResult, NormalizedEvidence | None]: ...
