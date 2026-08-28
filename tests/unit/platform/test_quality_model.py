from datetime import datetime

import pytest

from olist_data_platform.platform.quality import (
    AllowedValuesRule,
    DataQualityContract,
    DataQualityRejectedError,
    ExpectedCombinationsRule,
    QualityCategory,
    QualityOutcome,
    QualityReport,
    QualityResult,
    QualitySeverity,
    QualityStatus,
    UniqueRule,
)


def _result(
    *,
    rule_id: str,
    severity: QualitySeverity,
    status: QualityStatus,
) -> QualityResult:
    return QualityResult(
        run_id="run-1",
        dataset="example",
        layer="bronze",
        rule_id=rule_id,
        rule_version=1,
        category=QualityCategory.VALIDITY,
        severity=severity,
        status=status,
        observed_value="{}",
        expected_condition="example condition",
        evaluation_scope="{}",
        evaluated_at=datetime(2026, 8, 27),
    )


def test_quality_report_distinguishes_rule_status_from_blocking_policy() -> None:
    report = QualityReport(
        run_id="run-1",
        dataset="example",
        layer="bronze",
        evaluation_scope="{}",
        row_count=1,
        results=(
            _result(
                rule_id="WARN-1",
                severity=QualitySeverity.WARNING,
                status=QualityStatus.FAIL,
            ),
            _result(
                rule_id="INFO-1",
                severity=QualitySeverity.INFO,
                status=QualityStatus.PASS,
            ),
        ),
    )

    assert report.has_blocking_failures is False
    assert report.outcome is QualityOutcome.PASSED_WITH_WARNINGS
    report.raise_for_blocking_failures()


def test_quality_report_raises_only_for_failed_error_rules() -> None:
    report = QualityReport(
        run_id="run-1",
        dataset="example",
        layer="bronze",
        evaluation_scope="{}",
        row_count=1,
        results=(
            _result(
                rule_id="ERROR-1",
                severity=QualitySeverity.ERROR,
                status=QualityStatus.FAIL,
            ),
        ),
    )

    assert report.outcome is QualityOutcome.FAILED
    with pytest.raises(DataQualityRejectedError, match="ERROR-1"):
        report.raise_for_blocking_failures()


def test_data_quality_contract_rejects_duplicate_rule_identity() -> None:
    rule = UniqueRule(
        rule_id="KEY-1",
        version=1,
        description="Example uniqueness rule.",
        category=QualityCategory.UNIQUENESS,
        severity=QualitySeverity.ERROR,
        columns=("id",),
    )

    with pytest.raises(ValueError, match="duplicate rule_id/version"):
        DataQualityContract(
            dataset="example",
            layer="bronze",
            rules=(rule, rule),
        )


def test_rule_contracts_reject_ambiguous_empty_configuration() -> None:
    with pytest.raises(ValueError, match="allowed_values cannot be empty"):
        AllowedValuesRule(
            rule_id="VALUES-1",
            version=1,
            description="Example allowed values rule.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            column="status",
            allowed_values=(),
        )

    with pytest.raises(ValueError, match="configured column count"):
        ExpectedCombinationsRule(
            rule_id="COMBO-1",
            version=1,
            description="Example expected combinations rule.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("year", "variable"),
            expected_combinations=(("2018",),),
        )
