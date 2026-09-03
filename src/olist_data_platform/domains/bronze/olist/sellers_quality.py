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

SELLERS_KEY_COLUMNS = ("seller_id",)
SELLERS_REQUIRED_ATTRIBUTE_COLUMNS = (
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state",
)

OLIST_SELLERS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_sellers",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="SELLERS-DQ01",
            version=1,
            description="The authoritative Sellers snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="SELLERS-DQ02",
            version=1,
            description="The Sellers natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=SELLERS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="SELLERS-DQ03",
            version=1,
            description="The Sellers natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=SELLERS_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="SELLERS-DQ04",
            version=1,
            description=(
                "Required Sellers source attributes cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=SELLERS_REQUIRED_ATTRIBUTE_COLUMNS,
        ),
        PredicateRule(
            rule_id="SELLERS-DQ05",
            version=1,
            description=(
                "Seller ZIP code prefix must contain exactly five decimal digits."
            ),
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="seller_zip_code_prefix RLIKE '^[0-9]{5}$'",
            expected_condition="seller_zip_code_prefix is exactly five digits",
        ),
    ),
)
