from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from olist_data_platform.platform.delta.bronze.config import WriteStrategy
from olist_data_platform.platform.delta.contract import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.silver import SilverSnapshotWriter
from olist_data_platform.platform.quality import (
    DataQualityContract,
    NotNullRule,
    QualityCategory,
    QualityReport,
    QualitySeverity,
    UniqueRule,
)

_SOURCE_COLUMNS = (
    "product_category_name",
    "product_category_name_english",
    "source_file",
    "ingestion_timestamp",
)

OLIST_CATEGORY_TRANSLATION_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract(
            "product_category_name",
            "string",
            False,
            "Source product category name.",
        ),
        ColumnContract(
            "product_category_name_english",
            "string",
            False,
            "English product category name.",
        ),
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
    key_columns=("product_category_name",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Conformed Olist product category translation lookup.",
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_CATEGORY_TRANSLATION_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_product_category_name_translation",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-CATEGORY-TRANSLATION-DQ01",
            version=1,
            description="Category names must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("product_category_name", "product_category_name_english"),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-CATEGORY-TRANSLATION-DQ02",
            version=1,
            description="Source category name must be unique.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("product_category_name",),
        ),
    ),
)


def transform_category_translation(bronze: DataFrame) -> DataFrame:
    missing = sorted(set(_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Category Translation Bronze input is missing required columns: "
            f"{missing}"
        )
    return bronze.select(
        F.col("product_category_name")
        .cast("string")
        .alias("product_category_name"),
        F.col("product_category_name_english")
        .cast("string")
        .alias("product_category_name_english"),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
    )


def process_category_translation_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    """Validate and atomically replace the protected Silver snapshot."""
    transformed = transform_category_translation(bronze)
    return SilverSnapshotWriter(
        spark,
        target_table,
        OLIST_CATEGORY_TRANSLATION_SILVER_CONTRACT,
        OLIST_CATEGORY_TRANSLATION_SILVER_QUALITY_CONTRACT,
        quality_results_table,
        empty_snapshot_message=(
            "Silver Category Translation FULL_REPLACE snapshot cannot be empty; the existing target was preserved."
        ),
    ).write_checked(
        transformed,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
