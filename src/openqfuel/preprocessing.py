"""Leakage-resistant preprocessing for the frozen Phase 1 feature contract."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .gate4 import assert_split_access


def _input_payload(record: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = record.get("inputs", record)
    if not isinstance(payload, Mapping):
        raise ValueError("Each scenario must contain a mapping of inputs")
    return payload


class FrozenFeaturePreprocessor:
    """Fit the shared numeric/categorical transformation on development only."""

    def __init__(
        self,
        numeric_features: Sequence[str],
        categorical_features: Sequence[str],
    ) -> None:
        self.numeric_features = tuple(numeric_features)
        self.categorical_features = tuple(categorical_features)
        if not self.numeric_features or not self.categorical_features:
            raise ValueError("Numeric and categorical feature lists must be nonempty")
        combined = [*self.numeric_features, *self.categorical_features]
        if len(set(combined)) != len(combined):
            raise ValueError("Preprocessing feature names must be unique")

    def _matrix(self, records: Sequence[Mapping[str, Any]]) -> np.ndarray:
        if not records:
            raise ValueError("Preprocessing requires at least one scenario")
        rows: list[list[Any]] = []
        for record in records:
            payload = _input_payload(record)
            numeric = []
            for name in self.numeric_features:
                value = payload.get(name, np.nan)
                numeric.append(np.nan if value is None else float(value))
            categorical = []
            for name in self.categorical_features:
                value = payload.get(name, np.nan)
                categorical.append(np.nan if value is None else str(value))
            rows.append([*numeric, *categorical])
        return np.asarray(rows, dtype=object)

    def fit(
        self, records: Sequence[Mapping[str, Any]], split: str
    ) -> "FrozenFeaturePreprocessor":
        assert_split_access(split, "fit")
        if split != "development":
            raise ValueError("Preprocessing can be fitted on development data only")
        numeric_count = len(self.numeric_features)
        numeric_indices = list(range(numeric_count))
        categorical_indices = list(
            range(numeric_count, numeric_count + len(self.categorical_features))
        )
        self.transformer_ = ColumnTransformer(
            [
                (
                    "numeric",
                    make_pipeline(
                        SimpleImputer(strategy="median", add_indicator=True),
                        StandardScaler(),
                    ),
                    numeric_indices,
                ),
                (
                    "categorical",
                    make_pipeline(
                        SimpleImputer(strategy="most_frequent"),
                        OneHotEncoder(
                            handle_unknown="ignore",
                            sparse_output=False,
                            dtype=float,
                        ),
                    ),
                    categorical_indices,
                ),
            ],
            sparse_threshold=0.0,
        )
        self.transformer_.fit(self._matrix(records))
        return self

    def transform(self, records: Sequence[Mapping[str, Any]], split: str) -> np.ndarray:
        if not hasattr(self, "transformer_"):
            raise RuntimeError("FrozenFeaturePreprocessor is not fitted")
        assert_split_access(split, "transform")
        transformed = np.asarray(
            self.transformer_.transform(self._matrix(records)), dtype=float
        )
        if not np.all(np.isfinite(transformed)):
            raise ValueError("Preprocessing produced a non-finite value")
        return transformed

    def fit_transform(
        self, records: Sequence[Mapping[str, Any]], split: str
    ) -> np.ndarray:
        return self.fit(records, split).transform(records, split)


class QuantumFeatureProjector:
    """Map shared preprocessed features to standardized PCA circuit angles."""

    def __init__(self, n_qubits: int, clipping_standard_deviations: float = 3.0):
        self.n_qubits = n_qubits
        self.clipping_standard_deviations = clipping_standard_deviations
        if n_qubits not in {4, 6, 8, 10, 12}:
            raise ValueError("Qubit count must be one of 4, 6, 8, 10, or 12")
        if clipping_standard_deviations <= 0.0:
            raise ValueError("PCA clipping scale must be positive")

    @staticmethod
    def _matrix(values: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
        matrix = np.asarray(values, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("PCA inputs must be a nonempty two-dimensional array")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("PCA inputs must be finite")
        return matrix

    def fit(
        self, values: Sequence[Sequence[float]] | np.ndarray, split: str
    ) -> "QuantumFeatureProjector":
        assert_split_access(split, "fit")
        if split != "development":
            raise ValueError("Quantum PCA can be fitted on development data only")
        matrix = self._matrix(values)
        if min(matrix.shape) < self.n_qubits:
            raise ValueError("PCA input is too small for the requested qubit count")
        self.pca_ = PCA(n_components=self.n_qubits, svd_solver="full")
        self.pca_.fit(matrix)
        self.component_scale_ = np.sqrt(self.pca_.explained_variance_)
        if np.any(self.component_scale_ <= 0.0):
            raise ValueError("PCA components must have positive development variance")
        return self

    def transform(
        self, values: Sequence[Sequence[float]] | np.ndarray, split: str
    ) -> np.ndarray:
        if not hasattr(self, "pca_"):
            raise RuntimeError("QuantumFeatureProjector is not fitted")
        assert_split_access(split, "transform")
        standardized = self.pca_.transform(self._matrix(values)) / self.component_scale_
        limit = float(self.clipping_standard_deviations)
        return np.clip(standardized, -limit, limit) * (np.pi / limit)

    def fit_transform(
        self, values: Sequence[Sequence[float]] | np.ndarray, split: str
    ) -> np.ndarray:
        return self.fit(values, split).transform(values, split)
