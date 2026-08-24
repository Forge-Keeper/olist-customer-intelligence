from __future__ import annotations

import json
from typing import Any

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, StringType, StructField, StructType

from olist_data_platform.domains.bronze.ibge.municipalities_bronze_config import (
    IBGE_MUNICIPALITIES_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter


class BronzeMunicipalitiesWriter:
    """Adapt IBGE municipality-locality records to the Bronze table contract.

    This adapter owns source-specific row construction and the transient
    JSON-to-VARIANT conversion. Generic persistence and write semantics remain in
    ``BronzeWriter``.
    """

    INPUT_SCHEMA = StructType(
        [
            StructField("municipality_code", StringType(), False),
            StructField("dt_base", DateType(), False),
            StructField("payload_json", StringType(), False),
            StructField("request_id", StringType(), False),
        ]
    )

    def __init__(self, spark: SparkSession, target_table: str) -> None:
        self.spark = spark
        self.writer = BronzeWriter(
            spark=spark,
            target_table=target_table,
            config=IBGE_MUNICIPALITIES_BRONZE_CONFIG,
        )

    def write(self, records: list[dict[str, Any]], request_id: str) -> None:
        """Persist one municipality-locality ingestion batch to Bronze.

        Empty input is a no-op. Raw source payload content is preserved as a
        Delta VARIANT after transient JSON serialization.
        """
        if not records:
            return
        dataframe = self._build_dataframe(records=records, request_id=request_id)
        self.writer.write(dataframe)

    def _build_dataframe(
        self,
        *,
        records: list[dict[str, Any]],
        request_id: str,
    ) -> DataFrame:
        rows = [
            Row(
                municipality_code=str(record["municipality_code"]),
                dt_base=record["dt_base"],
                payload_json=json.dumps(
                    record["payload"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                request_id=request_id,
            )
            for record in records
        ]
        dataframe = self.spark.createDataFrame(rows, schema=self.INPUT_SCHEMA)
        return dataframe.withColumn("payload", F.parse_json("payload_json")).drop(
            "payload_json"
        )
