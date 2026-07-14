"""Contract tests for D040 training-only feature-map centering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import numpy as np

from run_post_gate5_d040_cegfrk import _fit_centered_rbf, _predict_centered_rbf


def test_centered_rbf_uses_training_mean_for_validation() -> None:
    training = np.asarray(
        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 1.0], [1.0, 2.0]],
        dtype=float,
    )
    target = np.asarray([0.0, 0.2, 0.3, 0.5, 0.8, 0.9], dtype=float)
    model = _fit_centered_rbf(
        training,
        target,
        [f"row-{index}" for index in range(training.shape[0])],
        "TEST",
        "CV01",
        1,
        0.25,
        1.0,
        4,
    )

    assert model["train_mean_abs_after_centering"] < 1e-12
    prediction = _predict_centered_rbf(model, np.asarray([[0.5, 0.5]], dtype=float))
    assert prediction.shape == (1,)
    assert np.all(np.isfinite(prediction))
