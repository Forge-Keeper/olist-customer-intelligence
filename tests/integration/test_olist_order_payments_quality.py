from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.order_payments_quality import (
    OLIST_ORDER_PAYMENTS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("order_id", StringType(), True),
        StructField("payment_sequential", StringType(), True),
        StructField("payment_type", StringType(), True),
        StructField("payment_installments", StringType(), True),
        StructField("payment_value", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_ORDER_PAYMENTS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def _row(order_id: str = "order-1", payment_sequential: str = "1"):
    return (
        order_id,
        payment_sequential,
        "credit_card",
        "1",
        "58.90",
        "/source.csv",
    )


def test_order_payments_quality_produces_reusable_composite_key_evidence(spark):
    checked = _evaluate(
        spark,
        [_row("order-1", "1"), _row("order-1", "2")],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("order_id", "payment_sequential")


def test_order_payments_quality_blocks_duplicate_composite_key(spark):
    checked = _evaluate(spark, [_row("order-1", "1"), _row("order-1", "1")])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDER-PAYMENTS-DQ03" in failed_rule_ids


def test_order_payments_quality_allows_source_zero_edge_cases(spark):
    row = list(_row())
    row[3] = "0"
    row[4] = "0"
    checked = _evaluate(spark, [tuple(row)])

    assert checked.report.outcome is QualityOutcome.PASSED


def test_order_payments_quality_blocks_invalid_payment_value(spark):
    row = list(_row())
    row[4] = "not-a-number"
    checked = _evaluate(spark, [tuple(row)])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDER-PAYMENTS-DQ07" in failed_rule_ids
