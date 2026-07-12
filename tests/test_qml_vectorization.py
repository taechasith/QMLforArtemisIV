"""Equivalence checks for the batched frozen QML circuit implementation."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

from openqfuel.qml import (
    circuit_features,
    circuit_state,
    quantum_kernel_matrix,
    statevector_batch,
)


def _scalar_statevector(
    matrix: np.ndarray,
    n_qubits: int,
    layers: int,
    parameters: np.ndarray | None,
    feature_scale: float,
    entangle: bool,
) -> np.ndarray:
    return np.vstack(
        [
            circuit_state(
                row,
                n_qubits,
                layers,
                parameters,
                feature_scale,
                entangle,
            )
            for row in matrix
        ]
    )


def _scalar_z_expectations(state: np.ndarray, n_qubits: int) -> np.ndarray:
    probabilities = np.abs(state) ** 2
    indices = np.arange(state.size, dtype=np.int64)
    return np.asarray(
        [
            float(
                np.dot(
                    probabilities,
                    np.where(
                        indices & (1 << (n_qubits - 1 - qubit)),
                        -1.0,
                        1.0,
                    ),
                )
            )
            for qubit in range(n_qubits)
        ]
    )


@pytest.mark.parametrize(
    ("n_qubits", "layers", "entangle"),
    [
        (4, 1, False),
        (4, 2, True),
        (6, 3, True),
        (8, 2, False),
        (10, 1, True),
        (12, 1, False),
    ],
)
def test_statevector_batch_matches_scalar_circuit_state(
    n_qubits: int, layers: int, entangle: bool
) -> None:
    rng = np.random.default_rng(10_000 + 100 * n_qubits + layers)
    matrix = rng.normal(size=(3, 7))
    parameters = rng.uniform(-0.2, 0.2, size=(layers, n_qubits, 2))

    expected = _scalar_statevector(matrix, n_qubits, layers, parameters, 0.5, entangle)
    actual = statevector_batch(
        matrix,
        n_qubits,
        layers,
        parameters,
        feature_scale=0.5,
        entangle=entangle,
    )

    np.testing.assert_allclose(actual, expected, rtol=5e-15, atol=1e-15)
    np.testing.assert_allclose(
        np.linalg.norm(actual, axis=1), 1.0, rtol=0.0, atol=2e-15
    )


def test_batched_features_and_kernel_match_scalar_states() -> None:
    rng = np.random.default_rng(20260712)
    left = rng.normal(size=(7, 5))
    right = rng.normal(size=(4, 5))
    parameters = rng.uniform(-0.15, 0.15, size=(2, 6, 2))
    left_states = _scalar_statevector(left, 6, 2, parameters, 2.0, True)
    expected_features = np.vstack(
        [_scalar_z_expectations(state, 6) for state in left_states]
    )

    actual_features = circuit_features(
        left,
        6,
        2,
        parameters,
        feature_scale=2.0,
        entangle=True,
    )
    np.testing.assert_allclose(
        actual_features, expected_features, rtol=5e-14, atol=2e-15
    )

    kernel_left = _scalar_statevector(left, 6, 2, None, 2.0, True)
    kernel_right = _scalar_statevector(right, 6, 2, None, 2.0, True)
    expected_kernel = np.clip(
        np.abs(kernel_left.conj() @ kernel_right.T) ** 2,
        0.0,
        1.0,
    )
    actual_kernel = quantum_kernel_matrix(
        left,
        right,
        6,
        2,
        feature_scale=2.0,
        entangle=True,
    )
    np.testing.assert_allclose(actual_kernel, expected_kernel, rtol=5e-14, atol=2e-15)

    sampled_expected = (
        np.random.default_rng(91).binomial(4096, expected_kernel) / 4096.0
    )
    sampled_actual = quantum_kernel_matrix(
        left,
        right,
        6,
        2,
        shots=4096,
        seed=91,
        feature_scale=2.0,
        entangle=True,
    )
    np.testing.assert_array_equal(sampled_actual, sampled_expected)


def _variational_objective(
    values: np.ndarray,
    matrix: np.ndarray,
    targets: np.ndarray,
    batched: bool,
) -> float:
    parameters = values[:16].reshape(2, 4, 2)
    head = values[16:20]
    bias = values[-1]
    if batched:
        encoded = circuit_features(
            matrix,
            4,
            2,
            parameters,
            feature_scale=0.5,
            entangle=True,
        )
    else:
        states = _scalar_statevector(matrix, 4, 2, parameters, 0.5, True)
        encoded = np.vstack([_scalar_z_expectations(state, 4) for state in states])
    residual = encoded @ head + bias - targets
    penalty = 0.0001 * np.dot(values[:-1], values[:-1])
    return float(np.mean(residual * residual) + penalty)


def _central_difference(
    values: np.ndarray,
    objective: Callable[[np.ndarray], float],
    step: float = 1e-6,
) -> np.ndarray:
    gradient = np.empty_like(values)
    for index in range(values.size):
        left = values.copy()
        right = values.copy()
        left[index] -= step
        right[index] += step
        gradient[index] = (objective(right) - objective(left)) / (2.0 * step)
    return gradient


def test_variational_objective_and_numerical_gradient_match_scalar_path() -> None:
    rng = np.random.default_rng(55)
    matrix = rng.normal(size=(6, 4))
    targets = rng.normal(size=6)
    values = rng.uniform(-0.1, 0.1, size=21)

    def scalar(candidate: np.ndarray) -> float:
        return _variational_objective(candidate, matrix, targets, False)

    def batched(candidate: np.ndarray) -> float:
        return _variational_objective(candidate, matrix, targets, True)

    assert batched(values) == pytest.approx(scalar(values), rel=5e-14, abs=2e-15)
    np.testing.assert_allclose(
        _central_difference(values, batched),
        _central_difference(values, scalar),
        rtol=2e-8,
        atol=5e-10,
    )
