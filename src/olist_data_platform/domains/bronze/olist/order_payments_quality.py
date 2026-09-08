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

ORDER_PAYMENTS_KEY_COLUMNS = ("order_id", "payment_sequential")
ORDER_PAYMENTS_REQUIRED_NON_KEY_COLUMNS = (
    "payment_type",
    "payment_installments",
    "payment_value",
)

OLIST_ORDER_PAYMENTS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_order_payments",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="ORDER-PAYMENTS-DQ01",
            version=1,
            description="The authoritative Order Payments snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="ORDER-PAYMENTS-DQ02",
            version=1,
            description="The Order Payments natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_PAYMENTS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="ORDER-PAYMENTS-DQ03",
            version=1,
            description="The Order Payments natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_PAYMENTS_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="ORDER-PAYMENTS-DQ04",
            version=1,
            description=(
                "Required non-key Order Payments attributes cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_PAYMENTS_REQUIRED_NON_KEY_COLUMNS,
        ),
        PredicateRule(
            rule_id="ORDER-PAYMENTS-DQ05",
            version=1,
            description="Payment sequence identifiers must be positive integers.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(payment_sequential AS BIGINT) IS NOT NULL "
                "AND try_cast(payment_sequential AS BIGINT) > 0 "
                "AND try_cast(payment_sequential AS DECIMAL(38,18)) = "
                "try_cast(payment_sequential AS BIGINT)"
            ),
            expected_condition="payment_sequential is a positive integer",
        ),
        PredicateRule(
            rule_id="ORDER-PAYMENTS-DQ06",
            version=1,
            description="Payment installment counts must be non-negative integers.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(payment_installments AS BIGINT) IS NOT NULL "
                "AND try_cast(payment_installments AS BIGINT) >= 0 "
                "AND try_cast(payment_installments AS DECIMAL(38,18)) = "
                "try_cast(payment_installments AS BIGINT)"
            ),
            expected_condition="payment_installments is a non-negative integer",
        ),
        PredicateRule(
            rule_id="ORDER-PAYMENTS-DQ07",
            version=1,
            description="Payment values must be parseable non-negative decimals.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(payment_value AS DECIMAL(38,18)) IS NOT NULL "
                "AND try_cast(payment_value AS DECIMAL(38,18)) >= 0"
            ),
            expected_condition="payment_value is a non-negative decimal",
        ),
        ObservedCountRule(
            rule_id="ORDER-PAYMENTS-DQ08",
            version=1,
            description="Count source rows with zero payment value.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="try_cast(payment_value AS DECIMAL(38,18)) = 0",
            expected_condition=(
                "observed count only; zero payment values remain source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-PAYMENTS-DQ09",
            version=1,
            description="Count source rows with zero payment installments.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="try_cast(payment_installments AS BIGINT) = 0",
            expected_condition=(
                "observed count only; zero installments remain source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDER-PAYMENTS-DQ10",
            version=1,
            description="Count source rows whose payment type is not_defined.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="payment_type = 'not_defined'",
            expected_condition=(
                "observed count only; not_defined payment types remain source-faithful"
            ),
        ),
    ),
)
