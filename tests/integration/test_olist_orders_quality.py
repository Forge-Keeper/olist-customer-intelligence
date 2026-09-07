from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.orders_quality import (
    OLIST_ORDERS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("order_status", StringType(), True),
        StructField("order_purchase_timestamp", StringType(), True),
        StructField("order_approved_at", StringType(), True),
        StructField("order_delivered_carrier_date", StringType(), True),
        StructField("order_delivered_customer_date", StringType(), True),
        StructField("order_estimated_delivery_date", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_ORDERS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def _row(order_id: str = "order-1"):
    return (
        order_id,
        "customer-1",
        "delivered",
        "2017-10-02 10:56:33",
        "2017-10-02 11:07:15",
        "2017-10-04 19:55:00",
        "2017-10-10 21:25:13",
        "2017-10-18 00:00:00",
        "/source.csv",
    )


def test_orders_quality_produces_reusable_order_id_key_evidence(spark):
    checked = _evaluate(spark, [_row("order-1"), _row("order-2")])

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("order_id",)


def test_orders_quality_blocks_duplicate_order_id(spark):
    checked = _evaluate(spark, [_row("order-1"), _row("order-1")])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDERS-DQ03" in failed_rule_ids


def test_orders_quality_blocks_missing_required_non_key_attribute(spark):
    row = list(_row())
    row[1] = None
    checked = _evaluate(spark, [tuple(row)])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDERS-DQ04" in failed_rule_ids
