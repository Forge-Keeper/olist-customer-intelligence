# Data Quality

This page is generated from the public Python API and docstrings.

## Contracts and results

::: olist_data_platform.platform.quality.model
    options:
      show_root_heading: true
      members:
        - QualitySeverity
        - QualityStatus
        - QualityOutcome
        - QualityCategory
        - QualityRule
        - DataQualityContract
        - QualityResult
        - QualityReport
        - QualityCheckedBatch

## Runner

::: olist_data_platform.platform.quality.runner.DataQualityRunner
    options:
      show_root_heading: true
      members:
        - evaluate

## Rule types

::: olist_data_platform.platform.quality.rules
    options:
      show_root_heading: true
      members:
        - NonEmptyRule
        - NotNullRule
        - UniqueRule
        - AllowedValuesRule
        - PredicateRule
        - ExpectedCombinationsRule
        - ObservedCountRule
