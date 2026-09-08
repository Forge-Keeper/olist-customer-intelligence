from olist_data_platform.domains.bronze.olist.order_payments_bronze_config import (
    OLIST_ORDER_PAYMENTS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.order_payments_quality import (
    OLIST_ORDER_PAYMENTS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.quality import QualitySeverity


def test_order_payments_bronze_contract_uses_composite_key_full_replace() -> None:
    assert OLIST_ORDER_PAYMENTS_BRONZE_CONFIG.key_columns == (
        "order_id",
        "payment_sequential",
    )
    assert (
        OLIST_ORDER_PAYMENTS_BRONZE_CONFIG.write_strategy
        is WriteStrategy.FULL_REPLACE
    )


def test_order_payments_bronze_contract_preserves_source_columns_as_strings() -> None:
    columns = {
        column.name: column for column in OLIST_ORDER_PAYMENTS_BRONZE_CONFIG.columns
    }

    assert set(columns) == {
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
        "source_file",
    }
    assert all(column.data_type == "string" for column in columns.values())
    for column_name in (
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ):
        assert columns[column_name].nullable is False


def test_order_payments_quality_contract_has_expected_severity_split() -> None:
    rules = OLIST_ORDER_PAYMENTS_QUALITY_CONTRACT.rules

    assert [rule.rule_id for rule in rules] == [
        "ORDER-PAYMENTS-DQ01",
        "ORDER-PAYMENTS-DQ02",
        "ORDER-PAYMENTS-DQ03",
        "ORDER-PAYMENTS-DQ04",
        "ORDER-PAYMENTS-DQ05",
        "ORDER-PAYMENTS-DQ06",
        "ORDER-PAYMENTS-DQ07",
        "ORDER-PAYMENTS-DQ08",
        "ORDER-PAYMENTS-DQ09",
        "ORDER-PAYMENTS-DQ10",
    ]
    assert [rule.severity for rule in rules[:7]] == [QualitySeverity.ERROR] * 7
    assert [rule.severity for rule in rules[7:]] == [QualitySeverity.INFO] * 3
