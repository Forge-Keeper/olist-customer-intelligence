from datetime import datetime
from unittest.mock import Mock

import pytest

from olist_data_platform.platform.delta import ColumnContract, DatasetContract
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    QualityCategory,
    QualityCheckedBatch,
    QualityReport,
    QualityResult,
    QualitySeverity,
    QualityStatus,
)


def _config() -> DatasetContract:
    return DatasetContract(
        columns=(
            ColumnContract("id", "string", False, "Logical identifier."),
            ColumnContract("payload", "string", False, "Test payload."),
        ),
        key_columns=("id",),
    )


def _report() -> QualityReport:
    return QualityReport(
        run_id="run-1",
        dataset="example",
        layer="bronze",
        evaluation_scope="{}",
        row_count=1,
        results=(),
    )


def _blocking_report() -> QualityReport:
    result = QualityResult(
        run_id="run-1",
        dataset="example",
        layer="bronze",
        rule_id="DQ01",
        rule_version=1,
        category=QualityCategory.COMPLETENESS,
        severity=QualitySeverity.ERROR,
        status=QualityStatus.FAIL,
        observed_value='{"null_row_count":1}',
        expected_condition="id contains no null values",
        evaluation_scope="{}",
        evaluated_at=datetime(2026, 8, 28),
    )
    return QualityReport(
        run_id="run-1",
        dataset="example",
        layer="bronze",
        evaluation_scope="{}",
        row_count=1,
        results=(result,),
    )


def test_checked_write_reuses_key_evidence_without_legacy_key_scan() -> None:
    writer = BronzeWriter(Mock(), "bronze.example", _config())
    prepared = Mock()
    writer._prepare_checked_dataframe = Mock(return_value=prepared)
    writer._persist_prepared = Mock()
    writer._validate_primary_key_values = Mock()
    checked = QualityCheckedBatch(
        dataframe=Mock(),
        report=_report(),
        validated_key_columns=("id",),
    )

    writer.write_checked(checked)

    writer._prepare_checked_dataframe.assert_called_once_with(checked.dataframe)
    writer._validate_primary_key_values.assert_not_called()
    writer._persist_prepared.assert_called_once_with(prepared)


def test_checked_write_rejects_key_evidence_for_different_contract() -> None:
    writer = BronzeWriter(Mock(), "bronze.example", _config())
    checked = QualityCheckedBatch(
        dataframe=Mock(),
        report=_report(),
        validated_key_columns=("other_id",),
    )

    with pytest.raises(ValueError, match="key evidence"):
        writer.write_checked(checked)


def test_checked_write_rejects_blocking_quality_before_key_evidence_check() -> None:
    writer = BronzeWriter(Mock(), "bronze.example", _config())
    checked = QualityCheckedBatch(
        dataframe=Mock(),
        report=_blocking_report(),
        validated_key_columns=(),
    )

    with pytest.raises(DataQualityRejectedError, match="DQ01"):
        writer.write_checked(checked)
