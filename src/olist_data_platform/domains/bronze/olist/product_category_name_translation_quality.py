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

TRANSLATION_KEY_COLUMNS = ("product_category_name",)
TRANSLATION_REQUIRED_COLUMNS = (
    "product_category_name",
    "product_category_name_english",
)

OLIST_PRODUCT_CATEGORY_NAME_TRANSLATION_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_product_category_name_translation",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="CATEGORY-TRANSLATION-DQ01",
            version=1,
            description=(
                "The authoritative category translation snapshot must contain records."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="CATEGORY-TRANSLATION-DQ02",
            version=1,
            description="The source category key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=TRANSLATION_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="CATEGORY-TRANSLATION-DQ03",
            version=1,
            description="The source category key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=TRANSLATION_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="CATEGORY-TRANSLATION-DQ04",
            version=1,
            description="The English translation cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("product_category_name_english",),
        ),
        PredicateRule(
            rule_id="CATEGORY-TRANSLATION-DQ05",
            version=1,
            description=(
                "Category and English translation values cannot be blank strings."
            ),
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "trim(product_category_name) <> '' AND "
                "trim(product_category_name_english) <> ''"
            ),
            expected_condition="both source values contain non-blank text",
        ),
    ),
)
