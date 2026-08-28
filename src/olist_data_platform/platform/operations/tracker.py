from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol

from olist_data_platform.platform.operations.model import (
    ExecutionRun,
    ExecutionStage,
    ExecutionStatus,
    QualityRunStatus,
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ExecutionRunStore(Protocol):
    def upsert(self, run: ExecutionRun) -> None: ...


class ExecutionRunTracker:
    """Track and persist the state of one-process platform executions.

    The tracker owns execution lifecycle state only. It deliberately does not
    orchestrate source access, data-quality evaluation or data persistence.
    """

    def __init__(self, store: ExecutionRunStore) -> None:
        self.store = store
        self._runs: dict[str, ExecutionRun] = {}

    def start(
        self,
        *,
        run_id: str,
        dataset: str,
        layer: str,
        source_system: str,
        target_table: str,
        execution_scope: str,
        orchestrator_run_id: str | None = None,
    ) -> ExecutionRun:
        run = ExecutionRun(
            run_id=run_id,
            dataset=dataset,
            layer=layer,
            source_system=source_system,
            target_table=target_table,
            execution_scope=execution_scope,
            started_at=_utcnow(),
            finished_at=None,
            status=ExecutionStatus.RUNNING,
            quality_status=QualityRunStatus.NOT_EVALUATED,
            records_extracted=None,
            records_evaluated=None,
            records_written=None,
            error_stage=None,
            error_type=None,
            error_message=None,
            orchestrator_run_id=orchestrator_run_id,
            last_stage=ExecutionStage.SOURCE,
        )
        self.store.upsert(run)
        self._runs[run_id] = run
        return run

    def current(self, run_id: str) -> ExecutionRun:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError(f"Unknown execution run: {run_id}") from exc

    def set_stage(self, run_id: str, stage: ExecutionStage) -> ExecutionRun:
        return self._update(run_id, last_stage=stage)

    def update_metrics(
        self,
        run_id: str,
        *,
        records_extracted: int | None = None,
        records_evaluated: int | None = None,
        records_written: int | None = None,
    ) -> ExecutionRun:
        changes: dict[str, int] = {}
        if records_extracted is not None:
            changes["records_extracted"] = records_extracted
        if records_evaluated is not None:
            changes["records_evaluated"] = records_evaluated
        if records_written is not None:
            changes["records_written"] = records_written
        return self._update(run_id, **changes)

    def update_quality(
        self,
        run_id: str,
        quality_status: QualityRunStatus,
        *,
        records_evaluated: int | None = None,
    ) -> ExecutionRun:
        changes: dict[str, object] = {"quality_status": quality_status}
        if records_evaluated is not None:
            changes["records_evaluated"] = records_evaluated
        return self._update(run_id, **changes)

    def succeed(self, run_id: str) -> ExecutionRun:
        return self._update(
            run_id,
            status=ExecutionStatus.SUCCEEDED,
            finished_at=_utcnow(),
            last_stage=ExecutionStage.COMPLETE,
        )

    def reject(
        self,
        run_id: str,
        *,
        error_message: str,
        records_written: int = 0,
    ) -> ExecutionRun:
        return self._update(
            run_id,
            status=ExecutionStatus.REJECTED,
            quality_status=QualityRunStatus.FAILED,
            finished_at=_utcnow(),
            records_written=records_written,
            error_stage=ExecutionStage.QUALITY.value,
            error_type="DataQualityRejectedError",
            error_message=error_message[:2000],
            last_stage=ExecutionStage.QUALITY,
        )

    def fail(self, run_id: str, error: Exception) -> ExecutionRun:
        current = self.current(run_id)
        return self._update(
            run_id,
            status=ExecutionStatus.FAILED,
            finished_at=_utcnow(),
            error_stage=current.last_stage.value,
            error_type=type(error).__name__,
            error_message=str(error)[:2000],
        )

    def _update(self, run_id: str, **changes: object) -> ExecutionRun:
        current = self.current(run_id)
        updated = replace(current, **changes)
        self.store.upsert(updated)
        self._runs[run_id] = updated
        return updated
