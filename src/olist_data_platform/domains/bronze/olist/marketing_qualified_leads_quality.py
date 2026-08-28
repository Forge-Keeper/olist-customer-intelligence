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

MQL_KEY_COLUMNS = ("mql_id",)


OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_marketing_qualified_leads",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="MQL-DQ01",
            version=1,
            description="The authoritative MQL snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="MQL-DQ02",
            version=1,
            description="The MQL natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=MQL_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="MQL-DQ03",
            version=1,
            description="The MQL natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=MQL_KEY_COLUMNS,
        ),
        NotNullRule(
            rule_id="MQL-DQ04",
            version=1,
            description=(
                "Required MQL source attributes first_contact_date and "
                "landing_page_id cannot contain null values."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("first_contact_date", "landing_page_id"),
        ),
        PredicateRule(
            rule_id="MQL-DQ05",
            version=1,
            description="MQL first_contact_date must be parseable as yyyy-MM-dd.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="to_date(first_contact_date, 'yyyy-MM-dd') IS NOT NULL",
            expected_condition="first_contact_date is parseable as yyyy-MM-dd",
        ),
    ),
)
