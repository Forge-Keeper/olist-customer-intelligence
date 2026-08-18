from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from olist_data_platform.platform.jdbc import JdbcReader


@dataclass(frozen=True, slots=True)
class AnpCombustiveisReadRequest:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date.")


class AnpCombustiveisPostgresReader:
    SOURCE_TABLE = "anp.combustiveis_precos"
    SOURCE_SYSTEM = "azure_postgresql"

    def __init__(self, jdbc_reader: JdbcReader) -> None:
        self._jdbc_reader = jdbc_reader

    def read(self, request: AnpCombustiveisReadRequest) -> DataFrame:
        dataframe = self._jdbc_reader.read(
            dbtable=self._build_dbtable(request),
        )
        return (
            dataframe.withColumn("dt_base", F.col("data_coleta"))
            .withColumn("source_system", F.lit(self.SOURCE_SYSTEM))
        )

    @classmethod
    def _build_dbtable(cls, request: AnpCombustiveisReadRequest) -> str:
        start = request.start_date.isoformat()
        end = request.end_date.isoformat()
        return (
            "(SELECT * "
            f"FROM {cls.SOURCE_TABLE} "
            f"WHERE data_coleta >= DATE '{start}' "
            f"AND data_coleta <= DATE '{end}') AS anp_combustiveis_source"
        )
