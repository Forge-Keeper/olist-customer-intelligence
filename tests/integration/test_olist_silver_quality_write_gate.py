from datetime import datetime

import pytest
from pyspark.sql.readwriter import DataFrameWriter

import olist_data_platform.domains.silver.olist.customers as customers_module
import olist_data_platform.domains.silver.olist.orders as orders_module
from olist_data_platform.platform.quality import DataQualityRejectedError


class _QualityEvidenceWriter:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def write(self, report) -> None:
        self.events.append(f"quality:{report.outcome.value}")


class _Lifecycle:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def ensure(self) -> None:
        self.events.append("lifecycle")


def _customers(spark, *, unique_id="person-1"):
    return spark.createDataFrame(
        [
            (
                "customer-1",
                unique_id,
                "01234",
                "sao paulo",
                "SP",
                "customers.csv",
                datetime(2026, 9, 9, 8, 0),
            )
        ],
        (
            "customer_id string, customer_unique_id string, "
            "customer_zip_code_prefix string, customer_city string, "
            "customer_state string, source_file string, ingestion_timestamp timestamp"
        ),
    )


def _orders(spark, *, customer_id="customer-1"):
    return spark.createDataFrame(
        [
            (
                "order-1",
                customer_id,
                "delivered",
                "2026-09-09 08:00:00",
                "2026-09-09 08:01:00",
                "2026-09-09 08:02:00",
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


def _patch_external_writes(monkeypatch, module, events: list[str]) -> None:
    monkeypatch.setattr(
        module,
        "QualityResultWriter",
        lambda spark, target: _QualityEvidenceWriter(events),
    )
    monkeypatch.setattr(
        module,
        "DeltaTableLifecycle",
        lambda spark, target, contract: _Lifecycle(events),
    )

    def _save_as_table(self, target_table):
        events.append(f"target:{target_table}")

    monkeypatch.setattr(DataFrameWriter, "saveAsTable", _save_as_table)


def test_customers_blocking_dq_preserves_target(monkeypatch, spark):
    events: list[str] = []
    _patch_external_writes(monkeypatch, customers_module, events)

    with pytest.raises(DataQualityRejectedError):
        customers_module.process_customers_snapshot(
            spark=spark,
            bronze=_customers(spark, unique_id=None),
            target_table="dev.silver.olist_customers",
            quality_results_table="dev.quality.results",
            run_id="customers-fail",
            evaluation_scope="{}",
        )

    assert events == ["quality:FAILED"]


def test_customers_success_writes_only_after_quality(monkeypatch, spark):
    events: list[str] = []
    _patch_external_writes(monkeypatch, customers_module, events)

    customers_module.process_customers_snapshot(
        spark=spark,
        bronze=_customers(spark),
        target_table="dev.silver.olist_customers",
        quality_results_table="dev.quality.results",
        run_id="customers-pass",
        evaluation_scope="{}",
    )

    assert events == [
        "quality:PASSED",
        "lifecycle",
        "target:dev.silver.olist_customers",
    ]


def test_orders_orphan_preserves_target(monkeypatch, spark):
    events: list[str] = []
    _patch_external_writes(monkeypatch, orders_module, events)

    with pytest.raises(DataQualityRejectedError):
        orders_module.process_orders_snapshot(
            spark=spark,
            bronze=_orders(spark, customer_id="orphan"),
            customers=customers_module.transform_customers(_customers(spark)),
            target_table="dev.silver.olist_orders",
            quality_results_table="dev.quality.results",
            run_id="orders-fail",
            evaluation_scope="{}",
        )

    assert events == ["quality:FAILED"]
