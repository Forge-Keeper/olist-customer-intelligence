from __future__ import annotations

from typing import Any

from pyspark.sql import Row, SparkSession
from pyspark.sql.types import (
    DateType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from olist_data_platform.domains.bronze.ibge.municipality_population_bronze_config import (
    IBGE_MUNICIPALITY_POPULATION_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter


class BronzeMunicipalityPopulationWriter:
    INPUT_SCHEMA = StructType(
        [
            StructField("municipality_code", StringType(), False),
            StructField("municipality_name", StringType(), False),
            StructField("variable_code", StringType(), False),
            StructField("variable_name", StringType(), False),
            StructField("reference_year", IntegerType(), False),
            StructField("unit_code", StringType(), False),
            StructField("unit_name", StringType(), False),
            StructField("territorial_level_code", StringType(), False),
            StructField("territorial_level_name", StringType(), False),
            StructField("value", LongType(), False),
            StructField("dt_base", DateType(), False),
            StructField("request_id", StringType(), False),
        ]
    )

    def __init__(self, spark: SparkSession, target_table: str) -> None:
        self.spark = spark
        self.writer = BronzeWriter(
            spark=spark,
            target_table=target_table,
            config=IBGE_MUNICIPALITY_POPULATION_BRONZE_CONFIG,
        )

    def write(self, records: list[dict[str, Any]], request_id: str) -> None:
        if not records:
            return
        rows = [Row(**record, request_id=request_id) for record in records]
        dataframe = self.spark.createDataFrame(rows, schema=self.INPUT_SCHEMA)
        self.writer.write(dataframe)
