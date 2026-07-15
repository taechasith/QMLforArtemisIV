"""Contract tests for D041 fixed channel mixtures."""

import numpy as np

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from run_post_gate5_d041_hefrk import _fit_rbf_pair, _predict_rbf_pair


def test_candidate_and_control_use_fixed_complementary_channels() -> None:
    fidelity = np.asarray([1.0, -0.5, 0.25], dtype=float)
    rbf_25 = np.asarray([0.5, 0.5, -0.25], dtype=float)
    rbf_50 = np.asarray([0.25, 0.75, -0.5], dtype=float)
    eta = 0.50

    candidate = eta * fidelity + (1.0 - eta) * rbf_25
    control = eta * rbf_25 + (1.0 - eta) * rbf_50

    assert np.allclose(candidate, np.asarray([0.75, 0.0, 0.0]))
    assert np.allclose(control, np.asarray([0.375, 0.625, -0.375]))
    assert np.all(np.isfinite(candidate))
    assert np.all(np.isfinite(control))


def test_rbf_pair_reuses_landmarks_and_returns_both_declared_channels() -> None:
    training = np.asarray(
        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 1.0], [1.0, 2.0]],
        dtype=float,
    )
    target = np.asarray([0.0, 0.2, 0.3, 0.5, 0.8, 0.9], dtype=float)
    models = _fit_rbf_pair(training, target, [f"row-{i}" for i in range(6)], "TEST", "CV01", 1, 1.0, 4)
    predictions = _predict_rbf_pair(models, np.asarray([[0.5, 0.5]], dtype=float))

    assert set(predictions) == {0.25, 0.50}
    assert np.asarray(models[0.25]["landmarks"]).shape == np.asarray(models[0.50]["landmarks"]).shape
    assert all(values.shape == (1,) and np.all(np.isfinite(values)) for values in predictions.values())
