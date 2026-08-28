# Operations

This page is generated from the public Python API and docstrings.

## Execution model

::: olist_data_platform.platform.operations.model
    options:
      show_root_heading: true
      members:
        - ExecutionStatus
        - QualityRunStatus
        - ExecutionStage
        - ExecutionRun

## Execution tracker

::: olist_data_platform.platform.operations.tracker.ExecutionRunTracker
    options:
      show_root_heading: true
      members:
        - start
        - current
        - set_stage
        - update_metrics
        - update_quality
        - succeed
        - reject
        - fail
