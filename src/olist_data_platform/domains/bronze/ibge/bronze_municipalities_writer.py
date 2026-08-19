from __future__ import annotations

from typing import Any

from pyspark.sql import Row, SparkSession
from pyspark.sql.types import DateType, StringType, StructField, StructType

from olist_data_platform.domains.bronze.ibge.municipalities_bronze_config import (
    IBGE_MUNICIPALITIES_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter


class BronzeMunicipalitiesWriter:
    INPUT_SCHEMA = StructType(
        [
            StructField("municipality_code", StringType(), False),
            StructField("municipality_name", StringType(), False),
            StructField("state_code", StringType(), False),
            StructField("state_abbreviation", StringType(), False),
            StructField("state_name", StringType(), False),
            StructField("region_code", StringType(), False),
            StructField("region_abbreviation", StringType(), False),
            StructField("region_name", StringType(), False),
            StructField("immediate_region_code", StringType(), False),
            StructField("immediate_region_name", StringType(), False),
            StructField("intermediate_region_code", StringType(), False),
            StructField("intermediate_region_name", StringType(), False),
            StructField("microregion_code", StringType(), False),
            StructField("microregion_name", StringType(), False),
            StructField("mesoregion_code", StringType(), False),
            StructField("mesoregion_name", StringType(), False),
            StructField("dt_base", DateType(), False),
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
        if not records:
            return
        rows = [Row(**record, request_id=request_id) for record in records]
        dataframe = self.spark.createDataFrame(rows, schema=self.INPUT_SCHEMA)
        self.writer.write(dataframe)
