from datetime import datetime
from decimal import Decimal

from olist_data_platform.domains.silver.olist.category_translation import (
    OLIST_CATEGORY_TRANSLATION_SILVER_CONTRACT,
    OLIST_CATEGORY_TRANSLATION_SILVER_QUALITY_CONTRACT,
    transform_category_translation,
)
from olist_data_platform.domains.silver.olist.order_items import (
    OLIST_ORDER_ITEMS_SILVER_CONTRACT,
    OLIST_ORDER_ITEMS_SILVER_QUALITY_CONTRACT,
    attach_item_relationships,
    transform_order_items,
)
from olist_data_platform.domains.silver.olist.products import (
    OLIST_PRODUCTS_SILVER_CONTRACT,
    OLIST_PRODUCTS_SILVER_QUALITY_CONTRACT,
    transform_products,
)
from olist_data_platform.domains.silver.olist.sellers import (
    OLIST_SELLERS_SILVER_CONTRACT,
    OLIST_SELLERS_SILVER_QUALITY_CONTRACT,
    transform_sellers,
)
from olist_data_platform.platform.quality import (
    DataQualityRunner,
    QualityOutcome,
    QualityStatus,
)


def _translation_bronze(spark):
    return spark.createDataFrame(
        [("beleza_saude", "health_beauty", "translation.csv", datetime(2026, 9, 12))],
        (
            "product_category_name string, product_category_name_english string, "
            "source_file string, ingestion_timestamp timestamp"
        ),
    )


def _products_bronze(spark, *, category="beleza_saude", weight="100"):
    return spark.createDataFrame(
        [
            (
                "product-1",
                category,
                "10",
                "100",
                "2",
                weight,
                "20",
                "10",
                "15",
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


def _sellers_bronze(spark):
    return spark.createDataFrame(
        [("seller-1", "01234", "sao paulo", "SP", "sellers.csv", datetime(2026, 9, 12))],
        (
            "seller_id string, seller_zip_code_prefix string, seller_city string, "
            "seller_state string, source_file string, ingestion_timestamp timestamp"
        ),
    )


def _order_items_bronze(spark, *, seller_id="seller-1", price="10.50"):
    return spark.createDataFrame(
        [
            (
                "order-1",
                "1",
                "product-1",
                seller_id,
                "2026-09-13 10:00:00",
                price,
                "2.25",
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


def _orders(spark):
    return spark.createDataFrame([("order-1",)], "order_id string")


def test_category_translation_preserves_unique_lookup(spark):
    transformed = transform_category_translation(_translation_bronze(spark))
    report = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_CATEGORY_TRANSLATION_SILVER_QUALITY_CONTRACT,
        run_id="translation",
        evaluation_scope="{}",
    ).report

    assert report.outcome is QualityOutcome.PASSED
    assert OLIST_CATEGORY_TRANSLATION_SILVER_CONTRACT.key_columns == (
        "product_category_name",
    )


def test_products_are_typed_and_translation_is_nullable_warning(spark):
    translations = transform_category_translation(_translation_bronze(spark))
    transformed = transform_products(
        _products_bronze(spark, category="untranslated"),
        translations,
    )
    row = transformed.first()
    assert row is not None
    assert row.product_name_length == 10
    assert row.product_weight_g == Decimal("100.00")
    assert row.product_category_name_english is None

    report = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_PRODUCTS_SILVER_QUALITY_CONTRACT,
        run_id="products",
        evaluation_scope="{}",
    ).report
    status = {result.rule_id: result.status for result in report.results}
    assert report.outcome is QualityOutcome.PASSED_WITH_WARNINGS
    assert status["OLIST-SILVER-PRODUCTS-DQ05"] is QualityStatus.FAIL
    assert OLIST_PRODUCTS_SILVER_CONTRACT.key_columns == ("product_id",)


def test_zero_weight_warns_but_negative_weight_blocks(spark):
    translations = transform_category_translation(_translation_bronze(spark))
    zero = transform_products(_products_bronze(spark, weight="0"), translations)
    zero_report = DataQualityRunner().evaluate(
        dataframe=zero,
        contract=OLIST_PRODUCTS_SILVER_QUALITY_CONTRACT,
        run_id="zero-weight",
        evaluation_scope="{}",
    ).report
    assert zero_report.outcome is QualityOutcome.PASSED_WITH_WARNINGS

    negative = transform_products(
        _products_bronze(spark, weight="-1"),
        translations,
    )
    negative_report = DataQualityRunner().evaluate(
        dataframe=negative,
        contract=OLIST_PRODUCTS_SILVER_QUALITY_CONTRACT,
        run_id="negative-weight",
        evaluation_scope="{}",
    ).report
    assert negative_report.has_blocking_failures


def test_sellers_preserve_zip_as_string(spark):
    transformed = transform_sellers(_sellers_bronze(spark))
    row = transformed.first()
    assert row is not None
    assert row.seller_zip_code_prefix == "01234"
    report = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_SELLERS_SILVER_QUALITY_CONTRACT,
        run_id="sellers",
        evaluation_scope="{}",
    ).report
    assert report.outcome is QualityOutcome.PASSED
    assert OLIST_SELLERS_SILVER_CONTRACT.key_columns == ("seller_id",)


def test_order_items_are_typed_and_relationships_block_orphans(spark):
    products = transform_products(
        _products_bronze(spark),
        transform_category_translation(_translation_bronze(spark)),
    )
    sellers = transform_sellers(_sellers_bronze(spark))
    items = attach_item_relationships(
        transform_order_items(_order_items_bronze(spark)),
        _orders(spark),
        products,
        sellers,
    )
    row = items.first()
    assert row is not None
    assert row.order_item_id == 1
    assert row.price == Decimal("10.50")
    assert row._order_exists is True
    assert row._product_exists is True
    assert row._seller_exists is True

    report = DataQualityRunner().evaluate(
        dataframe=items,
        contract=OLIST_ORDER_ITEMS_SILVER_QUALITY_CONTRACT,
        run_id="items",
        evaluation_scope="{}",
    ).report
    assert report.outcome is QualityOutcome.PASSED
    assert OLIST_ORDER_ITEMS_SILVER_CONTRACT.key_columns == (
        "order_id",
        "order_item_id",
    )

    orphan = attach_item_relationships(
        transform_order_items(_order_items_bronze(spark, seller_id="missing")),
        _orders(spark),
        products,
        sellers,
    )
    orphan_report = DataQualityRunner().evaluate(
        dataframe=orphan,
        contract=OLIST_ORDER_ITEMS_SILVER_QUALITY_CONTRACT,
        run_id="orphan",
        evaluation_scope="{}",
    ).report
    failed = {
        result.rule_id
        for result in orphan_report.results
        if result.status is QualityStatus.FAIL
    }
    assert orphan_report.has_blocking_failures
    assert "OLIST-SILVER-ORDER-ITEMS-DQ06" in failed


def test_negative_price_is_blocking(spark):
    products = transform_products(
        _products_bronze(spark),
        transform_category_translation(_translation_bronze(spark)),
    )
    items = attach_item_relationships(
        transform_order_items(_order_items_bronze(spark, price="-0.01")),
        _orders(spark),
        products,
        transform_sellers(_sellers_bronze(spark)),
    )
    report = DataQualityRunner().evaluate(
        dataframe=items,
        contract=OLIST_ORDER_ITEMS_SILVER_QUALITY_CONTRACT,
        run_id="negative-price",
        evaluation_scope="{}",
    ).report
    assert report.has_blocking_failures
