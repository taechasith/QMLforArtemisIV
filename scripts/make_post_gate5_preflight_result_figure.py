"""Generate RFIG-030 from the source-bound D010 compute-admission result."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
RESULT = (
    ROOT / "data/processed/reporting/post_gate5_compute_preflight_rerun.json"
)
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#1F2937"
BLUE = "#0072B2"
ORANGE = "#D55E00"
GRAY = "#5B6573"
GRID = "#D6DCE2"

CHECK_ORDER = [
    "cpu_core_hours",
    "wall_clock_days",
    "new_artifacts_gib",
    "peak_rss_gib",
    "free_disk_after_artifacts_gib",
]
CHECK_LABELS = {
    "cpu_core_hours": "CPU core-hours",
    "wall_clock_days": "Sequential wall time",
    "new_artifacts_gib": "New artifacts",
    "peak_rss_gib": "Peak process memory",
    "free_disk_after_artifacts_gib": "Free disk after artifacts",
}


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-rfig030-d010-pass-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob(commit: str, relative_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validated_result() -> dict[str, Any]:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    if (
        result.get("decision_id") != "D010"
        or result.get("corrects_decision_id") != "D009"
        or result.get("attempt") != 2
        or result.get("status") != "PASS"
    ):
        raise ValueError("RFIG-030 requires the successful D010 attempt-2 result")
    if result.get("source_hash_scope") != "committed Git blob bytes":
        raise ValueError("RFIG-030 requires committed Git-blob provenance")
    if result["telemetry_validation"].get("status") != "PASS":
        raise ValueError("RFIG-030 requires successful independent telemetry validation")

    integrity = result["integrity"]
    locked_zero_fields = (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
        "statevectors_persisted",
        "kernel_matrices_persisted",
    )
    if any(int(integrity.get(field, -1)) != 0 for field in locked_zero_fields):
        raise ValueError("RFIG-030 source violates a D010 zero-read or zero-run lock")

    source_commit = str(result["source_commit"])
    correction_blob = _git_blob(
        source_commit, "configs/post_gate5_telemetry_correction.yaml"
    )
    correction = yaml.safe_load(correction_blob.decode("utf-8"))
    source_paths = correction["source_binding"]
    for key, expected in result["source_hashes"].items():
        actual = hashlib.sha256(
            _git_blob(source_commit, str(source_paths[key]))
        ).hexdigest()
        if actual != expected:
            raise ValueError(f"RFIG-030 source hash mismatch: {key}")

    base = result["base_preflight_contract"]
    if not (
        base["current_git_blob_sha256"]
        == base["pinned_git_blob_sha256"]
        == result["source_hashes"]["base_preflight_config"]
    ):
        raise ValueError("RFIG-030 D009 base-contract binding is inconsistent")

    checks = result["admission"]["checks"]
    if set(checks) != set(CHECK_ORDER) or result["admission"]["status"] != "PASS":
        raise ValueError("RFIG-030 requires exactly five passing admission checks")
    for name in CHECK_ORDER:
        check = checks[name]
        values = (
            float(check["observed"]),
            float(check["limit"]),
            float(check["utilization_fraction"]),
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"RFIG-030 cannot plot missing/non-finite values: {name}")
        if not bool(check["passed"]):
            raise ValueError(f"RFIG-030 PASS source contains a failed check: {name}")
    return result


def _value_label(name: str, check: dict[str, Any]) -> str:
    observed = float(check["observed"])
    limit = float(check["limit"])
    if name == "cpu_core_hours":
        return f"PASS  {observed:.4f} / {limit:.1f} core-h maximum"
    if name == "wall_clock_days":
        return f"PASS  {observed:.4f} / {limit:.1f} days maximum"
    if name == "free_disk_after_artifacts_gib":
        return f"PASS  {observed:.4f} / {limit:.1f} GiB minimum"
    return f"PASS  {observed:.4f} / {limit:.1f} GiB maximum"


def _save(fig: plt.Figure, path: Path) -> tuple[Path, Path]:
    png = path.with_suffix(".png")
    svg = path.with_suffix(".svg")
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV RFIG-030 generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "QMLforArtemisIV RFIG-030 generator", "Date": None},
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def draw(path: Path) -> tuple[Path, Path]:
    result = _validated_result()
    checks = result["admission"]["checks"]
    pressure = np.asarray(
        [100.0 * float(checks[name]["utilization_fraction"]) for name in CHECK_ORDER]
    )
    passed = np.asarray([bool(checks[name]["passed"]) for name in CHECK_ORDER])
    colors = [BLUE if value else ORANGE for value in passed]
    hatches = ["" if value else "///" for value in passed]

    fig, ax = plt.subplots(figsize=(11.2, 6.3), constrained_layout=True)
    y = np.arange(len(CHECK_ORDER))
    bars = ax.barh(
        y,
        pressure,
        height=0.58,
        color=colors,
        edgecolor=INK,
        linewidth=0.6,
        zorder=3,
    )
    for bar, hatch in zip(bars, hatches, strict=True):
        bar.set_hatch(hatch)

    ax.axvline(100.0, color=ORANGE, linewidth=1.5, linestyle="--", zorder=2)
    ax.text(
        100.0,
        -0.72,
        "100% accepted boundary",
        ha="center",
        va="bottom",
        color=ORANGE,
        fontsize=8.2,
        fontweight="bold",
    )
    for index, name in enumerate(CHECK_ORDER):
        ax.text(
            max(float(pressure[index]) + 1.8, 2.2),
            index,
            _value_label(name, checks[name]),
            ha="left",
            va="center",
            fontsize=8.4,
            color=INK,
            fontweight="bold" if pressure[index] < 3.0 else "normal",
        )

    ax.set_yticks(y, [CHECK_LABELS[name] for name in CHECK_ORDER])
    ax.invert_yaxis()
    ax.set_xlim(0.0, max(115.0, float(np.max(pressure)) * 1.25 + 25.0))
    ax.set_xlabel("Fraction of accepted resource boundary (%)")
    ax.set_title(
        "D010 synthetic compute admission: PASS",
        loc="left",
        fontsize=14,
        fontweight="bold",
        color=INK,
        pad=24,
    )
    ax.text(
        0.0,
        1.025,
        "Conservative 477.5-work-unit projection with 25% margin; lower pressure means more headroom",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY,
    )
    ax.grid(axis="x", color=GRID, linewidth=0.7, zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.text(
        0.0,
        -0.17,
        (
            "Free-disk pressure is minimum required / projected available; all other bars are projected or observed / maximum.\n"
            f"Source commit {result['source_commit'][:8]}; synthetic rows only; development/calibration/final reads = 0; GPU and Gate 6 runs = 0."
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.8,
        color=GRAY,
        linespacing=1.4,
    )
    return _save(fig, path)


def register(png: Path, svg: Path) -> None:
    result = _validated_result()
    existing = _read_csv(REGISTRY)
    fields = list(existing[0])
    by_id = {row["figure_id"]: row for row in existing}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-030",
            "title": "D010 synthetic compute resource admission",
            "phase": "Post-Gate-5 exploratory protocol",
            "paper_section": "Methods: compute admission",
            "evidence_status": "synthetic_compute_admission_pass",
            "source_data": str(RESULT.relative_to(ROOT)).replace("\\", "/"),
            "generator": "scripts/make_post_gate5_preflight_result_figure.py",
            "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": (
                "The unchanged D009 synthetic workload passed all D010 laptop "
                "compute-admission limits after typed memory telemetry validation; "
                "bars show conservative boundary pressure after the frozen 25% margin."
            ),
            "claim_boundary": (
                "Synthetic compute-admission evidence only. This PASS authorizes "
                "preparation of D011, not research-data fitting, QML performance, "
                "Gate 5 reinterpretation, hardware advantage, or Gate 6."
            ),
            "reporting_source_commit": str(result["source_commit"]),
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id[row["figure_id"]] = row
    ordered = sorted(
        by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1])
    )
    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(REGISTRY)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png, svg = draw(OUTPUT / "post_gate5_d010_resource_admission")
    register(png, svg)
    print("Generated RFIG-030 D010 synthetic compute-admission figure")


if __name__ == "__main__":
    main()
