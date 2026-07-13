"""Generate RFIG-036 for the D016-C1 A02 exact-RBF compute correction."""

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
RESULT = ROOT / "data/processed/reporting/post_gate5_d016_c1_a02_preflight.json"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
GRAY = "#68737D"
LIGHT = "#D9E1E8"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d016-c1-a02-v1",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_result() -> dict[str, Any]:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D016-C1":
        raise ValueError("RFIG-036 requires D016-C1 evidence")
    if payload["status"] not in {"PASS", "STOP"}:
        raise ValueError("RFIG-036 requires terminal D016-C1 evidence")
    for field in (
        "development_rows_read",
        "calibration_rows_read",
        "final_test_rows_read",
        "hardware_jobs_submitted",
        "gate6_runs",
    ):
        if int(payload["integrity"][field]) != 0:
            raise PermissionError(f"D016-C1 figure source violates {field}")
    return payload


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / f"{stem}.png"
    svg = OUTPUT / f"{stem}.svg"
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV D016-C1 figure generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={
            "Creator": "QMLforArtemisIV D016-C1 figure generator",
            "Date": None,
        },
    )
    plt.close(fig)
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
        + "\n",
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
    pressure = np.asarray(
        [100.0 * float(checks[name]["utilization_fraction"]) for name in order]
    )
    colors = [BLUE if bool(checks[name]["passed"]) else GOLD for name in order]
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    y = np.arange(len(order))
    ax.barh(y, pressure, color=colors, edgecolor=INK, linewidth=0.6)
    ax.axvline(100.0, color=GOLD, linewidth=1.3, linestyle="--")
    ax.set_yticks(y, [labels[name] for name in order])
    ax.invert_yaxis()
    ax.set_xlabel("Boundary pressure after 25% margin (%)")
    ax.set_title(
        "D016-C1 A02 exact-RBF compute correction",
        loc="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.0,
        1.03,
        (
            "Synthetic correction for the D014-C A02 exact classical RBF control "
            "before any development-data fitting."
        ),
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY,
    )
    ax.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    for index, name in enumerate(order):
        check = checks[name]
        observed = float(check["observed"])
        limit = float(check["limit"])
        ax.text(
            pressure[index] + 1.5,
            index,
            f"{observed:.3g} / {limit:.3g}",
            va="center",
            fontsize=8,
            color=INK if bool(check["passed"]) else GOLD,
        )
    ax.text(
        0.0,
        -0.16,
        (
            f"Status: {payload['status']} | synthetic rows: "
            f"{payload['integrity']['synthetic_rows_used']} | development/calibration/final/Gate6 reads: 0"
        ),
        transform=ax.transAxes,
        ha="left",
        color=GRAY,
        fontsize=8.5,
    )
    return _save(fig, "post_gate5_d016_c1_a02_compute_admission")


def _register(png: Path, svg: Path, payload: dict[str, Any]) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-036",
            "title": "D016-C1 A02 exact-RBF synthetic compute admission",
            "phase": "Post-Gate-5 classical-first planning",
            "paper_section": "Methods: compute admission correction",
            "evidence_status": "a02_exact_rbf_synthetic_compute_admission",
            "source_data": RESULT.relative_to(ROOT).as_posix(),
            "generator": "scripts/make_post_gate5_d016_c1_a02_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": (
                "D016-C1 measures the A02 exact classical RBF control omitted "
                "from D016-C before any D017 development-data fitting."
            ),
            "claim_boundary": (
                "Synthetic A02 exact-RBF compute-admission evidence only; no "
                "development-data fitting, calibration/final-test access, "
                "hardware/GPU execution, Gate 5 reinterpretation, QML invention "
                "claim, quantum-advantage claim, or Gate 6."
            ),
            "reporting_source_commit": payload["source_commit"],
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-036"] = row
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
    payload = _load_result()
    png, svg = _draw(payload)
    _register(png, svg, payload)
    print("Generated RFIG-036 D016-C1 A02 exact-RBF compute admission")


if __name__ == "__main__":
    main()
