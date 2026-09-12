from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.contract import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle
from olist_data_platform.platform.delta.quality import QualityResultWriter
from olist_data_platform.platform.quality import (
    DataQualityContract,
    DataQualityRunner,
    NotNullRule,
    PredicateRule,
    QualityCategory,
    QualityReport,
    QualitySeverity,
    UniqueRule,
)

_SOURCE_COLUMNS = (
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
    "source_file",
    "ingestion_timestamp",
)

OLIST_ORDER_ITEMS_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract("order_id", "string", False, "Order identifier."),
        ColumnContract("order_item_id", "int", False, "Item sequence within order."),
        ColumnContract("product_id", "string", False, "Product identifier."),
        ColumnContract("seller_id", "string", False, "Seller identifier."),
        ColumnContract(
            "shipping_limit_date",
            "timestamp",
            False,
            "Shipping limit timestamp.",
        ),
        ColumnContract("price", "decimal(18,2)", False, "Item price."),
        ColumnContract("freight_value", "decimal(18,2)", False, "Freight value."),
        ColumnContract(
            "source_file",
            "string",
            True,
            "Source CSV lineage inherited from Bronze.",
        ),
        ColumnContract(
            "bronze_ingestion_timestamp",
            "timestamp",
            True,
            "Bronze ingestion timestamp retained as provenance.",
        ),
        ColumnContract(
            "silver_processed_timestamp",
            "timestamp",
            False,
            "Timestamp when the Silver row was produced.",
        ),
    ),
    key_columns=("order_id", "order_item_id"),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Typed Olist order items at order/item sequence grain.",
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_ORDER_ITEMS_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_order_items",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ01",
            version=1,
            description="Required item fields must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=(
                "order_id",
                "order_item_id",
                "product_id",
                "seller_id",
                "shipping_limit_date",
                "price",
                "freight_value",
            ),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ02",
            version=1,
            description="Order/item sequence key must be unique.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("order_id", "order_item_id"),
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ03",
            version=1,
            description="All non-null typed source fields must parse.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="NOT _invalid_typed_cast",
            expected_condition="all non-null typed item attributes are parseable",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ04",
            version=1,
            description="Every item must reference a Silver order.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression="_order_exists",
            expected_condition="zero Order Items -> Orders orphans",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ05",
            version=1,
            description="Every item must reference a Silver product.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression="_product_exists",
            expected_condition="zero Order Items -> Products orphans",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ06",
            version=1,
            description="Every item must reference a Silver seller.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression="_seller_exists",
            expected_condition="zero Order Items -> Sellers orphans",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-ITEMS-DQ07",
            version=1,
            description="Price and freight cannot be negative.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="price >= 0 AND freight_value >= 0",
            expected_condition="price and freight are non-negative",
        ),
    ),
)


def _try_cast(column_name: str, data_type: str):
    return F.expr(f"try_cast(`{column_name}` as {data_type})")


def transform_order_items(bronze: DataFrame) -> DataFrame:
    missing = sorted(set(_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Order Items Bronze input is missing required columns: "
            f"{missing}"
        )

    parsed_item_id = _try_cast("order_item_id", "int")
    parsed_shipping = _try_cast("shipping_limit_date", "timestamp")
    parsed_price = _try_cast("price", "decimal(18,2)")
    parsed_freight = _try_cast("freight_value", "decimal(18,2)")

    return bronze.select(
        F.col("order_id").cast("string").alias("order_id"),
        parsed_item_id.alias("order_item_id"),
        F.col("product_id").cast("string").alias("product_id"),
        F.col("seller_id").cast("string").alias("seller_id"),
        parsed_shipping.alias("shipping_limit_date"),
        parsed_price.alias("price"),
        parsed_freight.alias("freight_value"),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
        (
            (F.col("order_item_id").isNotNull() & parsed_item_id.isNull())
            | (
                F.col("shipping_limit_date").isNotNull()
                & parsed_shipping.isNull()
            )
            | (F.col("price").isNotNull() & parsed_price.isNull())
            | (F.col("freight_value").isNotNull() & parsed_freight.isNull())
        ).alias("_invalid_typed_cast"),
    )


def attach_item_relationships(
    items: DataFrame,
    orders: DataFrame,
    products: DataFrame,
    sellers: DataFrame,
) -> DataFrame:
    order_keys = (
        orders.select("order_id")
        .dropDuplicates()
        .withColumn("_order_exists", F.lit(True))
    )
    product_keys = (
        products.select("product_id")
        .dropDuplicates()
        .withColumn("_product_exists", F.lit(True))
    )
    seller_keys = (
        sellers.select("seller_id")
        .dropDuplicates()
        .withColumn("_seller_exists", F.lit(True))
    )
    return (
        items.join(order_keys, on="order_id", how="left")
        .join(product_keys, on="product_id", how="left")
        .join(seller_keys, on="seller_id", how="left")
        .withColumn(
            "_order_exists",
            F.coalesce(F.col("_order_exists"), F.lit(False)),
        )
        .withColumn(
            "_product_exists",
            F.coalesce(F.col("_product_exists"), F.lit(False)),
        )
        .withColumn(
            "_seller_exists",
            F.coalesce(F.col("_seller_exists"), F.lit(False)),
        )
    )


def process_order_items_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    orders: DataFrame,
    products: DataFrame,
    sellers: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    transformed = attach_item_relationships(
        transform_order_items(bronze),
        orders,
        products,
        sellers,
    )
    checked = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_ORDER_ITEMS_SILVER_QUALITY_CONTRACT,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
    QualityResultWriter(spark, quality_results_table).write(checked.report)
    checked.report.raise_for_blocking_failures()
    if checked.report.row_count == 0:
        raise ValueError(
            "Silver Order Items FULL_REPLACE snapshot cannot be empty; "
            "the existing target was preserved."
        )
    DeltaTableLifecycle(
        spark,
        target_table,
        OLIST_ORDER_ITEMS_SILVER_CONTRACT,
    ).ensure()
    (
        checked.dataframe.select(*OLIST_ORDER_ITEMS_SILVER_CONTRACT.required_columns)
        .write.format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
    )
    return checked.report
