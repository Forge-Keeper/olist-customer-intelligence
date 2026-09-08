from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.order_items_quality import (
    OLIST_ORDER_ITEMS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("order_item_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("seller_id", StringType(), True),
        StructField("shipping_limit_date", StringType(), True),
        StructField("price", StringType(), True),
        StructField("freight_value", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_ORDER_ITEMS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def _row(order_id: str = "order-1", order_item_id: str = "1"):
    return (
        order_id,
        order_item_id,
        "product-1",
        "seller-1",
        "2017-10-02 10:56:33",
        "58.90",
        "13.29",
        "/source.csv",
    )


def test_order_items_quality_produces_reusable_composite_key_evidence(spark):
    checked = _evaluate(
        spark,
        [_row("order-1", "1"), _row("order-1", "2")],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("order_id", "order_item_id")


def test_order_items_quality_blocks_duplicate_composite_key(spark):
    checked = _evaluate(spark, [_row("order-1", "1"), _row("order-1", "1")])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDER-ITEMS-DQ03" in failed_rule_ids


def test_order_items_quality_blocks_invalid_numeric_shape(spark):
    row = list(_row())
    row[5] = "not-a-number"
    checked = _evaluate(spark, [tuple(row)])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDER-ITEMS-DQ07" in failed_rule_ids
