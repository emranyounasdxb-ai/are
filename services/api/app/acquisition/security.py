from __future__ import annotations

import ipaddress
import socket
import time
from datetime import UTC, datetime
from email.message import Message
from threading import Lock
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from app.acquisition.contracts import FetchResult

USER_AGENT = "AREOfficialSourceAcquisition/1.0"
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "application/json",
    "application/ld+json",
    "application/pdf",
    "application/xml",
    "text/xml",
}


class AcquisitionSecurityError(ValueError):
    pass


SocketAddress = tuple[str, int] | tuple[str, int, int, int]


class Resolver(Protocol):
    def __call__(
        self, host: str, port: int, *, type: socket.SocketKind
    ) -> list[tuple[int, int, int, str, SocketAddress]]: ...


def _resolve(
    host: str, port: int, *, type: socket.SocketKind
) -> list[tuple[int, int, int, str, SocketAddress]]:
    return [
        (int(family), int(kind), protocol, canonical, cast(SocketAddress, address))
        for family, kind, protocol, canonical, address in socket.getaddrinfo(host, port, type=type)
    ]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> None:
        return None


def normalize_host(host: str) -> str:
    return host.rstrip(".").encode("idna").decode("ascii").lower()


def host_is_allowed(host: str, allowed_domains: tuple[str, ...]) -> bool:
    normalized = normalize_host(host)
    return any(
        normalized == normalize_host(domain) or normalized.endswith(f".{normalize_host(domain)}")
        for domain in allowed_domains
    )


def validate_public_url(
    url: str,
    allowed_domains: tuple[str, ...],
    *,
    resolver: Resolver = _resolve,
) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise AcquisitionSecurityError("Only credential-free HTTPS URLs are allowed.")
    if parsed.port not in (None, 443):
        raise AcquisitionSecurityError("Only the standard HTTPS port is allowed.")
    if not host_is_allowed(parsed.hostname, allowed_domains):
        raise AcquisitionSecurityError("The destination is outside the adapter allowlist.")
    try:
        addresses = resolver(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise AcquisitionSecurityError("The official hostname could not be resolved.") from exc
    if not addresses:
        raise AcquisitionSecurityError("The official hostname has no address.")
    for item in addresses:
        address = ipaddress.ip_address(str(item[4][0]))
        if not address.is_global:
            raise AcquisitionSecurityError(
                "Private, local, link-local and metadata IPs are denied."
            )
    return parsed.geturl()


class SecureFetcher:
    def __init__(self, *, timeout_seconds: float = 12, domain_delay_seconds: float = 0.5) -> None:
        self.timeout_seconds = timeout_seconds
        self.domain_delay_seconds = domain_delay_seconds
        self._opener = build_opener(_NoRedirect())
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}
        self._lock = Lock()

    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
        try:
            current = validate_public_url(url, allowed_domains)
            if not self._allowed_by_robots(current, allowed_domains):
                return self._failure(current, "robots_disallowed", "robots.txt disallows this URL.")
            for _ in range(4):
                result, redirect = self._request_once(current, allowed_domains)
                if redirect:
                    current = validate_public_url(urljoin(current, redirect), allowed_domains)
                    if not self._allowed_by_robots(current, allowed_domains):
                        return self._failure(
                            current, "robots_disallowed", "robots.txt disallows the redirect URL."
                        )
                    continue
                return result
            return self._failure(current, "redirect_limit", "The redirect limit was exceeded.")
        except AcquisitionSecurityError as exc:
            return self._failure(url, "security_rejected", str(exc))

    def _allowed_by_robots(self, url: str, allowed_domains: tuple[str, ...]) -> bool:
        parsed = urlsplit(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if parsed.path == "/robots.txt":
            return True
        if origin not in self._robots:
            result, _ = self._request_once(f"{origin}/robots.txt", allowed_domains)
            if result.status == 200 and result.body:
                robots_parser = RobotFileParser()
                robots_parser.set_url(f"{origin}/robots.txt")
                robots_parser.parse(result.body.decode("utf-8", errors="replace").splitlines())
                self._robots[origin] = robots_parser
            else:
                self._robots[origin] = None
        cached_parser = self._robots.get(origin)
        return cached_parser is None or cached_parser.can_fetch(USER_AGENT, url)

    def _request_once(
        self, url: str, allowed_domains: tuple[str, ...]
    ) -> tuple[FetchResult, str | None]:
        validate_public_url(url, allowed_domains)
        host = normalize_host(urlsplit(url).hostname or "")
        self._throttle(host)
        request = Request(  # noqa: S310 -- URL passed strict HTTPS/domain/IP validation above.
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,application/json,"
                    "application/pdf,application/xml;q=0.9"
                ),
            },
        )
        for attempt in range(3):
            try:
                with self._opener.open(request, timeout=self.timeout_seconds) as response:
                    content_type = _content_type(response.headers)
                    if content_type not in ALLOWED_CONTENT_TYPES:
                        return (
                            self._failure(
                                url,
                                "content_type_rejected",
                                f"Unsupported content type: {content_type or 'missing'}.",
                                status=response.status,
                            ),
                            None,
                        )
                    body = response.read(MAX_DOCUMENT_BYTES + 1)
                    if len(body) > MAX_DOCUMENT_BYTES:
                        return (
                            self._failure(
                                url,
                                "response_too_large",
                                "The response exceeded the acquisition size limit.",
                                status=response.status,
                            ),
                            None,
                        )
                    return (
                        FetchResult(
                            url=response.url,
                            status=response.status,
                            retrieved_at=datetime.now(UTC),
                            content_type=content_type,
                            body=body,
                            etag=response.headers.get("ETag"),
                            last_modified=response.headers.get("Last-Modified"),
                        ),
                        None,
                    )
            except HTTPError as exc:
                if exc.code in {301, 302, 303, 307, 308}:
                    return self._failure(
                        url, "redirect", "Redirect response.", status=exc.code
                    ), exc.headers.get("Location")
                if exc.code == 429 or 500 <= exc.code < 600:
                    if attempt < 2:
                        time.sleep(0.5 * (2**attempt))
                        continue
                return self._failure(
                    url,
                    f"http_{exc.code}",
                    "The official source returned an error.",
                    status=exc.code,
                ), None
            except (TimeoutError, URLError, OSError) as exc:
                if attempt < 2:
                    time.sleep(0.5 * (2**attempt))
                    continue
                return self._failure(url, "network_error", type(exc).__name__), None
        return self._failure(url, "network_error", "The request failed."), None

    def _throttle(self, host: str) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_request.get(host, 0)
            if elapsed < self.domain_delay_seconds:
                time.sleep(self.domain_delay_seconds - elapsed)
            self._last_request[host] = time.monotonic()

    @staticmethod
    def _failure(url: str, code: str, message: str, *, status: int | None = None) -> FetchResult:
        return FetchResult(
            url=url,
            status=status,
            retrieved_at=datetime.now(UTC),
            error_code=code,
            error_message=message[:500],
        )


class BatchCachingFetcher:
    """Reuse immutable responses only within one bounded acquisition command."""

    def __init__(self, delegate: SecureFetcher) -> None:
        self.delegate = delegate
        self._cache: dict[tuple[str, tuple[str, ...]], FetchResult] = {}

    def fetch(self, url: str, allowed_domains: tuple[str, ...]) -> FetchResult:
        key = (url, allowed_domains)
        if key not in self._cache:
            self._cache[key] = self.delegate.fetch(url, allowed_domains)
        return self._cache[key]


def _content_type(headers: Message) -> str | None:
    value = headers.get_content_type()
    return value.lower() if value else None
