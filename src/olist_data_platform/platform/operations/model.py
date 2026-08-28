from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ExecutionStatus(StrEnum):
    """Lifecycle status for one logical platform execution."""

    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class QualityRunStatus(StrEnum):
    """Data-quality outcome associated with a platform execution."""

    NOT_EVALUATED = "NOT_EVALUATED"
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"


class ExecutionStage(StrEnum):
    """Coarse execution stage used for operational diagnosis."""

    SOURCE = "SOURCE"
    QUALITY = "QUALITY"
    WRITE = "WRITE"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True)
class ExecutionRun:
    """Persistable operational state for one logical platform execution."""

    run_id: str
    dataset: str
    layer: str
    source_system: str
    target_table: str
    execution_scope: str
    started_at: datetime
    finished_at: datetime | None
    status: ExecutionStatus
    quality_status: QualityRunStatus
    records_extracted: int | None
    records_evaluated: int | None
    records_written: int | None
    error_stage: str | None
    error_type: str | None
    error_message: str | None
    orchestrator_run_id: str | None
    last_stage: ExecutionStage

    def __post_init__(self) -> None:
        for field_name in (
            "run_id",
            "dataset",
            "layer",
            "source_system",
            "target_table",
            "execution_scope",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")

        if not isinstance(self.started_at, datetime):
            raise TypeError("started_at must be a datetime.")
        if self.finished_at is not None and not isinstance(self.finished_at, datetime):
            raise TypeError("finished_at must be a datetime or None.")
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("status must be an ExecutionStatus.")
        if not isinstance(self.quality_status, QualityRunStatus):
            raise TypeError("quality_status must be a QualityRunStatus.")
        if not isinstance(self.last_stage, ExecutionStage):
            raise TypeError("last_stage must be an ExecutionStage.")

        for field_name in (
            "records_extracted",
            "records_evaluated",
            "records_written",
        ):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(f"{field_name} must be a non-negative int or None.")
