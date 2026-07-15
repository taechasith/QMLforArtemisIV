"""Contract tests for the D047 orthogonalized multi-scale stack."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d047_omfrk import _fit_linear_stack


def test_omfrk_stack_requires_four_columns() -> None:
    coefficients = _fit_linear_stack(np.ones((5, 4)), np.ones(5), 0.001)
    assert coefficients.shape == (4,)
    assert np.all(np.isfinite(coefficients))


def test_omfrk_stack_rejects_wrong_feature_count() -> None:
    try:
        _fit_linear_stack(np.ones((5, 3)), np.ones(5), 0.001)
    except ValueError:
        return
    raise AssertionError("three-column design was accepted")
