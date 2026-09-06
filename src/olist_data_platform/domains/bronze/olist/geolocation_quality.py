from __future__ import annotations

from olist_data_platform.platform.quality import (
    DataQualityContract,
    NonEmptyRule,
    NotNullRule,
    ObservedCountRule,
    PredicateRule,
    QualityCategory,
    QualitySeverity,
)

GEOLOCATION_SOURCE_COLUMNS = (
    "geolocation_zip_code_prefix",
    "geolocation_lat",
    "geolocation_lng",
    "geolocation_city",
    "geolocation_state",
)

OLIST_GEOLOCATION_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_geolocation",
    layer="bronze",
    rules=(
        NonEmptyRule(
            rule_id="GEOLOCATION-DQ01",
            version=1,
            description="The authoritative Geolocation snapshot must contain records.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
        ),
        NotNullRule(
            rule_id="GEOLOCATION-DQ02",
            version=1,
            description="Observed Geolocation source columns cannot contain null values.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=GEOLOCATION_SOURCE_COLUMNS,
        ),
        PredicateRule(
            rule_id="GEOLOCATION-DQ03",
            version=1,
            description="ZIP code prefixes must preserve a numeric source shape.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="geolocation_zip_code_prefix RLIKE '^[0-9]{1,5}$'",
            expected_condition="ZIP code prefix contains one to five decimal digits",
        ),
        PredicateRule(
            rule_id="GEOLOCATION-DQ04",
            version=1,
            description="Latitude and longitude text must represent valid coordinates.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "try_cast(geolocation_lat AS DOUBLE) BETWEEN -90 AND 90 AND "
                "try_cast(geolocation_lng AS DOUBLE) BETWEEN -180 AND 180"
            ),
            expected_condition="latitude is [-90,90] and longitude is [-180,180]",
        ),
        ObservedCountRule(
            rule_id="GEOLOCATION-DQ05",
            version=1,
            description="Count rows whose state code is not two uppercase letters.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="NOT (geolocation_state RLIKE '^[A-Z]{2}$')",
            expected_condition="observed count only; source value remains unchanged",
        ),
    ),
)
