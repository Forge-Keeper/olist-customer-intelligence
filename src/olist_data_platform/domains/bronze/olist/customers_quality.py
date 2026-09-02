from __future__ import annotations

from olist_data_platform.platform.quality import (
    DataQualityContract,
    NonEmptyRule,
    NotNullRule,
    PredicateRule,
    QualityCategory,
    QualitySeverity,
    UniqueRule,
)

CUSTOMERS_KEY_COLUMNS = ("customer_id",)
CUSTOMERS_REQUIRED_ATTRIBUTE_COLUMNS = (
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
)


OLIST_CUSTOMERS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_customers",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="CUSTOMERS-DQ01",
            version=1,
            description="The authoritative Customers snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="CUSTOMERS-DQ02",
            version=1,
            description="The Customers natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=CUSTOMERS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="CUSTOMERS-DQ03",
            version=1,
            description="The Customers natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=CUSTOMERS_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="CUSTOMERS-DQ04",
            version=1,
            description=(
                "Required Customers source attributes cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=CUSTOMERS_REQUIRED_ATTRIBUTE_COLUMNS,
        ),
        PredicateRule(
            rule_id="CUSTOMERS-DQ05",
            version=1,
            description=(
                "Customer ZIP code prefix must contain exactly five decimal digits."
            ),
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="customer_zip_code_prefix RLIKE '^[0-9]{5}$'",
            expected_condition="customer_zip_code_prefix is exactly five digits",
        ),
    ),
)
