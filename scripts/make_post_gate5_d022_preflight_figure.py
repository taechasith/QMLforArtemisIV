"""Generate RFIG-041 for D022-C CSAFE-RF synthetic compute preflight."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "data/processed/reporting/post_gate5_d022_recall_first_preflight.json"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
GREEN = "#009E73"
GRAY = "#68737D"
LIGHT = "#D9E1E8"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d022-preflight-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_result() -> dict[str, Any]:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D022-C" or payload["status"] not in {"PASS", "STOP"}:
        raise ValueError("RFIG-041 requires terminal D022-C evidence")
    for field in (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
    ):
        if int(payload["integrity"][field]) != 0:
            raise PermissionError(f"D022-C figure source violates {field}")
    return payload


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d022_recall_first_compute_admission.png"
    svg = OUTPUT / "post_gate5_d022_recall_first_compute_admission.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return png, svg


def _draw(payload: dict[str, Any]) -> tuple[Path, Path]:
    order = (
        "cpu_core_hours",
        "wall_clock_days",
        "new_artifacts_gib",
        "peak_working_set_gib",
        "free_disk_after_artifacts_gib",
        "gpu_hours",
    )
    labels = {
        "cpu_core_hours": "CPU core-hours",
        "wall_clock_days": "Wall days",
        "new_artifacts_gib": "Artifacts",
        "peak_working_set_gib": "Peak memory",
        "free_disk_after_artifacts_gib": "Disk reserve",
        "gpu_hours": "GPU hours",
    }
    checks = payload["admission"]["checks"]
    pressure = np.asarray([100.0 * float(checks[name]["utilization_fraction"]) for name in order])
    colors = [BLUE if bool(checks[name]["passed"]) else GOLD for name in order]
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    y = np.arange(len(order))
    ax.barh(y, pressure, color=colors, edgecolor=INK, linewidth=0.6)
    ax.axvline(100.0, color=GOLD, linewidth=1.3, linestyle="--", label="admission boundary")
    ax.set_yticks(y, [labels[name] for name in order])
    ax.invert_yaxis()
    ax.set_xlabel("Boundary pressure after 25% margin (%)")
    ax.set_title("D022-C CSAFE-RF synthetic compute admission", loc="left", fontsize=15, fontweight="bold", color=INK)
    ax.text(
        0.0,
        1.03,
        "Clean-source synthetic evidence only: projects recall-first safety scoring across 5 folds and 20 seeds.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY,
    )
    ax.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower right", frameon=False)
    for index, name in enumerate(order):
        check = checks[name]
        label = f"{float(check['observed']):.3g} / {float(check['limit']):.3g}"
        ax.text(pressure[index] + 1.5, index, label, va="center", fontsize=8, color=INK)
    footer = (
        f"Status: {payload['status']} | synthetic rows: {payload['integrity']['synthetic_rows_used']} | "
        "development/calibration/final/Gate6 reads: 0"
    )
    ax.text(0.0, -0.16, footer, transform=ax.transAxes, ha="left", color=GREEN, fontsize=8.5)
    return _save(fig)


def _register(png: Path, svg: Path, payload: dict[str, Any]) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-041",
            "title": "D022-C CSAFE-RF synthetic compute admission",
            "phase": "Post-Gate-5 CSAFE-RF compute admission",
            "paper_section": "Methods: compute admission",
            "evidence_status": "recall_first_synthetic_compute_admission",
            "source_data": RESULT.relative_to(ROOT).as_posix(),
            "generator": "scripts/make_post_gate5_d022_preflight_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D022-C projects the clean-source synthetic CSAFE-RF workload against local laptop compute limits.",
            "claim_boundary": "Synthetic compute-admission evidence only; no development-data fitting, threshold application to real data, calibration, final-test, hardware/GPU, mission, Gate 5 reinterpretation, QML invention, quantum advantage, or Gate 6.",
            "reporting_source_commit": payload["source_commit"],
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-041"] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    tmp.replace(REGISTRY)


def main() -> None:
    payload = _load_result()
    png, svg = _draw(payload)
    _register(png, svg, payload)
    print("Generated RFIG-041 D022-C synthetic compute admission")


if __name__ == "__main__":
    main()
