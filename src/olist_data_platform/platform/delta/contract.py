from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import cast

from pyspark.sql.types import StructField, StructType

from olist_data_platform.platform.delta.bronze.config import WriteStrategy


def _freeze_tags(tags: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(tags, Mapping):
        raise TypeError("tags must be a mapping of strings to strings.")

    normalized: dict[str, str] = {}
    for key, value in tags.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("tag keys and values must be strings.")
        if not key.strip():
            raise ValueError("tag keys cannot be empty.")
        if not value.strip():
            raise ValueError("tag values cannot be empty.")
        normalized[key] = value

    return MappingProxyType(normalized)


def _parse_single_field(name: str, data_type: str) -> StructField:
    parsed = cast(StructType, StructType.fromDDL(f"{name} {data_type}"))
    if len(parsed.fields) != 1:
        raise ValueError(f"Unable to parse data type for column {name!r}.")
    return parsed.fields[0]


@dataclass(frozen=True)
class ColumnContract:
    """Declarative persisted-column contract."""

    name: str
    data_type: str
    nullable: bool
    description: str
    tags: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("column name must be a string.")
        if not self.name.strip():
            raise ValueError("column name cannot be empty.")
        if not isinstance(self.data_type, str):
            raise TypeError("data_type must be a Spark DDL string.")
        if not self.data_type.strip():
            raise ValueError("data_type cannot be empty.")
        if not isinstance(self.nullable, bool):
            raise TypeError("nullable must be a bool.")
        if not isinstance(self.description, str):
            raise TypeError("description must be a string.")
        if not self.description.strip():
            raise ValueError("column description cannot be empty.")

        try:
            _parse_single_field(self.name, self.data_type)
        except Exception as exc:  # noqa: BLE001 - normalize Spark parser failures
            raise ValueError(
                f"Invalid Spark DDL type for column {self.name!r}: {self.data_type!r}."
            ) from exc

        object.__setattr__(self, "tags", _freeze_tags(self.tags))

    def to_struct_field(self) -> StructField:
        """Convert the contract into a Spark StructField."""
        parsed_field = _parse_single_field(self.name, self.data_type)
        return StructField(
            self.name,
            parsed_field.dataType,
            self.nullable,
            {"comment": self.description},
        )


@dataclass(frozen=True)
class TableLayout:
    """Physical Delta layout contract."""

    clustering_columns: tuple[str, ...] = ()
    partition_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self._validate_columns("clustering_columns", self.clustering_columns)
        self._validate_columns("partition_columns", self.partition_columns)

        conflicts = set(self.clustering_columns) & set(self.partition_columns)
        if conflicts:
            raise ValueError(
                "A column cannot be both clustered and partitioned: "
                f"{sorted(conflicts)}"
            )

    @staticmethod
    def _validate_columns(field_name: str, columns: tuple[str, ...]) -> None:
        if not isinstance(columns, tuple):
            raise TypeError(f"{field_name} must be a tuple of strings.")
        if not all(isinstance(column, str) for column in columns):
            raise TypeError(f"{field_name} must contain only strings.")
        if any(not column.strip() for column in columns):
            raise ValueError(f"{field_name} cannot contain empty column names.")
        if len(columns) != len(set(columns)):
            raise ValueError(f"{field_name} cannot contain duplicate columns.")


@dataclass(frozen=True)
class TableMetadata:
    """Unity Catalog table metadata intended by a dataset contract."""

    description: str
    tags: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.description, str):
            raise TypeError("table description must be a string.")
        if not self.description.strip():
            raise ValueError("table description cannot be empty.")
        object.__setattr__(self, "tags", _freeze_tags(self.tags))


@dataclass(frozen=True)
class SchemaEvolutionPolicy:
    """Explicit allow-list for automatic schema evolution."""

    enabled: bool = False
    allow_add_nullable_columns: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool.")
        if not isinstance(self.allow_add_nullable_columns, bool):
            raise TypeError("allow_add_nullable_columns must be a bool.")

    @property
    def can_add_nullable_columns(self) -> bool:
        return self.enabled and self.allow_add_nullable_columns


BRONZE_INGESTION_TIMESTAMP = ColumnContract(
    name="ingestion_timestamp",
    data_type="timestamp",
    nullable=False,
    description="Timestamp at which the row was persisted by the ingestion platform.",
    tags={"managed_by": "olist_data_platform"},
)


@dataclass(frozen=True)
class DatasetContract:
    """Executable persisted-table contract for a managed dataset."""

    columns: tuple[ColumnContract, ...]
    key_columns: tuple[str, ...]
    write_strategy: WriteStrategy = WriteStrategy.MERGE
    layout: TableLayout = field(default_factory=TableLayout)
    metadata: TableMetadata = field(
        default_factory=lambda: TableMetadata(description="Managed Delta dataset.")
    )
    managed_columns: tuple[ColumnContract, ...] = ()
    schema_evolution: SchemaEvolutionPolicy = field(
        default_factory=SchemaEvolutionPolicy
    )

    def __post_init__(self) -> None:
        self._validate_column_contracts("columns", self.columns, allow_empty=False)
        self._validate_column_contracts(
            "managed_columns", self.managed_columns, allow_empty=True
        )
        self._validate_names("key_columns", self.key_columns, allow_empty=False)

        resolved_names = tuple(column.name for column in self.resolved_columns)
        if len(resolved_names) != len(set(resolved_names)):
            raise ValueError(
                "Dataset and managed columns cannot contain duplicate column names."
            )

        missing_keys = set(self.key_columns) - set(resolved_names)
        if missing_keys:
            raise ValueError(
                "key_columns must be included in resolved columns: "
                f"{sorted(missing_keys)}"
            )

        layout_columns = (
            self.layout.clustering_columns + self.layout.partition_columns
        )
        missing_layout = set(layout_columns) - set(resolved_names)
        if missing_layout:
            raise ValueError(
                "layout columns must be included in resolved columns: "
                f"{sorted(missing_layout)}"
            )

        if not isinstance(self.write_strategy, WriteStrategy):
            raise TypeError("write_strategy must be a WriteStrategy.")
        if not isinstance(self.layout, TableLayout):
            raise TypeError("layout must be a TableLayout.")
        if not isinstance(self.metadata, TableMetadata):
            raise TypeError("metadata must be a TableMetadata.")
        if not isinstance(self.schema_evolution, SchemaEvolutionPolicy):
            raise TypeError("schema_evolution must be a SchemaEvolutionPolicy.")

    @property
    def resolved_columns(self) -> tuple[ColumnContract, ...]:
        return self.columns + self.managed_columns

    @property
    def required_columns(self) -> tuple[str, ...]:
        """Names required in the final persisted dataframe."""
        return tuple(column.name for column in self.resolved_columns)

    @property
    def primary_key_columns(self) -> tuple[str, ...]:
        """Compatibility alias while BronzeWriter migrates to key_columns."""
        return self.key_columns

    @property
    def clustering_columns(self) -> tuple[str, ...]:
        return self.layout.clustering_columns

    @property
    def partition_columns(self) -> tuple[str, ...]:
        return self.layout.partition_columns

    def to_struct_type(self) -> StructType:
        """Return the authoritative Spark schema for the persisted table."""
        fields = [column.to_struct_field() for column in self.resolved_columns]
        return StructType(fields)

    @staticmethod
    def _validate_column_contracts(
        field_name: str,
        columns: tuple[ColumnContract, ...],
        *,
        allow_empty: bool,
    ) -> None:
        if not isinstance(columns, tuple):
            raise TypeError(f"{field_name} must be a tuple of ColumnContract.")
        if not allow_empty and not columns:
            raise ValueError(f"{field_name} cannot be empty.")
        if not all(isinstance(column, ColumnContract) for column in columns):
            raise TypeError(f"{field_name} must contain only ColumnContract values.")

        names = tuple(column.name for column in columns)
        if len(names) != len(set(names)):
            raise ValueError(f"{field_name} cannot contain duplicate column names.")

    @staticmethod
    def _validate_names(
        field_name: str,
        values: tuple[str, ...],
        *,
        allow_empty: bool,
    ) -> None:
        if not isinstance(values, tuple):
            raise TypeError(f"{field_name} must be a tuple of strings.")
        if not allow_empty and not values:
            raise ValueError(f"{field_name} cannot be empty.")
        if not all(isinstance(value, str) for value in values):
            raise TypeError(f"{field_name} must contain only strings.")
        if any(not value.strip() for value in values):
            raise ValueError(f"{field_name} cannot contain empty values.")
        if len(values) != len(set(values)):
            raise ValueError(f"{field_name} cannot contain duplicate values.")
