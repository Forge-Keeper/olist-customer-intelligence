from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WriteStrategy(StrEnum):
    """Supported Bronze persistence strategies."""

    MERGE = "merge"
    REPLACE_WHERE = "replace_where"
    FULL_REPLACE = "full_replace"


@dataclass(frozen=True)
class BronzeDatasetConfig:
    """Declarative contract for a Bronze dataset."""

    primary_key_columns: tuple[str, ...]
    required_columns: tuple[str, ...]
    clustering_columns: tuple[str, ...] = ()
    partition_columns: tuple[str, ...] = ()
    write_strategy: WriteStrategy = WriteStrategy.MERGE

    def __post_init__(self) -> None:
        self._validate_columns(
            "primary_key_columns",
            self.primary_key_columns,
            allow_empty=False,
        )
        self._validate_columns(
            "required_columns",
            self.required_columns,
            allow_empty=False,
        )
        self._validate_columns(
            "clustering_columns",
            self.clustering_columns,
            allow_empty=True,
        )
        self._validate_columns(
            "partition_columns",
            self.partition_columns,
            allow_empty=True,
        )

        missing_required_primary_keys = set(self.primary_key_columns) - set(
            self.required_columns
        )
        if missing_required_primary_keys:
            raise ValueError(
                "primary_key_columns must be included in required_columns: "
                f"{sorted(missing_required_primary_keys)}"
            )

        conflicting_layout_columns = set(self.clustering_columns) & set(
            self.partition_columns
        )
        if conflicting_layout_columns:
            raise ValueError(
                "A column cannot be both clustered and partitioned: "
                f"{sorted(conflicting_layout_columns)}"
            )

        if not isinstance(self.write_strategy, WriteStrategy):
            raise TypeError("write_strategy must be a WriteStrategy.")

    @staticmethod
    def _validate_columns(
        field_name: str,
        columns: tuple[str, ...],
        *,
        allow_empty: bool,
    ) -> None:
        if not isinstance(columns, tuple):
            raise TypeError(f"{field_name} must be a tuple of strings.")

        if not allow_empty and not columns:
            raise ValueError(f"{field_name} cannot be empty.")

        if not all(isinstance(column, str) for column in columns):
            raise TypeError(f"{field_name} must contain only strings.")

        empty_columns = [column for column in columns if not column.strip()]
        if empty_columns:
            raise ValueError(f"{field_name} cannot contain empty column names.")

        if len(columns) != len(set(columns)):
            raise ValueError(f"{field_name} cannot contain duplicate columns.")
