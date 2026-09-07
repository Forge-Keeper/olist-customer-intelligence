from olist_data_platform.domains.bronze.olist.orders_bronze_config import (
    OLIST_ORDERS_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.orders_quality import (
    OLIST_ORDERS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.quality import QualitySeverity


def test_orders_bronze_contract_uses_order_id_full_replace() -> None:
    assert OLIST_ORDERS_BRONZE_CONFIG.key_columns == ("order_id",)
    assert OLIST_ORDERS_BRONZE_CONFIG.write_strategy is WriteStrategy.FULL_REPLACE


def test_orders_bronze_contract_preserves_source_columns_as_strings() -> None:
    columns = {column.name: column for column in OLIST_ORDERS_BRONZE_CONFIG.columns}

    assert set(columns) == {
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "source_file",
    }
    assert all(column.data_type == "string" for column in columns.values())
    assert columns["order_id"].nullable is False
    assert columns["customer_id"].nullable is False
    assert columns["order_status"].nullable is False
    assert columns["order_purchase_timestamp"].nullable is False
    assert columns["order_estimated_delivery_date"].nullable is False
    assert columns["order_approved_at"].nullable is True
    assert columns["order_delivered_carrier_date"].nullable is True
    assert columns["order_delivered_customer_date"].nullable is True


def test_orders_quality_contract_has_blocking_core_rules() -> None:
    rules = OLIST_ORDERS_QUALITY_CONTRACT.rules

    assert [rule.rule_id for rule in rules] == [
        "ORDERS-DQ01",
        "ORDERS-DQ02",
        "ORDERS-DQ03",
        "ORDERS-DQ04",
        "ORDERS-DQ05",
        "ORDERS-DQ06",
    ]
    assert [rule.severity for rule in rules[:4]] == [QualitySeverity.ERROR] * 4
    assert [rule.severity for rule in rules[4:]] == [QualitySeverity.INFO] * 2
