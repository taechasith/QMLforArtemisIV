from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from openqfuel.gate4 import read_yaml
from openqfuel.gate5 import (
    TargetStandardizer,
    deterministic_group_folds,
    execute_trial,
    fit_fold_features,
    gate5_preflight,
    initial_execution_plan,
    load_fold_checkpoint,
    matched_qubits_for_trial,
    nested_training_indices,
    rank_rung_summaries,
    write_fold_checkpoint,
)
from openqfuel.models import PhysicsResidualRegressor, build_classical_regressor
from openqfuel.qml import HybridQuantumResidualRegressor, VariationalQuantumRegressor


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase1_benchmark.yaml"


def test_group_folds_are_deterministic_complete_and_label_agnostic() -> None:
    groups = [f"G{index:02d}" for index in range(1, 13)]
    strata = {
        group: (f"U{(index - 1) % 5}", "T" if index > 8 else "C")
        for index, group in enumerate(groups, start=1)
    }
    first = deterministic_group_folds(groups, 20260710, 5, strata)
    second = deterministic_group_folds(list(reversed(groups)), 20260710, 5, strata)
    assert first == second
    assert set(first) == set(groups)
    assert sorted(Counter(first.values()).values()) == [2, 2, 2, 3, 3]
    for uncertainty in {value[0] for value in strata.values()}:
        assigned = [
            first[group] for group in groups if strata[group][0] == uncertainty
        ]
        assert len(assigned) == len(set(assigned))


def test_learning_rows_are_nested_and_ignore_outcomes() -> None:
    records = [
        {"scenario_id": f"F1-G01-{index:06d}", "outcomes": {"target": index}}
        for index in range(1, 40)
    ]
    eligible = np.arange(len(records))
    small = nested_training_indices(records, eligible, 8, 7)
    large = nested_training_indices(records, eligible, 16, 7)
    assert set(small).issubset(set(large))
    for record in records:
        record["outcomes"]["target"] *= -1000
    np.testing.assert_array_equal(
        small, nested_training_indices(records, eligible, 8, 7)
    )


def test_initial_plan_preserves_trials_and_balances_matched_dimensions() -> None:
    rows = initial_execution_plan(ROOT)
    assert len(rows) == 330
    assert len({row["task_id"] for row in rows}) == len(rows)
    matched = [
        row
        for row in rows
        if row["family_id"] == "A01" or row["view"] == "compressed_c05"
    ]
    assert Counter(row["effective_qubits"] for row in matched) == {
        4: 20,
        6: 20,
        8: 20,
    }
    assert [matched_qubits_for_trial(index) for index in (1, 2, 3, 4)] == [
        4,
        6,
        8,
        4,
    ]


def test_ranking_preserves_required_qubits_and_frozen_ties() -> None:
    summaries = []
    for order, qubits in enumerate((4, 4, 6, 6, 8, 8), start=1):
        summaries.append(
            {
                "eligible_to_advance": True,
                "pooled_oof_nrmse": 0.1 + order * 0.01,
                "mean_regret_m_s": 1.0,
                "trial": {
                    "trial_id": f"Q02-T{order:02d}",
                    "model_family": "variational_quantum_regressor",
                    "parameters": {
                        "qubits": qubits,
                        "data_reupload_layers": 1,
                        "entangle": False,
                    },
                },
            }
        )
    ranking = rank_rung_summaries(summaries, retain=4, preserve_required_qubits=True)
    selected = [row for row in ranking if row["selected_for_next_rung"]]
    assert len(selected) == 4
    assert {row["effective_qubits"] for row in selected} == {4, 6, 8}


def test_target_standardization_is_training_only_and_invertible() -> None:
    scaler = TargetStandardizer.fit([2.0, 4.0, 6.0])
    values = np.array([-1.0, 0.0, 8.0])
    np.testing.assert_allclose(
        scaler.inverse(scaler.transform(values)), values, atol=1e-12
    )
    with pytest.raises(ValueError):
        TargetStandardizer.fit([1.0, 1.0])


def test_fold_checkpoints_are_atomic_and_signature_guarded(tmp_path: Path) -> None:
    path = tmp_path / "fold_CV01.json"
    checkpoint = {"task_signature": "abc", "fold_metrics": {"nrmse": 0.1}}
    write_fold_checkpoint(path, checkpoint)
    assert load_fold_checkpoint(path, "abc") == checkpoint
    assert not path.with_suffix(".json.tmp").exists()
    with pytest.raises(PermissionError, match="signature mismatch"):
        load_fold_checkpoint(path, "different")


def test_fold_transforms_do_not_fit_on_validation_outlier() -> None:
    config = read_yaml(CONFIG)

    def record(value: float) -> dict[str, object]:
        inputs = {name: value for name in config["features"]["numeric"]}
        inputs.update({name: value for name in config["features"]["physics_derived"]})
        inputs.update({name: "A" for name in config["features"]["categorical"]})
        return {"inputs": inputs}

    train = [record(float(index)) for index in range(1, 10)]
    first_train, _ = fit_fold_features(train, [record(10.0)], config)
    second_train, _ = fit_fold_features(train, [record(1e12)], config)
    np.testing.assert_allclose(first_train, second_train)


def test_residual_factories_use_explicit_physical_baseline_column() -> None:
    model = build_classical_regressor(
        "physics_residual",
        {
            "residual_estimator": "ridge",
            "alpha": 0.1,
            "max_leaf_nodes": 15,
            "learning_rate": 0.03,
        },
        seed=3,
        low_fidelity_column=0,
    )
    assert isinstance(model, PhysicsResidualRegressor)
    assert model.low_fidelity_column == 0


def test_hybrid_residual_does_not_encode_the_appended_baseline() -> None:
    circuit = np.array(
        [[value, -value, value / 2, 0.25] for value in np.linspace(-0.5, 0.5, 6)]
    )
    baseline = np.linspace(-0.2, 0.2, 6)
    x = np.column_stack((circuit, baseline))
    y = baseline + 0.1 * circuit[:, 0]
    model = HybridQuantumResidualRegressor(
        low_fidelity_column=-1,
        n_qubits=4,
        layers=1,
        maximum_optimizer_iterations=2,
        seed=4,
    ).fit(x, y)
    shifted = x.copy()
    shifted[:, -1] += 2.0
    np.testing.assert_allclose(model.predict(shifted) - model.predict(x), 2.0)


def test_variational_fit_exposes_d004_optimizer_diagnostics() -> None:
    x = np.array(
        [[value, -value, value / 2, 0.25] for value in np.linspace(-0.5, 0.5, 5)]
    )
    model = VariationalQuantumRegressor(
        n_qubits=4,
        layers=1,
        maximum_optimizer_iterations=2,
        seed=12,
    ).fit(x, 0.2 + 0.3 * x[:, 0])
    assert np.isfinite(model.initial_loss_)
    assert np.isfinite(model.training_loss_)
    assert model.loss_improvement_ == pytest.approx(
        model.initial_loss_ - model.training_loss_
    )
    assert model.objective_evaluations_ > 0


def test_real_preflight_reads_development_only_and_keeps_final_blind() -> None:
    audit, folds = gate5_preflight(ROOT)
    assert audit["rows"] == 39000
    assert audit["decision_sets"] == 7800
    assert audit["calibration_rows_read"] == 0
    assert audit["final_test_rows_read"] == 0
    assert len(folds) == 12


def test_research_execution_is_blocked_pending_d005_acceptance(tmp_path: Path) -> None:
    with pytest.raises(PermissionError, match="accepts D005"):
        execute_trial(ROOT, "C01-T01", tmp_path)
