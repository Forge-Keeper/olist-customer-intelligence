from __future__ import annotations

from dataclasses import dataclass

from olist_data_platform.domains.ingestion.ibge.sidra_query import (
    SelectorInput,
    SidraQuery,
)


@dataclass(frozen=True)
class SidraDataset:
    """Logical SIDRA dataset configuration used by ingestion jobs."""

    name: str
    table_id: int
    territorial_level: int
    variables: tuple[str, ...]
    description: str = ""
    default_periods: tuple[str, ...] = ("last 1",)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")
        if not self.name.strip():
            raise ValueError("name cannot be empty.")
        SidraQuery._validate_positive_int(self.table_id, "table_id")
        SidraQuery._validate_positive_int(
            self.territorial_level,
            "territorial_level",
        )
        normalized_variables = SidraQuery._normalize_selector(
            self.variables,
            "variables",
        )
        normalized_periods = SidraQuery._normalize_selector(
            self.default_periods,
            "default_periods",
        )
        object.__setattr__(self, "variables", normalized_variables)
        object.__setattr__(self, "default_periods", normalized_periods)

    def build_query(
        self,
        *,
        territories: SelectorInput = "all",
        periods: SelectorInput | None = None,
        variables: SelectorInput | None = None,
    ) -> SidraQuery:
        return SidraQuery(
            table_id=self.table_id,
            territorial_level=self.territorial_level,
            territories=territories,
            variables=self.variables if variables is None else variables,
            periods=self.default_periods if periods is None else periods,
        )
