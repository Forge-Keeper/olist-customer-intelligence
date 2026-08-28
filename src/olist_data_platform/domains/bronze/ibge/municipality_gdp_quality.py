from __future__ import annotations

from olist_data_platform.domains.ingestion.ibge.datasets import MUNICIPALITY_GDP
from olist_data_platform.platform.quality import (
    AllowedValuesRule,
    DataQualityContract,
    ExpectedCombinationsRule,
    NonEmptyRule,
    NotNullRule,
    ObservedCountRule,
    PredicateRule,
    QualityCategory,
    QualitySeverity,
    UniqueRule,
)

GDP_KEY_COLUMNS = ("municipality_code", "reference_year", "variable_code")


def build_municipality_gdp_quality_contract(
    periods: tuple[str, ...],
) -> DataQualityContract:
    """Build the Bronze GDP quality contract for the explicit execution scope."""
    if not periods:
        raise ValueError("GDP quality periods cannot be empty.")
    expected_combinations = tuple(
        (period, variable)
        for period in periods
        for variable in MUNICIPALITY_GDP.variables
    )
    return DataQualityContract(
        dataset="ibge_municipality_gdp",
        layer="bronze",
        rules=(
            NonEmptyRule(
                rule_id="GDP-DQ01",
                version=1,
                description=(
                    "The evaluated GDP execution scope must contain records."
                ),
                category=QualityCategory.COMPLETENESS,
                severity=QualitySeverity.ERROR,
            ),
            NotNullRule(
                rule_id="GDP-DQ02",
                version=1,
                description="GDP natural-key columns cannot contain null values.",
                category=QualityCategory.COMPLETENESS,
                severity=QualitySeverity.ERROR,
                columns=GDP_KEY_COLUMNS,
            ),
            UniqueRule(
                rule_id="GDP-DQ03",
                version=1,
                description=(
                    "GDP natural keys must be unique within the evaluated scope."
                ),
                category=QualityCategory.UNIQUENESS,
                severity=QualitySeverity.ERROR,
                columns=GDP_KEY_COLUMNS,
            ),
            AllowedValuesRule(
                rule_id="GDP-DQ04",
                version=1,
                description=(
                    "Reference years must belong to the requested execution scope."
                ),
                category=QualityCategory.VALIDITY,
                severity=QualitySeverity.ERROR,
                column="reference_year",
                allowed_values=periods,
            ),
            AllowedValuesRule(
                rule_id="GDP-DQ05",
                version=1,
                description=(
                    "Variable codes must belong to the approved GDP dataset "
                    "selection."
                ),
                category=QualityCategory.VALIDITY,
                severity=QualitySeverity.ERROR,
                column="variable_code",
                allowed_values=MUNICIPALITY_GDP.variables,
            ),
            PredicateRule(
                rule_id="GDP-DQ06",
                version=1,
                description="GDP dt_base must be January 1 of reference_year.",
                category=QualityCategory.CONSISTENCY,
                severity=QualitySeverity.ERROR,
                expression="dt_base = make_date(CAST(reference_year AS INT), 1, 1)",
                expected_condition="dt_base equals January 1 of reference_year",
            ),
            ExpectedCombinationsRule(
                rule_id="GDP-DQ07",
                version=1,
                description=(
                    "Every requested reference-year and variable combination "
                    "must be represented."
                ),
                category=QualityCategory.COMPLETENESS,
                severity=QualitySeverity.ERROR,
                columns=("reference_year", "variable_code"),
                expected_combinations=expected_combinations,
            ),
            ObservedCountRule(
                rule_id="GDP-DQ08",
                version=1,
                description=(
                    "Observe SIDRA special-value markers without altering Bronze "
                    "payload fidelity."
                ),
                category=QualityCategory.OBSERVATION,
                severity=QualitySeverity.INFO,
                expression="variant_get(payload, '$.Valor', 'string') = '...'",
                expected_condition=(
                    "observation only; source special-value markers are preserved"
                ),
            ),
        ),
    )
