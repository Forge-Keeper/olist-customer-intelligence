from olist_data_platform.domains.bronze.olist.order_reviews_bronze_config import (
    OLIST_ORDER_REVIEWS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.order_reviews_quality import (
    OLIST_ORDER_REVIEWS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.quality import QualitySeverity


def test_order_reviews_bronze_contract_uses_composite_key_full_replace() -> None:
    assert OLIST_ORDER_REVIEWS_BRONZE_CONFIG.key_columns == (
        "review_id",
        "order_id",
    )
    assert (
        OLIST_ORDER_REVIEWS_BRONZE_CONFIG.write_strategy
        is WriteStrategy.FULL_REPLACE
    )


def test_order_reviews_bronze_contract_preserves_source_nullability() -> None:
    columns = {
        column.name: column for column in OLIST_ORDER_REVIEWS_BRONZE_CONFIG.columns
    }

    assert set(columns) == {
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
        "source_file",
    }
    assert all(column.data_type == "string" for column in columns.values())
    assert columns["review_comment_title"].nullable is True
    assert columns["review_comment_message"].nullable is True
    for column_name in (
        "review_id",
        "order_id",
        "review_score",
        "review_creation_date",
        "review_answer_timestamp",
    ):
        assert columns[column_name].nullable is False


def test_order_reviews_quality_contract_has_expected_severity_split() -> None:
    rules = OLIST_ORDER_REVIEWS_QUALITY_CONTRACT.rules

    assert [rule.rule_id for rule in rules] == [
        "ORDER-REVIEWS-DQ01",
        "ORDER-REVIEWS-DQ02",
        "ORDER-REVIEWS-DQ03",
        "ORDER-REVIEWS-DQ04",
        "ORDER-REVIEWS-DQ05",
        "ORDER-REVIEWS-DQ06",
        "ORDER-REVIEWS-DQ07",
        "ORDER-REVIEWS-DQ08",
        "ORDER-REVIEWS-DQ09",
        "ORDER-REVIEWS-DQ10",
        "ORDER-REVIEWS-DQ11",
        "ORDER-REVIEWS-DQ12",
        "ORDER-REVIEWS-DQ13",
    ]
    assert [rule.severity for rule in rules[:7]] == [QualitySeverity.ERROR] * 7
    assert [rule.severity for rule in rules[7:]] == [QualitySeverity.INFO] * 6
