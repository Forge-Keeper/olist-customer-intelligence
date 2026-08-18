from datetime import date

import pytest
from pyspark.sql import SparkSession

from olist_data_platform.domains.ingestion.anp.combustiveis_postgres_reader import (
    AnpCombustiveisPostgresReader,
    AnpCombustiveisReadRequest,
)


class StubJdbcReader:
    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark
        self.dbtable: str | None = None

    def read(self, *, dbtable: str):
        self.dbtable = dbtable
        return self._spark.createDataFrame(
            [(1, date(2016, 1, 4))],
            ["id", "data_coleta"],
        )


def test_request_rejects_inverted_interval() -> None:
    with pytest.raises(ValueError, match="start_date cannot be after end_date"):
        AnpCombustiveisReadRequest(
            start_date=date(2016, 6, 30),
            end_date=date(2016, 1, 4),
        )


def test_build_dbtable_pushes_date_filter_to_postgres() -> None:
    request = AnpCombustiveisReadRequest(
        start_date=date(2016, 1, 4),
        end_date=date(2016, 6, 30),
    )

    dbtable = AnpCombustiveisPostgresReader._build_dbtable(request)

    assert "FROM anp.combustiveis_precos" in dbtable
    assert "data_coleta >= DATE '2016-01-04'" in dbtable
    assert "data_coleta <= DATE '2016-06-30'" in dbtable


def test_read_adds_bronze_metadata_columns(spark: SparkSession) -> None:
    jdbc_reader = StubJdbcReader(spark)
    reader = AnpCombustiveisPostgresReader(jdbc_reader)  # type: ignore[arg-type]
    request = AnpCombustiveisReadRequest(
        start_date=date(2016, 1, 4),
        end_date=date(2016, 6, 30),
    )

    row = reader.read(request).select(
        "data_coleta",
        "dt_base",
        "source_system",
    ).first()

    assert row is not None
    assert row.data_coleta == date(2016, 1, 4)
    assert row.dt_base == date(2016, 1, 4)
    assert row.source_system == "azure_postgresql"
    assert jdbc_reader.dbtable is not None
