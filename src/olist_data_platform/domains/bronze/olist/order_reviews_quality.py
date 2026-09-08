from __future__ import annotations

from olist_data_platform.platform.quality import (
    DataQualityContract,
    NonEmptyRule,
    NotNullRule,
    ObservedCountRule,
    PredicateRule,
    QualityCategory,
    QualitySeverity,
    UniqueRule,
)

ORDER_REVIEWS_KEY_COLUMNS = ("review_id", "order_id")
ORDER_REVIEWS_REQUIRED_NON_KEY_COLUMNS = (
    "review_score",
    "review_creation_date",
    "review_answer_timestamp",
)

OLIST_ORDER_REVIEWS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_order_reviews",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="ORDER-REVIEWS-DQ01",
            version=1,
            description=(
                "The authoritative Order Reviews snapshot must contain records."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="ORDER-REVIEWS-DQ02",
            version=1,
            description="The Order Reviews natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_REVIEWS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="ORDER-REVIEWS-DQ03",
            version=1,
            description="The Order Reviews natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_REVIEWS_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="ORDER-REVIEWS-DQ04",
            version=1,
            description=(
                "Required non-key Order Reviews attributes cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_REVIEWS_REQUIRED_NON_KEY_COLUMNS,
        ),
        PredicateRule(
            rule_id="ORDER-REVIEWS-DQ05",
            version=1,
            description="Review scores must retain their observed integer shape.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(review_score AS BIGINT) IS NOT NULL "
                "AND try_cast(review_score AS DECIMAL(38,18)) = "
                "try_cast(review_score AS BIGINT)"
            ),
            expected_condition="review_score is integer-shaped",
        ),
        PredicateRule(
            rule_id="ORDER-REVIEWS-DQ06",
            version=1,
            description="Review creation dates must remain parseable timestamps.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="try_cast(review_creation_date AS TIMESTAMP) IS NOT NULL",
            expected_condition="review_creation_date is timestamp-parseable",
        ),
        PredicateRule(
            rule_id="ORDER-REVIEWS-DQ07",
            version=1,
            description="Review answer timestamps must remain parseable timestamps.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="try_cast(review_answer_timestamp AS TIMESTAMP) IS NOT NULL",
            expected_condition="review_answer_timestamp is timestamp-parseable",
        ),
        ObservedCountRule(
            rule_id="ORDER-REVIEWS-DQ08",
            version=1,
            description="Count source rows without a review comment title.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="review_comment_title IS NULL",
            expected_condition=(
                "observed count only; missing titles remain valid source data"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-REVIEWS-DQ09",
            version=1,
            description="Count source rows without a review comment message.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="review_comment_message IS NULL",
            expected_condition=(
                "observed count only; missing messages remain valid source data"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-REVIEWS-DQ10",
            version=1,
            description="Count non-null blank review comment titles.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression=(
                "review_comment_title IS NOT NULL "
                "AND trim(review_comment_title) = ''"
            ),
            expected_condition=(
                "observed count only; blank titles remain source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-REVIEWS-DQ11",
            version=1,
            description="Count non-null blank review comment messages.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression=(
                "review_comment_message IS NOT NULL "
                "AND trim(review_comment_message) = ''"
            ),
            expected_condition=(
                "observed count only; blank messages remain source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-REVIEWS-DQ12",
            version=1,
            description=(
                "Count review titles whose source whitespace would change on trim."
            ),
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression=(
                "review_comment_title IS NOT NULL "
                "AND review_comment_title <> trim(review_comment_title)"
            ),
            expected_condition=(
                "observed count only; title whitespace remains source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-REVIEWS-DQ13",
            version=1,
            description=(
                "Count review messages whose source whitespace would change on trim."
            ),
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression=(
                "review_comment_message IS NOT NULL "
                "AND review_comment_message <> trim(review_comment_message)"
            ),
            expected_condition=(
                "observed count only; message whitespace remains source-faithful"
            ),
        ),
    ),
)
