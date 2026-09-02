from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.customers_quality import (
    OLIST_CUSTOMERS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("customer_id", StringType(), True),
        StructField("customer_unique_id", StringType(), True),
        StructField("customer_zip_code_prefix", StringType(), True),
        StructField("customer_city", StringType(), True),
        StructField("customer_state", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_CUSTOMERS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def test_customers_quality_should_pass_valid_shape_and_repeated_unique_identity(spark):
    checked = _evaluate(
        spark,
        [
            ("customer-1", "unique-1", "01234", "sao paulo", "SP", "/source.csv"),
            ("customer-2", "unique-1", "12345", "campinas", "SP", "/source.csv"),
        ],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("customer_id",)


def test_customers_quality_should_block_duplicate_customer_id(spark):
    checked = _evaluate(
        spark,
        [
            ("customer-1", "unique-1", "01234", "sao paulo", "SP", "/source.csv"),
            ("customer-1", "unique-2", "12345", "campinas", "SP", "/source.csv"),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "CUSTOMERS-DQ03" in failed_rule_ids


def test_customers_quality_should_block_missing_required_attribute(spark):
    checked = _evaluate(
        spark,
        [
            ("customer-1", None, "01234", "sao paulo", "SP", "/source.csv"),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "CUSTOMERS-DQ04" in failed_rule_ids


def test_customers_quality_should_block_malformed_zip_prefix(spark):
    checked = _evaluate(
        spark,
        [
            ("customer-1", "unique-1", "1234X", "sao paulo", "SP", "/source.csv"),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "CUSTOMERS-DQ05" in failed_rule_ids
