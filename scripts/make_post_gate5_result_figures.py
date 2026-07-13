"""Generate and register the source-bound D011 paper-ready figures."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
REPORTING = ROOT / "data/processed/reporting/post_gate5_p001"
PREFLIGHT = ROOT / "data/processed/reporting/post_gate5_d011_fold_shape_preflight.json"
C1_PREFLIGHT = (
    ROOT / "data/processed/reporting/post_gate5_d011_c1_fold_shape_preflight.json"
)
FUTURE = ROOT / "data/processed/reporting/post_gate5_future_research_discussion.csv"
OUTPUT = ROOT / "artifacts/research_figures"
REGISTRY = OUTPUT / "figure_registry.csv"

INK = "#17202A"
BLUE = "#0072B2"
GOLD = "#E69F00"
GRAY = "#68737D"
LIGHT = "#D9E1E8"
PALE_BLUE = "#DCEEF8"
PALE_GOLD = "#F9E8BE"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "svg.hashsalt": "qmlforartemisiv-d011-result-figures-v1",
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


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Figure source must be an object: {path}")
    return payload


def _bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def _float(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _validated_preflight() -> dict[str, Any]:
    source_path = C1_PREFLIGHT if C1_PREFLIGHT.is_file() else PREFLIGHT
    preflight = _json(source_path)
    if (
        preflight.get("decision_id") not in {"D011", "D011-C1"}
        or preflight.get("status") not in {"PASS", "STOP"}
        or int(preflight.get("development_rows_read", -1)) != 0
        or int(preflight.get("calibration_rows_read", -1)) != 0
        or int(preflight.get("final_test_rows_read", -1)) != 0
    ):
        raise PermissionError("D011 preflight figure source is invalid")
    source_commit = str(preflight["source_commit"])
    if "source_paths" in preflight:
        source_paths = {
            str(key): str(value) for key, value in preflight["source_paths"].items()
        }
    else:
        config = yaml.safe_load(
            _git_blob(
                source_commit, "configs/post_gate5_development_execution.yaml"
            ).decode("utf-8")
        )
        source_paths = {
            str(key): str(value) for key, value in config["source_binding"].items()
        }
    for key, expected in preflight["source_hashes"].items():
        path = source_paths[str(key)]
        actual = hashlib.sha256(_git_blob(source_commit, path)).hexdigest()
        if actual != expected:
            raise PermissionError(f"D011 figure source hash mismatch: {key}")
    preflight["_source_path"] = source_path.relative_to(ROOT).as_posix()
    return preflight


def _validated_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    preflight = _validated_preflight()
    summary = _json(REPORTING / "campaign_summary.json")
    decision = _json(REPORTING / "exploratory_decision.json")
    source_commit = str(summary["source_commit"])
    if (
        preflight.get("status") != "PASS"
        or preflight.get("source_commit") != source_commit
        or summary.get("status") != "complete"
        or decision.get("status") != "complete"
        or decision.get("source_commit") != source_commit
    ):
        raise PermissionError("D011 figure sources are not source-aligned")
    for payload in (preflight, summary, decision):
        if (
            int(payload.get("calibration_rows_read", -1)) != 0
            or int(payload.get("final_test_rows_read", -1)) != 0
        ):
            raise PermissionError("D011 figure source violates a locked split")
    evidence = _json(REPORTING / "evidence_manifest.json")
    if evidence.get("source_commit") != source_commit:
        raise PermissionError("D011 evidence manifest source mismatch")
    for name, metadata in evidence["files"].items():
        path = REPORTING / name
        if _sha256(path) != metadata["sha256"] or path.stat().st_size != int(
            metadata["bytes"]
        ):
            raise PermissionError(f"D011 compact evidence mismatch: {name}")
    if _sha256(FUTURE) != evidence["future_discussion_register_sha256"]:
        raise PermissionError("D011 future-discussion register digest mismatch")
    return preflight, summary, decision


def _save(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png = OUTPUT / f"{stem}.png"
    svg = OUTPUT / f"{stem}.svg"
    fig.savefig(
        png,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "QMLforArtemisIV D011 figure generator"},
    )
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={
            "Creator": "QMLforArtemisIV D011 figure generator",
            "Date": None,
        },
    )
    plt.close(fig)
    normalized = "\n".join(
        line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()
    )
    svg.write_text(normalized + "\n", encoding="utf-8", newline="\n")
    return png, svg


def _style_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=LIGHT, linewidth=0.7, zorder=0)
    ax.tick_params(colors=INK)


def draw_rfig031(preflight: Mapping[str, Any]) -> tuple[Path, Path]:
    order = (
        "cpu_core_hours",
        "wall_clock_days",
        "new_artifacts_gib",
        "peak_working_set_gib",
        "free_disk_after_artifacts_gib",
    )
    labels = {
        "cpu_core_hours": "CPU core-hours",
        "wall_clock_days": "Sequential wall time",
        "new_artifacts_gib": "New artifacts",
        "peak_working_set_gib": "Peak process memory",
        "free_disk_after_artifacts_gib": "Free disk after artifacts",
    }
    checks = preflight["admission"]["checks"]
    pressure = np.asarray(
        [100.0 * float(checks[name]["utilization_fraction"]) for name in order]
    )
    colors = [BLUE if bool(checks[name]["passed"]) else GOLD for name in order]
    fig, ax = plt.subplots(figsize=(11.2, 6.3), constrained_layout=True)
    y = np.arange(len(order))
    bars = ax.barh(
        y,
        pressure,
        height=0.58,
        color=colors,
        edgecolor=INK,
        linewidth=0.7,
        zorder=3,
    )
    for bar, name in zip(bars, order, strict=True):
        if not bool(checks[name]["passed"]):
            bar.set_hatch("///")
    ax.axvline(100.0, color=INK, linestyle="--", linewidth=1.2)
    for index, name in enumerate(order):
        check = checks[name]
        ax.text(
            float(pressure[index]) + 1.5,
            index,
            f"{float(check['observed']):.4g} / {float(check['limit']):.4g}",
            va="center",
            color=INK,
            fontsize=8.2,
        )
    ax.set_yticks(y, [labels[name] for name in order])
    ax.invert_yaxis()
    ax.set_xlim(0.0, max(115.0, float(np.max(pressure)) * 1.25 + 12.0))
    ax.set_xlabel("Fraction of accepted resource boundary (%)")
    ax.set_title(
        f"D011 largest-fold compute admission: {preflight['status']}",
        loc="left",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.0,
        1.015,
        "1,024 training + 9,750 validation rows; 1,220 worst-fold bundles; 25% margin",
        transform=ax.transAxes,
        color=GRAY,
        va="bottom",
    )
    ax.text(
        0.0,
        -0.15,
        "Free-disk pressure is minimum required / projected available; all other bars are observed or projected / maximum. Synthetic rows only.",
        transform=ax.transAxes,
        color=GRAY,
        fontsize=7.8,
        va="top",
    )
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax.tick_params(axis="y", length=0)
    return _save(fig, "post_gate5_d011_fold_shape_admission")


def _learning_points(
    rows: Sequence[Mapping[str, str]], track: str
) -> dict[str, list[tuple[int, float]]]:
    metric = "pooled_oof_nrmse" if track == "Q01b" else "pooled_oof_brier"
    by_series: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        if row["track_id"] != track or not _bool(row.get("eligible", "false")):
            continue
        value = _float(row.get(metric))
        if value is None:
            continue
        category = row["category"]
        if category == "projected":
            series = track
        elif category == "A02":
            series = "A02"
        elif track == "Q01b" and row.get("control_id") == "C06-T17":
            series = "C06"
        elif track == "FQK":
            series = "Strongest control"
        else:
            continue
        by_series[series][int(row["rung_samples"])].append(value)
    points: dict[str, list[tuple[int, float]]] = {}
    for series, by_rung in by_series.items():
        reducer = min
        points[series] = sorted(
            (rung, float(reducer(values))) for rung, values in by_rung.items()
        )
    return points


def draw_rfig026() -> tuple[Path, Path]:
    rows = _rows(REPORTING / "tuning_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.5), constrained_layout=True)
    styles = {
        "Q01b": (BLUE, "o", "-"),
        "FQK": (BLUE, "o", "-"),
        "A02": (GOLD, "s", "--"),
        "C06": (GRAY, "^", ":"),
        "Strongest control": (GRAY, "^", ":"),
    }
    for ax, track in zip(axes, ("Q01b", "FQK"), strict=True):
        points = _learning_points(rows, track)
        for series, values in points.items():
            color, marker, linestyle = styles[series]
            ax.plot(
                [value[0] for value in values],
                [value[1] for value in values],
                label=series,
                color=color,
                marker=marker,
                markerfacecolor="white" if series != track else color,
                linestyle=linestyle,
                linewidth=1.8,
                markersize=5.5,
            )
        ax.set_xscale("log", base=2)
        ax.set_xticks([128, 256, 512, 1024], ["128", "256", "512", "1,024"])
        ax.set_xlabel("Training rows per grouped fold")
        ax.set_ylabel(
            "Best eligible pooled OOF "
            + ("NRMSE" if track == "Q01b" else "Brier score")
        )
        ax.set_title(
            "Q01b cost regression"
            if track == "Q01b"
            else "FQK feasibility classification",
            loc="left",
            fontweight="bold",
            color=INK,
        )
        _style_axis(ax)
        if points:
            ax.legend(frameon=False, fontsize=8)
        else:
            ax.text(
                0.5,
                0.5,
                "Not reached under frozen eligibility",
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=GRAY,
            )
    fig.suptitle(
        "D011 development learning curves and matched controls",
        x=0.01,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.01,
        -0.02,
        "Each point is the best eligible configuration at that frozen rung; stopped tracks remain absent rather than being plotted as zero.",
        color=GRAY,
        fontsize=7.8,
    )
    return _save(fig, "post_gate5_d011_learning_curves")


def draw_rfig027() -> tuple[Path, Path]:
    path = REPORTING / "kernel_diagnostics.csv"
    rows = (
        [row for row in _rows(path) if _bool(row["eligible"])] if path.is_file() else []
    )
    groups = []
    for track in ("Q01b", "FQK"):
        for category in ("projected", "A02"):
            if any(
                row["track_id"] == track and row["category"] == category for row in rows
            ):
                groups.append((track, category))
    fields = (
        ("kernel_target_alignment", "Centered kernel-target alignment"),
        ("effective_rank", "Effective rank"),
        ("off_diagonal_std", "Off-diagonal kernel SD"),
        ("log_condition", "log10 regularized condition number"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 8.0), constrained_layout=True)
    labels = [f"{track}\n{category}" for track, category in groups]
    for ax, (field, title) in zip(axes.flat, fields, strict=True):
        values: list[list[float]] = []
        active_labels: list[str] = []
        for label, (track, category) in zip(labels, groups, strict=True):
            source_field = field
            if field == "kernel_target_alignment":
                source_field = (
                    "kernel_target_alignment_q01b"
                    if track == "Q01b"
                    else "kernel_target_alignment_fqk"
                )
            group_values = [
                value
                for row in rows
                if row["track_id"] == track and row["category"] == category
                for value in [
                    _float(
                        row.get(
                            source_field
                            if field != "log_condition"
                            else "regularized_condition_number"
                        )
                    )
                ]
                if value is not None
                and (value > 0.0 if field == "log_condition" else True)
            ]
            if field == "log_condition":
                group_values = [math.log10(value) for value in group_values]
            if group_values:
                values.append(group_values)
                active_labels.append(label)
        if values:
            box = ax.boxplot(
                values,
                labels=active_labels,
                patch_artist=True,
                showfliers=False,
                widths=0.58,
                medianprops={"color": INK, "linewidth": 1.4},
                whiskerprops={"color": INK},
                capprops={"color": INK},
            )
            for index, patch in enumerate(box["boxes"]):
                patch.set_facecolor(
                    BLUE if "projected" in active_labels[index] else PALE_GOLD
                )
                patch.set_edgecolor(INK)
                if "A02" in active_labels[index]:
                    patch.set_hatch("//")
        else:
            ax.text(0.5, 0.5, "No eligible diagnostic", ha="center", va="center")
        ax.set_title(title, loc="left", fontweight="bold", color=INK)
        _style_axis(ax)
    fig.suptitle(
        "D011 projected-kernel geometry and dequantization diagnostics",
        x=0.01,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.01,
        -0.015,
        "Distributions summarize 20 selected-seed, five-fold means. A02 uses identical PCA rows and Nystrom construction with a classical RBF geometry.",
        color=GRAY,
        fontsize=7.8,
    )
    return _save(fig, "post_gate5_d011_kernel_diagnostics")


def draw_rfig028(decision: Mapping[str, Any]) -> tuple[Path, Path]:
    fqk = decision["tracks"]["FQK"]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.5), constrained_layout=True)
    if not bool(fqk.get("all_five_folds_and_twenty_seeds", False)):
        for ax in axes:
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                "FQK not reached under frozen eligibility\nNo missing metric is plotted as zero",
                ha="center",
                va="center",
                color=GRAY,
                fontsize=11,
            )
    else:
        strongest_id = str(fqk["strongest_comparator_id"])
        if strongest_id == "A02":
            comparator_rows = [
                row
                for row in _rows(REPORTING / "selected_summary.csv")
                if row["track_id"] == "FQK"
                and row["category"] == "A02"
                and _bool(row["eligible"])
            ]
        else:
            comparator_rows = [
                row
                for row in _rows(REPORTING / "control_summary.csv")
                if row["track_id"] == "FQK"
                and row["control_id"] == strongest_id
                and _bool(row["eligible"])
            ]
        if len(comparator_rows) != 20:
            raise PermissionError("RFIG-028 strongest comparator is incomplete")
        metrics = ("Brier", "AUROC", "Recall @ 0.5", "Precision @ 0.5")
        q_values = (
            float(fqk["mean_pooled_oof_brier"]),
            float(fqk["mean_auroc"]),
            float(fqk["mean_recall_at_0_5"]),
            float(fqk["mean_precision_at_0_5"]),
        )
        c_values = (
            float(fqk["strongest_comparator_mean_brier"]),
            float(fqk["strongest_comparator_mean_auroc"]),
            float(fqk["strongest_comparator_mean_recall_at_0_5"]),
            float(np.mean([float(row["precision_at_0_5"]) for row in comparator_rows])),
        )
        x = np.arange(len(metrics))
        width = 0.36
        axes[0].bar(
            x - width / 2,
            q_values,
            width,
            label="FQK",
            color=BLUE,
            edgecolor=INK,
            linewidth=0.6,
        )
        control_bars = axes[0].bar(
            x + width / 2,
            c_values,
            width,
            label=str(fqk["strongest_comparator_id"]),
            color=PALE_GOLD,
            edgecolor=INK,
            linewidth=0.6,
        )
        for bar in control_bars:
            bar.set_hatch("//")
        axes[0].set_xticks(x, metrics, rotation=14, ha="right")
        axes[0].set_ylim(0.0, 1.05)
        axes[0].set_ylabel("Mean across 20 selected seeds")
        axes[0].set_title("Predictive endpoints", loc="left", fontweight="bold")
        axes[0].legend(frameon=False)
        _style_axis(axes[0])

        safety_metrics = ("False-negative rate", "False-positive rate")
        q_safety = (
            float(fqk["mean_false_negative_rate"]),
            float(fqk["mean_false_positive_rate"]),
        )
        c_safety = (
            float(
                np.mean([float(row["false_negative_rate"]) for row in comparator_rows])
            ),
            float(
                np.mean([float(row["false_positive_rate"]) for row in comparator_rows])
            ),
        )
        sx = np.arange(2)
        axes[1].bar(
            sx - width / 2,
            q_safety,
            width,
            color=BLUE,
            edgecolor=INK,
            linewidth=0.6,
        )
        bars = axes[1].bar(
            sx + width / 2,
            c_safety,
            width,
            color=PALE_GOLD,
            edgecolor=INK,
            linewidth=0.6,
        )
        for bar in bars:
            bar.set_hatch("//")
        axes[1].set_xticks(sx, safety_metrics, rotation=12, ha="right")
        axes[1].set_ylim(0.0, max(0.05, 1.15 * max(*q_safety, *c_safety)))
        axes[1].set_ylabel("Rate at frozen threshold 0.5")
        axes[1].set_title("Safety-filter consequences", loc="left", fontweight="bold")
        _style_axis(axes[1])
    fig.suptitle(
        "D011 feasibility-only quantum-kernel evidence",
        x=0.01,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.01,
        -0.02,
        f"Development-only result: {fqk['status']}. Sensitivities are report-only and do not alter this decision.",
        color=GRAY,
        fontsize=7.8,
    )
    return _save(fig, "post_gate5_d011_fqk_endpoints")


def draw_rfig029(decision: Mapping[str, Any]) -> tuple[Path, Path] | None:
    future = [row for row in _rows(FUTURE) if row["record_id"] != "P001-FR001"]
    if not future:
        return None
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13.0, 7.0),
        constrained_layout=True,
        gridspec_kw={"width_ratios": [0.9, 1.5]},
    )
    stages = [
        ("D009", "technical STOP", GOLD),
        ("D010", "compute PASS", BLUE),
        ("D011 Q01b", decision["tracks"]["Q01b"]["status"], BLUE),
        ("D011 FQK", decision["tracks"]["FQK"]["status"], BLUE),
    ]
    axes[0].axis("off")
    for index, (stage, status, color) in enumerate(stages):
        y = 0.88 - 0.22 * index
        axes[0].add_patch(
            plt.Rectangle(
                (0.05, y - 0.07),
                0.9,
                0.13,
                transform=axes[0].transAxes,
                facecolor=PALE_GOLD if color == GOLD else PALE_BLUE,
                edgecolor=color,
                linewidth=1.2,
                hatch="//" if color == GOLD else None,
            )
        )
        axes[0].text(
            0.09, y, stage, transform=axes[0].transAxes, va="center", fontweight="bold"
        )
        axes[0].text(
            0.42,
            y,
            status.replace("_", " "),
            transform=axes[0].transAxes,
            va="center",
            fontsize=8,
        )
    axes[0].set_title("Observed disposition", loc="left", fontweight="bold")

    axes[1].axis("off")
    visible = future[-3:]
    for index, row in enumerate(visible):
        y = 0.92 - index * 0.31
        axes[1].add_patch(
            plt.Rectangle(
                (0.02, y - 0.22),
                0.96,
                0.25,
                transform=axes[1].transAxes,
                facecolor="#F7F8F9",
                edgecolor=GRAY,
                linewidth=0.8,
            )
        )
        axes[1].text(
            0.05,
            y,
            f"{row['record_id']}  {row['track_id']}  {row['terminal_status']}",
            transform=axes[1].transAxes,
            va="top",
            fontweight="bold",
            color=INK,
        )
        wrapped = textwrap.fill(row["future_research_improvement"], width=82)
        axes[1].text(
            0.05,
            y - 0.055,
            wrapped,
            transform=axes[1].transAxes,
            va="top",
            fontsize=7.6,
            color=GRAY,
        )
        axes[1].text(
            0.05,
            y - 0.19,
            "NEW PROTOCOL REQUIRED  |  ACTIVE CHANGE: NO  |  POST-OUTCOME RETRY: NO",
            transform=axes[1].transAxes,
            va="top",
            fontsize=7.2,
            fontweight="bold",
            color=GOLD,
        )
    axes[1].set_title("Future-research firewall", loc="left", fontweight="bold")
    fig.suptitle(
        "Post-Gate-5 failures, negative results, and future-research boundary",
        x=0.01,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.01,
        -0.01,
        "Suggestions record what later protocols could improve; they do not alter, extend, or retry the active P001 pipeline.",
        color=GRAY,
        fontsize=7.8,
    )
    return _save(fig, "post_gate5_failure_and_future_firewall")


def draw_preflight_stop_rfig029(
    preflight: Mapping[str, Any],
) -> tuple[Path, Path]:
    step_id = (
        "D011_C1_fold_shape_preflight"
        if preflight.get("decision_id") == "D011-C1"
        else "D011_fold_shape_preflight"
    )
    records = [
        row for row in _rows(FUTURE) if row["step_id"] == step_id
    ]
    if len(records) != 1 or records[0]["terminal_status"] != "resource_stop":
        raise PermissionError("D011 preflight STOP lacks its future-research record")
    record = records[0]
    failed = [
        (name, check)
        for name, check in preflight["admission"]["checks"].items()
        if not bool(check["passed"])
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 6.2), constrained_layout=True)
    axes[0].axis("off")
    axes[0].text(
        0.02,
        0.92,
        "Observed resource STOP",
        transform=axes[0].transAxes,
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    for index, (name, check) in enumerate(failed):
        axes[0].text(
            0.04,
            0.78 - 0.13 * index,
            f"{name.replace('_', ' ')}: {float(check['observed']):.4g} vs {float(check['limit']):.4g}",
            transform=axes[0].transAxes,
            color=GOLD,
            fontweight="bold",
        )
    axes[0].text(
        0.04,
        0.15,
        "Development/calibration/final reads = 0\nQML performance = not evaluated",
        transform=axes[0].transAxes,
        color=GRAY,
    )

    axes[1].axis("off")
    axes[1].add_patch(
        plt.Rectangle(
            (0.02, 0.22),
            0.96,
            0.66,
            transform=axes[1].transAxes,
            facecolor="#F7F8F9",
            edgecolor=GRAY,
            linewidth=0.8,
        )
    )
    axes[1].text(
        0.06,
        0.82,
        f"{record['record_id']} future-only response",
        transform=axes[1].transAxes,
        fontweight="bold",
        color=INK,
    )
    axes[1].text(
        0.06,
        0.70,
        textwrap.fill(record["future_research_improvement"], width=68),
        transform=axes[1].transAxes,
        va="top",
        color=GRAY,
        fontsize=8.2,
    )
    axes[1].text(
        0.06,
        0.29,
        "NEW PROTOCOL REQUIRED\nACTIVE CHANGE: NO\nPOST-OUTCOME RETRY: NO",
        transform=axes[1].transAxes,
        color=GOLD,
        fontweight="bold",
        fontsize=8,
    )
    fig.suptitle(
        "D011 resource stop and future-research firewall",
        x=0.01,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )
    return _save(fig, "post_gate5_d011_resource_stop_firewall")


def _register(
    source_commit: str,
    figures: Sequence[tuple[str, str, str, str, str, str, tuple[Path, Path]]],
) -> None:
    existing = _rows(REGISTRY)
    fields = list(existing[0])
    by_id = {row["figure_id"]: row for row in existing}
    for figure_id, title, section, status, source, caption, paths in figures:
        png, svg = paths
        row = {field: "" for field in fields}
        row.update(
            {
                "figure_id": figure_id,
                "title": title,
                "phase": "Post-Gate-5 exploratory protocol",
                "paper_section": section,
                "evidence_status": status,
                "source_data": source,
                "generator": "scripts/make_post_gate5_result_figures.py",
                "png_path": png.relative_to(ROOT).as_posix(),
                "png_sha256": _sha256(png),
                "png_bytes": str(png.stat().st_size),
                "svg_path": svg.relative_to(ROOT).as_posix(),
                "svg_sha256": _sha256(svg),
                "svg_bytes": str(svg.stat().st_size),
                "caption": caption,
                "claim_boundary": (
                    "Development-only exploratory or synthetic compute evidence; "
                    "no calibration, final-test, mission, hardware, quantum-advantage, "
                    "Gate 5 revision, or Gate 6 claim."
                ),
                "reporting_source_commit": source_commit,
                "figure_generator_sha256": _sha256(Path(__file__)),
            }
        )
        by_id[figure_id] = row
    ordered = sorted(
        by_id.values(), key=lambda row: int(row["figure_id"].split("-")[1])
    )
    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ordered)
    temporary.replace(REGISTRY)


def main() -> None:
    preflight = _validated_preflight()
    if not (REPORTING / "campaign_summary.json").is_file():
        caption = (
            "The largest frozen validation-fold shape passed every unchanged "
            "laptop boundary under conservative no-reuse accounting."
            if preflight["status"] == "PASS"
            else "The largest frozen validation-fold shape exceeded at least one "
            "unchanged laptop boundary; no research payload was opened."
        )
        figures = [
            (
                "RFIG-031",
                "D011 largest-fold synthetic compute admission",
                "Methods: corrected compute admission",
                "synthetic_fold_shape_compute_admission",
                str(preflight["_source_path"]),
                caption,
                draw_rfig031(preflight),
            )
        ]
        if preflight["status"] == "STOP":
            figures.append(
                (
                    "RFIG-029",
                    "D011 resource stop and future-research firewall",
                    "Methods: compute limitations and failed execution",
                    "governed_resource_stop",
                    f"{preflight['_source_path']};data/processed/reporting/post_gate5_future_research_discussion.csv",
                    "The corrected largest-fold workload stopped at unchanged laptop boundaries; its future suggestion cannot alter or retry P001.",
                    draw_preflight_stop_rfig029(preflight),
                )
            )
        _register(str(preflight["source_commit"]), figures)
        print(f"Generated RFIG-031 D011 preflight {preflight['status']} figure")
        if preflight["status"] == "STOP":
            print("Updated RFIG-029 D011 resource-stop firewall")
        return

    preflight, summary, decision = _validated_sources()
    figures = [
        (
            "RFIG-031",
            "D011 largest-fold synthetic compute admission",
            "Methods: corrected compute admission",
            "synthetic_fold_shape_compute_admission",
            str(preflight["_source_path"]),
            "The largest frozen validation-fold shape passed every unchanged laptop boundary under conservative no-reuse accounting.",
            draw_rfig031(preflight),
        ),
        (
            "RFIG-026",
            "D011 exploratory learning curves and matched controls",
            "Results: post-Gate-5 exploratory models",
            "development_only_exploratory_model_evidence",
            "data/processed/reporting/post_gate5_p001/tuning_summary.csv",
            "Best eligible projected configurations are shown across frozen training rungs beside source-matched controls; stopped evidence remains absent.",
            draw_rfig026(),
        ),
        (
            "RFIG-027",
            "D011 projected-kernel geometry and dequantization diagnostics",
            "Results: post-Gate-5 exploratory diagnostics",
            "development_only_kernel_diagnostics",
            "data/processed/reporting/post_gate5_p001/kernel_diagnostics.csv",
            "Selected projected kernels are compared with A02 classical RBF geometry on identical fold-local PCA rows and Nystrom construction.",
            draw_rfig027(),
        ),
        (
            "RFIG-028",
            "D011 FQK predictive and safety-filter endpoints",
            "Results: post-Gate-5 exploratory feasibility",
            "development_only_feasibility_evidence",
            "data/processed/reporting/post_gate5_p001/exploratory_decision.json;data/processed/reporting/post_gate5_p001/control_summary.csv",
            "FQK development-only Brier, discrimination, fixed-threshold recall/precision, and error consequences are compared with the strongest complete control.",
            draw_rfig028(decision),
        ),
    ]
    failure = draw_rfig029(decision)
    if failure is not None:
        figures.append(
            (
                "RFIG-029",
                "Post-Gate-5 failure and future-research firewall",
                "Discussion: limitations and future research",
                "governed_failure_or_exploratory_negative",
                "data/processed/reporting/post_gate5_future_research_discussion.csv;data/processed/reporting/post_gate5_p001/exploratory_decision.json",
                "Technical stops, terminal nonadvancement, or valid negative results are separated from suggestions that require a new protocol and cannot rescue P001.",
                failure,
            )
        )
    _register(str(summary["source_commit"]), figures)
    print("Generated D011 RFIG-026 through RFIG-028 and RFIG-031")
    if failure is not None:
        print("Updated cumulative RFIG-029 failure/future-research firewall")


if __name__ == "__main__":
    main()
