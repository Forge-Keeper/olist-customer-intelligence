from unittest.mock import Mock

import pytest

from olist_data_platform.domains.ingestion.olist.snapshot_ingestion_service import (
    OlistSnapshotIngestionService,
)
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    QualityOutcome,
)


def _reader_and_dataframe(row_count: int = 42):
    dataframe = Mock()
    dataframe.count.return_value = row_count
    dataframe.columns = ["id", "source_file"]

    reader = Mock()
    reader.source_path = "/Volumes/source.csv"
    reader.read.return_value = dataframe
    return reader, dataframe


def test_should_read_count_write_and_return_row_count():
    reader, dataframe = _reader_and_dataframe()
    writer = Mock()
    writer.target_table = "test_catalog.bronze.test"

    service = OlistSnapshotIngestionService(
        dataset_name="olist_test",
        reader=reader,
        bronze_writer=writer,
    )

    result = service.ingest()

    assert result == 42
    reader.read.assert_called_once_with()
    writer.write.assert_called_once_with(dataframe)


def test_should_require_complete_quality_configuration():
    reader, _ = _reader_and_dataframe()
    writer = Mock()
    writer.target_table = "test_catalog.bronze.test"

    with pytest.raises(ValueError, match="must be configured together"):
        OlistSnapshotIngestionService(
            dataset_name="olist_test",
            reader=reader,
            bronze_writer=writer,
            quality_contract=Mock(dataset="olist_test"),
        )


def test_should_evaluate_persist_evidence_and_write_checked_batch():
    reader, dataframe = _reader_and_dataframe()
    writer = Mock()
    writer.target_table = "test_catalog.bronze.test"
    contract = Mock()
    contract.dataset = "olist_test"
    runner = Mock()
    result_writer = Mock()
    tracker = Mock()

    checked = Mock()
    checked.report.outcome = QualityOutcome.PASSED
    checked.report.row_count = 42
    checked.report.has_blocking_failures = False
    runner.evaluate.return_value = checked

    service = OlistSnapshotIngestionService(
        dataset_name="olist_test",
        reader=reader,
        bronze_writer=writer,
        quality_contract=contract,
        quality_runner=runner,
        quality_result_writer=result_writer,
        run_tracker=tracker,
    )

    result = service.ingest(run_id="run-1", evaluation_scope='{"snapshot":"test"}')

    assert result == 42
    runner.evaluate.assert_called_once_with(
        dataframe=dataframe,
        contract=contract,
        run_id="run-1",
        evaluation_scope='{"snapshot":"test"}',
    )
    result_writer.write.assert_called_once_with(checked.report)
    writer.write_checked.assert_called_once_with(checked)
    writer.write.assert_not_called()
    tracker.update_metrics.assert_any_call("run-1", records_extracted=42)
    tracker.update_metrics.assert_any_call("run-1", records_written=42)


def test_should_reject_before_write_when_blocking_quality_rule_fails():
    reader, _ = _reader_and_dataframe()
    writer = Mock()
    writer.target_table = "test_catalog.bronze.test"
    contract = Mock()
    contract.dataset = "olist_test"
    runner = Mock()
    result_writer = Mock()
    tracker = Mock()

    failed_result = Mock()
    failed_result.rule_id = "TEST-DQ01"
    failed_result.status.value = "FAIL"
    failed_result.severity.value = "ERROR"

    checked = Mock()
    checked.report.outcome = QualityOutcome.FAILED
    checked.report.row_count = 42
    checked.report.has_blocking_failures = True
    checked.report.results = (failed_result,)
    checked.report.raise_for_blocking_failures.side_effect = DataQualityRejectedError(
        "rejected"
    )
    runner.evaluate.return_value = checked

    service = OlistSnapshotIngestionService(
        dataset_name="olist_test",
        reader=reader,
        bronze_writer=writer,
        quality_contract=contract,
        quality_runner=runner,
        quality_result_writer=result_writer,
        run_tracker=tracker,
    )

    with pytest.raises(DataQualityRejectedError, match="rejected"):
        service.ingest(run_id="run-1")

    result_writer.write.assert_called_once_with(checked.report)
    tracker.reject.assert_called_once()
    writer.write_checked.assert_not_called()
    writer.write.assert_not_called()
