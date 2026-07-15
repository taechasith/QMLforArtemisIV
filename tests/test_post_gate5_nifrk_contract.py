"""Contract tests for the D044 nonlinear interaction stack."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d044_nifrk import _fit_interaction, _interaction_features


def test_interaction_feature_map_has_fixed_columns() -> None:
    features = _interaction_features(np.asarray([1.0, 2.0]), np.asarray([3.0, 4.0]))
    assert features.shape == (2, 6)
    np.testing.assert_allclose(features[0], [1.0, 1.0, 3.0, 3.0, 1.0, 9.0])


def test_interaction_fit_returns_finite_coefficients() -> None:
    first = np.asarray([0.0, 1.0, 2.0, 3.0])
    second = np.asarray([1.0, 1.0, 1.0, 1.0])
    target = np.asarray([0.0, 1.0, 4.0, 9.0])
    coefficients = _fit_interaction(first, second, target, 0.001)
    assert coefficients.shape == (6,)
    assert np.all(np.isfinite(coefficients))
