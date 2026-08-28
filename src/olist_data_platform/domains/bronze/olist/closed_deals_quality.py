from __future__ import annotations

from olist_data_platform.platform.quality import (
    DataQualityContract,
    NonEmptyRule,
    NotNullRule,
    QualityCategory,
    QualitySeverity,
    UniqueRule,
)

CLOSED_DEALS_KEY_COLUMNS = ("mql_id",)


OLIST_CLOSED_DEALS_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_closed_deals",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="CLOSED-DEALS-DQ01",
            version=1,
            description="The authoritative Closed Deals snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="CLOSED-DEALS-DQ02",
            version=1,
            description="The Closed Deals natural key cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=CLOSED_DEALS_KEY_COLUMNS,
        ),
        UniqueRule(
            rule_id="CLOSED-DEALS-DQ03",
            version=1,
            description="The Closed Deals natural key must be unique in the snapshot.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=CLOSED_DEALS_KEY_COLUMNS,
        ),
    ),
)
