from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.order_reviews_quality import (
    OLIST_ORDER_REVIEWS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("review_id", StringType(), True),
        StructField("order_id", StringType(), True),
        StructField("review_score", StringType(), True),
        StructField("review_comment_title", StringType(), True),
        StructField("review_comment_message", StringType(), True),
        StructField("review_creation_date", StringType(), True),
        StructField("review_answer_timestamp", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_ORDER_REVIEWS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def _row(review_id: str = "review-1", order_id: str = "order-1"):
    return (
        review_id,
        order_id,
        "5",
        None,
        None,
        "2018-01-01 00:00:00",
        "2018-01-02 10:30:00",
        "/source.csv",
    )


def test_order_reviews_quality_produces_reusable_composite_key_evidence(spark):
    checked = _evaluate(
        spark,
        [_row("review-1", "order-1"), _row("review-1", "order-2")],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("review_id", "order_id")


def test_order_reviews_quality_blocks_duplicate_composite_key(spark):
    checked = _evaluate(spark, [_row(), _row()])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "ORDER-REVIEWS-DQ03" in failed_rule_ids


def test_order_reviews_quality_allows_optional_comment_fields(spark):
    checked = _evaluate(spark, [_row()])

    assert checked.report.outcome is QualityOutcome.PASSED


def test_order_reviews_quality_blocks_unparseable_required_values(spark):
    row = list(_row())
    row[2] = "not-an-integer"
    row[5] = "not-a-date"
    checked = _evaluate(spark, [tuple(row)])

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert {"ORDER-REVIEWS-DQ05", "ORDER-REVIEWS-DQ06"} <= failed_rule_ids
