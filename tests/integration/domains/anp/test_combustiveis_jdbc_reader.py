import os
import sys
from collections.abc import Generator
from datetime import date

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from olist_data_platform.domains.ingestion.anp import (
    AnpCombustiveisPostgresReader,
    AnpCombustiveisReadRequest,
)
from olist_data_platform.platform.jdbc import JdbcConfig, JdbcReader

POSTGRES_JDBC_PACKAGE = "org.postgresql:postgresql:42.7.13"


@pytest.fixture(scope="module")
def jdbc_spark() -> Generator[SparkSession, None, None]:
    session = (
        SparkSession.builder.master("local[2]")
        .appName("olist-anp-jdbc-integration")
        .config("spark.ui.enabled", "false")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .config("spark.jars.packages", POSTGRES_JDBC_PACKAGE)
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def _local_jdbc_config() -> JdbcConfig:
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(
            "Missing PostgreSQL environment variables: " + ", ".join(missing)
        )

    return JdbcConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        sslmode="disable",
    )


@pytest.mark.integration
def test_reads_anp_date_slice_from_local_postgres_via_jdbc(
    jdbc_spark: SparkSession,
) -> None:
    reader = AnpCombustiveisPostgresReader(
        JdbcReader(spark=jdbc_spark, config=_local_jdbc_config())
    )
    request = AnpCombustiveisReadRequest(
        start_date=date(2016, 1, 4),
        end_date=date(2016, 1, 4),
    )

    dataframe = reader.read(request).cache()
    try:
        assert dataframe.limit(1).count() == 1
        assert {"id", "data_coleta", "dt_base", "source_system"}.issubset(
            dataframe.columns
        )

        bounds = dataframe.agg(
            F.min("dt_base").alias("min_dt_base"),
            F.max("dt_base").alias("max_dt_base"),
        ).first()

        assert bounds is not None
        assert bounds.min_dt_base == date(2016, 1, 4)
        assert bounds.max_dt_base == date(2016, 1, 4)
        assert (
            dataframe.where(F.col("source_system") != "azure_postgresql")
            .limit(1)
            .count()
            == 0
        )
    finally:
        dataframe.unpersist()
