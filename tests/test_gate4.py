from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from openqfuel.gate4 import (
    FINAL_SPLITS,
    FinalTestAccessError,
    assert_no_final_payloads,
    assert_split_access,
    boundary_case_ids,
    build_final_test_manifest,
    build_scenario_manifest,
    build_scenario_schema,
    build_seed_manifest,
    build_tuning_manifest,
    manifest_counts,
    read_csv,
    read_yaml,
    validate_freeze_config,
)
from openqfuel.models import (
    CLASSICAL_FAMILIES,
    QML_CONTROL_FAMILIES,
    QUANTUM_FAMILIES,
    PhysicsResidualRegressor,
    build_classical_classifier,
    build_classical_regressor,
    build_qml_control_classifier,
    build_qml_control_regressor,
)
from openqfuel.phase1_analysis import (
    burn_vector_errors,
    development_target_scale,
    feasibility_constrained_regret,
    feasibility_metrics,
    holm_adjust,
    paired_bootstrap_mean_interval,
    paired_sign_permutation_pvalue,
    regression_metrics,
)
from openqfuel.preprocessing import FrozenFeaturePreprocessor, QuantumFeatureProjector
from openqfuel.qml import (
    NoiseSensitivity,
    QuantumKernelRegressor,
    VariationalQuantumRegressor,
    circuit_state,
    quantum_kernel_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase1_benchmark.yaml"
WINDOWS = ROOT / "data/processed/artemis2/validation_windows.csv"


class Gate4ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_yaml(CONFIG)
        cls.windows = read_csv(WINDOWS)
        cls.rows = build_scenario_manifest(cls.config, cls.windows)

    def test_gate4_remains_pending_human_approval(self) -> None:
        validate_freeze_config(self.config, self.windows)
        self.assertEqual(
            self.config["status"],
            "gate_4_freeze_candidate_pending_human_approval",
        )

    def test_manifest_locks_exact_case_and_split_counts(self) -> None:
        self.assertEqual(len(self.rows), 60)
        self.assertEqual(
            manifest_counts(self.rows),
            {
                "development": 39000,
                "uncertainty_calibration": 6500,
                "in_distribution_final_test": 9750,
                "out_of_distribution_final_test": 9750,
            },
        )
        by_fidelity: dict[str, int] = defaultdict(int)
        for row in self.rows:
            by_fidelity[row["fidelity"]] += int(row["case_count"])
        self.assertEqual(by_fidelity, {"F0": 10000, "F1": 50000, "F2": 5000})
        self.assertEqual(
            sum(int(row["decision_set_count"]) for row in self.rows), 13000
        )
        self.assertTrue(
            all(int(row["candidates_per_decision_set"]) == 5 for row in self.rows)
        )

    def test_group_keys_never_cross_splits(self) -> None:
        split_by_fingerprint: dict[str, set[str]] = defaultdict(set)
        for row in self.rows:
            split_by_fingerprint[row["group_fingerprint"]].add(row["split"])
        self.assertTrue(all(len(value) == 1 for value in split_by_fingerprint.values()))

    def test_boundary_or_tail_fraction_is_at_least_one_quarter(self) -> None:
        total = sum(int(row["case_count"]) for row in self.rows)
        boundary = sum(int(row["boundary_or_tail_case_count"]) for row in self.rows)
        self.assertGreaterEqual(boundary / total, 0.25)

    def test_boundary_identity_selection_is_exact_and_deterministic(self) -> None:
        first = boundary_case_ids(11, "F2", "G01", 10, "U1")
        second = boundary_case_ids(11, "F2", "G01", 10, "U1")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(
            boundary_case_ids(11, "F2", "G18", 10, "U5"),
            [f"F2-G18-{index:06d}" for index in range(1, 11)],
        )

    def test_final_manifest_contains_commitments_but_no_payload(self) -> None:
        rows = build_final_test_manifest(self.rows)
        self.assertEqual(sum(int(row["case_count"]) for row in rows), 19500)
        self.assertEqual(sum(int(row["decision_set_count"]) for row in rows), 3900)
        self.assertTrue(all(row["split"] in FINAL_SPLITS for row in rows))
        self.assertTrue(
            all(row["feature_payload"] == "LOCKED_NOT_GENERATED" for row in rows)
        )
        self.assertTrue(
            all(row["label_payload"] == "LOCKED_NOT_GENERATED" for row in rows)
        )

    def test_seed_and_tuning_manifests_are_complete_and_unique(self) -> None:
        seeds = build_seed_manifest(self.config)
        tuning = build_tuning_manifest(self.config)
        self.assertEqual(len(seeds), 10 * 30)
        self.assertEqual(len({row["training_seed"] for row in seeds}), len(seeds))
        self.assertEqual(len(tuning), 10 * 30)
        counts = Counter(row["model_family"] for row in tuning)
        self.assertEqual(set(counts.values()), {30})
        for row in tuning:
            self.assertIsInstance(json.loads(row["parameters_json"]), dict)
            self.assertEqual(row["execution_status"], "frozen_not_run")
        controls = [
            row for row in tuning if row["model_family"] in QML_CONTROL_FAMILIES
        ]
        self.assertTrue(controls)
        self.assertTrue(
            all(
                row["candidate_role"] == "interpretation_control_not_eligible_to_win"
                for row in controls
            )
        )
        ridge_trials = [
            json.loads(row["parameters_json"])
            for row in tuning
            if row["model_family"] == "ridge_elastic_net"
        ]
        self.assertEqual(
            len({json.dumps(row, sort_keys=True) for row in ridge_trials}), 30
        )
        self.assertTrue(
            all(
                "l1_ratio" not in row if row["estimator"] == "ridge" else True
                for row in ridge_trials
            )
        )

    def test_schema_excludes_identifiers_from_model_inputs(self) -> None:
        schema = build_scenario_schema(self.config)
        inputs = schema["properties"]["inputs"]["properties"]
        for prohibited in self.config["features"]["prohibited"]:
            self.assertNotIn(prohibited, inputs)
        self.assertIn("decision_set_id", schema["properties"])
        self.assertIn("candidate_index", schema["properties"])
        self.assertIn("base_trajectory", schema["properties"])
        self.assertNotIn("outcomes", schema["required"])
        self.assertIn("final_feature_record", schema["x-payload-rules"])
        self.assertIn(
            "robust_total_correction_delta_v_m_s",
            schema["properties"]["outcomes"]["properties"],
        )


class Gate4AccessControlTests(unittest.TestCase):
    def test_both_final_splits_are_blocked_for_every_purpose(self) -> None:
        for split in FINAL_SPLITS:
            with self.subTest(split=split):
                with self.assertRaises(FinalTestAccessError):
                    assert_split_access(split, "read")

    def test_calibration_cannot_select_models(self) -> None:
        for purpose in ("fit", "tune", "feature_selection"):
            with self.subTest(purpose=purpose):
                with self.assertRaises(FinalTestAccessError):
                    assert_split_access("uncertainty_calibration", purpose)
        assert_split_access("uncertainty_calibration", "uncertainty_calibration")

    def test_unexpected_final_payload_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assert_no_final_payloads(root)
            (root / "labels.csv").write_text("forbidden\n", encoding="utf-8")
            with self.assertRaises(FinalTestAccessError):
                assert_no_final_payloads(root)


class FrozenPreprocessingTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(19)
        self.numeric = [f"numeric_{index}" for index in range(6)]
        self.records = []
        for index, values in enumerate(rng.normal(size=(20, 6))):
            inputs = {name: value for name, value in zip(self.numeric, values)}
            inputs["category"] = "A" if index % 2 else "B"
            self.records.append({"inputs": inputs})
        self.records[0]["inputs"]["numeric_0"] = None

    def test_shared_preprocessing_and_quantum_projection_are_development_only(
        self,
    ) -> None:
        preprocessor = FrozenFeaturePreprocessor(self.numeric, ["category"])
        transformed = preprocessor.fit_transform(self.records, "development")
        self.assertEqual(transformed.shape[0], len(self.records))
        self.assertTrue(np.all(np.isfinite(transformed)))

        projector = QuantumFeatureProjector(4)
        angles = projector.fit_transform(transformed, "development")
        self.assertEqual(angles.shape, (len(self.records), 4))
        self.assertTrue(np.all(np.abs(angles) <= np.pi))
        np.testing.assert_array_equal(
            angles, projector.transform(transformed, "development")
        )

        calibration = [{"inputs": {**self.records[1]["inputs"], "category": "C"}}]
        self.assertEqual(
            preprocessor.transform(calibration, "uncertainty_calibration").shape[1],
            transformed.shape[1],
        )
        with self.assertRaises(FinalTestAccessError):
            preprocessor.fit(calibration, "uncertainty_calibration")
        with self.assertRaises(FinalTestAccessError):
            preprocessor.transform(calibration, "in_distribution_final_test")


class FrozenModelTests(unittest.TestCase):
    def test_registered_family_counts_match_gate2_budget(self) -> None:
        self.assertEqual(len(CLASSICAL_FAMILIES), 6)
        self.assertEqual(len(QUANTUM_FAMILIES), 3)

    def test_circuit_and_kernel_are_normalized_and_deterministic(self) -> None:
        x = np.array([[0.1, -0.2, 0.3, 0.4], [0.4, 0.3, -0.2, 0.1]])
        state = circuit_state(x[0], 4, 2)
        self.assertAlmostEqual(float(np.vdot(state, state).real), 1.0, places=12)
        kernel = quantum_kernel_matrix(x, x, 4, 2)
        np.testing.assert_allclose(kernel, kernel.T, atol=1e-12)
        np.testing.assert_allclose(np.diag(kernel), 1.0, atol=1e-12)
        sampled_a = quantum_kernel_matrix(x, x, 4, 2, shots=1024, seed=17)
        sampled_b = quantum_kernel_matrix(x, x, 4, 2, shots=1024, seed=17)
        np.testing.assert_array_equal(sampled_a, sampled_b)

    def test_noise_sensitivity_is_explicit_and_bounded(self) -> None:
        noise = NoiseSensitivity(0.001, 0.01, 0.02)
        x = np.array([[0.1, 0.2, 0.3, 0.4]])
        noisy = quantum_kernel_matrix(x, x, 4, 1, noise=noise)
        self.assertGreaterEqual(noisy[0, 0], 0.5)
        self.assertLess(noisy[0, 0], 1.0)

    def test_bandwidth_and_entanglement_controls_are_executable(self) -> None:
        x = np.array([[0.1, 0.2, -0.3, 0.4], [0.4, -0.1, 0.2, 0.3]])
        narrow = quantum_kernel_matrix(x, x, 4, 1, feature_scale=0.5)
        wide = quantum_kernel_matrix(x, x, 4, 1, feature_scale=2.0)
        unentangled = quantum_kernel_matrix(x, x, 4, 1, entangle=False)
        self.assertFalse(np.allclose(narrow, wide))
        np.testing.assert_allclose(unentangled, unentangled.T, atol=1e-12)
        np.testing.assert_allclose(np.diag(unentangled), 1.0, atol=1e-12)

    def test_quantum_kernel_regressor_fits_synthetic_development_data(self) -> None:
        x = np.array(
            [[value, value**2, -value, 0.5 * value] for value in np.linspace(-1, 1, 8)]
        )
        y = x[:, 0] - 0.25 * x[:, 2]
        model = QuantumKernelRegressor(4, 1, alpha=0.01, landmarks=4, seed=4)
        prediction = model.fit(x, y).predict(x)
        self.assertEqual(prediction.shape, y.shape)
        self.assertTrue(np.all(np.isfinite(prediction)))

    def test_variational_regressor_runs_only_a_tiny_synthetic_smoke(self) -> None:
        x = np.array(
            [[value, -value, value / 2, 0.25] for value in np.linspace(-0.5, 0.5, 5)]
        )
        y = 0.2 + 0.3 * x[:, 0]
        model = VariationalQuantumRegressor(
            n_qubits=4,
            layers=1,
            maximum_optimizer_iterations=2,
            seed=12,
        ).fit(x, y)
        prediction = model.predict(x)
        self.assertEqual(prediction.shape, y.shape)
        self.assertTrue(np.all(np.isfinite(prediction)))

    def test_classical_and_physics_residual_factories_fit_synthetic_data(self) -> None:
        x = np.column_stack((np.linspace(-1, 1, 20), np.linspace(0, 2, 20)))
        y = 1.5 * x[:, 0] + 0.2
        ridge = build_classical_regressor(
            "ridge_elastic_net",
            {"estimator": "ridge", "alpha": 0.01, "l1_ratio": 0.5},
            seed=1,
        )
        self.assertEqual(ridge.fit(x, y).predict(x).shape, y.shape)
        classifier = build_classical_classifier(
            "ridge_elastic_net",
            {"estimator": "elastic_net", "alpha": 0.01, "l1_ratio": 0.5},
            seed=1,
        )
        labels = np.tile([0, 1], 10)
        self.assertEqual(classifier.fit(x, labels).predict(x).shape, labels.shape)
        residual = PhysicsResidualRegressor(ridge, low_fidelity_column=1)
        self.assertEqual(residual.fit(x, y).predict(x).shape, y.shape)
        rff = build_qml_control_regressor(
            "random_fourier_ridge",
            {"gamma": 1.0, "n_components": 16, "alpha": 0.01},
            seed=3,
        )
        self.assertEqual(rff.fit(x, y).predict(x).shape, y.shape)
        rff_classifier = build_qml_control_classifier(
            "random_fourier_ridge",
            {"gamma": 1.0, "n_components": 16, "alpha": 0.01},
            seed=3,
        )
        self.assertEqual(rff_classifier.fit(x, labels).predict(x).shape, labels.shape)


class Phase1AnalysisTests(unittest.TestCase):
    def test_regression_metrics_use_development_only_scale(self) -> None:
        scale = development_target_scale([1.0, 2.0, 3.0, 4.0])
        metrics = regression_metrics([1.0, 2.0], [1.5, 1.5], scale)
        self.assertAlmostEqual(metrics.rmse, 0.5)
        self.assertAlmostEqual(metrics.nrmse, 0.5 / scale)

    def test_feasibility_metrics_and_regret_keep_failures(self) -> None:
        metrics = feasibility_metrics([0, 0, 1, 1], [0.1, 0.4, 0.6, 0.9])
        self.assertEqual(metrics.precision, 1.0)
        self.assertEqual(metrics.recall, 1.0)
        regret = feasibility_constrained_regret(
            ["A", "A", "B", "B"],
            [1.0, 2.0, 1.0, 2.0],
            [0.9, 0.8, 0.9, 0.1],
            [5.0, 4.0, 9.0, 2.0],
            [1, 1, 0, 1],
            infeasible_penalty_m_s=20.0,
        )
        self.assertEqual(regret.decision_sets, 2)
        self.assertEqual(regret.mean_regret_m_s, 10.5)
        self.assertEqual(regret.independently_infeasible_selection_rate, 0.5)
        self.assertEqual(regret.no_reference_feasible_rate, 0.0)

    def test_regret_retains_sets_with_no_feasible_reference(self) -> None:
        regret = feasibility_constrained_regret(
            ["A", "A", "B", "B"],
            [1.0, 2.0, 1.0, 2.0],
            [0.9, 0.8, 0.9, 0.8],
            [5.0, 4.0, 3.0, 2.0],
            [0, 0, 1, 1],
            infeasible_penalty_m_s=20.0,
        )
        self.assertEqual(regret.decision_sets, 2)
        self.assertEqual(regret.mean_regret_m_s, 10.5)
        self.assertEqual(regret.no_reference_feasible_rate, 0.5)

    def test_vector_statistics_and_multiplicity_helpers(self) -> None:
        magnitude, angle = burn_vector_errors(
            [[1, 0, 0], [0, 0, 0]], [[0, 1, 0], [1, 0, 0]]
        )
        np.testing.assert_allclose(magnitude, [0, 1])
        np.testing.assert_allclose(angle, [90, 180])
        np.testing.assert_allclose(holm_adjust([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])

    def test_paired_resampling_is_seed_reproducible(self) -> None:
        values = [0.1, 0.2, -0.1, 0.4]
        first = paired_bootstrap_mean_interval(values, replicates=200, seed=5)
        second = paired_bootstrap_mean_interval(values, replicates=200, seed=5)
        self.assertEqual(first, second)
        p_first = paired_sign_permutation_pvalue(values, replicates=200, seed=9)
        p_second = paired_sign_permutation_pvalue(values, replicates=200, seed=9)
        self.assertEqual(p_first, p_second)


if __name__ == "__main__":
    unittest.main()
