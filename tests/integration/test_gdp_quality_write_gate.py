from datetime import date, datetime

import pytest

from olist_data_platform.domains.bronze.ibge.bronze_municipality_gdp_writer import (
    BronzeMunicipalityGdpWriter,
)
from olist_data_platform.domains.bronze.ibge.municipality_gdp_quality import (
    GDP_KEY_COLUMNS,
)
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    QualityCategory,
    QualityCheckedBatch,
    QualityReport,
    QualityResult,
    QualitySeverity,
    QualityStatus,
)


class _QualityRunner:
    def __init__(self, report: QualityReport) -> None:
        self.report = report

    def evaluate(self, *, dataframe, contract, run_id, evaluation_scope):
        return QualityCheckedBatch(
            dataframe=dataframe,
            report=self.report,
            validated_key_columns=(
                GDP_KEY_COLUMNS
                if not self.report.has_blocking_failures
                else ()
            ),
        )


class _QualityResultWriter:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def write(self, report: QualityReport) -> None:
        self.events.append("quality")


class _BronzeWriter:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def write_checked(self, checked_batch: QualityCheckedBatch) -> None:
        self.events.append("bronze")


def _report(status: QualityStatus) -> QualityReport:
    result = QualityResult(
        run_id="run-1",
        dataset="ibge_municipality_gdp",
        layer="bronze",
        rule_id="GDP-DQ01",
        rule_version=1,
        category=QualityCategory.COMPLETENESS,
        severity=QualitySeverity.ERROR,
        status=status,
        observed_value='{"row_count":1}',
        expected_condition="row_count > 0",
        evaluation_scope='{"periods":["2018"]}',
        evaluated_at=datetime(2026, 8, 27),
    )
    return QualityReport(
        run_id="run-1",
        dataset="ibge_municipality_gdp",
        layer="bronze",
        evaluation_scope='{"periods":["2018"]}',
        row_count=1,
        results=(result,),
    )


def _records():
    return [
        {
            "municipality_code": "3550308",
            "reference_year": "2018",
            "variable_code": "37",
            "dt_base": date(2018, 1, 1),
            "payload": {"Valor": "1000"},
        }
    ]


def test_gdp_quality_evidence_is_persisted_before_accepted_bronze_write(spark):
    events: list[str] = []
    writer = BronzeMunicipalityGdpWriter(
        spark,
        "dev.bronze.test_gdp",
        quality_runner=_QualityRunner(_report(QualityStatus.PASS)),
        quality_result_writer=_QualityResultWriter(events),
    )
    writer.writer = _BronzeWriter(events)

    writer.write(_records(), "run-1", ("2018",))

    assert events == ["quality", "bronze"]


def test_gdp_blocking_failure_persists_evidence_without_bronze_write(spark):
    events: list[str] = []
    writer = BronzeMunicipalityGdpWriter(
        spark,
        "dev.bronze.test_gdp",
        quality_runner=_QualityRunner(_report(QualityStatus.FAIL)),
        quality_result_writer=_QualityResultWriter(events),
    )
    writer.writer = _BronzeWriter(events)

    with pytest.raises(DataQualityRejectedError):
        writer.write(_records(), "run-1", ("2018",))

    assert events == ["quality"]
