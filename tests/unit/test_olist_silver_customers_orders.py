from datetime import datetime

from pyspark.sql import functions as F

from olist_data_platform.domains.silver.olist.customers import (
    OLIST_CUSTOMERS_SILVER_CONTRACT,
    OLIST_CUSTOMERS_SILVER_QUALITY_CONTRACT,
    transform_customers,
)
from olist_data_platform.domains.silver.olist.orders import (
    OLIST_ORDERS_SILVER_CONTRACT,
    OLIST_ORDERS_SILVER_QUALITY_CONTRACT,
    attach_customer_relationship,
    transform_orders,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)


def _customers_bronze(spark):
    return spark.createDataFrame(
        [
            (
                "customer-1",
                "person-1",
                "01234",
                "sao paulo",
                "SP",
                "customers.csv",
                datetime(2026, 9, 9, 8, 0),
            ),
            (
                "customer-2",
                "person-1",
                "56789",
                "campinas",
                "SP",
                "customers.csv",
                datetime(2026, 9, 9, 8, 0),
            ),
        ],
        (
            "customer_id string, customer_unique_id string, "
            "customer_zip_code_prefix string, customer_city string, "
            "customer_state string, source_file string, ingestion_timestamp timestamp"
        ),
    )


def _orders_bronze(spark, *, customer_id="customer-1", approved="2026-09-09 08:05:00"):
    return spark.createDataFrame(
        [
            (
                "order-1",
                customer_id,
                "delivered",
                "2026-09-09 08:00:00",
                approved,
                "2026-09-09 08:04:00",
                "2026-09-09 08:03:00",
                "2026-09-15 00:00:00",
                "orders.csv",
                datetime(2026, 9, 9, 8, 0),
            )
        ],
        (
            "order_id string, customer_id string, order_status string, "
            "order_purchase_timestamp string, order_approved_at string, "
            "order_delivered_carrier_date string, "
            "order_delivered_customer_date string, "
            "order_estimated_delivery_date string, source_file string, "
            "ingestion_timestamp timestamp"
        ),
    )


def test_customers_preserve_transactional_and_longitudinal_identity(spark):
    transformed = transform_customers(_customers_bronze(spark))

    rows = transformed.orderBy("customer_id").collect()
    assert [row.customer_id for row in rows] == ["customer-1", "customer-2"]
    assert {row.customer_unique_id for row in rows} == {"person-1"}
    assert rows[0].customer_zip_code_prefix == "01234"
    assert transformed.select("customer_id").distinct().count() == 2

    report = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_CUSTOMERS_SILVER_QUALITY_CONTRACT,
        run_id="test-customers",
        evaluation_scope="{}",
    ).report
    assert report.outcome is QualityOutcome.PASSED
    assert OLIST_CUSTOMERS_SILVER_CONTRACT.key_columns == ("customer_id",)


def test_orders_are_typed_and_temporal_source_anomalies_are_warnings(spark):
    customers = transform_customers(_customers_bronze(spark))
    orders = attach_customer_relationship(
        transform_orders(_orders_bronze(spark)),
        customers,
    )

    row = orders.first()
    assert isinstance(row.order_purchase_timestamp, datetime)
    assert row._customer_exists is True

    report = DataQualityRunner().evaluate(
        dataframe=orders,
        contract=OLIST_ORDERS_SILVER_QUALITY_CONTRACT,
        run_id="test-orders",
        evaluation_scope="{}",
    ).report
    status_by_rule = {result.rule_id: result.status for result in report.results}
    assert report.outcome is QualityOutcome.PASSED_WITH_WARNINGS
    assert status_by_rule["OLIST-SILVER-ORDERS-DQ08"] is QualityStatus.FAIL
    assert status_by_rule["OLIST-SILVER-ORDERS-DQ09"] is QualityStatus.FAIL
    assert OLIST_ORDERS_SILVER_CONTRACT.key_columns == ("order_id",)


def test_orders_orphan_is_a_blocking_failure(spark):
    customers = transform_customers(_customers_bronze(spark))
    orders = attach_customer_relationship(
        transform_orders(_orders_bronze(spark, customer_id="missing-customer")),
        customers,
    )

    report = DataQualityRunner().evaluate(
        dataframe=orders,
        contract=OLIST_ORDERS_SILVER_QUALITY_CONTRACT,
        run_id="test-orphan",
        evaluation_scope="{}",
    ).report

    assert report.has_blocking_failures
    failed = {result.rule_id for result in report.results if result.status is QualityStatus.FAIL}
    assert "OLIST-SILVER-ORDERS-DQ05" in failed


def test_optional_timestamp_parse_failure_is_blocking(spark):
    customers = transform_customers(_customers_bronze(spark))
    orders = attach_customer_relationship(
        transform_orders(_orders_bronze(spark, approved="not-a-timestamp")),
        customers,
    )

    report = DataQualityRunner().evaluate(
        dataframe=orders,
        contract=OLIST_ORDERS_SILVER_QUALITY_CONTRACT,
        run_id="test-parse",
        evaluation_scope="{}",
    ).report

    failed = {result.rule_id for result in report.results if result.status is QualityStatus.FAIL}
    assert report.has_blocking_failures
    assert "OLIST-SILVER-ORDERS-DQ04" in failed


def test_silver_projection_does_not_pass_through_unexpected_bronze_columns(spark):
    bronze = _customers_bronze(spark).withColumn("unexpected_source_field", F.lit("x"))
    transformed = transform_customers(bronze)

    assert "unexpected_source_field" not in transformed.columns
    assert set(OLIST_CUSTOMERS_SILVER_CONTRACT.required_columns) == set(
        transformed.columns
    )
