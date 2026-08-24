import os
import sys
from collections.abc import Generator

import pytest

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> Generator[SparkSession, None, None]:
    spark_session = (
        SparkSession.builder.master("local[2]")
        .appName("olist-customer-intelligence-tests")
        .config(
            "spark.ui.enabled",
            "false",
        )
        .config(
            "spark.pyspark.python",
            sys.executable,
        )
        .config(
            "spark.pyspark.driver.python",
            sys.executable,
        )
        .getOrCreate()
    )

    spark_session.sparkContext.setLogLevel("ERROR")

    yield spark_session

    spark_session.stop()
