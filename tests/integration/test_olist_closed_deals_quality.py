from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.closed_deals_quality import (
    OLIST_CLOSED_DEALS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("mql_id", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_CLOSED_DEALS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def test_closed_deals_quality_should_pass_valid_natural_keys(spark):
    checked = _evaluate(
        spark,
        [
            ("mql-1",),
            ("mql-2",),
        ],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("mql_id",)


def test_closed_deals_quality_should_block_null_and_duplicate_keys(spark):
    checked = _evaluate(
        spark,
        [
            ("mql-1",),
            ("mql-1",),
            (None,),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert {"CLOSED-DEALS-DQ02", "CLOSED-DEALS-DQ03"} <= failed_rule_ids
