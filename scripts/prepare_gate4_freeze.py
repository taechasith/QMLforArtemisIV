#!/usr/bin/env python3
"""Generate or verify the manifest-only Gate 4 freeze package."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openqfuel.gate4 import (  # noqa: E402
    assert_no_final_payloads,
    manifest_counts,
    read_csv,
    write_freeze_artifacts,
)


CONFIG = ROOT / "configs/phase1_benchmark.yaml"
WINDOWS = ROOT / "data/processed/artemis2/validation_windows.csv"
OUTPUT = ROOT / "data/processed/simulator"


def _artifact_names() -> tuple[str, ...]:
    return (
        "scenario_manifest.csv",
        "final_test_manifest.csv",
        "seed_manifest.csv",
        "tuning_manifest.csv",
        "scenario_schema.json",
        "gate4_freeze_checksums.csv",
    )


def generate(output: Path) -> None:
    assert_no_final_payloads(ROOT / "data/locked/phase1")
    write_freeze_artifacts(CONFIG, WINDOWS, output)


def check() -> None:
    with tempfile.TemporaryDirectory() as directory:
        candidate = Path(directory)
        generate(candidate)
        failures = []
        for name in _artifact_names():
            tracked = OUTPUT / name
            generated = candidate / name
            if not tracked.exists():
                failures.append(
                    f"missing tracked artifact: {tracked.relative_to(ROOT)}"
                )
            elif tracked.read_bytes() != generated.read_bytes():
                failures.append(f"stale tracked artifact: {tracked.relative_to(ROOT)}")
        if failures:
            raise RuntimeError("\n".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify tracked manifests without modifying the workspace",
    )
    args = parser.parse_args()
    if args.check:
        check()
        print("Gate 4 freeze artifacts are deterministic and current.")
        return

    generate(OUTPUT)
    counts = manifest_counts(read_csv(OUTPUT / "scenario_manifest.csv"))
    total = sum(counts.values())
    print(f"Defined {total} manifest-only scenarios: {counts}")
    print("Final-test feature and label payloads remain ungenerated and locked.")


if __name__ == "__main__":
    main()
