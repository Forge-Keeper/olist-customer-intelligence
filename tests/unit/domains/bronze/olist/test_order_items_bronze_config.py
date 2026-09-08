from olist_data_platform.domains.bronze.olist.order_items_bronze_config import (
    OLIST_ORDER_ITEMS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.order_items_quality import (
    OLIST_ORDER_ITEMS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.quality import QualitySeverity


def test_order_items_bronze_contract_uses_composite_key_full_replace() -> None:
    assert OLIST_ORDER_ITEMS_BRONZE_CONFIG.key_columns == (
        "order_id",
        "order_item_id",
    )
    assert OLIST_ORDER_ITEMS_BRONZE_CONFIG.write_strategy is WriteStrategy.FULL_REPLACE


def test_order_items_bronze_contract_preserves_source_columns_as_strings() -> None:
    columns = {
        column.name: column for column in OLIST_ORDER_ITEMS_BRONZE_CONFIG.columns
    }

    assert set(columns) == {
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
        "source_file",
    }
    assert all(column.data_type == "string" for column in columns.values())
    for column_name in (
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ):
        assert columns[column_name].nullable is False


def test_order_items_quality_contract_has_blocking_core_rules() -> None:
    rules = OLIST_ORDER_ITEMS_QUALITY_CONTRACT.rules

    assert [rule.rule_id for rule in rules] == [
        "ORDER-ITEMS-DQ01",
        "ORDER-ITEMS-DQ02",
        "ORDER-ITEMS-DQ03",
        "ORDER-ITEMS-DQ04",
        "ORDER-ITEMS-DQ05",
        "ORDER-ITEMS-DQ06",
        "ORDER-ITEMS-DQ07",
        "ORDER-ITEMS-DQ08",
    ]
    assert [rule.severity for rule in rules[:7]] == [QualitySeverity.ERROR] * 7
    assert rules[7].severity is QualitySeverity.INFO
