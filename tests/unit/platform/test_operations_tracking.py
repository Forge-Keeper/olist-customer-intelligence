from olist_data_platform.platform.operations import (
    ExecutionRunTracker,
    ExecutionStage,
    ExecutionStatus,
    QualityRunStatus,
)


class _Store:
    def __init__(self) -> None:
        self.runs = []

    def upsert(self, run) -> None:
        self.runs.append(run)


def test_execution_tracker_persists_lifecycle_transitions() -> None:
    store = _Store()
    tracker = ExecutionRunTracker(store)

    tracker.start(
        run_id="run-1",
        dataset="ibge_municipality_gdp",
        layer="bronze",
        source_system="ibge_sidra",
        target_table="dev.bronze.ibge_municipality_gdp",
        execution_scope='{"periods":["2018"]}',
    )
    tracker.update_metrics("run-1", records_extracted=10)
    tracker.set_stage("run-1", ExecutionStage.QUALITY)
    tracker.update_quality(
        "run-1",
        QualityRunStatus.PASSED,
        records_evaluated=10,
    )
    tracker.set_stage("run-1", ExecutionStage.WRITE)
    tracker.update_metrics("run-1", records_written=10)
    final = tracker.succeed("run-1")

    assert final.status is ExecutionStatus.SUCCEEDED
    assert final.quality_status is QualityRunStatus.PASSED
    assert final.records_extracted == 10
    assert final.records_evaluated == 10
    assert final.records_written == 10
    assert final.last_stage is ExecutionStage.COMPLETE
    assert final.finished_at is not None
    assert store.runs[-1] == final


def test_execution_tracker_distinguishes_quality_rejection() -> None:
    store = _Store()
    tracker = ExecutionRunTracker(store)
    tracker.start(
        run_id="run-2",
        dataset="ibge_municipality_gdp",
        layer="bronze",
        source_system="ibge_sidra",
        target_table="dev.bronze.ibge_municipality_gdp",
        execution_scope='{"periods":["2018"]}',
    )

    rejected = tracker.reject("run-2", error_message="GDP-DQ07 failed")

    assert rejected.status is ExecutionStatus.REJECTED
    assert rejected.quality_status is QualityRunStatus.FAILED
    assert rejected.error_stage == "QUALITY"
    assert rejected.records_written == 0
