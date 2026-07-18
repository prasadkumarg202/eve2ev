"""Async, resumable downloader with dynamic Geofabrik index discovery.

Discovers every ``.osm.pbf`` extract linked from ``source.base_url`` (so new
zone/regional files appear automatically), prefers the configured zone stems,
and falls back to the full-country extract when discovery yields nothing.

Downloads stream to ``<filename>.part`` in ``settings.path("raw")`` with HTTP
Range resume, tenacity-driven exponential-backoff retries, atomic rename on
completion, and optional size/md5 verification.

Public API:
    - :func:`discover_files`
    - :func:`download_item`
    - :func:`download_all`
    - :func:`run_download`
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Settings, get_settings
from .logging_setup import StageTimer, get_console, log
from .models import DownloadItem

__all__ = [
    "DownloadVerificationError",
    "discover_files",
    "download_item",
    "download_all",
    "run_download",
]

_HREF_RE = re.compile(r"""href\s*=\s*["']([^"'#?\s]+)["']""", re.IGNORECASE)
_MD5_RE = re.compile(r"[0-9a-fA-F]{32}")
_USER_AGENT = "osm-india-etl/1.0 (+https://github.com/ev2ev)"
_DEFAULT_FILE_PATTERN = r".*\.osm\.pbf$"


class DownloadVerificationError(RuntimeError):
    """A completed download failed size or md5 verification."""


class _RangeNotSatisfiableError(RuntimeError):
    """Server answered HTTP 416 to our resume Range request."""


# --------------------------------------------------------------------------- #
# Index parsing / discovery
# --------------------------------------------------------------------------- #
def _preference_rank(filename: str, preferred_zones: Sequence[str]) -> int:
    """Rank of *filename* among *preferred_zones* (lower = earlier).

    A file matches a preferred zone when its name starts with the zone stem,
    e.g. ``southern-zone-latest.osm.pbf`` matches ``southern-zone``. Files
    matching no preferred stem rank after all preferred ones.
    """
    for i, stem in enumerate(preferred_zones):
        if filename.startswith(stem):
            return i
    return len(preferred_zones)


def _parse_index(
    html: str,
    base_url: str,
    *,
    file_pattern: str = _DEFAULT_FILE_PATTERN,
    preferred_zones: Sequence[str] = (),
) -> list[DownloadItem]:
    """Parse an HTML directory index into :class:`DownloadItem` entries.

    Every ``href`` whose basename matches *file_pattern* becomes an item with
    an absolute URL (resolved against *base_url*). When the index also links a
    ``<file>.md5`` sidecar, its absolute URL is attached as ``md5_url``.
    Results are ordered with *preferred_zones* stems first (in the given
    order), then all remaining files alphabetically.
    """
    pattern = re.compile(file_pattern)
    pbf_hrefs: dict[str, str] = {}
    md5_hrefs: dict[str, str] = {}

    for href in _HREF_RE.findall(html):
        name = href.rstrip("/").rsplit("/", 1)[-1]
        if not name:
            continue
        if name.endswith(".md5"):
            md5_hrefs.setdefault(name, href)
        elif pattern.match(name):
            pbf_hrefs.setdefault(name, href)

    items: list[DownloadItem] = []
    for name, href in pbf_hrefs.items():
        md5_href = md5_hrefs.get(f"{name}.md5")
        items.append(
            DownloadItem(
                filename=name,
                url=urljoin(base_url, href),
                md5_url=urljoin(base_url, md5_href) if md5_href else None,
            )
        )

    items.sort(key=lambda it: (_preference_rank(it.filename, preferred_zones), it.filename))
    return items


def _fallback_item(country_fallback_url: str) -> DownloadItem:
    """Build the single full-country item used when discovery finds nothing."""
    filename = urlparse(country_fallback_url).path.rsplit("/", 1)[-1]
    return DownloadItem(
        filename=filename,
        url=country_fallback_url,
        md5_url=f"{country_fallback_url}.md5",
    )


async def discover_files(settings: Settings) -> list[DownloadItem]:
    """Discover downloadable ``.osm.pbf`` extracts from the source index.

    Fetches ``settings.source.base_url``, parses every matching link, and
    orders preferred zones first. Falls back to a single item for
    ``settings.source.country_fallback_url`` if nothing is discovered (or the
    index cannot be fetched).
    """
    src = settings.source
    timeout = httpx.Timeout(settings.download.timeout_seconds)
    items: list[DownloadItem] = []
    try:
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": _USER_AGENT}
        ) as client:
            resp = await client.get(src.base_url)
            resp.raise_for_status()
            items = _parse_index(
                resp.text,
                str(resp.url),
                file_pattern=src.file_pattern,
                preferred_zones=src.preferred_zones,
            )
    except httpx.HTTPError as exc:
        log.warning(f"index discovery failed for {src.base_url}: {exc}")

    if not items:
        log.warning(f"no files discovered at {src.base_url}; using country fallback")
        items = [_fallback_item(src.country_fallback_url)]

    log.info(f"discovered {len(items)} file(s): {[it.zone for it in items]}")
    return items


# --------------------------------------------------------------------------- #
# Verification helpers
# --------------------------------------------------------------------------- #
def _file_md5(path: Path, chunk_size: int = 1_048_576) -> str:
    """Compute the hex md5 digest of *path*, streaming in *chunk_size* chunks."""
    digest = hashlib.md5()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_file(
    path: Path,
    *,
    expected_size: int | None,
    expected_md5: str | None,
    chunk_size: int = 1_048_576,
) -> str | None:
    """Verify *path* against the expectations; return a reason string on failure.

    Returns ``None`` when every provided expectation holds (expectations that
    are ``None`` are skipped).
    """
    if not path.exists():
        return "file missing"
    if expected_size is not None:
        actual_size = path.stat().st_size
        if actual_size != expected_size:
            return f"size mismatch (expected {expected_size}, got {actual_size})"
    if expected_md5 is not None:
        actual_md5 = _file_md5(path, chunk_size)
        if actual_md5.lower() != expected_md5.lower():
            return f"md5 mismatch (expected {expected_md5}, got {actual_md5})"
    return None


def _resume_offset(part_path: Path, resume: bool) -> int:
    """Byte offset to resume from: size of the ``.part`` file, or 0."""
    if resume and part_path.exists():
        return part_path.stat().st_size
    return 0


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
async def _fetch_content_length(client: httpx.AsyncClient, url: str) -> int | None:
    """HEAD *url* and return its ``Content-Length``, or ``None`` if unknown."""
    try:
        resp = await client.head(url)
        resp.raise_for_status()
        length = resp.headers.get("Content-Length")
        return int(length) if length else None
    except (httpx.HTTPError, ValueError) as exc:
        log.debug(f"HEAD failed for {url}: {exc}")
        return None


async def _fetch_expected_md5(client: httpx.AsyncClient, item: DownloadItem) -> str | None:
    """Resolve the expected md5 for *item* (inline value or ``.md5`` sidecar)."""
    if item.md5:
        return item.md5.lower()
    if not item.md5_url:
        return None
    try:
        resp = await client.get(item.md5_url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning(f"md5 sidecar unavailable for {item.filename}: {exc}")
        return None
    match = _MD5_RE.search(resp.text)
    if not match:
        log.warning(f"md5 sidecar for {item.filename} contained no digest")
        return None
    item.md5 = match.group(0).lower()
    return item.md5


async def _stream_to_part(
    client: httpx.AsyncClient,
    url: str,
    part: Path,
    offset: int,
    chunk_size: int,
    progress: Progress | None,
    task_id: TaskID | None,
) -> None:
    """Stream *url* into *part*, appending from *offset* when the server honors it.

    Sends ``Range: bytes=<offset>-`` when *offset* > 0. HTTP 206 appends; a
    plain 200 means the server ignored the range, so the file restarts from
    scratch; 416 raises :class:`_RangeNotSatisfiableError` for the caller.
    """
    headers = {"Range": f"bytes={offset}-"} if offset > 0 else {}
    async with client.stream("GET", url, headers=headers) as resp:
        if resp.status_code == 416:
            raise _RangeNotSatisfiableError(f"range bytes={offset}- rejected for {url}")
        if resp.status_code == 200 and offset > 0:
            log.debug(f"server ignored Range for {url}; restarting from 0")
            offset = 0
        resp.raise_for_status()
        if progress is not None and task_id is not None:
            progress.update(task_id, completed=offset)
        mode = "ab" if offset > 0 else "wb"
        with part.open(mode) as fh:
            async for chunk in resp.aiter_bytes(chunk_size):
                fh.write(chunk)
                if progress is not None and task_id is not None:
                    progress.update(task_id, advance=len(chunk))


# --------------------------------------------------------------------------- #
# Public download API
# --------------------------------------------------------------------------- #
async def download_item(
    item: DownloadItem,
    settings: Settings,
    *,
    session: httpx.AsyncClient | None = None,
    progress: Progress | None = None,
) -> Path:
    """Download one extract to ``settings.path("raw")``, resumable and verified.

    Skips the download entirely when the final file already exists and passes
    the enabled size/md5 checks. Otherwise streams to ``<filename>.part``
    (resuming via HTTP Range when ``download.resume``), retries transient
    failures with exponential backoff, atomically renames on completion, and
    verifies the result — raising :class:`DownloadVerificationError` on
    mismatch.
    """
    dl = settings.download
    src = settings.source
    raw_dir = settings.path("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / item.filename
    part = raw_dir / f"{item.filename}.part"

    own_session = session is None
    client = session or httpx.AsyncClient(
        timeout=httpx.Timeout(dl.timeout_seconds),
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT},
    )
    try:
        head_size = await _fetch_content_length(client, item.url)
        if item.size is None:
            item.size = head_size
        expected_md5 = await _fetch_expected_md5(client, item) if src.verify_checksum else None
        expected_size = head_size if src.verify_size else None

        if dest.exists():
            reason = await asyncio.to_thread(
                _verify_file,
                dest,
                expected_size=expected_size,
                expected_md5=expected_md5,
                chunk_size=dl.chunk_size,
            )
            if reason is None:
                log.info(f"{item.filename}: already downloaded and verified; skipping")
                if progress is not None:
                    done = dest.stat().st_size
                    progress.add_task(f"{item.filename} (cached)", total=done, completed=done)
                return dest
            log.warning(f"{item.filename}: existing file invalid ({reason}); re-downloading")
            dest.unlink()

        task_id: TaskID | None = None
        if progress is not None:
            task_id = progress.add_task(item.filename, total=head_size)

        def _log_retry(state: RetryCallState) -> None:
            exc = state.outcome.exception() if state.outcome else None
            log.warning(f"{item.filename}: attempt {state.attempt_number} failed ({exc}); retrying")

        retryer = AsyncRetrying(
            stop=stop_after_attempt(max(1, dl.max_retries)),
            wait=wait_exponential(multiplier=1.0, exp_base=dl.backoff_factor, min=1, max=120),
            retry=retry_if_exception_type((httpx.HTTPError, OSError)),
            before_sleep=_log_retry,
            reraise=True,
        )
        async for attempt in retryer:
            with attempt:
                offset = _resume_offset(part, dl.resume)
                if head_size is not None and offset > head_size:
                    log.warning(f"{item.filename}: partial larger than remote; restarting")
                    part.unlink(missing_ok=True)
                    offset = 0
                if offset == 0:
                    part.unlink(missing_ok=True)
                else:
                    log.info(f"{item.filename}: resuming from byte {offset:,}")
                try:
                    await _stream_to_part(
                        client, item.url, part, offset, dl.chunk_size, progress, task_id
                    )
                except _RangeNotSatisfiableError:
                    if head_size is not None and part.exists() and part.stat().st_size >= head_size:
                        log.info(f"{item.filename}: partial already complete (HTTP 416)")
                    else:
                        log.warning(f"{item.filename}: resume rejected (HTTP 416); restarting")
                        part.unlink(missing_ok=True)
                        await _stream_to_part(
                            client, item.url, part, 0, dl.chunk_size, progress, task_id
                        )

        os.replace(part, dest)

        reason = await asyncio.to_thread(
            _verify_file,
            dest,
            expected_size=expected_size,
            expected_md5=expected_md5,
            chunk_size=dl.chunk_size,
        )
        if reason is not None:
            dest.unlink(missing_ok=True)
            raise DownloadVerificationError(f"{item.filename}: {reason}")

        final_size = dest.stat().st_size
        if progress is not None and task_id is not None:
            progress.update(task_id, total=final_size, completed=final_size)
        log.info(f"{item.filename}: downloaded {final_size:,} bytes -> {dest}")
        return dest
    finally:
        if own_session:
            await client.aclose()


async def download_all(
    settings: Settings,
    items: list[DownloadItem] | None = None,
) -> list[Path]:
    """Download every item concurrently (bounded by ``download.concurrency``).

    Discovers items when *items* is ``None``, shows per-file Rich progress
    bars plus an overall bar, and returns the downloaded paths in item order.
    """
    with StageTimer("download") as timer:
        if items is None:
            items = await discover_files(settings)

        semaphore = asyncio.Semaphore(max(1, settings.download.concurrency))
        columns = (
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.download.timeout_seconds),
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            with Progress(*columns, console=get_console()) as progress:
                overall = progress.add_task(
                    f"[green]overall ({len(items)} files)", total=len(items)
                )

                async def _worker(it: DownloadItem) -> Path:
                    async with semaphore:
                        path = await download_item(it, settings, session=client, progress=progress)
                    progress.advance(overall)
                    timer.add()
                    return path

                paths = list(await asyncio.gather(*(_worker(it) for it in items)))
        return paths


def run_download(settings: Settings | None = None) -> list[Path]:
    """Synchronous entrypoint: discover and download everything, return paths."""
    settings = settings or get_settings()
    return asyncio.run(download_all(settings))
