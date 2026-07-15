"""Contract tests for the D045 multi-scale stack."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d045_msfrk import _fit_linear_stack


def test_multiscale_stack_requires_seven_columns() -> None:
    features = np.ones((4, 7))
    coefficients = _fit_linear_stack(features, np.ones(4), 0.001)
    assert coefficients.shape == (7,)
    assert np.all(np.isfinite(coefficients))


def test_multiscale_stack_rejects_wrong_feature_count() -> None:
    try:
        _fit_linear_stack(np.ones((4, 6)), np.ones(4), 0.001)
    except ValueError:
        return
    raise AssertionError("six-column design was accepted")
