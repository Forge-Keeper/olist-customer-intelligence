from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.products_quality import (
    OLIST_PRODUCTS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("product_id", StringType(), True),
        StructField("product_category_name", StringType(), True),
        StructField("product_name_lenght", StringType(), True),
        StructField("product_description_lenght", StringType(), True),
        StructField("product_photos_qty", StringType(), True),
        StructField("product_weight_g", StringType(), True),
        StructField("product_length_cm", StringType(), True),
        StructField("product_height_cm", StringType(), True),
        StructField("product_width_cm", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_PRODUCTS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def _row(product_id="product-1", *, weight="100"):
    return (
        product_id,
        "cama_mesa_banho",
        "50",
        "500",
        "1",
        weight,
        "30",
        "20",
        "25",
        "/source.csv",
    )


def test_products_quality_should_pass_valid_snapshot_and_observe_anomalies(spark):
    incomplete = (
        "product-2",
        None,
        None,
        None,
        None,
        "0",
        "30",
        "20",
        "25",
        "/source.csv",
    )

    checked = _evaluate(spark, [_row(), incomplete])

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("product_id",)
    observations = {
        result.rule_id: result.observed_value
        for result in checked.report.results
        if result.rule_id in {"PRODUCTS-DQ05", "PRODUCTS-DQ07"}
    }
    assert '"observed_row_count":1' in observations["PRODUCTS-DQ05"]
    assert '"observed_row_count":1' in observations["PRODUCTS-DQ07"]


def test_products_quality_should_block_duplicate_product_id(spark):
    checked = _evaluate(spark, [_row(), _row()])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "PRODUCTS-DQ03" in failed_rule_ids


def test_products_quality_should_block_malformed_numeric_source_value(spark):
    malformed = list(_row())
    malformed[5] = "1.5kg"

    checked = _evaluate(spark, [tuple(malformed)])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "PRODUCTS-DQ04" in failed_rule_ids
