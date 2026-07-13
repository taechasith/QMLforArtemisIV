"""Generate RFIG-029 for governed post-Gate-5 failures and stops."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
D009_FAILURE = ROOT / "data/processed/reporting/post_gate5_compute_preflight.json"
D010_RESULT = (
    ROOT / "data/processed/reporting/post_gate5_compute_preflight_rerun.json"
)
D011_FAILURE = (
    ROOT / "data/processed/reporting/post_gate5_d011_fold_shape_preflight.json"
)
D011_C1_FAILURE = (
    ROOT / "data/processed/reporting/post_gate5_d011_c1_fold_shape_preflight.json"
)
DISCUSSION = (
    ROOT / "data/processed/reporting/post_gate5_future_research_discussion.csv"
)
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#1F2937"
BLUE = "#0072B2"
ORANGE = "#D55E00"
MAGENTA = "#CC79A7"
GRAY = "#5B6573"
PALE_BLUE = "#EAF3F8"
PALE_ORANGE = "#FFF0E6"
PALE_MAGENTA = "#F7EDF4"
PALE_GRAY = "#F2F4F6"


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-rfig029-cumulative-stop-v2",
    }
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _card(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    *,
    facecolor: str,
    edgecolor: str,
    linestyle: str = "-",
) -> None:
    ax.add_patch(
        patches.FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.012,rounding_size=0.014",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.15,
            linestyle=linestyle,
        )
    )
    ax.text(
        x + 0.016,
        y + height - 0.030,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.016,
        y + height - 0.078,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.8,
        color=INK,
        linespacing=1.25,
    )


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = GRAY,
) -> None:
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.05,
            color=color,
        )
    )


def _save(fig: plt.Figure, path: Path) -> tuple[Path, Path]:
    png = path.with_suffix(".png")
    svg = path.with_suffix(".svg")
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV RFIG-029 generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "QMLforArtemisIV RFIG-029 generator", "Date": None},
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def _validated_sources() -> tuple[dict, dict, dict, dict | None, dict[str, dict[str, str]]]:
    d009 = json.loads(D009_FAILURE.read_text(encoding="utf-8"))
    d010 = json.loads(D010_RESULT.read_text(encoding="utf-8"))
    d011 = json.loads(D011_FAILURE.read_text(encoding="utf-8"))
    d011_c1 = (
        json.loads(D011_C1_FAILURE.read_text(encoding="utf-8"))
        if D011_C1_FAILURE.is_file()
        else None
    )
    rows = _read_csv(DISCUSSION)
    if d009.get("status") != "STOP" or d009.get("terminal_status") != "technical_failure":
        raise ValueError("RFIG-029 requires the governed D009 technical STOP")
    if d010.get("decision_id") != "D010" or d010.get("status") != "PASS":
        raise ValueError("RFIG-029 requires the closed D010 correction PASS")
    progress = d011.get("workload_progress", {})
    integrity = d011.get("integrity", {})
    if (
        d011.get("status") != "STOP"
        or d011.get("terminal_status") != "technical_failure"
        or d011.get("failed_stage") != "launcher_import_before_authority_verification"
        or progress.get("authority_verification_reached") is not False
        or progress.get("synthetic_workload_started") is not False
        or progress.get("resource_admission_evaluated") is not False
        or any(
            int(integrity.get(key, -1)) != 0
            for key in (
                "development_rows_read",
                "calibration_rows_read",
                "final_test_rows_read",
                "hardware_jobs_submitted",
                "gate6_runs",
            )
        )
    ):
        raise ValueError("RFIG-029 requires the governed pre-launch D011 STOP")
    if d011_c1 is not None:
        c1_progress = d011_c1.get("workload_progress", {})
        c1_integrity = d011_c1.get("integrity", {})
        if (
            d011_c1.get("status") != "STOP"
            or d011_c1.get("terminal_status") != "technical_failure"
            or d011_c1.get("failed_stage")
            != "d011_c1_authority_dependency_hash_check"
            or c1_progress.get("synthetic_workload_started") is not False
            or c1_progress.get("resource_admission_evaluated") is not False
            or any(
                int(c1_integrity.get(key, -1)) != 0
                for key in (
                    "development_rows_read",
                    "calibration_rows_read",
                    "final_test_rows_read",
                    "hardware_jobs_submitted",
                    "gate6_runs",
                )
            )
        ):
            raise ValueError("RFIG-029 requires the governed D011-C1 STOP")
    futures = {row["record_id"]: row for row in rows}
    required = {"P001-FR001", "P001-FR002"}
    if d011_c1 is not None:
        required.add("P001-FR003")
    if set(futures) != required:
        raise ValueError("RFIG-029 requires the governed future records")
    for future in futures.values():
        if (
            future["new_protocol_required"].lower() != "true"
            or future["active_pipeline_change_authorized"].lower() != "false"
            or future["post_outcome_retry_authorized"].lower() != "false"
        ):
            raise ValueError("RFIG-029 future-research firewall is invalid")
    return d009, d010, d011, d011_c1, futures


def draw(path: Path) -> tuple[Path, Path]:
    _, _, _, d011_c1, futures = _validated_sources()
    fig, ax = plt.subplots(figsize=(13.2, 7.2), constrained_layout=True)
    ax.set_axis_off()
    ax.text(
        0.0,
        0.985,
        "Post-Gate-5 technical stops and future-research firewall",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.0,
        0.940,
        "Execution disposition through D011-C1; missing admission and model evidence is not plotted as zero",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=GRAY,
    )

    ax.text(0.02, 0.875, "Governed execution disposition", transform=ax.transAxes,
            fontsize=10, fontweight="bold", color=INK)
    _card(ax, 0.02, 0.675, 0.54, 0.145, "D009  TECHNICAL STOP",
          "Reached the first shared 1,024-row synthetic projection.\n"
          "Windows process-memory telemetry then failed.\n"
          "Projected heads, controls, and admission were not reached.",
          facecolor=PALE_ORANGE, edgecolor=ORANGE)
    _card(ax, 0.02, 0.485, 0.54, 0.145, "D010  CORRECTION PASS (CLOSED)",
          "Typed telemetry passed independent validation.\n"
          "The unchanged D009-shaped synthetic workload passed admission.\n"
          "This historical PASS did not authorize research-data fitting.",
          facecolor=PALE_BLUE, edgecolor=BLUE)
    _card(ax, 0.02, 0.295, 0.54, 0.145, "D011  PRE-LAUNCH TECHNICAL STOP",
          "Direct-file execution could not import the scripts namespace.\n"
          "Authority/source verification and synthetic work were not reached.\n"
          "Admission unavailable; development/calibration/final reads = 0.",
          facecolor=PALE_ORANGE, edgecolor=ORANGE)
    if d011_c1 is not None:
        _card(ax, 0.02, 0.105, 0.54, 0.145, "D011-C1  AUTHORITY-HASH STOP",
              "Package-safe import smoke test passed.\n"
              "Pinned dependency hash was invalid before synthetic work.\n"
              "Admission unavailable; development/calibration/final reads = 0.",
              facecolor=PALE_ORANGE, edgecolor=ORANGE)
    _arrow(ax, (0.29, 0.675), (0.29, 0.63), color=GRAY)
    _arrow(ax, (0.29, 0.485), (0.29, 0.44), color=ORANGE)
    if d011_c1 is not None:
        _arrow(ax, (0.29, 0.295), (0.29, 0.25), color=ORANGE)

    ax.text(
        0.62,
        0.875,
        "Future-only records",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        fontweight="bold",
        color=INK,
    )
    _card(ax, 0.62, 0.64, 0.36, 0.18, "P001-FR001  telemetry adapter",
          "Later protocol: validate typed Windows memory telemetry\n"
          "against an independent OS reading.\n\n"
          "New protocol: YES   Active change: NO   Retry: NO",
          facecolor=PALE_MAGENTA, edgecolor=MAGENTA, linestyle="--")
    _card(ax, 0.62, 0.42, 0.36, 0.18, "P001-FR002  launcher/import",
          "Later decision: freeze package-safe invocation/import and\n"
          "a clean-source import-only smoke test. Scientific design unchanged.\n\n"
          "New protocol: YES   Active change: NO   Retry: NO",
          facecolor=PALE_MAGENTA, edgecolor=MAGENTA, linestyle="--")
    if d011_c1 is not None:
        _card(ax, 0.62, 0.20, 0.36, 0.18, "P001-FR003  raw-blob hashes",
              "Later decision: prevalidate pinned raw Git-blob hashes\n"
              "before accepting a successor correction.\n\n"
              "New protocol: YES   Active change: NO   Retry: NO",
              facecolor=PALE_MAGENTA, edgecolor=MAGENTA, linestyle="--")
    _card(ax, 0.62, 0.035, 0.36, 0.12, "Boundary retained",
          "No D011-C1 retry. No research fit, Gate 5 revision,\n"
          "hardware claim, or Gate 6. New human decision required.",
          facecolor=PALE_GRAY, edgecolor=INK)

    if futures["P001-FR002"]["step_id"] != "D011_fold_shape_preflight_launcher":
        raise ValueError("P001-FR002 is not bound to the D011 launcher stop")
    if d011_c1 is not None and futures["P001-FR003"]["step_id"] != (
        "D011_C1_authority_hash_check"
    ):
        raise ValueError("P001-FR003 is not bound to the D011-C1 hash stop")

    ax.text(
        0.0,
        0.005,
        "Sources: D009 STOP, D010 PASS, D011/D011-C1 STOP evidence, and future-only records. RFIG-031 is absent because corrected admission was not reached.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.8,
        color=GRAY,
    )
    return _save(fig, path)


def register(png: Path, svg: Path) -> None:
    _, _, d011_failure, d011_c1_failure, _ = _validated_sources()
    existing = _read_csv(REGISTRY)
    fields = list(existing[0])
    by_id = {row["figure_id"]: row for row in existing}
    source_paths = [
        str(D009_FAILURE.relative_to(ROOT)).replace("\\", "/"),
        str(D010_RESULT.relative_to(ROOT)).replace("\\", "/"),
        str(D011_FAILURE.relative_to(ROOT)).replace("\\", "/"),
    ]
    if d011_c1_failure is not None:
        source_paths.append(str(D011_C1_FAILURE.relative_to(ROOT)).replace("\\", "/"))
    source_paths.append(str(DISCUSSION.relative_to(ROOT)).replace("\\", "/"))
    reporting_source_commit = str(
        (d011_c1_failure or d011_failure).get("reporting_commit")
    )
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-029",
            "title": "Post-Gate-5 technical stops and future-research firewall",
            "phase": "Post-Gate-5 exploratory protocol",
            "paper_section": "Methods: compute limitations and failed execution",
            "evidence_status": "technical_failure_preflight_stop",
            "source_data": ";".join(source_paths),
            "generator": "scripts/make_post_gate5_failure_figure.py",
            "png_path": str(png.relative_to(ROOT)).replace("\\", "/"),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": str(svg.relative_to(ROOT)).replace("\\", "/"),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": (
                "D009 stopped at process-memory telemetry, D010 passed its closed "
                "telemetry correction and unchanged synthetic benchmark, and D011 "
                "then D011-C1 stopped before corrected admission was reached."
            ),
            "claim_boundary": (
                "Technical execution-disposition evidence only. P001-FR001 and "
                "future records require new prospective authority and cannot alter or "
                "retry their stopped attempts; no D011-C1 resource, QML, research-data, "
                "Gate 5, hardware, or Gate 6 claim."
            ),
            "reporting_source_commit": reporting_source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id[row["figure_id"]] = row
    ordered = sorted(by_id.values(), key=lambda item: int(item["figure_id"].split("-")[1]))
    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(REGISTRY)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png, svg = draw(OUTPUT / "post_gate5_cumulative_technical_stops")
    register(png, svg)
    print("Generated cumulative RFIG-029 technical-stop figure through D011-C1")


if __name__ == "__main__":
    main()
