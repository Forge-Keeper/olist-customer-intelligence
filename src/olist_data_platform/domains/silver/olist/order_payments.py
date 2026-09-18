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
    ObservedCountRule,
    PredicateRule,
    QualityCategory,
    QualityReport,
    QualitySeverity,
    UniqueRule,
)

_SOURCE_COLUMNS = (
    "order_id",
    "payment_sequential",
    "payment_type",
    "payment_installments",
    "payment_value",
    "source_file",
    "ingestion_timestamp",
)

_PAYMENT_VALUE_EXACT_PATTERN = (
    r"^[+-]?[0-9]{1,16}(?:\.[0-9]{1,2}0*)?$"
)

OLIST_ORDER_PAYMENTS_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract("order_id", "string", False, "Order identifier."),
        ColumnContract(
            "payment_sequential",
            "int",
            False,
            "Payment sequence identifier within the order.",
        ),
        ColumnContract(
            "payment_type",
            "string",
            False,
            "Payment method label preserved from the source snapshot.",
        ),
        ColumnContract(
            "payment_installments",
            "int",
            False,
            "Number of payment installments.",
        ),
        ColumnContract(
            "payment_value",
            "decimal(18,2)",
            False,
            "Payment value represented exactly at cent precision.",
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
    key_columns=("order_id", "payment_sequential"),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Typed Olist order payments at order/payment-sequence grain.",
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_ORDER_PAYMENTS_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_order_payments",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ01",
            version=1,
            description="Required payment fields must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=(
                "order_id",
                "payment_sequential",
                "payment_type",
                "payment_installments",
                "payment_value",
            ),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ02",
            version=1,
            description="Order/payment sequence key must be unique.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("order_id", "payment_sequential"),
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ03",
            version=1,
            description=(
                "Required typed source values must cast without precision loss."
            ),
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="NOT _invalid_typed_cast",
            expected_condition=(
                "integer fields fit INT and payment_value is exactly representable "
                "as DECIMAL(18,2)"
            ),
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ04",
            version=1,
            description="Every payment must reference a Silver order.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression="_order_exists",
            expected_condition="zero Order Payments -> Orders orphans",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ05",
            version=1,
            description="Payment sequence identifiers must be positive.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="payment_sequential > 0",
            expected_condition="payment_sequential is greater than zero",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ06",
            version=1,
            description="Payment installment counts cannot be negative.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="payment_installments >= 0",
            expected_condition="payment_installments is non-negative",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ07",
            version=1,
            description="Payment values cannot be negative.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression="payment_value >= 0",
            expected_condition="payment_value is non-negative",
        ),
        ObservedCountRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ08",
            version=1,
            description="Count Silver rows with zero payment value.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="payment_value = CAST(0 AS DECIMAL(18,2))",
            expected_condition=(
                "observed count only; zero payment values remain source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ09",
            version=1,
            description="Count Silver rows with zero payment installments.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="payment_installments = 0",
            expected_condition=(
                "observed count only; zero installments remain source-faithful"
            ),
        ),
        ObservedCountRule(
            rule_id="OLIST-SILVER-ORDER-PAYMENTS-DQ10",
            version=1,
            description="Count Silver rows whose payment type is not_defined.",
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.INFO,
            expression="payment_type = 'not_defined'",
            expected_condition=(
                "observed count only; not_defined payment types remain source-faithful"
            ),
        ),
    ),
)


def _try_cast(column_name: str, data_type: str):
    return F.expr(f"try_cast(`{column_name}` as {data_type})")


def transform_order_payments(bronze: DataFrame) -> DataFrame:
    missing = sorted(set(_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Order Payments Bronze input is missing required columns: "
            f"{missing}"
        )

    parsed_sequence = _try_cast("payment_sequential", "int")
    parsed_installments = _try_cast("payment_installments", "int")
    parsed_value = _try_cast("payment_value", "decimal(18,2)")
    source_value = F.col("payment_value").cast("string")
    exact_value_shape = source_value.rlike(_PAYMENT_VALUE_EXACT_PATTERN)

    return bronze.select(
        F.col("order_id").cast("string").alias("order_id"),
        parsed_sequence.alias("payment_sequential"),
        F.col("payment_type").cast("string").alias("payment_type"),
        parsed_installments.alias("payment_installments"),
        parsed_value.alias("payment_value"),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
        (
            (F.col("payment_sequential").isNotNull() & parsed_sequence.isNull())
            | (
                F.col("payment_installments").isNotNull()
                & parsed_installments.isNull()
            )
            | (
                source_value.isNotNull()
                & (parsed_value.isNull() | ~exact_value_shape)
            )
        ).alias("_invalid_typed_cast"),
    )


def attach_payment_relationship(
    payments: DataFrame,
    orders: DataFrame,
) -> DataFrame:
    order_keys = (
        orders.select("order_id")
        .dropDuplicates()
        .withColumn("_order_exists", F.lit(True))
    )
    return payments.join(order_keys, on="order_id", how="left").withColumn(
        "_order_exists",
        F.coalesce(F.col("_order_exists"), F.lit(False)),
    )


def process_order_payments_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    orders: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    """Validate and atomically replace the protected Silver snapshot."""
    transformed = attach_payment_relationship(
        transform_order_payments(bronze),
        orders,
    )
    return SilverSnapshotWriter(
        spark,
        target_table,
        OLIST_ORDER_PAYMENTS_SILVER_CONTRACT,
        OLIST_ORDER_PAYMENTS_SILVER_QUALITY_CONTRACT,
        quality_results_table,
        empty_snapshot_message=(
            "Silver Order Payments FULL_REPLACE snapshot cannot be empty; "
            "the existing target was preserved."
        ),
    ).write_checked(
        transformed,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
