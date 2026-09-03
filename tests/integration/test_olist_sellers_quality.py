from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.sellers_quality import (
    OLIST_SELLERS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("seller_id", StringType(), True),
        StructField("seller_zip_code_prefix", StringType(), True),
        StructField("seller_city", StringType(), True),
        StructField("seller_state", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_SELLERS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def test_sellers_quality_should_pass_valid_snapshot_shape(spark):
    checked = _evaluate(
        spark,
        [
            ("seller-1", "01234", "sao paulo", "SP", "/source.csv"),
            ("seller-2", "12345", "campinas", "SP", "/source.csv"),
        ],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("seller_id",)


def test_sellers_quality_should_block_duplicate_seller_id(spark):
    checked = _evaluate(
        spark,
        [
            ("seller-1", "01234", "sao paulo", "SP", "/source.csv"),
            ("seller-1", "12345", "campinas", "SP", "/source.csv"),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "SELLERS-DQ03" in failed_rule_ids


def test_sellers_quality_should_block_missing_required_attribute(spark):
    checked = _evaluate(
        spark,
        [("seller-1", "01234", None, "SP", "/source.csv")],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "SELLERS-DQ04" in failed_rule_ids


def test_sellers_quality_should_block_malformed_zip_prefix(spark):
    checked = _evaluate(
        spark,
        [("seller-1", "1234X", "sao paulo", "SP", "/source.csv")],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "SELLERS-DQ05" in failed_rule_ids
