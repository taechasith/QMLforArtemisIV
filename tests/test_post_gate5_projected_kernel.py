from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from openqfuel.gate4 import FinalTestAccessError
from openqfuel.post_gate5 import (
    assert_post_gate5_scope,
    validate_future_research_discussion_row,
)
from openqfuel.qml import (
    ProjectedQuantumKernelClassifier,
    ProjectedQuantumKernelRegressor,
    deterministic_landmark_indices,
    median_projected_kernel_gamma,
    one_rdm_distance_matrix,
    pauli_xyz_expectations,
    projected_quantum_features,
    projected_quantum_kernel_from_features,
    statevector_batch,
    symmetrize_and_clip_psd,
)


ROOT = Path(__file__).resolve().parents[1]


def test_pauli_xyz_projection_matches_known_reduced_states() -> None:
    one_qubit = np.asarray(
        [
            [1.0, 0.0],
            [1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)],
            [1.0 / np.sqrt(2.0), 1.0j / np.sqrt(2.0)],
        ],
        dtype=complex,
    )
    expected = np.asarray(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )
    np.testing.assert_allclose(
        pauli_xyz_expectations(one_qubit, 1), expected, atol=1e-14
    )

    bell = np.zeros((1, 4), dtype=complex)
    bell[0, 0] = 1.0 / np.sqrt(2.0)
    bell[0, 3] = 1.0 / np.sqrt(2.0)
    np.testing.assert_allclose(pauli_xyz_expectations(bell, 2), 0.0, atol=1e-14)


def test_projected_features_match_batched_statevector_projection() -> None:
    rng = np.random.default_rng(20260713)
    values = rng.normal(size=(5, 4))
    states = statevector_batch(
        values,
        4,
        2,
        feature_scale=0.5,
        entangle=True,
    )
    expected = pauli_xyz_expectations(states, 4)
    actual = projected_quantum_features(
        values,
        4,
        2,
        feature_scale=0.5,
        entangle=True,
    )
    np.testing.assert_allclose(actual, expected, rtol=5e-14, atol=2e-15)


def test_projected_kernel_uses_one_rdm_frobenius_distance() -> None:
    left = np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    right = np.asarray([[0.0, 0.0, 1.0]])
    distance = one_rdm_distance_matrix(left, right)
    expected_distance = 0.5 * np.asarray([[2.0], [2.0]])
    np.testing.assert_allclose(distance, expected_distance)

    kernel = projected_quantum_kernel_from_features(left, right, gamma=2.0)
    np.testing.assert_allclose(kernel, np.exp(-2.0 * expected_distance))


def test_median_gamma_is_training_fold_local_and_fails_on_zero_distance() -> None:
    training = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    validation = np.asarray([[100.0, 100.0, 100.0]])
    gamma = median_projected_kernel_gamma(training, gamma_multiplier=4.0)
    same_gamma_after_validation_changes = median_projected_kernel_gamma(
        training,
        gamma_multiplier=4.0,
    )
    assert gamma == same_gamma_after_validation_changes
    assert validation.shape == (1, 3)

    with pytest.raises(ValueError, match="median distance is zero"):
        median_projected_kernel_gamma(np.ones((3, 3)))


def test_deterministic_landmarks_are_shared_by_q01b_and_fqk() -> None:
    row_ids = [f"F1-G01-{index:06d}" for index in range(1, 12)]
    q01b = deterministic_landmark_indices(row_ids, "P007", "CV03", 4, 5)
    fqk = deterministic_landmark_indices(row_ids, "P007", "CV03", 4, 5)
    changed_seed = deterministic_landmark_indices(row_ids, "P007", "CV03", 5, 5)
    np.testing.assert_array_equal(q01b, fqk)
    assert set(q01b).issubset(set(range(len(row_ids))))
    assert not np.array_equal(q01b, changed_seed)


def test_psd_clipping_records_negative_eigenvalues() -> None:
    kernel = np.asarray([[1.0, 2.0], [2.0, 1.0]])
    clipped, info = symmetrize_and_clip_psd(kernel)
    eigenvalues = np.linalg.eigvalsh(clipped)
    assert info.clipped_eigenvalues == 1
    assert info.max_negative_eigenvalue == pytest.approx(-1.0)
    assert np.min(eigenvalues) >= 0.0


def test_projected_estimators_fit_synthetic_data_and_share_landmarks() -> None:
    grid = np.linspace(-1.0, 1.0, 14)
    x = np.column_stack((grid, grid**2, -grid, 0.25 * grid))
    y = 0.4 * x[:, 0] - 0.1 * x[:, 2]
    labels = (y > np.median(y)).astype(int)
    row_ids = [f"synthetic-{index:03d}" for index in range(x.shape[0])]
    common = {
        "n_qubits": 4,
        "layers": 1,
        "alpha": 0.01,
        "landmarks": 6,
        "gamma_multiplier": 1.0,
        "projection_id": "P003",
        "fold_id": "CV01",
        "seed_index": 2,
        "feature_scale": 1.0,
        "entangle": True,
    }
    regressor = ProjectedQuantumKernelRegressor(**common).fit(x, y, row_ids=row_ids)
    classifier = ProjectedQuantumKernelClassifier(**common).fit(
        x, labels, row_ids=row_ids
    )

    prediction = regressor.predict(x)
    probability = classifier.predict_proba(x)[:, 1]
    assert prediction.shape == y.shape
    assert probability.shape == y.shape
    assert np.all(np.isfinite(prediction))
    assert np.all((0.0 <= probability) & (probability <= 1.0))
    np.testing.assert_array_equal(
        regressor.landmark_indices_,
        classifier.regressor_.landmark_indices_,
    )
    assert regressor.gamma_ == classifier.regressor_.gamma_


def test_d008_scope_guard_allows_only_synthetic_before_execution_decision() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_exploratory.yaml").read_text(encoding="utf-8")
    )
    assert_post_gate5_scope(
        config,
        action="implementation",
        data_scope="synthetic",
    )
    assert_post_gate5_scope(
        config,
        action="synthetic_validation",
        data_scope="synthetic",
    )
    with pytest.raises(PermissionError, match="research-data fitting"):
        assert_post_gate5_scope(config, action="research_fit", data_scope="development")
    with pytest.raises(FinalTestAccessError):
        assert_post_gate5_scope(
            config,
            action="research_fit",
            data_scope="in_distribution_final_test",
        )


def test_future_discussion_rows_are_firewalled() -> None:
    config = yaml.safe_load(
        (ROOT / "configs/post_gate5_exploratory.yaml").read_text(encoding="utf-8")
    )
    required = config["failure_and_stop_policy"]["required_fields"]
    row = {
        field: "synthetic-placeholder"
        for field in [*required, "reporting_commit"]
    }
    row.update(
        {
            "new_protocol_required": "true",
            "active_pipeline_change_authorized": "false",
            "post_outcome_retry_authorized": "false",
        }
    )
    validate_future_research_discussion_row(row, required)

    row["active_pipeline_change_authorized"] = "true"
    with pytest.raises(ValueError, match="active_pipeline_change_authorized"):
        validate_future_research_discussion_row(row, required)

