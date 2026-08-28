from datetime import datetime
from unittest.mock import Mock

import pytest

from olist_data_platform.platform.delta import ColumnContract, DatasetContract
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.quality import (
    QualityCheckedBatch,
    QualityReport,
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
