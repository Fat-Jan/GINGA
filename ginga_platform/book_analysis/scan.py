"""Source scanning helpers for Reference Corpus P0."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from .limits import BookAnalysisLimits, DEFAULT_LIMITS


@dataclass(frozen=True)
class SourceScanResult:
    """Metadata extracted from a source file without analyzing its content."""

    status: str
    path: str
    sha256: str
    input_size_bytes: int
    encoding: str | None
    title: str
    source_kind: str
    text: str | None
    original_mtime: str | None
    errors: tuple[dict[str, str], ...] = ()
    warnings: tuple[dict[str, str], ...] = ()

    def to_source_payload(self) -> dict[str, Any]:
        """Return the manifest `source` payload without decoded text."""

        payload = {
            "path": self.path,
            "sha256": self.sha256,
            "encoding": self.encoding or "",
            "title": self.title,
            "input_size_bytes": self.input_size_bytes,
            "source_kind": self.source_kind,
        }
        if self.original_mtime:
            payload["original_mtime"] = self.original_mtime
        return payload

    def to_dict(self, include_text: bool = False) -> dict[str, Any]:
        """Return a serializable representation.

        Text is omitted by default to avoid accidentally propagating reference
        source content into reports or manifests.
        """

        payload = asdict(self)
        if not include_text:
            payload.pop("text", None)
        return payload


def scan_source_bytes(
    data: bytes,
    *,
    path: str | Path,
    title: str | None = None,
    source_kind: str = "user_file",
    mtime: float | datetime | str | None = None,
    encoding: str | None = None,
    limits: BookAnalysisLimits = DEFAULT_LIMITS,
) -> SourceScanResult:
    """Scan source bytes and decode text for downstream split helpers.

    The function never guesses success after decoding failure: if no configured
    or common encoding can decode the bytes, the returned status is `error` and
    `text` is `None`.
    """

    source_path = str(path)
    digest = sha256(data).hexdigest()
    size = len(data)
    inferred_title = title or _title_from_path(source_path)
    original_mtime = _format_mtime(mtime)

    if size > limits.max_input_size_bytes:
        return SourceScanResult(
            status="error",
            path=source_path,
            sha256=digest,
            input_size_bytes=size,
            encoding=encoding,
            title=inferred_title,
            source_kind=source_kind,
            text=None,
            original_mtime=original_mtime,
            errors=(
                {
                    "code": "input_too_large",
                    "message": f"input size {size} exceeds limit {limits.max_input_size_bytes}",
                },
            ),
        )

    candidates = [encoding] if encoding else ["utf-8", "utf-8-sig", "gb18030", "big5"]
    decode_errors: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        try:
            text = data.decode(candidate)
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{candidate}: {exc.reason}")
            continue
        return SourceScanResult(
            status="ok",
            path=source_path,
            sha256=digest,
            input_size_bytes=size,
            encoding=candidate,
            title=inferred_title,
            source_kind=source_kind,
            text=text,
            original_mtime=original_mtime,
        )

    return SourceScanResult(
        status="error",
        path=source_path,
        sha256=digest,
        input_size_bytes=size,
        encoding=encoding,
        title=inferred_title,
        source_kind=source_kind,
        text=None,
        original_mtime=original_mtime,
        errors=(
            {
                "code": "encoding_error",
                "message": "failed to decode source bytes",
            },
        ),
        warnings=tuple({"code": "decode_attempt", "message": item} for item in decode_errors),
    )


def _title_from_path(path: str) -> str:
    stem = Path(path).stem.strip()
    return stem or "untitled_source"


def _format_mtime(mtime: float | datetime | str | None) -> str | None:
    if mtime is None:
        return None
    if isinstance(mtime, str):
        return mtime
    if isinstance(mtime, datetime):
        value = mtime
    else:
        value = datetime.fromtimestamp(mtime, tz=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
