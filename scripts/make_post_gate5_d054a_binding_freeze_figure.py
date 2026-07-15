"""Generate the methods-boundary figure for the D054-A P018 binding freeze."""

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
CONFIG = ROOT / "configs/post_gate5_d054a_p018_binding_freeze.yaml"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#172026"
BLUE = "#246A8D"
GREEN = "#1B7F5A"
GOLD = "#B7791F"
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
        "svg.hashsalt": "qmlforartemisiv-d054a-binding-freeze-v1",
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
    if payload["decision_id"] != "D054-A":
        raise ValueError("RFIG-086 requires D054-A")
    if payload["status"] != "accepted_binding_freeze_no_execution":
        raise ValueError("RFIG-086 requires the accepted D054-A binding freeze")
    authority = payload["authority_boundary"]
    if authority["binding_freeze_authorized"] is not True:
        raise PermissionError("D054-A binding freeze is not authorized")
    if authority["binding_figure_authorized"] is not True:
        raise PermissionError("D054-A binding figure is not authorized")
    for key in (
        "numerical_audit_execution_authorized",
        "source_manifest_read_authorized",
        "development_data_read_authorized",
        "dataset_generation_authorized",
        "model_fit_authorized",
        "calibration_access_authorized",
        "final_test_access_authorized",
        "hardware_execution_authorized",
        "gpu_execution_authorized",
        "future_audit_figure_rendering_authorized",
        "gate6_authorized",
    ):
        if authority[key] is not False:
            raise PermissionError(f"D054-A figure source unlocks {key}")
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
        y + height - 0.078,
        body,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.25,
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


def _save(fig: plt.Figure) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / "post_gate5_d054a_binding_freeze.png"
    svg = OUTPUT / "post_gate5_d054a_binding_freeze.svg"
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV D054-A binding freeze figure"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={
            "Creator": "QMLforArtemisIV D054-A binding freeze figure",
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
    algebra = config["quantum_algebra_binding"]
    cases = config["development_only_case_binding"]
    defects = config["defect_and_target_binding"]
    figure = config["reporting_and_figures"]["generated_now"]

    fig, ax = plt.subplots(figsize=(13.5, 7.35))
    ax.set_axis_off()
    ax.text(
        0.02,
        0.98,
        "D054-A P018 Stage 1 binding freeze",
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
        "Methods boundary only: binds future audit inputs; no numerical audit, data read, fit, SRP, hardware/GPU, or Gate 6 authority.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.5,
        color=GRAY,
    )
    _card(
        ax,
        0.03,
        0.57,
        0.27,
        0.25,
        "Physical contract",
        "Earth-centered J2000 axes\nF0: Earth point mass\nF1: Moon/Sun third body\nF2: F1 plus J2\n\nDeterministic SRP: excluded",
        facecolor=PALE_GRAY,
        edgecolor=GRAY,
    )
    _card(
        ax,
        0.365,
        0.57,
        0.27,
        0.25,
        "Algebraic audit probe",
        f"q={algebra['qubit_count']} collective-spin SO(3)\n255-element iPauli basis\nJx, Jy, Jz centralizer\nX/Z local controls plus ZZ chain\n\nNo PQC is assembled.",
        facecolor=PALE_BLUE,
        edgecolor=BLUE,
    )
    _card(
        ax,
        0.70,
        0.57,
        0.27,
        0.25,
        "Development-only cases",
        f"{cases['source_case_count']} identities\nG01-G12, F0/F1/F2\nCandidate 2, decision set 1\nU0-U4 only\n\nCalibration/final-test: prohibited",
        facecolor=PALE_GREEN,
        edgecolor=GREEN,
    )
    _card(
        ax,
        0.125,
        0.18,
        0.29,
        0.23,
        "Transformation and stability",
        "Seven fixed SO(3) rotations\nJoint and fixed-context branches\nD053 direct SVD plus closure\nDOP853 baseline/tight replay\n\nUnstable effects stop.",
        facecolor=PALE_GOLD,
        edgecolor=GOLD,
    )
    _card(
        ax,
        0.585,
        0.18,
        0.29,
        0.23,
        "Bounded future decision",
        f"eps_a={defects['acceleration_floor']['eps_a_km_s2']:.0e} km/s^2\ny scale={defects['primary_target']['y_scale_m_s']:.0f} m/s\nRFIG-087 to RFIG-089 reserved\n\nD055 is required before execution.",
        facecolor=PALE_BLUE,
        edgecolor=BLUE,
    )
    _arrow(ax, (0.30, 0.695), (0.365, 0.695))
    _arrow(ax, (0.635, 0.695), (0.70, 0.695))
    _arrow(ax, (0.50, 0.565), (0.27, 0.41))
    _arrow(ax, (0.50, 0.565), (0.73, 0.41))
    ax.text(
        0.02,
        0.045,
        f"{figure['id']}: accepted binding-freeze evidence only. Future audit evidence must be immutable, development-only, and separately authorized.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.4,
        color=GRAY,
    )
    return _save(fig)


def _read_registry() -> tuple[list[str], list[dict[str, str]]]:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _register(png: Path, svg: Path, config: dict) -> None:
    fields, rows = _read_registry()
    source_data = CONFIG.relative_to(ROOT).as_posix()
    generator = Path(__file__).relative_to(ROOT).as_posix()
    figure = config["reporting_and_figures"]["generated_now"]
    root = config["output_paths"]["root"]
    required = config["output_paths"]["required_future_files"]
    base = {field: "" for field in fields}
    entries = [
        {
            **base,
            "figure_id": figure["id"],
            "title": figure["title"],
            "phase": "P018 Stage 1 binding freeze",
            "paper_section": "Methods: prospective numerical audit",
            "evidence_status": figure["evidence_status"],
            "source_data": source_data,
            "generator": generator,
            "png_path": png.relative_to(ROOT).as_posix(),
            "png_sha256": _sha256(png),
            "png_bytes": str(png.stat().st_size),
            "svg_path": svg.relative_to(ROOT).as_posix(),
            "svg_sha256": _sha256(svg),
            "svg_bytes": str(svg.stat().st_size),
            "caption": "D054-A binds the P018 physical scope, q=4 algebraic probe, rotations, development-only identities, defect scales, output paths, and future figures before any audit execution.",
            "claim_boundary": "Accepted methods-boundary evidence only; no DLA, trajectory, dataset, model, QML-invention, quantum-advantage, or Gate 6 result.",
            "campaign_source_commit": _git_head(),
            "reporting_source_commit": _git_head(),
            "figure_generator_sha256": _sha256(Path(__file__)),
        },
        {
            **base,
            "figure_id": "RFIG-087",
            "title": "P018 DLA singular spectrum and centralizer stability",
            "phase": "P018 Stage 1 numerical audit",
            "paper_section": "Methods: DLA centralizer audit",
            "evidence_status": "reserved_future_authorized_audit",
            "source_data": f"{root}/{Path(required['singular_spectrum']).name};{root}/{Path(required['centralizer_summary']).name}",
            "generator": "not authorized until D055",
            "caption": "Reserved for the full direct-SVD spectrum, threshold sweep, basis-closure, and centralizer evidence.",
            "claim_boundary": "Reservation only; no spectrum or centralizer result exists.",
        },
        {
            **base,
            "figure_id": "RFIG-088",
            "title": "P018 trajectory covariance and fixed-context breaking",
            "phase": "P018 Stage 1 numerical audit",
            "paper_section": "Methods: numerical covariance audit",
            "evidence_status": "reserved_future_authorized_audit",
            "source_data": f"{root}/{Path(required['covariance_audit']).name};{root}/{Path(required['breaking_audit']).name}",
            "generator": "not authorized until D055",
            "caption": "Reserved for baseline-versus-tightened DOP853 covariance and fixed-context breaking evidence.",
            "claim_boundary": "Reservation only; no trajectory or physical-breaking result exists.",
        },
        {
            **base,
            "figure_id": "RFIG-089",
            "title": "P018 target sensitivity and counterexamples",
            "phase": "P018 Stage 1 numerical audit",
            "paper_section": "Results: target-mechanism admission",
            "evidence_status": "reserved_future_authorized_audit",
            "source_data": f"{root}/{Path(required['target_sensitivity']).name}",
            "generator": "not authorized until D055",
            "caption": "Reserved for fixed-context label defects, target-sensitivity admission, and counterexamples.",
            "claim_boundary": "Reservation only; no target response or model-design admission result exists.",
        },
    ]
    replacement_ids = {entry["figure_id"] for entry in entries}
    retained = [row for row in rows if row.get("figure_id") not in replacement_ids]
    all_rows = [*retained, *entries]
    all_rows.sort(key=lambda row: int(row["figure_id"].split("-")[1]))
    tmp = REGISTRY.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            [{field: row.get(field, "") for field in fields} for row in all_rows]
        )
    tmp.replace(REGISTRY)


def main() -> None:
    config = _load_config()
    png, svg = _draw(config)
    _register(png, svg, config)
    print("Generated RFIG-086 and reserved RFIG-087 through RFIG-089")


if __name__ == "__main__":
    main()
