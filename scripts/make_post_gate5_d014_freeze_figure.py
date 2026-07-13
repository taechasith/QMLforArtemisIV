"""Generate RFIG-032 for the D014-C classical-first freeze proposal."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/post_gate5_d014_classical_first_freeze.yaml"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GREEN = "#009E73"
GOLD = "#E69F00"
GRAY = "#64717D"
PALE_BLUE = "#EAF3F8"
PALE_GREEN = "#EAF7F1"
PALE_GOLD = "#FFF4D6"
PALE_GRAY = "#F2F4F6"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d014-freeze-v1",
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _load_config() -> dict:
    payload = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if payload["decision_id"] != "D014-C":
        raise ValueError("RFIG-032 requires D014-C")
    if payload["status"] != "accepted_freeze_proposal_no_execution":
        raise ValueError("RFIG-032 requires the accepted D014-C freeze")
    authority = payload["authority"]
    required_false = [
        "implementation_authorized",
        "synthetic_validation_authorized",
        "development_data_fitting_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "gate5_reinterpretation_authorized",
        "gate6_authorized",
    ]
    if authority["freeze_proposal_authorized"] is not True:
        raise PermissionError("D014-C freeze proposal is not authorized")
    for key in required_false:
        if authority[key] is not False:
            raise PermissionError(f"D014-C figure source unlocks {key}")
    return payload


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
        )
    )
    ax.text(
        x + 0.016,
        y + height - 0.030,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        x + 0.016,
        y + height - 0.080,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.2,
        color=INK,
        linespacing=1.25,
    )


def _arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            transform=ax.transAxes,
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.1,
            color=GRAY,
        )
    )


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / f"{stem}.png"
    svg = OUTPUT / f"{stem}.svg"
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV D014 freeze figure generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={
            "Creator": "QMLforArtemisIV D014 freeze figure generator",
            "Date": None,
        },
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def _draw(config: dict) -> tuple[Path, Path]:
    cres = config["locked_tracks"]["residual_cost_hardening"]
    csafe = config["locked_tracks"]["safety_filter_hardening"]
    fig, ax = plt.subplots(figsize=(13.4, 7.2))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.98,
        "D014-C classical-first freeze before QML invention",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.02,
        0.91,
        "Planning record only: locks stronger classical targets; no implementation, data fitting, hardware, Gate 5 reinterpretation, or Gate 6.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        color=GRAY,
    )
    _card(
        ax,
        0.03,
        0.61,
        0.28,
        0.21,
        "Evidence input",
        "D011-R1 negatives\nQ01b: NRMSE gap vs C06\nFQK: weaker than C02-T02\n\nPurpose: define a fairer target\nbefore any new QML design.",
        facecolor=PALE_GRAY,
        edgecolor=GRAY,
    )
    _card(
        ax,
        0.37,
        0.56,
        0.25,
        0.28,
        "CRES residual-cost track",
        "Target: robust correction delta-v\nPrimary: pooled OOF NRMSE\nControls:\n- C06-T17\n- A02 exact RBF\n- random-feature RBF\n- compressed MLP\n- ridge residual",
        facecolor=PALE_BLUE,
        edgecolor=BLUE,
    )
    _card(
        ax,
        0.70,
        0.56,
        0.25,
        0.28,
        "CSAFE safety-filter track",
        "Target: propagated feasibility\nPrimary: pooled OOF Brier\nControls:\n- C02-T02\n- calibrated logistic\n- class-weighted trees\n- conformal/quantile threshold\n- A02 feasibility",
        facecolor=PALE_GREEN,
        edgecolor=GREEN,
    )
    _card(
        ax,
        0.18,
        0.18,
        0.26,
        0.22,
        "Required before fitting",
        "D015: implementation + synthetic validation only\nLater: clean-source compute admission\nThen: separate development-data decision\n\nMissing stages remain absent.",
        facecolor=PALE_GOLD,
        edgecolor=GOLD,
    )
    _card(
        ax,
        0.56,
        0.18,
        0.29,
        0.22,
        "Invention-readiness output",
        "Every result labels:\n- useful design signal\n- prohibited rescue use\n- required future control\n- claim boundary",
        facecolor=PALE_GRAY,
        edgecolor=INK,
    )
    _arrow(ax, (0.31, 0.715), (0.37, 0.715))
    _arrow(ax, (0.62, 0.715), (0.70, 0.715))
    _arrow(ax, (0.50, 0.56), (0.36, 0.40))
    _arrow(ax, (0.78, 0.56), (0.70, 0.40))
    ax.text(
        0.02,
        0.06,
        (
            f"Locked tracks: {cres['track_id']} and {csafe['track_id']}. "
            "D014-C authorizes only the freeze proposal; D015 is required before implementation."
        ),
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=8.5,
        color=GRAY,
    )
    return _save(fig, "post_gate5_d014_classical_first_freeze")


def _register(png: Path, svg: Path, source_commit: str) -> None:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_id = {row["figure_id"]: row for row in rows}
    row = {field: "" for field in fields}
    row.update(
        {
            "figure_id": "RFIG-032",
            "title": "D014-C classical-first freeze map",
            "phase": "Post-Gate-5 classical-first planning",
            "paper_section": "Methods: future protocol boundary",
            "evidence_status": "classical_first_freeze_proposal",
            "source_data": "configs/post_gate5_d014_classical_first_freeze.yaml",
            "generator": "scripts/make_post_gate5_d014_freeze_figure.py",
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": (
                "D014-C locks residual-cost and safety-filter classical targets "
                "before any later QML invention or executable successor work."
            ),
            "claim_boundary": (
                "Freeze-proposal evidence only; no implementation, synthetic "
                "validation, development-data fitting, calibration/final-test "
                "access, hardware, Gate 5 reinterpretation, QML invention claim, "
                "quantum-advantage claim, or Gate 6."
            ),
            "reporting_source_commit": source_commit,
            "figure_generator_sha256": _sha256(Path(__file__)),
        }
    )
    by_id["RFIG-032"] = row
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
    config = _load_config()
    png, svg = _draw(config)
    _register(png, svg, _git_head())
    print("Generated RFIG-032 D014-C classical-first freeze map")


if __name__ == "__main__":
    main()
