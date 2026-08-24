from __future__ import annotations

from dataclasses import dataclass

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

from olist_data_platform.platform.delta.contract import ColumnContract, DatasetContract
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


@dataclass(frozen=True)
class TypeMismatch:
    """Observed type drift for one persisted column."""

    column: str
    expected: str
    actual: str


@dataclass(frozen=True)
class SchemaDiff:
    """Structural difference between a DatasetContract and an existing table."""

    missing_columns: tuple[str, ...] = ()
    unexpected_columns: tuple[str, ...] = ()
    type_mismatches: tuple[TypeMismatch, ...] = ()

    @property
    def is_compatible(self) -> bool:
        """Return whether no breaking schema drift is present."""
        return not (
            self.missing_columns
            or self.unexpected_columns
            or self.type_mismatches
        )


@dataclass(frozen=True)
class LayoutDiff:
    """Physical-layout difference between a DatasetContract and a Delta table."""

    expected_clustering_columns: tuple[str, ...] = ()
    actual_clustering_columns: tuple[str, ...] = ()
    expected_partition_columns: tuple[str, ...] = ()
    actual_partition_columns: tuple[str, ...] = ()

    @property
    def is_compatible(self) -> bool:
        """Return whether the persisted physical layout matches the contract."""
        return (
            self.expected_clustering_columns == self.actual_clustering_columns
            and self.expected_partition_columns == self.actual_partition_columns
        )


class DeltaTableLifecycle:
    """Own Delta table existence, contract validation and metadata lifecycle.

    This boundary manages the external Delta/Unity Catalog object state. It does
    not perform domain ingestion or MERGE/FULL_REPLACE write semantics, which
    remain responsibilities of writers and domain services.
    """

    def __init__(
        self,
        spark: SparkSession,
        target_table: str,
        contract: DatasetContract,
    ) -> None:
        if not isinstance(target_table, str):
            raise TypeError("target_table must be a string.")
        if not target_table.strip():
            raise ValueError("target_table cannot be empty.")

        self.spark = spark
        self.target_table = target_table
        self.contract = contract

    def ensure(self) -> None:
        """Create or validate the table and reconcile supported metadata drift."""
        if not self.spark.catalog.tableExists(self.target_table):
            self.create()
            return

        diff = self.inspect_schema()
        if not diff.is_compatible:
            if self._can_apply_additive_evolution(diff):
                self._add_missing_nullable_columns(diff.missing_columns)
                post_evolution = self.inspect_schema()
                if not post_evolution.is_compatible:
                    raise ValueError(self._format_schema_drift(post_evolution))
            else:
                raise ValueError(self._format_schema_drift(diff))

        layout_diff = self.inspect_layout()
        if not layout_diff.is_compatible:
            raise ValueError(self._format_layout_drift(layout_diff))

        self.reconcile_metadata()

    def create(self) -> None:
        """Create an empty Delta table from the authoritative dataset contract."""
        logger.info("delta_table_create_started | target_table=%s", self.target_table)
        dataframe = self.spark.createDataFrame([], self.contract.to_struct_type())
        writer = dataframe.write.format("delta").mode("errorifexists")

        if self.contract.layout.clustering_columns:
            writer = writer.clusterBy(*self.contract.layout.clustering_columns)
        elif self.contract.layout.partition_columns:
            writer = writer.partitionBy(*self.contract.layout.partition_columns)

        writer.saveAsTable(self.target_table)
        self.reconcile_metadata()
        logger.info("delta_table_create_completed | target_table=%s", self.target_table)

    def inspect_schema(self) -> SchemaDiff:
        """Compare the persisted table schema with the declared dataset contract."""
        return self.diff_schema(self.spark.table(self.target_table).schema)

    def diff_schema(self, actual_schema: StructType) -> SchemaDiff:
        """Return structural schema drift without mutating the table."""
        expected = {
            column.name: column for column in self.contract.resolved_columns
        }
        actual = {field.name: field for field in actual_schema.fields}
        missing = tuple(sorted(set(expected) - set(actual)))
        unexpected = tuple(sorted(set(actual) - set(expected)))
        mismatches: list[TypeMismatch] = []
        for name in sorted(set(expected) & set(actual)):
            expected_type = self._canonical_type(expected[name].data_type)
            actual_type = self._canonical_type(
                actual[name].dataType.simpleString()
            )
            if expected_type != actual_type:
                mismatches.append(TypeMismatch(name, expected_type, actual_type))
        return SchemaDiff(missing, unexpected, tuple(mismatches))

    def inspect_layout(self) -> LayoutDiff:
        """Inspect persisted partitioning and liquid-clustering metadata."""
        detail_rows = self.spark.sql(
            f"DESCRIBE DETAIL {self.target_table}"
        ).collect()
        if not detail_rows:
            raise ValueError(
                f"Unable to inspect Delta table layout: {self.target_table}"
            )
        detail = detail_rows[0]
        partition_columns = tuple(
            self._row_value(detail, "partitionColumns") or ()
        )
        clustering_columns = tuple(
            self._row_value(detail, "clusteringColumns") or ()
        )
        return LayoutDiff(
            expected_clustering_columns=self.contract.layout.clustering_columns,
            actual_clustering_columns=clustering_columns,
            expected_partition_columns=self.contract.layout.partition_columns,
            actual_partition_columns=partition_columns,
        )

    def reconcile_metadata(self) -> None:
        """Apply declared table/column comments and tag assignments."""
        description = self._sql_literal(self.contract.metadata.description)
        self.spark.sql(
            f"COMMENT ON TABLE {self.target_table} IS {description}"
        )
        for column in self.contract.resolved_columns:
            column_name = self._quoted_identifier(column.name)
            column_description = self._sql_literal(column.description)
            self.spark.sql(
                f"ALTER TABLE {self.target_table} ALTER COLUMN {column_name} "
                f"COMMENT {column_description}"
            )
        if self.contract.metadata.tags:
            formatted_tags = self._format_tags(self.contract.metadata.tags)
            self.spark.sql(
                f"ALTER TABLE {self.target_table} SET TAGS ({formatted_tags})"
            )
        for column in self.contract.resolved_columns:
            if column.tags:
                column_name = self._quoted_identifier(column.name)
                formatted_tags = self._format_tags(column.tags)
                self.spark.sql(
                    f"ALTER TABLE {self.target_table} ALTER COLUMN {column_name} "
                    f"SET TAGS ({formatted_tags})"
                )

    def _can_apply_additive_evolution(self, diff: SchemaDiff) -> bool:
        if not self.contract.schema_evolution.can_add_nullable_columns:
            return False
        if (
            diff.unexpected_columns
            or diff.type_mismatches
            or not diff.missing_columns
        ):
            return False
        columns = self._columns_by_name()
        return all(columns[name].nullable for name in diff.missing_columns)

    def _add_missing_nullable_columns(self, column_names: tuple[str, ...]) -> None:
        columns = self._columns_by_name()
        for name in column_names:
            column = columns[name]
            logger.info(
                "delta_schema_evolution_add_column | target_table=%s | column=%s",
                self.target_table,
                name,
            )
            self.spark.sql(
                f"ALTER TABLE {self.target_table} ADD COLUMNS ("
                f"{self._quoted_identifier(column.name)} {column.data_type} "
                f"COMMENT {self._sql_literal(column.description)})"
            )

    def _columns_by_name(self) -> dict[str, ColumnContract]:
        return {
            column.name: column for column in self.contract.resolved_columns
        }

    @staticmethod
    def _row_value(row, key: str):
        try:
            return row[key]
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _canonical_type(data_type: str) -> str:
        normalized = data_type.strip().lower()
        aliases = {
            "integer": "int",
            "long": "bigint",
            "bool": "boolean",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _quoted_identifier(identifier: str) -> str:
        return f"`{identifier.replace('`', '``')}`"

    @staticmethod
    def _sql_literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    @classmethod
    def _format_tags(cls, tags) -> str:
        return ", ".join(
            f"{cls._sql_literal(key)} = {cls._sql_literal(value)}"
            for key, value in sorted(tags.items())
        )

    @staticmethod
    def _format_schema_drift(diff: SchemaDiff) -> str:
        mismatch_text = [
            f"{item.column}:{item.actual}->{item.expected}"
            for item in diff.type_mismatches
        ]
        return (
            "Delta table schema is incompatible with DatasetContract: "
            f"missing_columns={list(diff.missing_columns)}, "
            f"unexpected_columns={list(diff.unexpected_columns)}, "
            f"type_mismatches={mismatch_text}"
        )

    @staticmethod
    def _format_layout_drift(diff: LayoutDiff) -> str:
        return (
            "Delta table layout is incompatible with DatasetContract: "
            f"clustering={list(diff.actual_clustering_columns)}->"
            f"{list(diff.expected_clustering_columns)}, "
            f"partitioning={list(diff.actual_partition_columns)}->"
            f"{list(diff.expected_partition_columns)}"
        )
