from unittest.mock import Mock

import pytest

from olist_data_platform.platform.governance import (
    GovernancePolicyDefinition,
    GovernancePolicyLifecycle,
    GovernancePolicyScope,
    GovernancePolicyType,
)


def _row_filter() -> GovernancePolicyDefinition:
    return GovernancePolicyDefinition(
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


def _column_mask() -> GovernancePolicyDefinition:
    return GovernancePolicyDefinition(
        name="mask_secret",
        policy_type=GovernancePolicyType.COLUMN_MASK,
        scope=GovernancePolicyScope.SCHEMA,
        scope_name="dev.governance_validation",
        function_name="dev.governance_validation.mask_secret_udf",
        principals=("account users",),
        match_condition="has_tag('sensitivity', 'secret')",
        match_alias="secret_column",
        description="Mask governed secret columns.",
    )


def test_should_render_row_filter_sql():
    lifecycle = GovernancePolicyLifecycle(Mock(), _row_filter())
    sql = lifecycle.render_create_or_replace_sql()

    assert "CREATE OR REPLACE POLICY `filter_region`" in sql
    assert "ON SCHEMA dev.governance_validation" in sql
    assert "ROW FILTER dev.governance_validation.filter_region_udf" in sql
    assert "MATCH COLUMNS has_tag('region') AS `region_column`" in sql
    assert "USING COLUMNS (region_column)" in sql


def test_should_render_column_mask_sql():
    lifecycle = GovernancePolicyLifecycle(Mock(), _column_mask())
    sql = lifecycle.render_create_or_replace_sql()

    assert "COLUMN MASK dev.governance_validation.mask_secret_udf" in sql
    assert "MATCH COLUMNS has_tag('sensitivity', 'secret') AS `secret_column`" in sql
    assert "ON COLUMN `secret_column`" in sql


def test_should_create_policy_when_missing():
    spark = Mock()
    spark.sql.return_value.collect.return_value = []
    lifecycle = GovernancePolicyLifecycle(spark, _row_filter())

    lifecycle.ensure()

    sql_calls = [call.args[0] for call in spark.sql.call_args_list]
    assert sql_calls[0] == "SHOW POLICIES ON SCHEMA dev.governance_validation"
    assert any("CREATE OR REPLACE POLICY" in sql for sql in sql_calls)


def test_should_fail_on_existing_policy_type_drift():
    spark = Mock()
    spark.sql.return_value.collect.return_value = [
        {
            "Policy Name": "filter_region",
            "Policy Type": "COLUMN_MASK",
            "Comment": None,
        }
    ]
    lifecycle = GovernancePolicyLifecycle(spark, _row_filter())

    with pytest.raises(ValueError, match="policy type is incompatible"):
        lifecycle.ensure()
