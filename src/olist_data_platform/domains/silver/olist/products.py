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
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "source_file",
    "ingestion_timestamp",
)

_NUMERIC_SOURCE_COLUMNS = {
    "product_name_lenght": "int",
    "product_description_lenght": "int",
    "product_photos_qty": "int",
    "product_weight_g": "decimal(18,2)",
    "product_length_cm": "decimal(18,2)",
    "product_height_cm": "decimal(18,2)",
    "product_width_cm": "decimal(18,2)",
}

OLIST_PRODUCTS_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract("product_id", "string", False, "Product identifier."),
        ColumnContract(
            "product_category_name",
            "string",
            True,
            "Source product category name.",
        ),
        ColumnContract(
            "product_category_name_english",
            "string",
            True,
            "English category when a translation exists.",
        ),
        ColumnContract("product_name_length", "int", True, "Product name length."),
        ColumnContract(
            "product_description_length",
            "int",
            True,
            "Product description length.",
        ),
        ColumnContract("product_photos_qty", "int", True, "Product photo count."),
        ColumnContract("product_weight_g", "decimal(18,2)", True, "Weight in grams."),
        ColumnContract("product_length_cm", "decimal(18,2)", True, "Length in cm."),
        ColumnContract("product_height_cm", "decimal(18,2)", True, "Height in cm."),
        ColumnContract("product_width_cm", "decimal(18,2)", True, "Width in cm."),
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
    key_columns=("product_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Typed and conformed Olist products at product_id grain.",
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_PRODUCTS_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_products",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-PRODUCTS-DQ01",
            version=1,
            description="product_id must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("product_id",),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-PRODUCTS-DQ02",
            version=1,
            description="product_id must be unique.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("product_id",),
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-PRODUCTS-DQ03",
            version=1,
            description="All non-null typed source attributes must parse.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="NOT _invalid_numeric_cast",
            expected_condition="all non-null typed product attributes are parseable",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-PRODUCTS-DQ04",
            version=1,
            description="Physical product measures cannot be negative.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "(product_weight_g IS NULL OR product_weight_g >= 0) AND "
                "(product_length_cm IS NULL OR product_length_cm >= 0) AND "
                "(product_height_cm IS NULL OR product_height_cm >= 0) AND "
                "(product_width_cm IS NULL OR product_width_cm >= 0)"
            ),
            expected_condition="physical product measures are non-negative",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-PRODUCTS-DQ05",
            version=1,
            description="Observe non-null categories missing an English translation.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.WARNING,
            expression="product_category_name IS NULL OR _translation_exists",
            expected_condition="non-null product categories should have translations",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-PRODUCTS-DQ06",
            version=1,
            description="Observe zero product weight without blocking the snapshot.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.WARNING,
            expression="product_weight_g IS NULL OR product_weight_g <> 0",
            expected_condition="product weight should be greater than zero when present",
        ),
    ),
)


def _try_cast(column_name: str, data_type: str):
    return F.expr(f"try_cast(`{column_name}` as {data_type})")


def transform_products(bronze: DataFrame, translations: DataFrame) -> DataFrame:
    missing = sorted(set(_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Products Bronze input is missing required columns: "
            f"{missing}"
        )

    parsed = {
        name: _try_cast(name, data_type)
        for name, data_type in _NUMERIC_SOURCE_COLUMNS.items()
    }
    transformed = bronze.select(
        F.col("product_id").cast("string").alias("product_id"),
        F.col("product_category_name")
        .cast("string")
        .alias("product_category_name"),
        parsed["product_name_lenght"].alias("product_name_length"),
        parsed["product_description_lenght"].alias(
            "product_description_length"
        ),
        parsed["product_photos_qty"].alias("product_photos_qty"),
        parsed["product_weight_g"].alias("product_weight_g"),
        parsed["product_length_cm"].alias("product_length_cm"),
        parsed["product_height_cm"].alias("product_height_cm"),
        parsed["product_width_cm"].alias("product_width_cm"),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
        F.lit(False).alias("_invalid_numeric_cast"),
    )

    invalid_expression = None
    for source_name, parsed_column in parsed.items():
        condition = F.col(source_name).isNotNull() & parsed_column.isNull()
        invalid_expression = (
            condition
            if invalid_expression is None
            else invalid_expression | condition
        )

    transformed = transformed.drop("_invalid_numeric_cast").withColumn(
        "_invalid_numeric_cast",
        invalid_expression,
    )

    translation_keys = (
        translations.select(
            "product_category_name",
            "product_category_name_english",
        )
        .dropDuplicates(["product_category_name"])
        .withColumn("_translation_exists", F.lit(True))
    )
    return (
        transformed.join(
            translation_keys,
            on="product_category_name",
            how="left",
        )
        .withColumn(
            "_translation_exists",
            F.coalesce(F.col("_translation_exists"), F.lit(False)),
        )
    )


def process_products_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    translations: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    transformed = transform_products(bronze, translations)
    checked = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_PRODUCTS_SILVER_QUALITY_CONTRACT,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
    QualityResultWriter(spark, quality_results_table).write(checked.report)
    checked.report.raise_for_blocking_failures()
    if checked.report.row_count == 0:
        raise ValueError(
            "Silver Products FULL_REPLACE snapshot cannot be empty; "
            "the existing target was preserved."
        )
    DeltaTableLifecycle(
        spark,
        target_table,
        OLIST_PRODUCTS_SILVER_CONTRACT,
    ).ensure()
    (
        checked.dataframe.select(*OLIST_PRODUCTS_SILVER_CONTRACT.required_columns)
        .write.format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
    )
    return checked.report
