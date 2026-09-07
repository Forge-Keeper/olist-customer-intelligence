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

ORDERS_KEY_COLUMNS = ("order_id",)
ORDERS_REQUIRED_NON_KEY_COLUMNS = (
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_estimated_delivery_date",
)
ORDERS_TIMESTAMP_COLUMNS = (
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
)

_TIMESTAMP_SOURCE_SHAPE = " AND ".join(
    f"({column} IS NULL OR try_cast({column} AS TIMESTAMP) IS NOT NULL)"
    for column in ORDERS_TIMESTAMP_COLUMNS
)

OLIST_ORDERS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_orders",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="ORDERS-DQ01",
            version=1,
            description="The authoritative Orders snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="ORDERS-DQ02",
            version=1,
            description="The Orders natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDERS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="ORDERS-DQ03",
            version=1,
            description="The Orders natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDERS_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="ORDERS-DQ04",
            version=1,
            description=(
                "Required non-key Orders attributes cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=ORDERS_REQUIRED_NON_KEY_COLUMNS,
        ),
        PredicateRule(
            rule_id="ORDERS-DQ05",
            version=1,
            description="Present Orders timestamp attributes must parse as timestamps.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=_TIMESTAMP_SOURCE_SHAPE,
            expected_condition=(
                "timestamp source values are null or parseable timestamps"
            ),
        ),
        ObservedCountRule(
            rule_id="ORDERS-DQ06",
            version=1,
            description="Count orders without an approval timestamp.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="order_approved_at IS NULL",
            expected_condition="observed count only; source value remains unchanged",
        ),
        ObservedCountRule(
            rule_id="ORDERS-DQ07",
            version=1,
            description="Count orders without a customer delivery timestamp.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="order_delivered_customer_date IS NULL",
            expected_condition="observed count only; source value remains unchanged",
        ),
    ),
)
