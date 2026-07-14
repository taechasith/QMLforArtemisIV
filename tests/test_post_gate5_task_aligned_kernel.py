from __future__ import annotations

import numpy as np
import pytest

from openqfuel.qml import TaskAlignedProjection


def test_task_aligned_projection_is_fold_local_and_finite() -> None:
    rng = np.random.default_rng(2036)
    x = rng.normal(size=(32, 5))
    y = 2.0 * x[:, 0] - 0.5 * x[:, 2] + 0.05 * rng.normal(size=32)
    projection = TaskAlignedProjection(n_components=3).fit(x, y)
    scores = projection.transform(x)
    changed_validation = projection.transform(x + 100.0)
    assert scores.shape == (32, 3)
    assert np.all(np.isfinite(scores))
    assert not np.allclose(scores, changed_validation)


def test_task_aligned_projection_rejects_degenerate_inputs() -> None:
    with pytest.raises(ValueError, match="degenerate score"):
        TaskAlignedProjection(n_components=2).fit(
            np.ones((8, 3)), np.linspace(0.0, 1.0, 8)
        )
