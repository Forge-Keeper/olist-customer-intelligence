from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.domains.bronze.olist.marketing_qualified_leads_quality import (
    OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)

SCHEMA = StructType(
    [
        StructField("mql_id", StringType(), True),
        StructField("first_contact_date", StringType(), True),
        StructField("landing_page_id", StringType(), True),
        StructField("origin", StringType(), True),
        StructField("source_file", StringType(), True),
    ]
)


def _evaluate(spark, rows):
    dataframe = spark.createDataFrame(rows, schema=SCHEMA)
    return DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )


def test_mql_quality_should_pass_discovered_valid_shape(spark):
    checked = _evaluate(
        spark,
        [
            ("mql-1", "2018-02-01", "landing-1", "social", "/source.csv"),
            ("mql-2", "2018-02-02", "landing-2", None, "/source.csv"),
        ],
    )

    assert checked.report.outcome is QualityOutcome.PASSED
    assert checked.validated_key_columns == ("mql_id",)


def test_mql_quality_should_block_duplicate_natural_keys(spark):
    checked = _evaluate(
        spark,
        [
            ("mql-1", "2018-02-01", "landing-1", "social", "/source.csv"),
            ("mql-1", "2018-02-02", "landing-2", "email", "/source.csv"),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert "MQL-DQ03" in failed_rule_ids


def test_mql_quality_should_block_missing_required_values_and_invalid_date(spark):
    checked = _evaluate(
        spark,
        [
            ("mql-1", "not-a-date", None, "social", "/source.csv"),
        ],
    )

    failed_rule_ids = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }

    assert checked.report.outcome is QualityOutcome.FAILED
    assert {"MQL-DQ04", "MQL-DQ05"} <= failed_rule_ids
