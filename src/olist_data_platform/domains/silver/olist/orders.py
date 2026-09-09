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

_ORDER_TIMESTAMP_COLUMNS = (
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
)

_ORDER_SOURCE_COLUMNS = (
    "order_id",
    "customer_id",
    "order_status",
    *_ORDER_TIMESTAMP_COLUMNS,
    "source_file",
    "ingestion_timestamp",
)

OLIST_ORDERS_SILVER_CONTRACT = DatasetContract(
    columns=(
        ColumnContract(
            "order_id",
            "string",
            False,
            "Order identifier and Silver grain.",
        ),
        ColumnContract(
            "customer_id",
            "string",
            False,
            "Semantic foreign key to Silver Customers.customer_id.",
        ),
        ColumnContract(
            "order_status",
            "string",
            False,
            "Source order lifecycle status.",
        ),
        ColumnContract(
            "order_purchase_timestamp",
            "timestamp",
            False,
            "Order purchase timestamp.",
        ),
        ColumnContract(
            "order_approved_at",
            "timestamp",
            True,
            "Order approval timestamp when present.",
        ),
        ColumnContract(
            "order_delivered_carrier_date",
            "timestamp",
            True,
            "Carrier handoff timestamp when present.",
        ),
        ColumnContract(
            "order_delivered_customer_date",
            "timestamp",
            True,
            "Customer delivery timestamp when present.",
        ),
        ColumnContract(
            "order_estimated_delivery_date",
            "timestamp",
            False,
            "Source estimated delivery timestamp.",
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
            "Bronze ingestion timestamp retained as Silver provenance.",
        ),
        ColumnContract(
            "silver_processed_timestamp",
            "timestamp",
            False,
            "Timestamp when the row was produced by the Silver transformation.",
        ),
    ),
    key_columns=("order_id",),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description="Typed and validated Olist orders at one row per order_id.",
        tags={"layer": "silver", "source_system": "olist"},
    ),
)

OLIST_ORDERS_SILVER_QUALITY_CONTRACT = DataQualityContract(
    dataset="olist_orders",
    layer="silver",
    rules=(
        NotNullRule(
            rule_id="OLIST-SILVER-ORDERS-DQ01",
            version=1,
            description="order_id must be present.",
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=("order_id",),
        ),
        UniqueRule(
            rule_id="OLIST-SILVER-ORDERS-DQ02",
            version=1,
            description="order_id must remain unique at the Silver grain.",
            category=QualityCategory.UNIQUENESS,
            severity=QualitySeverity.ERROR,
            columns=("order_id",),
        ),
        NotNullRule(
            rule_id="OLIST-SILVER-ORDERS-DQ03",
            version=1,
            description=(
                "Required order relationship, status, purchase and estimated "
                "delivery fields must be present."
            ),
            category=QualityCategory.COMPLETENESS,
            severity=QualitySeverity.ERROR,
            columns=(
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
                "order_estimated_delivery_date",
            ),
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDERS-DQ04",
            version=1,
            description="All non-null Bronze lifecycle timestamps must parse.",
            category=QualityCategory.VALIDITY,
            severity=QualitySeverity.ERROR,
            expression=(
                "NOT (_invalid_purchase_timestamp OR _invalid_approved_at OR "
                "_invalid_carrier_date OR _invalid_customer_delivery_date OR "
                "_invalid_estimated_delivery_date)"
            ),
            expected_condition="all non-null lifecycle timestamp strings are parseable",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDERS-DQ05",
            version=1,
            description="Every Silver order must reference a Silver customer.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression="_customer_exists",
            expected_condition="zero Orders -> Customers orphans",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDERS-DQ06",
            version=1,
            description="Approval cannot precede purchase when approval exists.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression=(
                "order_approved_at IS NULL OR "
                "order_approved_at >= order_purchase_timestamp"
            ),
            expected_condition="approval >= purchase when approval exists",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDERS-DQ07",
            version=1,
            description="Customer delivery cannot precede purchase when present.",
            category=QualityCategory.CONSISTENCY,
            severity=QualitySeverity.ERROR,
            expression=(
                "order_delivered_customer_date IS NULL OR "
                "order_delivered_customer_date >= order_purchase_timestamp"
            ),
            expected_condition="customer delivery >= purchase when delivery exists",
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDERS-DQ08",
            version=1,
            description=(
                "Observe carrier handoff before approval without blocking the batch."
            ),
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.WARNING,
            expression=(
                "order_delivered_carrier_date IS NULL OR order_approved_at IS NULL OR "
                "order_delivered_carrier_date >= order_approved_at"
            ),
            expected_condition=(
                "carrier handoff should not precede approval; observed deviations warn"
            ),
        ),
        PredicateRule(
            rule_id="OLIST-SILVER-ORDERS-DQ09",
            version=1,
            description=(
                "Observe customer delivery before carrier handoff without blocking."
            ),
            category=QualityCategory.OBSERVATION,
            severity=QualitySeverity.WARNING,
            expression=(
                "order_delivered_customer_date IS NULL OR "
                "order_delivered_carrier_date IS NULL OR "
                "order_delivered_customer_date >= order_delivered_carrier_date"
            ),
            expected_condition=(
                "customer delivery should not precede carrier handoff; deviations warn"
            ),
        ),
    ),
)


def _try_timestamp(column_name: str):
    return F.expr(f"try_cast(`{column_name}` as timestamp)")


def transform_orders(bronze: DataFrame) -> DataFrame:
    """Build typed Silver Orders plus temporary DQ conversion evidence."""
    missing = sorted(set(_ORDER_SOURCE_COLUMNS) - set(bronze.columns))
    if missing:
        raise ValueError(
            "Olist Orders Bronze input is missing required columns: "
            f"{missing}"
        )

    parsed = {name: _try_timestamp(name) for name in _ORDER_TIMESTAMP_COLUMNS}
    transformed = bronze.select(
        F.col("order_id").cast("string").alias("order_id"),
        F.col("customer_id").cast("string").alias("customer_id"),
        F.col("order_status").cast("string").alias("order_status"),
        parsed["order_purchase_timestamp"].alias("order_purchase_timestamp"),
        parsed["order_approved_at"].alias("order_approved_at"),
        parsed["order_delivered_carrier_date"].alias(
            "order_delivered_carrier_date"
        ),
        parsed["order_delivered_customer_date"].alias(
            "order_delivered_customer_date"
        ),
        parsed["order_estimated_delivery_date"].alias(
            "order_estimated_delivery_date"
        ),
        F.col("source_file").cast("string").alias("source_file"),
        F.col("ingestion_timestamp")
        .cast("timestamp")
        .alias("bronze_ingestion_timestamp"),
        F.current_timestamp().alias("silver_processed_timestamp"),
        *[
            (
                F.col(name).isNotNull() & parsed[name].isNull()
            ).alias(f"_invalid_{suffix}")
            for name, suffix in (
                ("order_purchase_timestamp", "purchase_timestamp"),
                ("order_approved_at", "approved_at"),
                ("order_delivered_carrier_date", "carrier_date"),
                (
                    "order_delivered_customer_date",
                    "customer_delivery_date",
                ),
                (
                    "order_estimated_delivery_date",
                    "estimated_delivery_date",
                ),
            )
        ],
    )
    return transformed


def attach_customer_relationship(
    orders: DataFrame,
    customers: DataFrame,
) -> DataFrame:
    """Attach temporary referential evidence without changing persisted grain."""
    customer_keys = customers.select("customer_id").dropDuplicates().withColumn(
        "_customer_exists",
        F.lit(True),
    )
    return (
        orders.join(customer_keys, on="customer_id", how="left")
        .withColumn(
            "_customer_exists",
            F.coalesce(F.col("_customer_exists"), F.lit(False)),
        )
    )


def process_orders_snapshot(
    *,
    spark: SparkSession,
    bronze: DataFrame,
    customers: DataFrame,
    target_table: str,
    quality_results_table: str,
    run_id: str,
    evaluation_scope: str,
) -> QualityReport:
    """Validate and atomically replace the Silver Orders snapshot."""
    transformed = attach_customer_relationship(transform_orders(bronze), customers)
    checked = DataQualityRunner().evaluate(
        dataframe=transformed,
        contract=OLIST_ORDERS_SILVER_QUALITY_CONTRACT,
        run_id=run_id,
        evaluation_scope=evaluation_scope,
    )
    QualityResultWriter(spark, quality_results_table).write(checked.report)
    checked.report.raise_for_blocking_failures()

    if checked.report.row_count == 0:
        raise ValueError(
            "Silver Orders FULL_REPLACE snapshot cannot be empty; "
            "the existing target was preserved."
        )

    lifecycle = DeltaTableLifecycle(
        spark,
        target_table,
        OLIST_ORDERS_SILVER_CONTRACT,
    )
    lifecycle.ensure()
    (
        checked.dataframe.select(*OLIST_ORDERS_SILVER_CONTRACT.required_columns)
        .write.format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
    )
    return checked.report
