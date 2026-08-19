from __future__ import annotations

from dataclasses import dataclass


SelectorInput = str | tuple[str, ...] | list[str]


@dataclass(frozen=True)
class SidraQuery:
    """Immutable representation of a SIDRA values query."""

    table_id: int
    territorial_level: int
    territories: tuple[str, ...]
    variables: tuple[str, ...]
    periods: tuple[str, ...]

    def __init__(
        self,
        *,
        table_id: int,
        territorial_level: int,
        territories: SelectorInput,
        variables: SelectorInput,
        periods: SelectorInput,
    ) -> None:
        object.__setattr__(self, "table_id", table_id)
        object.__setattr__(self, "territorial_level", territorial_level)
        object.__setattr__(
            self,
            "territories",
            self._normalize_selector(territories, "territories"),
        )
        object.__setattr__(
            self,
            "variables",
            self._normalize_selector(variables, "variables"),
        )
        object.__setattr__(
            self,
            "periods",
            self._normalize_selector(periods, "periods"),
        )
        self._validate_positive_int(self.table_id, "table_id")
        self._validate_positive_int(
            self.territorial_level,
            "territorial_level",
        )

    @staticmethod
    def _normalize_selector(
        value: SelectorInput,
        field_name: str,
    ) -> tuple[str, ...]:
        if isinstance(value, str):
            items = (value,)
        elif isinstance(value, (tuple, list)):
            items = tuple(value)
        else:
            raise TypeError(
                f"{field_name} must be a string or a sequence of strings."
            )

        if not items:
            raise ValueError(f"{field_name} cannot be empty.")

        normalized: list[str] = []
        for item in items:
            if not isinstance(item, str):
                raise TypeError(
                    f"{field_name} must contain only strings."
                )
            candidate = item.strip()
            if not candidate:
                raise ValueError(
                    f"{field_name} cannot contain empty values."
                )
            normalized.append(candidate)

        return tuple(normalized)

    @staticmethod
    def _validate_positive_int(value: int, field_name: str) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{field_name} must be an integer.")
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
