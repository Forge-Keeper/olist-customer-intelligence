from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import reduce

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from olist_data_platform.platform.quality.model import (
    DataQualityContract,
    QualityCheckedBatch,
    QualityResult,
    QualityStatus,
)
from olist_data_platform.platform.quality.rules import (
    AllowedValuesRule,
    ExpectedCombinationsRule,
    NonEmptyRule,
    NotNullRule,
    ObservedCountRule,
    PredicateRule,
    UniqueRule,
)

_SEPARATOR = "\u001f"


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sum_when(condition: Column) -> Column:
    return F.coalesce(F.sum(F.when(condition, F.lit(1)).otherwise(F.lit(0))), F.lit(0))


class DataQualityRunner:
    """Evaluate small declarative quality contracts with shared Spark aggregates."""

    def evaluate(
        self,
        *,
        dataframe: DataFrame,
        contract: DataQualityContract,
        run_id: str,
        evaluation_scope: str,
        validated_key_columns: tuple[str, ...] = (),
    ) -> QualityCheckedBatch:
        aggregate_expressions: list[Column] = [F.count(F.lit(1)).alias("_row_count")]
        metric_aliases: dict[tuple[str, int], str] = {}

        for index, rule in enumerate(contract.rules):
            alias = f"_rule_{index}"
            identity = (rule.rule_id, rule.version)
            if isinstance(rule, NotNullRule):
                conditions = [F.col(column).isNull() for column in rule.columns]
                aggregate_expressions.append(
                    _sum_when(reduce(lambda left, right: left | right, conditions)).alias(alias)
                )
                metric_aliases[identity] = alias
            elif isinstance(rule, AllowedValuesRule):
                column = F.col(rule.column).cast("string")
                invalid = column.isNull() | (~column.isin(*rule.allowed_values))
                aggregate_expressions.append(_sum_when(invalid).alias(alias))
                metric_aliases[identity] = alias
            elif isinstance(rule, PredicateRule):
                predicate = F.expr(rule.expression)
                invalid = predicate.isNull() | (~predicate)
                aggregate_expressions.append(_sum_when(invalid).alias(alias))
                metric_aliases[identity] = alias
            elif isinstance(rule, ObservedCountRule):
                aggregate_expressions.append(
                    _sum_when(F.expr(rule.expression)).alias(alias)
                )
                metric_aliases[identity] = alias
            elif isinstance(rule, ExpectedCombinationsRule):
                encoded = F.concat_ws(
                    _SEPARATOR,
                    *[
                        F.coalesce(F.col(column).cast("string"), F.lit("<NULL>"))
                        for column in rule.columns
                    ],
                )
                aggregate_expressions.append(F.collect_set(encoded).alias(alias))
                metric_aliases[identity] = alias

        summary = dataframe.agg(*aggregate_expressions).first()
        if summary is None:
            raise RuntimeError("Data Quality aggregate did not return a summary row.")
        row_count = int(summary["_row_count"] or 0)
        evaluated_at = _utcnow()
        results: list[QualityResult] = []

        unique_metrics: dict[tuple[str, ...], tuple[int, int]] = {}
        for rule in contract.rules:
            if isinstance(rule, UniqueRule) and rule.columns not in unique_metrics:
                duplicate_summary = (
                    dataframe.groupBy(*rule.columns)
                    .count()
                    .where(F.col("count") > 1)
                    .agg(
                        F.count(F.lit(1)).alias("duplicate_groups"),
                        F.coalesce(
                            F.sum(F.col("count") - F.lit(1)), F.lit(0)
                        ).alias("duplicate_excess_rows"),
                    )
                    .first()
                )
                unique_metrics[rule.columns] = (
                    int(duplicate_summary["duplicate_groups"] or 0),
                    int(duplicate_summary["duplicate_excess_rows"] or 0),
                )

        for rule in contract.rules:
            status = QualityStatus.PASS
            observed: object
            expected: str
            identity = (rule.rule_id, rule.version)

            if isinstance(rule, NonEmptyRule):
                observed = {"row_count": row_count}
                expected = "row_count > 0"
                status = QualityStatus.PASS if row_count > 0 else QualityStatus.FAIL
            elif isinstance(rule, NotNullRule):
                invalid_count = int(summary[metric_aliases[identity]] or 0)
                observed = {"null_row_count": invalid_count, "columns": rule.columns}
                expected = "configured columns contain no null values"
                status = QualityStatus.PASS if invalid_count == 0 else QualityStatus.FAIL
            elif isinstance(rule, UniqueRule):
                duplicate_groups, excess_rows = unique_metrics[rule.columns]
                observed = {
                    "duplicate_group_count": duplicate_groups,
                    "duplicate_excess_row_count": excess_rows,
                    "columns": rule.columns,
                }
                expected = "configured key columns are unique within the evaluated scope"
                status = QualityStatus.PASS if duplicate_groups == 0 else QualityStatus.FAIL
            elif isinstance(rule, AllowedValuesRule):
                invalid_count = int(summary[metric_aliases[identity]] or 0)
                observed = {
                    "invalid_row_count": invalid_count,
                    "column": rule.column,
                }
                expected = f"{rule.column} belongs to the approved execution values"
                status = QualityStatus.PASS if invalid_count == 0 else QualityStatus.FAIL
            elif isinstance(rule, PredicateRule):
                invalid_count = int(summary[metric_aliases[identity]] or 0)
                observed = {"invalid_row_count": invalid_count}
                expected = rule.expected_condition
                status = QualityStatus.PASS if invalid_count == 0 else QualityStatus.FAIL
            elif isinstance(rule, ExpectedCombinationsRule):
                encoded_values = summary[metric_aliases[identity]] or []
                observed_combinations = {
                    tuple(str(value).split(_SEPARATOR)) for value in encoded_values
                }
                expected_combinations = set(rule.expected_combinations)
                missing = sorted(expected_combinations - observed_combinations)
                observed = {
                    "observed_combination_count": len(observed_combinations),
                    "expected_combination_count": len(expected_combinations),
                    "missing_combinations": missing,
                }
                expected = "all requested dimension combinations are represented"
                status = QualityStatus.PASS if not missing else QualityStatus.FAIL
            elif isinstance(rule, ObservedCountRule):
                observed = {"observed_row_count": int(summary[metric_aliases[identity]] or 0)}
                expected = rule.expected_condition
            else:
                raise TypeError(f"Unsupported Data Quality rule type: {type(rule).__name__}")

            results.append(
                QualityResult(
                    run_id=run_id,
                    dataset=contract.dataset,
                    layer=contract.layer,
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    category=rule.category,
                    severity=rule.severity,
                    status=status,
                    observed_value=_json(observed),
                    expected_condition=expected,
                    evaluation_scope=evaluation_scope,
                    evaluated_at=evaluated_at,
                )
            )

        from olist_data_platform.platform.quality.model import QualityReport

        report = QualityReport(
            run_id=run_id,
            dataset=contract.dataset,
            layer=contract.layer,
            evaluation_scope=evaluation_scope,
            row_count=row_count,
            results=tuple(results),
        )
        return QualityCheckedBatch(
            dataframe=dataframe,
            report=report,
            validated_key_columns=validated_key_columns,
        )
