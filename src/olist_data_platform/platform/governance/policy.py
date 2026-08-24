from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GovernancePolicyType(StrEnum):
    """Supported Unity Catalog ABAC policy types."""

    ROW_FILTER = "ROW_FILTER"
    COLUMN_MASK = "COLUMN_MASK"


class GovernancePolicyScope(StrEnum):
    """Supported securable scopes for ABAC policies."""

    CATALOG = "CATALOG"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"


@dataclass(frozen=True)
class GovernancePolicyDefinition:
    """Declarative Unity Catalog ABAC row-filter or column-mask policy.

    The definition contains only SQL-level policy metadata. It references a
    Unity Catalog SQL/UDF function and does not embed arbitrary Python logic.
    """

    name: str
    policy_type: GovernancePolicyType
    scope: GovernancePolicyScope
    scope_name: str
    function_name: str
    principals: tuple[str, ...]
    match_condition: str | None = None
    match_alias: str | None = None
    using_columns: tuple[str, ...] = ()
    description: str | None = None
    except_principals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self._validate_non_empty("name", self.name)
        self._validate_non_empty("scope_name", self.scope_name)
        self._validate_non_empty("function_name", self.function_name)
        self._validate_names("principals", self.principals, allow_empty=False)
        self._validate_names(
            "except_principals", self.except_principals, allow_empty=True
        )
        self._validate_names("using_columns", self.using_columns, allow_empty=True)

        if not isinstance(self.policy_type, GovernancePolicyType):
            raise TypeError("policy_type must be a GovernancePolicyType.")
        if not isinstance(self.scope, GovernancePolicyScope):
            raise TypeError("scope must be a GovernancePolicyScope.")

        if self.match_condition is not None:
            self._validate_non_empty("match_condition", self.match_condition)
        if self.match_alias is not None:
            self._validate_non_empty("match_alias", self.match_alias)
        if self.description is not None:
            self._validate_non_empty("description", self.description)

        if self.policy_type is GovernancePolicyType.COLUMN_MASK:
            if self.match_condition is None or self.match_alias is None:
                raise ValueError(
                    "COLUMN_MASK requires match_condition and match_alias."
                )
        elif self.match_alias is not None and self.match_condition is None:
            raise ValueError("match_alias requires match_condition.")

    @staticmethod
    def _validate_non_empty(field_name: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")
        if not value.strip():
            raise ValueError(f"{field_name} cannot be empty.")

    @classmethod
    def _validate_names(
        cls,
        field_name: str,
        values: tuple[str, ...],
        *,
        allow_empty: bool,
    ) -> None:
        if not isinstance(values, tuple):
            raise TypeError(f"{field_name} must be a tuple of strings.")
        if not allow_empty and not values:
            raise ValueError(f"{field_name} cannot be empty.")
        for value in values:
            cls._validate_non_empty(field_name, value)
        if len(values) != len(set(values)):
            raise ValueError(f"{field_name} cannot contain duplicate values.")
