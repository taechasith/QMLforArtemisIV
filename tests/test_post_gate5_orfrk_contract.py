"""Contract tests for the D046 orthogonalized residual construction."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_post_gate5_d046_orfrk import _orthogonalized_target


def test_orthogonalized_target_removes_shared_training_prediction() -> None:
    residual = np.asarray([1.0, -2.0, 4.0])
    shared = np.asarray([0.25, -1.5, 1.0])
    np.testing.assert_allclose(_orthogonalized_target(residual, shared), [0.75, -0.5, 3.0])


def test_orthogonalized_target_is_zero_when_shared_signal_is_exact() -> None:
    values = np.asarray([0.0, 1.0, -3.0])
    np.testing.assert_allclose(_orthogonalized_target(values, values), 0.0)


def test_orthogonalized_target_rejects_shape_mismatch() -> None:
    try:
        _orthogonalized_target(np.ones(3), np.ones(2))
    except ValueError:
        return
    raise AssertionError("mismatched residual and shared prediction shapes were accepted")
