import json

import pytest
from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.geolocation_quality import (
    OLIST_GEOLOCATION_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRejectedError,
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("geolocation_zip_code_prefix", StringType(), True),
        StructField("geolocation_lat", StringType(), True),
        StructField("geolocation_lng", StringType(), True),
        StructField("geolocation_city", StringType(), True),
        StructField("geolocation_state", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_GEOLOCATION_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def _result(checked, rule_id):
    return next(
        result
        for result in checked.report.results
        if result.rule_id == rule_id
    )


def _assert_blocking(checked, rule_id):
    assert checked.report.outcome is QualityOutcome.FAILED
    assert _result(checked, rule_id).status is QualityStatus.FAIL
    with pytest.raises(DataQualityRejectedError, match=rule_id):
        checked.report.raise_for_blocking_failures()


def test_geolocation_quality_should_pass_valid_duplicate_observations(spark):
    row = ("01234", "-27.5945", "-48.5477", "florianopolis", "SC", "/source.csv")

    checked = _evaluate(spark, [row, row])

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.report.has_blocking_failures is False
    assert checked.validated_key_columns == ()
    assert json.loads(_result(checked, "GEOLOCATION-DQ05").observed_value) == {
        "observed_row_count": 0
    }


def test_geolocation_quality_should_block_empty_snapshot(spark):
    checked = _evaluate(spark, [])

    _assert_blocking(checked, "GEOLOCATION-DQ01")
    assert json.loads(_result(checked, "GEOLOCATION-DQ01").observed_value) == {
        "row_count": 0
    }


def test_geolocation_quality_should_block_null_source_attributes(spark):
    rows = [
        (None, "-27.5945", "-48.5477", "florianopolis", "SC", "/source.csv"),
        ("01234", None, "-48.5477", "florianopolis", "SC", "/source.csv"),
        ("01234", "-27.5945", None, "florianopolis", "SC", "/source.csv"),
        ("01234", "-27.5945", "-48.5477", None, "SC", "/source.csv"),
        ("01234", "-27.5945", "-48.5477", "florianopolis", None, "/source.csv"),
    ]

    checked = _evaluate(spark, rows)

    _assert_blocking(checked, "GEOLOCATION-DQ02")
    observed = json.loads(_result(checked, "GEOLOCATION-DQ02").observed_value)
    assert observed["null_row_count"] == 5
    assert observed["columns"] == [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ]


def test_geolocation_quality_should_block_malformed_zip_source_shape(spark):
    checked = _evaluate(
        spark,
        [("12A45", "-27.5945", "-48.5477", "florianopolis", "SC", "/source.csv")],
    )

    _assert_blocking(checked, "GEOLOCATION-DQ03")
    assert json.loads(_result(checked, "GEOLOCATION-DQ03").observed_value) == {
        "invalid_row_count": 1
    }


def test_geolocation_quality_should_block_invalid_coordinates(spark):
    checked = _evaluate(
        spark,
        [
            ("01234", "91", "-48.5477", "florianopolis", "SC", "/source.csv"),
            ("01234", "-27.5945", "-181", "florianopolis", "SC", "/source.csv"),
            ("01234", "not-a-number", "-48.5477", "florianopolis", "SC", "/source.csv"),
        ],
    )

    _assert_blocking(checked, "GEOLOCATION-DQ04")
    assert json.loads(_result(checked, "GEOLOCATION-DQ04").observed_value) == {
        "invalid_row_count": 3
    }


def test_geolocation_quality_should_observe_state_shape_without_blocking(spark):
    checked = _evaluate(
        spark,
        [("01234", "-27.5945", "-48.5477", "florianopolis", "sc", "/source.csv")],
    )

    state_result = _result(checked, "GEOLOCATION-DQ05")
    assert state_result.status is QualityStatus.PASS
    assert json.loads(state_result.observed_value) == {"observed_row_count": 1}
    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.report.has_blocking_failures is False
    checked.report.raise_for_blocking_failures()
