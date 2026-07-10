#!/usr/bin/env python3
"""Safely unpack the nested public Artemis II OEM archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "data/raw/artemis2/all-artemis-ii-oem-files.zip"
DEFAULT_OUTPUT = ROOT / "data/raw/artemis2/oem"


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_flat_name(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
        raise ValueError(f"Unsafe or nested archive member: {name!r}")
    return path.name


def write_checked(path: Path, content: bytes, force: bool) -> None:
    if path.exists():
        if path.read_bytes() == content:
            return
        if not force:
            raise FileExistsError(f"Refusing to replace differing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def extract_nested_archive(
    archive: Path, output: Path, force: bool = False
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with ZipFile(archive) as outer:
        nested_names = sorted(
            name for name in outer.namelist() if not name.endswith("/")
        )
        if not nested_names or any(not name.lower().endswith(".zip") for name in nested_names):
            raise ValueError("The outer archive must contain only nested ZIP products")

        for nested_name in nested_names:
            safe_nested_name = safe_flat_name(nested_name)
            nested_content = outer.read(nested_name)
            nested_path = output / safe_nested_name
            write_checked(nested_path, nested_content, force)

            with ZipFile(io.BytesIO(nested_content)) as nested:
                payload_names = [
                    name for name in nested.namelist() if not name.endswith("/")
                ]
                if len(payload_names) != 1:
                    raise ValueError(
                        f"Expected one ephemeris payload in {nested_name}, found "
                        f"{len(payload_names)}"
                    )
                payload_name = safe_flat_name(payload_names[0])
                payload = nested.read(payload_names[0])
                payload_path = output / "asc" / payload_name
                write_checked(payload_path, payload, force)
                records.append(
                    {
                        "nested_archive": safe_nested_name,
                        "nested_sha256": digest_bytes(nested_content),
                        "payload": payload_name,
                        "payload_sha256": digest_bytes(payload),
                        "payload_size_bytes": len(payload),
                    }
                )
    return records


def write_manifest(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    records = extract_nested_archive(args.archive, args.output, args.force)
    write_manifest(args.output / "nested_manifest.csv", records)
    print(f"Extracted and hashed {len(records)} nested ephemeris products.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
