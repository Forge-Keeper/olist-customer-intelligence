from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pyspark.sql import DataFrame


class DataQualityRejectedError(ValueError):
    """Raised when blocking Data Quality rules reject a batch before persistence."""


class QualitySeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class QualityStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class QualityOutcome(StrEnum):
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"


class QualityCategory(StrEnum):
    COMPLETENESS = "COMPLETENESS"
    UNIQUENESS = "UNIQUENESS"
    VALIDITY = "VALIDITY"
    CONSISTENCY = "CONSISTENCY"
    OBSERVATION = "OBSERVATION"


@dataclass(frozen=True)
class QualityRule:
    """Common declarative metadata for one Data Quality rule."""

    rule_id: str
    version: int
    description: str
    category: QualityCategory
    severity: QualitySeverity

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string.")
        if not isinstance(self.version, int) or self.version < 1:
            raise ValueError("rule version must be a positive integer.")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("rule description must be a non-empty string.")
        if not isinstance(self.category, QualityCategory):
            raise TypeError("category must be a QualityCategory.")
        if not isinstance(self.severity, QualitySeverity):
            raise TypeError("severity must be a QualitySeverity.")


@dataclass(frozen=True)
class DataQualityContract:
    """Declarative quality contract kept separate from persisted-table contracts."""

    dataset: str
    layer: str
    rules: tuple[QualityRule, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.dataset, str) or not self.dataset.strip():
            raise ValueError("dataset must be a non-empty string.")
        if not isinstance(self.layer, str) or not self.layer.strip():
            raise ValueError("layer must be a non-empty string.")
        if not isinstance(self.rules, tuple) or not self.rules:
            raise ValueError("rules must be a non-empty tuple.")
        if not all(isinstance(rule, QualityRule) for rule in self.rules):
            raise TypeError("rules must contain only QualityRule values.")
        identities = tuple((rule.rule_id, rule.version) for rule in self.rules)
        if len(identities) != len(set(identities)):
            raise ValueError(
                "quality rules cannot duplicate rule_id/version identities."
            )


@dataclass(frozen=True)
class QualityResult:
    run_id: str
    dataset: str
    layer: str
    rule_id: str
    rule_version: int
    category: QualityCategory
    severity: QualitySeverity
    status: QualityStatus
    observed_value: str
    expected_condition: str
    evaluation_scope: str
    evaluated_at: datetime


@dataclass(frozen=True)
class QualityReport:
    """Structured result of evaluating one dataset quality contract."""

    run_id: str
    dataset: str
    layer: str
    evaluation_scope: str
    row_count: int
    results: tuple[QualityResult, ...]

    @property
    def has_blocking_failures(self) -> bool:
        return any(
            result.status is QualityStatus.FAIL
            and result.severity is QualitySeverity.ERROR
            for result in self.results
        )

    @property
    def outcome(self) -> QualityOutcome:
        if self.has_blocking_failures:
            return QualityOutcome.FAILED
        if any(
            result.status is QualityStatus.FAIL
            and result.severity is QualitySeverity.WARNING
            for result in self.results
        ):
            return QualityOutcome.PASSED_WITH_WARNINGS
        return QualityOutcome.PASSED

    def raise_for_blocking_failures(self) -> None:
        if not self.has_blocking_failures:
            return
        failed = [
            result.rule_id
            for result in self.results
            if result.status is QualityStatus.FAIL
            and result.severity is QualitySeverity.ERROR
        ]
        raise DataQualityRejectedError(
            "Data Quality rejected the batch; blocking rules failed: "
            + ", ".join(failed)
        )


@dataclass(frozen=True)
class QualityCheckedBatch:
    """Batch plus reusable evidence that blocking quality checks already ran."""

    dataframe: DataFrame
    report: QualityReport
    validated_key_columns: tuple[str, ...]
