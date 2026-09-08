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

ORDER_ITEMS_KEY_COLUMNS = ("order_id", "order_item_id")
ORDER_ITEMS_REQUIRED_NON_KEY_COLUMNS = (
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
)

OLIST_ORDER_ITEMS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_order_items",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="ORDER-ITEMS-DQ01",
            version=1,
            description="The authoritative Order Items snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="ORDER-ITEMS-DQ02",
            version=1,
            description="The Order Items natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_ITEMS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="ORDER-ITEMS-DQ03",
            version=1,
            description="The Order Items natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_ITEMS_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="ORDER-ITEMS-DQ04",
            version=1,
            description=(
                "Required non-key Order Items attributes cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDER_ITEMS_REQUIRED_NON_KEY_COLUMNS,
        ),
        PredicateRule(
            rule_id="ORDER-ITEMS-DQ05",
            version=1,
            description="Order item sequence identifiers must be positive integers.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(order_item_id AS BIGINT) IS NOT NULL "
                "AND try_cast(order_item_id AS BIGINT) > 0 "
                "AND try_cast(order_item_id AS DECIMAL(38,18)) = "
                "try_cast(order_item_id AS BIGINT)"
            ),
            expected_condition="order_item_id is a positive integer",
        ),
        PredicateRule(
            rule_id="ORDER-ITEMS-DQ06",
            version=1,
            description="Shipping limit dates must parse as timestamps.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="try_cast(shipping_limit_date AS TIMESTAMP) IS NOT NULL",
            expected_condition="shipping_limit_date is parseable as timestamp",
        ),
        PredicateRule(
            rule_id="ORDER-ITEMS-DQ07",
            version=1,
            description=(
                "Price and freight values must be parseable non-negative decimals."
            ),
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(price AS DECIMAL(38,18)) IS NOT NULL "
                "AND try_cast(price AS DECIMAL(38,18)) >= 0 "
                "AND try_cast(freight_value AS DECIMAL(38,18)) IS NOT NULL "
                "AND try_cast(freight_value AS DECIMAL(38,18)) >= 0"
            ),
            expected_condition="price and freight_value are non-negative decimals",
        ),
        ObservedCountRule(
            rule_id="ORDER-ITEMS-DQ08",
            version=1,
            description="Count source rows with zero freight value.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="try_cast(freight_value AS DECIMAL(38,18)) = 0",
            expected_condition=(
                "observed count only; zero freight remains source-faithful"
            ),
        ),
    ),
)
