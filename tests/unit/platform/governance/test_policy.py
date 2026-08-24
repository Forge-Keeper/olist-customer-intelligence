import pytest

from olist_data_platform.platform.governance import (
    GovernancePolicyDefinition,
    GovernancePolicyScope,
    GovernancePolicyType,
)


def test_should_define_row_filter_policy():
    policy = GovernancePolicyDefinition(
        name="filter_region",
        policy_type=GovernancePolicyType.ROW_FILTER,
        scope=GovernancePolicyScope.SCHEMA,
        scope_name="dev.governance_validation",
        function_name="dev.governance_validation.filter_region_udf",
        principals=("account users",),
        match_condition="has_tag('region')",
        match_alias="region_column",
        using_columns=("region_column",),
        description="Filter rows by governed region attribute.",
    )

    assert policy.policy_type is GovernancePolicyType.ROW_FILTER
    assert policy.scope is GovernancePolicyScope.SCHEMA


def test_should_require_column_match_for_column_mask():
    with pytest.raises(ValueError, match="COLUMN_MASK requires"):
        GovernancePolicyDefinition(
            name="mask_secret",
            policy_type=GovernancePolicyType.COLUMN_MASK,
            scope=GovernancePolicyScope.SCHEMA,
            scope_name="dev.governance_validation",
            function_name="dev.governance_validation.mask_secret_udf",
            principals=("account users",),
        )


def test_should_reject_empty_principals():
    with pytest.raises(ValueError, match="principals cannot be empty"):
        GovernancePolicyDefinition(
            name="filter_region",
            policy_type=GovernancePolicyType.ROW_FILTER,
            scope=GovernancePolicyScope.SCHEMA,
            scope_name="dev.governance_validation",
            function_name="dev.governance_validation.filter_region_udf",
            principals=(),
        )
