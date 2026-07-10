#!/usr/bin/env python3
"""Fetch immutable public sources listed in data/source_registry.csv.

The script downloads only rows whose download field is true and whose
local_filename is populated. It records SHA-256, byte size, retrieval time,
and original URL in data/raw/source_manifest.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "source_registry.csv"
DEFAULT_OUTPUT = ROOT / "data" / "raw"
MANIFEST_FIELDS = [
    "source_id",
    "local_path",
    "sha256",
    "size_bytes",
    "retrieved_at_utc",
    "url",
]


@dataclass(frozen=True)
class Source:
    source_id: str
    url: str
    local_filename: str


def is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def read_sources(registry: Path, selected_ids: set[str] | None) -> list[Source]:
    with registry.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    sources: list[Source] = []
    for row in rows:
        if not is_true(row.get("download", "")):
            continue
        source_id = row["source_id"].strip()
        if selected_ids and source_id not in selected_ids:
            continue
        url = row["url"].strip()
        local_filename = row["local_filename"].strip()
        if not url or not local_filename:
            raise ValueError(f"{source_id} is downloadable but lacks URL or filename")
        sources.append(Source(source_id, url, local_filename))

    if selected_ids:
        resolved = {source.source_id for source in sources}
        missing = selected_ids - resolved
        if missing:
            raise ValueError(
                "Requested source IDs are unavailable or not downloadable: "
                + ", ".join(sorted(missing))
            )
    return sources


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(source: Source, output: Path, force: bool) -> dict[str, str | int]:
    destination = output / source.local_filename
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not force:
        raise FileExistsError(
            f"{destination} already exists; use --force only after confirming "
            "that a new source version is intended"
        )

    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "OpenQFuel-Cislunar/0.1 public-research-fetcher"},
    )
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=destination.name + ".",
        suffix=".part",
        dir=destination.parent,
    )
    os.close(file_descriptor)
    temporary = Path(temporary_name)

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as output_handle:
                while chunk := response.read(1024 * 1024):
                    output_handle.write(chunk)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    return {
        "source_id": source.source_id,
        "local_path": str(destination.relative_to(ROOT)),
        "sha256": sha256_file(destination),
        "size_bytes": destination.stat().st_size,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "url": source.url,
    }


def write_manifest(output: Path, new_records: list[dict[str, str | int]]) -> None:
    manifest = output / "source_manifest.csv"
    existing: dict[str, dict[str, str]] = {}
    if manifest.exists():
        with manifest.open(newline="", encoding="utf-8") as handle:
            existing = {
                row["source_id"]: row
                for row in csv.DictReader(handle)
            }

    for record in new_records:
        existing[str(record["source_id"])] = {
            key: str(record[key]) for key in MANIFEST_FIELDS
        }

    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing[key] for key in sorted(existing))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to the public-source registry",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for immutable raw source files",
    )
    parser.add_argument(
        "--id",
        action="append",
        dest="source_ids",
        help="Download one source ID; repeat for multiple IDs",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing local file and update its manifest record",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    selected = set(args.source_ids) if args.source_ids else None
    sources = read_sources(args.registry, selected)
    if not sources:
        print("No downloadable sources matched.")
        return 0

    records = []
    for source in sources:
        record = download(source, args.output, args.force)
        records.append(record)
        print(
            f"{source.source_id}: {record['local_path']} "
            f"({record['size_bytes']} bytes)"
        )
    write_manifest(args.output, records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
