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

PRODUCTS_KEY_COLUMNS = ("product_id",)
PRODUCTS_NUMERIC_SOURCE_COLUMNS = (
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
)
PRODUCTS_DESCRIPTIVE_COLUMNS = (
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
)
PRODUCTS_PHYSICAL_COLUMNS = (
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
)

_NUMERIC_SOURCE_SHAPE = " AND ".join(
    f"({column} IS NULL OR {column} RLIKE '^[0-9]+$')"
    for column in PRODUCTS_NUMERIC_SOURCE_COLUMNS
)
_MISSING_DESCRIPTIVE_ATTRIBUTE = " OR ".join(
    f"{column} IS NULL" for column in PRODUCTS_DESCRIPTIVE_COLUMNS
)
_MISSING_PHYSICAL_ATTRIBUTE = " OR ".join(
    f"{column} IS NULL" for column in PRODUCTS_PHYSICAL_COLUMNS
)

OLIST_PRODUCTS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_products",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="PRODUCTS-DQ01",
            version=1,
            description="The authoritative Products snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="PRODUCTS-DQ02",
            version=1,
            description="The Products natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=PRODUCTS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="PRODUCTS-DQ03",
            version=1,
            description="The Products natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=PRODUCTS_KEY_COLUMNS,
        ),
        PredicateRule(
            rule_id="PRODUCTS-DQ04",
            version=1,
            description=(
                "Present Products numeric source attributes must contain "
                "non-negative integer text."
            ),
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=_NUMERIC_SOURCE_SHAPE,
            expected_condition=(
                "numeric source attributes are null or non-negative integer text"
            ),
        ),
        ObservedCountRule(
            rule_id="PRODUCTS-DQ05",
            version=1,
            description="Count products with an incomplete descriptive attribute set.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression=_MISSING_DESCRIPTIVE_ATTRIBUTE,
            expected_condition="observed count only; does not block persistence",
        ),
        ObservedCountRule(
            rule_id="PRODUCTS-DQ06",
            version=1,
            description="Count products with an incomplete physical attribute set.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression=_MISSING_PHYSICAL_ATTRIBUTE,
            expected_condition="observed count only; does not block persistence",
        ),
        ObservedCountRule(
            rule_id="PRODUCTS-DQ07",
            version=1,
            description="Count products whose observed source weight is zero.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="try_cast(product_weight_g AS BIGINT) = 0",
            expected_condition="observed count only; does not block persistence",
        ),
    ),
)
