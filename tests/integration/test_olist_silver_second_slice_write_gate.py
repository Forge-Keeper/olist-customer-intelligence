from datetime import datetime

import pytest
from pyspark.sql.readwriter import DataFrameWriter

import olist_data_platform.domains.silver.olist.order_items as items_module
import olist_data_platform.domains.silver.olist.products as products_module
import olist_data_platform.domains.silver.olist.sellers as sellers_module
from olist_data_platform.domains.silver.olist.category_translation import (
    transform_category_translation,
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


def _translation(spark):
    return spark.createDataFrame(
        [("cat", "category", "translation.csv", datetime(2026, 9, 12))],
        (
            "product_category_name string, product_category_name_english string, "
            "source_file string, ingestion_timestamp timestamp"
        ),
    )


def _products(spark, *, weight="100"):
    return spark.createDataFrame(
        [
            (
                "product-1",
                "cat",
                "10",
                "20",
                "1",
                weight,
                "10",
                "20",
                "30",
                "products.csv",
                datetime(2026, 9, 12),
            )
        ],
        (
            "product_id string, product_category_name string, "
            "product_name_lenght string, product_description_lenght string, "
            "product_photos_qty string, product_weight_g string, "
            "product_length_cm string, product_height_cm string, "
            "product_width_cm string, source_file string, "
            "ingestion_timestamp timestamp"
        ),
    )


def _sellers(spark):
    return spark.createDataFrame(
        [("seller-1", "01234", "city", "SC", "sellers.csv", datetime(2026, 9, 12))],
        (
            "seller_id string, seller_zip_code_prefix string, seller_city string, "
            "seller_state string, source_file string, ingestion_timestamp timestamp"
        ),
    )


def _items(spark, *, seller_id="seller-1"):
    return spark.createDataFrame(
        [
            (
                "order-1",
                "1",
                "product-1",
                seller_id,
                "2026-09-13 00:00:00",
                "10.00",
                "2.00",
                "items.csv",
                datetime(2026, 9, 12),
            )
        ],
        (
            "order_id string, order_item_id string, product_id string, "
            "seller_id string, shipping_limit_date string, price string, "
            "freight_value string, source_file string, ingestion_timestamp timestamp"
        ),
    )


def test_products_blocking_dq_preserves_target(monkeypatch, spark):
    events: list[str] = []
    _patch_external_writes(monkeypatch, products_module, events)

    with pytest.raises(DataQualityRejectedError):
        products_module.process_products_snapshot(
            spark=spark,
            bronze=_products(spark, weight="-1"),
            translations=transform_category_translation(_translation(spark)),
            target_table="dev.silver.olist_products",
            quality_results_table="dev.quality.results",
            run_id="products-fail",
            evaluation_scope="{}",
        )

    assert events == ["quality:FAILED"]


def test_order_items_orphan_preserves_target(monkeypatch, spark):
    events: list[str] = []
    _patch_external_writes(monkeypatch, items_module, events)

    products = products_module.transform_products(
        _products(spark),
        transform_category_translation(_translation(spark)),
    )
    sellers = sellers_module.transform_sellers(_sellers(spark))
    orders = spark.createDataFrame([("order-1",)], "order_id string")

    with pytest.raises(DataQualityRejectedError):
        items_module.process_order_items_snapshot(
            spark=spark,
            bronze=_items(spark, seller_id="missing"),
            orders=orders,
            products=products,
            sellers=sellers,
            target_table="dev.silver.olist_order_items",
            quality_results_table="dev.quality.results",
            run_id="items-fail",
            evaluation_scope="{}",
        )

    assert events == ["quality:FAILED"]
