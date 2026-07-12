"""Frozen Phase 1 model factories and multi-outcome wrappers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.gaussian_process import GaussianProcessClassifier, GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, RBF
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.kernel_approximation import RBFSampler
from sklearn.preprocessing import StandardScaler

from .qml import (
    HybridQuantumResidualRegressor,
    QuantumKernelClassifier,
    QuantumKernelRegressor,
    VariationalQuantumClassifier,
    VariationalQuantumRegressor,
)


CLASSICAL_FAMILIES = (
    "ridge_elastic_net",
    "extra_trees",
    "histogram_gradient_boosting",
    "sparse_gaussian_process",
    "multilayer_perceptron",
    "physics_residual",
)
QUANTUM_FAMILIES = (
    "quantum_kernel",
    "variational_quantum_regressor",
    "hybrid_quantum_residual",
)
QML_CONTROL_FAMILIES = ("random_fourier_ridge",)


def _kernel(name: str, length_scale: float) -> Any:
    if name == "rbf":
        base = RBF(length_scale=length_scale)
    elif name == "matern_1.5":
        base = Matern(length_scale=length_scale, nu=1.5)
    elif name == "matern_2.5":
        base = Matern(length_scale=length_scale, nu=2.5)
    else:
        raise ValueError(f"Unknown Gaussian-process kernel: {name}")
    return ConstantKernel(1.0, constant_value_bounds="fixed") * base


class PhysicsResidualRegressor(RegressorMixin, BaseEstimator):
    """Fit a registered estimator to high-minus-low-fidelity cost."""

    def __init__(
        self,
        estimator: BaseEstimator,
        low_fidelity_column: int = -1,
    ) -> None:
        self.estimator = estimator
        self.low_fidelity_column = low_fidelity_column

    def fit(self, x: np.ndarray, y: Sequence[float]) -> "PhysicsResidualRegressor":
        matrix = np.asarray(x, dtype=float)
        targets = np.asarray(y, dtype=float)
        if matrix.ndim != 2 or targets.shape != (matrix.shape[0],):
            raise ValueError("Physics residual inputs and targets are misaligned")
        baseline = matrix[:, self.low_fidelity_column]
        self.estimator_ = clone(self.estimator).fit(matrix, targets - baseline)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "estimator_"):
            raise RuntimeError("PhysicsResidualRegressor is not fitted")
        matrix = np.asarray(x, dtype=float)
        return matrix[:, self.low_fidelity_column] + self.estimator_.predict(matrix)


def build_classical_regressor(
    family: str,
    parameters: Mapping[str, Any],
    seed: int,
    low_fidelity_column: int = -1,
) -> BaseEstimator:
    """Build one frozen classical cost model from a tuning-manifest row."""

    if family == "ridge_elastic_net":
        if parameters["estimator"] == "ridge":
            model: BaseEstimator = Ridge(alpha=float(parameters["alpha"]))
        else:
            model = ElasticNet(
                alpha=float(parameters["alpha"]),
                l1_ratio=float(parameters["l1_ratio"]),
                max_iter=5000,
                random_state=seed,
            )
        return make_pipeline(StandardScaler(), model)
    if family == "extra_trees":
        return ExtraTreesRegressor(
            n_estimators=int(parameters["n_estimators"]),
            max_features=float(parameters["max_features"]),
            min_samples_leaf=int(parameters["min_samples_leaf"]),
            max_depth=(
                None
                if parameters["max_depth"] is None
                else int(parameters["max_depth"])
            ),
            n_jobs=1,
            random_state=seed,
        )
    if family == "histogram_gradient_boosting":
        return HistGradientBoostingRegressor(
            learning_rate=float(parameters["learning_rate"]),
            max_iter=int(parameters["max_iter"]),
            max_leaf_nodes=int(parameters["max_leaf_nodes"]),
            l2_regularization=float(parameters["l2_regularization"]),
            random_state=seed,
        )
    if family == "sparse_gaussian_process":
        model = GaussianProcessRegressor(
            kernel=_kernel(
                str(parameters["kernel"]), float(parameters["length_scale"])
            ),
            alpha=float(parameters["alpha"]),
            normalize_y=True,
            random_state=seed,
        )
        return make_pipeline(StandardScaler(), model)
    if family == "multilayer_perceptron":
        hidden = tuple(int(value) for value in parameters["hidden_layers"])
        model = MLPRegressor(
            hidden_layer_sizes=hidden,
            activation=str(parameters["activation"]),
            alpha=float(parameters["alpha"]),
            learning_rate_init=float(parameters["learning_rate_init"]),
            early_stopping=True,
            max_iter=500,
            random_state=seed,
        )
        return make_pipeline(StandardScaler(), model)
    if family == "physics_residual":
        if parameters["residual_estimator"] == "ridge":
            residual: BaseEstimator = make_pipeline(
                StandardScaler(), Ridge(alpha=float(parameters["alpha"]))
            )
        else:
            residual = HistGradientBoostingRegressor(
                learning_rate=float(parameters["learning_rate"]),
                max_leaf_nodes=int(parameters["max_leaf_nodes"]),
                l2_regularization=float(parameters["alpha"]),
                max_iter=200,
                random_state=seed,
            )
        return PhysicsResidualRegressor(
            residual,
            low_fidelity_column=low_fidelity_column,
        )
    raise ValueError(f"Unknown classical model family: {family}")


def build_classical_classifier(
    family: str, parameters: Mapping[str, Any], seed: int
) -> BaseEstimator:
    """Build the paired feasibility model for a classical family."""

    if family == "ridge_elastic_net":
        common = {
            "C": 1.0 / max(float(parameters["alpha"]), 1e-12),
            "max_iter": 5000,
            "random_state": seed,
        }
        if parameters["estimator"] == "elastic_net":
            model: BaseEstimator = LogisticRegression(
                **common,
                solver="saga",
                l1_ratio=float(parameters["l1_ratio"]),
            )
        else:
            model = LogisticRegression(**common)
        return make_pipeline(StandardScaler(), model)
    if family == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=int(parameters["n_estimators"]),
            max_features=float(parameters["max_features"]),
            min_samples_leaf=int(parameters["min_samples_leaf"]),
            max_depth=(
                None
                if parameters["max_depth"] is None
                else int(parameters["max_depth"])
            ),
            n_jobs=1,
            random_state=seed,
        )
    if family == "histogram_gradient_boosting":
        return HistGradientBoostingClassifier(
            learning_rate=float(parameters["learning_rate"]),
            max_iter=int(parameters["max_iter"]),
            max_leaf_nodes=int(parameters["max_leaf_nodes"]),
            l2_regularization=float(parameters["l2_regularization"]),
            random_state=seed,
        )
    if family == "sparse_gaussian_process":
        model = GaussianProcessClassifier(
            kernel=_kernel(
                str(parameters["kernel"]), float(parameters["length_scale"])
            ),
            random_state=seed,
        )
        return make_pipeline(StandardScaler(), model)
    if family == "multilayer_perceptron":
        hidden = tuple(int(value) for value in parameters["hidden_layers"])
        model = MLPClassifier(
            hidden_layer_sizes=hidden,
            activation=str(parameters["activation"]),
            alpha=float(parameters["alpha"]),
            learning_rate_init=float(parameters["learning_rate_init"]),
            early_stopping=True,
            max_iter=500,
            random_state=seed,
        )
        return make_pipeline(StandardScaler(), model)
    if family == "physics_residual":
        return HistGradientBoostingClassifier(
            learning_rate=float(parameters["learning_rate"]),
            max_leaf_nodes=int(parameters["max_leaf_nodes"]),
            l2_regularization=float(parameters["alpha"]),
            max_iter=200,
            random_state=seed,
        )
    raise ValueError(f"Unknown classical model family: {family}")


def build_quantum_regressor(
    family: str,
    parameters: Mapping[str, Any],
    seed: int,
    low_fidelity_column: int = -1,
) -> BaseEstimator:
    qubits = int(parameters["qubits"])
    layers = int(parameters["data_reupload_layers"])
    feature_scale = float(parameters.get("feature_scale", 1.0))
    entangle = bool(parameters.get("entangle", True))
    if family == "quantum_kernel":
        return QuantumKernelRegressor(
            n_qubits=qubits,
            layers=layers,
            alpha=float(parameters["alpha"]),
            landmarks=int(parameters["landmarks"]),
            seed=seed,
            feature_scale=feature_scale,
            entangle=entangle,
        )
    if family == "variational_quantum_regressor":
        return VariationalQuantumRegressor(
            n_qubits=qubits,
            layers=layers,
            regularization=float(parameters["regularization"]),
            maximum_optimizer_iterations=int(
                parameters["maximum_optimizer_iterations"]
            ),
            seed=seed,
            feature_scale=feature_scale,
            entangle=entangle,
        )
    if family == "hybrid_quantum_residual":
        return HybridQuantumResidualRegressor(
            low_fidelity_column=low_fidelity_column,
            n_qubits=qubits,
            layers=layers,
            regularization=float(parameters["regularization"]),
            maximum_optimizer_iterations=int(
                parameters["maximum_optimizer_iterations"]
            ),
            seed=seed,
            feature_scale=feature_scale,
            entangle=entangle,
        )
    raise ValueError(f"Unknown quantum model family: {family}")


def build_quantum_classifier(
    family: str, parameters: Mapping[str, Any], seed: int
) -> BaseEstimator:
    qubits = int(parameters["qubits"])
    layers = int(parameters["data_reupload_layers"])
    feature_scale = float(parameters.get("feature_scale", 1.0))
    entangle = bool(parameters.get("entangle", True))
    if family == "quantum_kernel":
        return QuantumKernelClassifier(
            n_qubits=qubits,
            layers=layers,
            alpha=float(parameters["alpha"]),
            landmarks=int(parameters["landmarks"]),
            seed=seed,
            feature_scale=feature_scale,
            entangle=entangle,
        )
    return VariationalQuantumClassifier(
        n_qubits=qubits,
        layers=layers,
        regularization=float(parameters["regularization"]),
        maximum_optimizer_iterations=int(parameters["maximum_optimizer_iterations"]),
        seed=seed,
        feature_scale=feature_scale,
        entangle=entangle,
    )


def build_qml_control_regressor(
    family: str, parameters: Mapping[str, Any], seed: int
) -> BaseEstimator:
    """Build a preregistered classical control for interpreting a QML result."""

    if family == "random_fourier_ridge":
        return make_pipeline(
            StandardScaler(),
            RBFSampler(
                gamma=float(parameters["gamma"]),
                n_components=int(parameters["n_components"]),
                random_state=seed,
            ),
            Ridge(alpha=float(parameters["alpha"])),
        )
    raise ValueError(f"Unknown QML control family: {family}")


def build_qml_control_classifier(
    family: str, parameters: Mapping[str, Any], seed: int
) -> BaseEstimator:
    """Build the feasibility head paired with a QML interpretation control."""

    if family == "random_fourier_ridge":
        return make_pipeline(
            StandardScaler(),
            RBFSampler(
                gamma=float(parameters["gamma"]),
                n_components=int(parameters["n_components"]),
                random_state=seed,
            ),
            LogisticRegression(
                C=1.0 / max(float(parameters["alpha"]), 1e-12),
                max_iter=5000,
                random_state=seed,
            ),
        )
    raise ValueError(f"Unknown QML control family: {family}")


@dataclass
class CostFeasibilitySurrogate:
    """Paired cost and feasibility estimators with one shared split."""

    cost_model: BaseEstimator
    feasibility_model: BaseEstimator

    def fit(
        self,
        x: np.ndarray,
        cost: Sequence[float],
        feasible: Sequence[int],
    ) -> "CostFeasibilitySurrogate":
        self.cost_model.fit(x, cost)
        self.feasibility_model.fit(x, feasible)
        return self

    def predict(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        cost = np.asarray(self.cost_model.predict(x), dtype=float)
        probability = np.asarray(
            self.feasibility_model.predict_proba(x)[:, 1], dtype=float
        )
        return cost, probability
