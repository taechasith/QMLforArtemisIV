"""Contract tests for the D039 error-conditioned projection input."""

import numpy as np

from openqfuel.qml import TaskAlignedProjection


def test_error_conditioned_projection_appends_one_baseline_feature() -> None:
    compressed = np.asarray(
        [[0.0, 1.0], [1.0, 0.0], [2.0, 1.0], [3.0, 2.0], [4.0, 3.0], [5.0, 5.0]],
        dtype=float,
    )
    cross_fitted_baseline = np.asarray([0.1, 0.3, 0.8, 1.2, 1.9, 2.7], dtype=float)
    target = np.asarray([0.2, 0.4, 0.9, 1.3, 2.0, 2.8], dtype=float)
    training_input = np.column_stack((compressed, cross_fitted_baseline))

    projection = TaskAlignedProjection(n_components=2).fit(training_input, target)
    scores = projection.transform(training_input)

    assert training_input.shape == (6, 3)
    assert scores.shape == (6, 2)
    assert np.all(np.isfinite(scores))
