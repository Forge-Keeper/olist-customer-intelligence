from __future__ import annotations

from dataclasses import dataclass

from olist_data_platform.platform.quality.model import QualityRule


@dataclass(frozen=True)
class NonEmptyRule(QualityRule):
    pass


@dataclass(frozen=True)
class NotNullRule(QualityRule):
    columns: tuple[str, ...]


@dataclass(frozen=True)
class UniqueRule(QualityRule):
    columns: tuple[str, ...]


@dataclass(frozen=True)
class AllowedValuesRule(QualityRule):
    column: str
    allowed_values: tuple[str, ...]


@dataclass(frozen=True)
class PredicateRule(QualityRule):
    expression: str
    expected_condition: str


@dataclass(frozen=True)
class ExpectedCombinationsRule(QualityRule):
    columns: tuple[str, ...]
    expected_combinations: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ObservedCountRule(QualityRule):
    expression: str
    expected_condition: str
