from __future__ import annotations

from dataclasses import dataclass

from pyspark.sql import SparkSession

from olist_data_platform.platform.governance.policy import (
    GovernancePolicyDefinition,
    GovernancePolicyType,
)
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


@dataclass(frozen=True)
class GovernancePolicyState:
    """Minimal observed state for one policy attached to a securable."""

    exists: bool
    policy_type: str | None = None
    comment: str | None = None


class GovernancePolicyLifecycle:
    """Inspect and reconcile Unity Catalog ABAC policy definitions.

    The lifecycle emits Databricks SQL for ROW FILTER and COLUMN MASK policies.
    Governed-tag taxonomy creation and UDF creation remain separate deployment
    prerequisites and are not hidden inside this boundary.
    """

    def __init__(
        self,
        spark: SparkSession,
        definition: GovernancePolicyDefinition,
    ) -> None:
        self.spark = spark
        self.definition = definition

    def inspect(self) -> GovernancePolicyState:
        """Return minimal direct policy state from the target securable."""
        sql = (
            f"SHOW POLICIES ON {self.definition.scope.value} "
            f"{self.definition.scope_name}"
        )
        rows = self.spark.sql(sql).collect()
        for row in rows:
            name = self._row_value(row, "Policy Name") or self._row_value(
                row, "policy_name"
            )
            if name == self.definition.name:
                return GovernancePolicyState(
                    exists=True,
                    policy_type=self._row_value(row, "Policy Type")
                    or self._row_value(row, "policy_type"),
                    comment=self._row_value(row, "Comment")
                    or self._row_value(row, "comment"),
                )
        return GovernancePolicyState(exists=False)

    def ensure(self) -> None:
        """Create or replace the declared policy and verify its visible type."""
        state = self.inspect()
        if state.exists and state.policy_type not in {
            None,
            self.definition.policy_type.value,
        }:
            raise ValueError(
                "Existing ABAC policy type is incompatible with definition: "
                f"actual={state.policy_type!r}, "
                f"expected={self.definition.policy_type.value!r}."
            )

        logger.info(
            "governance_policy_reconcile_started | policy=%s | scope=%s | target=%s",
            self.definition.name,
            self.definition.scope.value,
            self.definition.scope_name,
        )
        self.spark.sql(self.render_create_or_replace_sql())
        logger.info(
            "governance_policy_reconcile_completed | policy=%s | scope=%s | target=%s",
            self.definition.name,
            self.definition.scope.value,
            self.definition.scope_name,
        )

    def render_create_or_replace_sql(self) -> str:
        """Render supported Databricks CREATE OR REPLACE POLICY SQL."""
        definition = self.definition
        parts = [
            f"CREATE OR REPLACE POLICY {self._quote_identifier(definition.name)}",
            f"ON {definition.scope.value} {definition.scope_name}",
        ]
        if definition.description is not None:
            parts.append(f"COMMENT {self._sql_literal(definition.description)}")

        if definition.policy_type is GovernancePolicyType.ROW_FILTER:
            parts.append(f"ROW FILTER {definition.function_name}")
        else:
            parts.append(f"COLUMN MASK {definition.function_name}")

        parts.append(f"TO {self._format_principals(definition.principals)}")
        if definition.except_principals:
            parts.append(
                "EXCEPT " + self._format_principals(definition.except_principals)
            )
        parts.append("FOR TABLES")

        if definition.match_condition is not None:
            match = f"MATCH COLUMNS {definition.match_condition}"
            if definition.match_alias is not None:
                match += f" AS {self._quote_identifier(definition.match_alias)}"
            parts.append(match)

        if definition.policy_type is GovernancePolicyType.COLUMN_MASK:
            parts.append(
                f"ON COLUMN {self._quote_identifier(definition.match_alias or '')}"
            )

        if definition.using_columns:
            parts.append(
                "USING COLUMNS (" + ", ".join(definition.using_columns) + ")"
            )

        return "\n".join(parts)

    @staticmethod
    def _quote_identifier(value: str) -> str:
        return f"`{value.replace('`', '``')}`"

    @classmethod
    def _format_principals(cls, principals: tuple[str, ...]) -> str:
        return ", ".join(cls._quote_identifier(principal) for principal in principals)

    @staticmethod
    def _sql_literal(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    @staticmethod
    def _row_value(row, key: str):
        try:
            return row[key]
        except (KeyError, TypeError, ValueError):
            return None
