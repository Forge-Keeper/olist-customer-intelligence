from __future__ import annotations

from dataclasses import dataclass

from olist_data_platform.platform.quality.model import QualityRule


def _validate_columns(field_name: str, columns: tuple[str, ...]) -> None:
    if not isinstance(columns, tuple):
        raise TypeError(f"{field_name} must be a tuple of strings.")
    if not columns:
        raise ValueError(f"{field_name} cannot be empty.")
    if not all(isinstance(column, str) for column in columns):
        raise TypeError(f"{field_name} must contain only strings.")
    if any(not column.strip() for column in columns):
        raise ValueError(f"{field_name} cannot contain empty column names.")
    if len(columns) != len(set(columns)):
        raise ValueError(f"{field_name} cannot contain duplicate columns.")


@dataclass(frozen=True)
class NonEmptyRule(QualityRule):
    """Require at least one row in the evaluated DataFrame scope."""


@dataclass(frozen=True)
class NotNullRule(QualityRule):
    """Require the configured columns to contain no null values."""

    columns: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_columns("columns", self.columns)


@dataclass(frozen=True)
class UniqueRule(QualityRule):
    """Require configured columns to form a unique key in the evaluated scope."""

    columns: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_columns("columns", self.columns)


@dataclass(frozen=True)
class AllowedValuesRule(QualityRule):
    """Require a column value to belong to an explicit allow-list."""

    column: str
    allowed_values: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.column, str):
            raise TypeError("column must be a string.")
        if not self.column.strip():
            raise ValueError("column cannot be empty.")
        if not isinstance(self.allowed_values, tuple):
            raise TypeError("allowed_values must be a tuple of strings.")
        if not self.allowed_values:
            raise ValueError("allowed_values cannot be empty.")
        if not all(isinstance(value, str) for value in self.allowed_values):
            raise TypeError("allowed_values must contain only strings.")
        if any(not value.strip() for value in self.allowed_values):
            raise ValueError("allowed_values cannot contain empty values.")
        if len(self.allowed_values) != len(set(self.allowed_values)):
            raise ValueError("allowed_values cannot contain duplicates.")


@dataclass(frozen=True)
class PredicateRule(QualityRule):
    """Require every evaluated row to satisfy one Spark SQL predicate."""

    expression: str
    expected_condition: str

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("expression", "expected_condition"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")


@dataclass(frozen=True)
class ExpectedCombinationsRule(QualityRule):
    """Require all explicitly expected dimension combinations to be present."""

    columns: tuple[str, ...]
    expected_combinations: tuple[tuple[str, ...], ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _validate_columns("columns", self.columns)
        if not isinstance(self.expected_combinations, tuple):
            raise TypeError("expected_combinations must be a tuple of tuples.")
        if not self.expected_combinations:
            raise ValueError("expected_combinations cannot be empty.")
        for combination in self.expected_combinations:
            if not isinstance(combination, tuple):
                raise TypeError("expected_combinations must contain only tuples.")
            if len(combination) != len(self.columns):
                raise ValueError(
                    "each expected combination must match the configured column count."
                )
            if not all(
                isinstance(value, str) and value.strip()
                for value in combination
            ):
                raise ValueError(
                    "expected combinations must contain non-empty string values."
                )
        if len(self.expected_combinations) != len(set(self.expected_combinations)):
            raise ValueError("expected_combinations cannot contain duplicates.")


@dataclass(frozen=True)
class ObservedCountRule(QualityRule):
    """Count rows matching a Spark SQL expression without blocking by itself."""

    expression: str
    expected_condition: str

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("expression", "expected_condition"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")
