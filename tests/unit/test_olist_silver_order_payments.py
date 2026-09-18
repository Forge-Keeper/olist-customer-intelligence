from datetime import datetime
from decimal import Decimal
import json

import pytest

from olist_data_platform.domains.silver.olist.order_payments import (
    OLIST_ORDER_PAYMENTS_SILVER_CONTRACT,
    OLIST_ORDER_PAYMENTS_SILVER_QUALITY_CONTRACT,
    attach_payment_relationship,
    transform_order_payments,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualitySeverity,
    QualityStatus,
)


def _bronze(
    spark,
    *,
    payment_sequential="1",
    payment_type="credit_card",
    payment_installments="1",
    payment_value="58.90",
):
    return spark.createDataFrame(
        [
            (
                "order-1",
                payment_sequential,
                payment_type,
                payment_installments,
                payment_value,
                "payments.csv",
                datetime(2026, 9, 18),
            )
        ],
        (
            "order_id string, payment_sequential string, payment_type string, "
            "payment_installments string, payment_value string, "
            "source_file string, ingestion_timestamp timestamp"
        ),
    )


def _orders(spark, *order_ids):
    return spark.createDataFrame(
        [(order_id,) for order_id in order_ids],
        "order_id string",
    )


def _evaluate(spark, bronze, orders):
    transformed = attach_payment_relationship(
        transform_order_payments(bronze),
        orders,
    )
    checked = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_ORDER_PAYMENTS_SILVER_QUALITY_CONTRACT,
        run_id="test-run",
        evaluation_scope="{}",
    )
    return transformed, checked.report


def _failed_rule_ids(report):
    return {
        result.rule_id
        for result in report.results
        if result.status is QualityStatus.FAIL
    }


def test_contract_freezes_typed_composite_grain() -> None:
    assert OLIST_ORDER_PAYMENTS_SILVER_CONTRACT.key_columns == (
        "order_id",
        "payment_sequential",
    )
    assert (
        OLIST_ORDER_PAYMENTS_SILVER_CONTRACT.write_strategy
        is WriteStrategy.FULL_REPLACE
    )

    columns = {
        column.name: (column.data_type, column.nullable)
        for column in OLIST_ORDER_PAYMENTS_SILVER_CONTRACT.columns
    }
    assert columns == {
        "order_id": ("string", False),
        "payment_sequential": ("int", False),
        "payment_type": ("string", False),
        "payment_installments": ("int", False),
        "payment_value": ("decimal(18,2)", False),
        "source_file": ("string", True),
        "bronze_ingestion_timestamp": ("timestamp", True),
        "silver_processed_timestamp": ("timestamp", False),
    }

    rules = OLIST_ORDER_PAYMENTS_SILVER_QUALITY_CONTRACT.rules
    assert [rule.rule_id for rule in rules] == [
        "OLIST-SILVER-ORDER-PAYMENTS-DQ01",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ02",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ03",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ04",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ05",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ06",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ07",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ08",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ09",
        "OLIST-SILVER-ORDER-PAYMENTS-DQ10",
    ]
    assert [rule.severity for rule in rules[:7]] == [QualitySeverity.ERROR] * 7
    assert [rule.severity for rule in rules[7:]] == [QualitySeverity.INFO] * 3


def test_multiple_payments_per_order_are_preserved_with_lineage(spark):
    bronze = spark.createDataFrame(
        [
            (
                "order-1",
                "1",
                "credit_card",
                "1",
                "58.90",
                "payments.csv",
                datetime(2026, 9, 18),
            ),
            (
                "order-1",
                "2",
                "voucher",
                "0",
                "0",
                "payments.csv",
                datetime(2026, 9, 18),
            ),
            (
                "order-2",
                "1",
                "not_defined",
                "1",
                "10.00",
                "payments.csv",
                datetime(2026, 9, 18),
            ),
        ],
        (
            "order_id string, payment_sequential string, payment_type string, "
            "payment_installments string, payment_value string, "
            "source_file string, ingestion_timestamp timestamp"
        ),
    )
    transformed, report = _evaluate(
        spark,
        bronze,
        _orders(spark, "order-1", "order-2"),
    )
    rows = transformed.orderBy("order_id", "payment_sequential").collect()

    assert len(rows) == 3
    assert [row.payment_sequential for row in rows[:2]] == [1, 2]
    assert rows[0].payment_value == Decimal("58.90")
    assert rows[1].payment_installments == 0
    assert rows[1].payment_value == Decimal("0.00")
    assert rows[0].bronze_ingestion_timestamp == datetime(2026, 9, 18)
    assert rows[0].silver_processed_timestamp is not None
    assert not report.has_blocking_failures

    observed = {
        result.rule_id: json.loads(result.observed_value)["observed_row_count"]
        for result in report.results
        if result.rule_id
        in {
            "OLIST-SILVER-ORDER-PAYMENTS-DQ08",
            "OLIST-SILVER-ORDER-PAYMENTS-DQ09",
            "OLIST-SILVER-ORDER-PAYMENTS-DQ10",
        }
    }
    assert observed == {
        "OLIST-SILVER-ORDER-PAYMENTS-DQ08": 1,
        "OLIST-SILVER-ORDER-PAYMENTS-DQ09": 1,
        "OLIST-SILVER-ORDER-PAYMENTS-DQ10": 1,
    }


@pytest.mark.parametrize(
    ("payment_value", "should_block"),
    [
        ("99.335", True),
        ("99.3300", False),
        ("0.0000000000000000001", True),
        ("1e2", True),
        ("12345678901234567.00", True),
    ],
)
def test_payment_value_requires_exact_decimal_18_2_representation(
    spark,
    payment_value,
    should_block,
):
    transformed, report = _evaluate(
        spark,
        _bronze(spark, payment_value=payment_value),
        _orders(spark, "order-1"),
    )

    if should_block:
        assert "OLIST-SILVER-ORDER-PAYMENTS-DQ03" in _failed_rule_ids(report)
    else:
        row = transformed.first()
        assert row is not None
        assert row.payment_value == Decimal("99.33")
        assert not report.has_blocking_failures


def test_int_overflow_is_blocked_by_typed_cast_rule(spark):
    _, report = _evaluate(
        spark,
        _bronze(spark, payment_sequential="2147483648"),
        _orders(spark, "order-1"),
    )

    assert "OLIST-SILVER-ORDER-PAYMENTS-DQ03" in _failed_rule_ids(report)


@pytest.mark.parametrize(
    ("field", "value", "expected_rule"),
    [
        ("payment_sequential", "0", "OLIST-SILVER-ORDER-PAYMENTS-DQ05"),
        ("payment_installments", "-1", "OLIST-SILVER-ORDER-PAYMENTS-DQ06"),
        ("payment_value", "-0.01", "OLIST-SILVER-ORDER-PAYMENTS-DQ07"),
    ],
)
def test_numeric_domains_remain_fail_closed(spark, field, value, expected_rule):
    kwargs = {field: value}
    _, report = _evaluate(
        spark,
        _bronze(spark, **kwargs),
        _orders(spark, "order-1"),
    )

    assert expected_rule in _failed_rule_ids(report)


def test_orphan_payment_is_blocking(spark):
    transformed, report = _evaluate(
        spark,
        _bronze(spark),
        _orders(spark, "other-order"),
    )
    row = transformed.first()

    assert row is not None
    assert row._order_exists is False
    assert "OLIST-SILVER-ORDER-PAYMENTS-DQ04" in _failed_rule_ids(report)


def test_duplicate_composite_key_is_blocking(spark):
    bronze = _bronze(spark).unionByName(_bronze(spark))
    _, report = _evaluate(
        spark,
        bronze,
        _orders(spark, "order-1"),
    )

    assert "OLIST-SILVER-ORDER-PAYMENTS-DQ02" in _failed_rule_ids(report)


def test_missing_bronze_columns_are_rejected_before_dq(spark):
    incomplete = _bronze(spark).drop("payment_value")

    with pytest.raises(
        ValueError,
        match="missing required columns.*payment_value",
    ):
        transform_order_payments(incomplete)
