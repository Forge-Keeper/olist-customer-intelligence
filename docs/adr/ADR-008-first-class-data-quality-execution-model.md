# ADR-008 — First-Class Data Quality Execution Model

- **Status:** Accepted
- **Date:** 2026-08-27
- **Decision owners:** Project maintainers
- **Scope:** Reusable Data Quality evaluation, blocking semantics and persisted evidence

## Context

The platform already validates persisted schemas through `DatasetContract` and `DeltaTableLifecycle`, and `BronzeWriter` performs runtime logical-key checks. Source/domain adapters also contain structural validation. These checks protect correctness but do not form a first-class Data Quality capability: rules have no stable identities/severities, results are not persisted consistently, and equivalent checks can require repeated Spark actions when reporting is added after the fact.

The first concrete consumer is IBGE municipality GDP. The design must provide useful portfolio/production semantics without introducing a large external framework or migrating imperative Python wheel jobs to a different execution model merely to obtain Data Quality features.

## Decision

Implement a small native PySpark Data Quality capability under `platform/quality`.

`DataQualityContract` remains separate from `DatasetContract`:

- `DatasetContract` defines the persisted Delta table contract;
- `DataQualityContract` defines evaluable data-quality rules for one dataset/layer.

Rules carry stable identity, version, category and severity. Initial severities are `ERROR`, `WARNING` and `INFO`; rule evaluation status is independently `PASS` or `FAIL`.

Blocking semantics are:

- failed `ERROR` rules reject the protected write;
- failed `WARNING` rules allow the write and produce a warning outcome;
- `INFO` rules are observational and do not block.

Quality results are persisted before a blocking rejection in `<admin_catalog>.quality.data_quality_results` and reference the same platform `run_id` used by `operations.execution_runs`.

The MVP evaluates pre-write quality on the incoming GDP DataFrame. The runner groups compatible metrics so the implementation does not deliberately perform one full Spark action per rule. Logical-key evidence produced by Data Quality can be consumed through `BronzeWriter.write_checked()` so the GDP path does not repeat legacy null/duplicate scans. Existing `BronzeWriter.write()` remains available and unchanged in semantics for datasets not yet migrated.

The initial reusable rule types are intentionally small: non-empty, not-null, uniqueness, allowed values, predicate validation, expected combinations and observed-count rules. Adding instances of an existing rule type must not require changing the runner's public orchestration contract.

GDP is the pilot. Its initial rules cover non-empty scope, non-null and unique natural key, requested years, approved variable codes, `dt_base` consistency, year×variable coverage, and observation of SIDRA special-value markers. The historically observed municipality count is not promoted to a permanent source invariant.

Quarantine/drop behavior, historical anomaly detection, freshness/SLA alerting, Silver/Gold rules and external Data Quality frameworks are outside the MVP.

## Alternatives considered

### Databricks/Lakeflow Expectations

Not selected for the MVP because the current workloads are imperative Python wheel jobs. Adopting a different pipeline execution model solely for Data Quality would expand the feature beyond its concrete need.

### Great Expectations

Not selected because its Data Context/Data Source/Data Asset/Batch abstractions and dependency/configuration surface are larger than the current use case requires.

### Delta constraints only

Not sufficient because constraints do not provide the required warning/info semantics, structured evaluation history, coverage checks, thresholds or source-observation results.

### Keep only procedural checks in writers/services

Rejected because it preserves duplicated computation and does not provide durable rule identity, severity, audit evidence or reusable execution semantics.

## Consequences

### Positive

- Data Quality becomes an explicit reusable platform capability;
- rejected runs retain queryable evidence explaining the rejection;
- rule outcome and blocking policy remain distinct concepts;
- GDP can reuse key-integrity evidence rather than repeat scans;
- existing Bronze datasets can migrate incrementally rather than through a repository-wide rewrite.

### Negative / cost

- the project owns a small amount of rule-engine code;
- custom rule types require careful boundaries to avoid evolving into a generic framework;
- Data Quality adds Spark work before protected writes;
- result persistence becomes an operational dependency of the protected write path.

### Operational implications

- Data Quality result persistence is fail-closed before the Bronze write;
- rule definitions must be deterministic and environment independent;
- backfill/reprocess scopes must be explicit rather than inferred solely from observed data;
- a rule semantic change requires a version change when historical interpretation would otherwise become ambiguous.

## Implementation constraints

- keep Data Quality and persisted-table contracts separate;
- keep domain-specific semantics under the owning domain and reusable mechanics under `platform/`;
- do not deliberately execute one full DataFrame action per rule when compatible metrics can be grouped;
- do not repeat key null/duplicate scans on the checked GDP write path;
- persist quality results before raising a blocking Data Quality rejection;
- keep legacy `BronzeWriter.write()` behavior available for non-migrated datasets;
- do not hardcode the observed GDP municipality count as an `ERROR` invariant;
- do not add quarantine or a broad rule DSL without a concrete approved use case.

## Validation

The decision is considered correctly implemented when:

1. GDP rules produce structured PASS/FAIL results with stable IDs and severities;
2. a blocking GDP failure persists Data Quality evidence and leaves Bronze unchanged;
3. a passing GDP run persists quality evidence and writes Bronze;
4. `BronzeWriter.write_checked()` reuses matching key evidence without invoking the legacy key scan;
5. legacy `BronzeWriter.write()` regression tests remain green;
6. unit/integration tests cover rule invariants and failure paths.

## Supersession

None.
