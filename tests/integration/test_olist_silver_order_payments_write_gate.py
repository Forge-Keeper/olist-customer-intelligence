from datetime import datetime

import pytest
from pyspark.sql.readwriter import DataFrameWriter

import olist_data_platform.domains.silver.olist.order_payments as payments_module
from olist_data_platform.platform.delta.silver import (
    snapshot_writer as snapshot_writer_module,
)
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


def _patch_external_writes(monkeypatch, events: list[str]) -> None:
    monkeypatch.setattr(
        snapshot_writer_module,
        "QualityResultWriter",
        lambda spark, target: _QualityEvidenceWriter(events),
    )
    monkeypatch.setattr(
        snapshot_writer_module,
        "DeltaTableLifecycle",
        lambda spark, target, contract: _Lifecycle(events),
    )

    def _save_as_table(self, target_table):
        events.append(f"target:{target_table}")

    monkeypatch.setattr(DataFrameWriter, "saveAsTable", _save_as_table)


def _bronze(spark, *, payment_value="58.90"):
    return spark.createDataFrame(
        [
            (
                "order-1",
                "1",
                "credit_card",
                "1",
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


def _orders(spark, order_id="order-1"):
    return spark.createDataFrame([(order_id,)], "order_id string")


def test_order_payments_orphan_persists_dq_and_preserves_target(
    monkeypatch,
    spark,
):
    events: list[str] = []
    _patch_external_writes(monkeypatch, events)

    with pytest.raises(DataQualityRejectedError):
        payments_module.process_order_payments_snapshot(
            spark=spark,
            bronze=_bronze(spark),
            orders=_orders(spark, "other-order"),
            target_table="dev.silver.olist_order_payments",
            quality_results_table="dev_admin.quality.data_quality_results",
            run_id="run-orphan",
            evaluation_scope="{}",
        )

    assert events == ["quality:FAILED"]


def test_order_payments_inexact_money_persists_dq_and_preserves_target(
    monkeypatch,
    spark,
):
    events: list[str] = []
    _patch_external_writes(monkeypatch, events)

    with pytest.raises(DataQualityRejectedError):
        payments_module.process_order_payments_snapshot(
            spark=spark,
            bronze=_bronze(spark, payment_value="99.335"),
            orders=_orders(spark),
            target_table="dev.silver.olist_order_payments",
            quality_results_table="dev_admin.quality.data_quality_results",
            run_id="run-inexact-money",
            evaluation_scope="{}",
        )

    assert events == ["quality:FAILED"]


def test_order_payments_success_writes_only_contract_columns(
    monkeypatch,
    spark,
):
    events: list[str] = []
    _patch_external_writes(monkeypatch, events)

    payments_module.process_order_payments_snapshot(
        spark=spark,
        bronze=_bronze(spark),
        orders=_orders(spark),
        target_table="dev.silver.olist_order_payments",
        quality_results_table="dev_admin.quality.data_quality_results",
        run_id="run-success",
        evaluation_scope="{}",
    )

    assert events == [
        "quality:PASSED",
        "lifecycle",
        "target:dev.silver.olist_order_payments",
    ]
    assert "_invalid_typed_cast" not in (
        payments_module.OLIST_ORDER_PAYMENTS_SILVER_CONTRACT.required_columns
    )
    assert "_order_exists" not in (
        payments_module.OLIST_ORDER_PAYMENTS_SILVER_CONTRACT.required_columns
    )
