from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from olist_data_platform.platform.delta.silver import snapshot_writer as snapshot_writer_module
from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.contract import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.silver import SilverSnapshotWriter
from olist_data_platform.platform.quality import (
    DataQualityContract,
    DataQualityRejectedError,
    NotNullRule,
    QualityCategory,
    QualityCheckedBatch,
    QualityReport,
    QualityResult,
    QualitySeverity,
    QualityStatus,
)


def _dataset_contract(
    write_strategy: WriteStrategy = WriteStrategy.FULL_REPLACE,
) -> DatasetContract:
    return DatasetContract(
        columns=(
            ColumnContract("id", "string", False, "Test identifier."),
            ColumnContract("value", "string", True, "Test value."),
        ),
        key_columns=("id",),
        write_strategy=write_strategy,
        metadata=TableMetadata(description="Test Silver dataset."),
    )


def _quality_contract() -> DataQualityContract:
    return DataQualityContract(
        dataset="test_silver",
        layer="silver",
        rules=(
            NotNullRule(
                rule_id="TEST-SILVER-DQ01",
                version=1,
                description="id must be present.",
                category=QualityCategory.COMPLETENESS,
                severity=QualitySeverity.ERROR,
                columns=("id",),
            ),
        ),
    )


def _report(
    *,
    row_count: int = 1,
    status: QualityStatus = QualityStatus.PASS,
) -> QualityReport:
    return QualityReport(
        run_id="run-1",
        dataset="test_silver",
        layer="silver",
        evaluation_scope='{"source":"test"}',
        row_count=row_count,
        results=(
            QualityResult(
                run_id="run-1",
                dataset="test_silver",
                layer="silver",
                rule_id="TEST-SILVER-DQ01",
                rule_version=1,
                category=QualityCategory.COMPLETENESS,
                severity=QualitySeverity.ERROR,
                status=status,
                observed_value="{}",
                expected_condition="id must be present",
                evaluation_scope='{"source":"test"}',
                evaluated_at=datetime(2026, 9, 17, 20, 0, 0),
            ),
        ),
    )


def _install_quality_mocks(
    monkeypatch: pytest.MonkeyPatch,
    *,
    dataframe: MagicMock,
    report: QualityReport,
) -> tuple[MagicMock, MagicMock]:
    runner = MagicMock()
    runner.evaluate.return_value = QualityCheckedBatch(
        dataframe=dataframe,
        report=report,
        validated_key_columns=("id",),
    )
    result_writer = MagicMock()

    monkeypatch.setattr(
        snapshot_writer_module,
        "DataQualityRunner",
        lambda: runner,
    )
    monkeypatch.setattr(
        snapshot_writer_module,
        "QualityResultWriter",
        lambda spark, target_table: result_writer,
    )
    return runner, result_writer


def test_requires_full_replace_contract() -> None:
    with pytest.raises(
        ValueError,
        match="requires DatasetContract.write_strategy to be FULL_REPLACE",
    ):
        SilverSnapshotWriter(
            MagicMock(),
            "catalog.silver.test",
            _dataset_contract(WriteStrategy.MERGE),
            _quality_contract(),
            "admin.quality.data_quality_results",
        )


def test_blocking_quality_is_persisted_before_target_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataframe = MagicMock()
    report = _report(status=QualityStatus.FAIL)
    runner, result_writer = _install_quality_mocks(
        monkeypatch,
        dataframe=dataframe,
        report=report,
    )
    lifecycle = MagicMock()
    lifecycle_factory = MagicMock(return_value=lifecycle)
    monkeypatch.setattr(
        snapshot_writer_module,
        "DeltaTableLifecycle",
        lifecycle_factory,
    )

    writer = SilverSnapshotWriter(
        MagicMock(),
        "catalog.silver.test",
        _dataset_contract(),
        _quality_contract(),
        "admin.quality.data_quality_results",
    )

    with pytest.raises(DataQualityRejectedError):
        writer.write_checked(
            dataframe,
            run_id="run-1",
            evaluation_scope='{"source":"test"}',
        )

    runner.evaluate.assert_called_once()
    result_writer.write.assert_called_once_with(report)
    lifecycle_factory.assert_not_called()
    dataframe.select.assert_not_called()


def test_empty_snapshot_preserves_target_and_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataframe = MagicMock()
    report = _report(row_count=0)
    _, result_writer = _install_quality_mocks(
        monkeypatch,
        dataframe=dataframe,
        report=report,
    )
    lifecycle_factory = MagicMock()
    monkeypatch.setattr(
        snapshot_writer_module,
        "DeltaTableLifecycle",
        lifecycle_factory,
    )
    message = (
        "Silver Test FULL_REPLACE snapshot cannot be empty; "
        "the existing target was preserved."
    )
    writer = SilverSnapshotWriter(
        MagicMock(),
        "catalog.silver.test",
        _dataset_contract(),
        _quality_contract(),
        "admin.quality.data_quality_results",
        empty_snapshot_message=message,
    )

    with pytest.raises(ValueError) as exc_info:
        writer.write_checked(
            dataframe,
            run_id="run-1",
            evaluation_scope='{"source":"test"}',
        )

    assert str(exc_info.value) == message
    result_writer.write.assert_called_once_with(report)
    lifecycle_factory.assert_not_called()
    dataframe.select.assert_not_called()


def test_success_projects_contract_columns_and_overwrites_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataframe = MagicMock()
    persisted = MagicMock()
    dataframe.select.return_value = persisted
    report = _report()
    _, result_writer = _install_quality_mocks(
        monkeypatch,
        dataframe=dataframe,
        report=report,
    )
    lifecycle = MagicMock()
    lifecycle_factory = MagicMock(return_value=lifecycle)
    monkeypatch.setattr(
        snapshot_writer_module,
        "DeltaTableLifecycle",
        lifecycle_factory,
    )

    writer = SilverSnapshotWriter(
        MagicMock(),
        "catalog.silver.test",
        _dataset_contract(),
        _quality_contract(),
        "admin.quality.data_quality_results",
    )
    returned = writer.write_checked(
        dataframe,
        run_id="run-1",
        evaluation_scope='{"source":"test"}',
    )

    assert returned is report
    result_writer.write.assert_called_once_with(report)
    lifecycle_factory.assert_called_once()
    lifecycle.ensure.assert_called_once_with()
    dataframe.select.assert_called_once_with("id", "value")
    persisted.write.format.assert_called_once_with("delta")
    persisted.write.format.return_value.mode.assert_called_once_with("overwrite")
    save_as_table = persisted.write.format.return_value.mode.return_value.saveAsTable
    save_as_table.assert_called_once_with("catalog.silver.test")


def test_temporary_quality_columns_are_not_persisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataframe = MagicMock()
    persisted = MagicMock()
    dataframe.select.return_value = persisted
    report = _report()
    _install_quality_mocks(
        monkeypatch,
        dataframe=dataframe,
        report=report,
    )
    lifecycle = MagicMock()
    monkeypatch.setattr(
        snapshot_writer_module,
        "DeltaTableLifecycle",
        MagicMock(return_value=lifecycle),
    )

    writer = SilverSnapshotWriter(
        MagicMock(),
        "catalog.silver.test",
        _dataset_contract(),
        _quality_contract(),
        "admin.quality.data_quality_results",
    )
    writer.write_checked(
        dataframe,
        run_id="run-1",
        evaluation_scope='{"source":"test"}',
    )

    selected_columns = dataframe.select.call_args.args
    assert "_temporary_dq_evidence" not in selected_columns
    assert selected_columns == ("id", "value")
