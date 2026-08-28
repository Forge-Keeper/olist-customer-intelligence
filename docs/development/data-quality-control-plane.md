# Data Quality + Administrative Control Plane

## 0. Status

- Owner: Project maintainers
- Branch: `feature/data-quality-control-plane`
- Pull request: #36 into `dev`
- Current gate: Done
- Decision status: Architecture accepted; implementation validated through DEV -> STG -> PRD

## 1. Objective

Introduce first-class, reusable Data Quality for the Olist Data Platform while preserving a durable operational history outside the Bronze/Silver/Gold Data Plane. The first vertical slice is IBGE municipality GDP.

### Expected result

A GDP run must have one correlated `run_id`, persist execution state in the administrative Control Plane, evaluate and persist quality-rule results before the protected Bronze write, reject blocking failures without changing Bronze, and write accepted batches without repeating equivalent logical-key scans.

### Non-goals

- quarantine/drop of invalid rows;
- Silver/Gold implementation;
- freshness/SLA alerting or dashboards;
- historical anomaly detection;
- raw application/Spark/CI log storage in Delta;
- migration to Lakeflow Expectations;
- Great Expectations;
- a generic orchestration framework or broad Data Quality DSL.

## 2. Discovery — accepted summary

Existing correctness checks were distributed across `DatasetContract`, `DeltaTableLifecycle`, `BronzeWriter`, source parsers/extractors and validation scripts. They provided fail-fast protection but not stable Data Quality rule identities, severities, structured persisted results or shared execution semantics.

The GDP dataset is a suitable pilot because it already has a stable natural key, bounded reference-year/variable scope, a deployed DAB job and validated source evidence. The observed GDP municipality count is evidence, not a permanent source contract, and is deliberately not used as a hard failure threshold.

External alternatives were considered. Lakeflow Expectations would change the current imperative Python-wheel execution model; Great Expectations adds more framework/configuration surface than the MVP needs; Delta constraints are useful complementary invariants but do not replace warning/info rules, coverage checks or quality-result history.

## 3. Requirements

### P0 functional requirements

- DQ-R01 — reusable mechanics belong under `platform/`; dataset/source semantics remain under `domains/`.
- DQ-R02 — `DataQualityContract` remains separate from `DatasetContract`.
- DQ-R03 — every rule has stable ID, version, description, category and severity.
- DQ-R04 — `ERROR` blocks; `WARNING` and `INFO` do not block.
- DQ-R05 — incoming-batch rules execute before the GDP Bronze write.
- DQ-R06 — a blocking quality failure persists evidence and leaves Bronze unchanged.
- DQ-R07 — mandatory quality-result persistence failure prevents the protected Bronze write.
- DQ-R08 — quality results are structured and correlated to the platform execution.
- DQ-R09 — quality results are persisted as Delta history in the administrative catalog.
- DQ-R10 — retrying the same run/rule/scope does not duplicate quality rows.
- DQ-R11 — equivalent validation is not deliberately re-scanned merely for reporting.
- DQ-R12 — compatible rule metrics share Spark computation where practical.
- DQ-R13 — rule definitions do not contain environment-specific catalog names.
- DQ-R14 — the MVP has no external Data Quality framework dependency.
- DQ-R15 — every pilot execution has a persisted platform `run_id`.
- DQ-R16 — operational metadata is stored in an administrative catalog separate from the Data Plane.
- DQ-R17 — the Control Plane remains isolated by environment.
- DQ-R18 — quality results use the same `run_id` as the execution.
- DQ-R19 — execution status and Data Quality status remain distinct.
- DQ-R20 — mandatory administrative persistence before Bronze is fail-closed.
- DQ-R21 — raw runtime/application logs are outside Control Plane storage.
- DQ-R22 — administrative writes are idempotent by their logical keys.
- DQ-R23 — domain code contains no concrete `dev`/`stg`/`prd` administrative catalog names.

### GDP pilot rules

| Rule | Condition | Severity |
| --- | --- | --- |
| GDP-DQ01 | evaluated scope is non-empty | ERROR |
| GDP-DQ02 | natural-key columns contain no nulls | ERROR |
| GDP-DQ03 | natural key is unique in the evaluated scope | ERROR |
| GDP-DQ04 | `reference_year` belongs to requested periods | ERROR |
| GDP-DQ05 | `variable_code` belongs to approved GDP variables | ERROR |
| GDP-DQ06 | `dt_base` is January 1 of `reference_year` | ERROR |
| GDP-DQ07 | every requested year × variable combination is represented | ERROR |
| GDP-DQ08 | count preserved SIDRA special-value markers | INFO |

## 4. Technical Design

### Data Plane / Control Plane

```text
<data_catalog>                  <admin_catalog>
├── bronze                      ├── operations
├── silver                      │   └── execution_runs
└── gold                        └── quality
                                    └── data_quality_results
```

DAB resolves:

```text
dev  -> data_catalog=dev, admin_catalog=dev_admin
stg  -> data_catalog=stg, admin_catalog=stg_admin
prd  -> data_catalog=prd, admin_catalog=prd_admin
```

Catalog/schema creation is an infrastructure prerequisite. Managed application tables use the existing `DatasetContract` + `DeltaTableLifecycle` foundation.

### Control Plane model

`operations.execution_runs` has one row per logical execution, including source/target context, execution scope, lifecycle/quality status, stage, row metrics and sanitized error information.

Execution status:

```text
RUNNING | SUCCEEDED | REJECTED | FAILED
```

Quality status:

```text
NOT_EVALUATED | PASSED | PASSED_WITH_WARNINGS | FAILED
```

`quality.data_quality_results` has one row per `run_id × dataset × rule_id × rule_version × evaluation_scope` and stores PASS/FAIL plus observed and expected evidence.

### Data Quality components

```text
DataQualityContract
    -> DataQualityRunner
    -> QualityReport / QualityCheckedBatch
    -> QualityResultWriter
    -> BronzeWriter.write_checked()
```

`BronzeWriter.write()` remains the legacy path for non-migrated datasets. `write_checked()` requires matching key-integrity evidence and rejects blocking reports defensively without repeating the legacy key null/duplicate scans.

### GDP flow

```text
start execution run
  -> SIDRA source / extraction
  -> build GDP DataFrame
  -> evaluate DQ
  -> persist quality results
  -> update execution status
  -> blocking ERROR? REJECTED : Bronze write
  -> SUCCEEDED / FAILED
```

Source/parsing failures remain technical ingestion failures. A processable but incomplete year×variable scope is a Data Quality failure so its evidence can be persisted.

### Performance

Compatible row-level metrics are evaluated through a shared aggregate action. Uniqueness uses a grouped aggregate per distinct key set. The GDP pilot therefore avoids the anti-pattern of one full DataFrame action per rule and avoids re-running Bronze logical-key checks after DQ.

## 5. Impact Analysis

### Main code impact

- new `platform/operations` execution model/tracker;
- new Delta repository for execution runs;
- new `platform/quality` models/rules/runner;
- new Delta writer for quality results;
- GDP domain quality contract;
- incremental `BronzeWriter.write_checked()` path;
- GDP service/writer/job composition changes;
- DAB `admin_catalog` parameterization and smoke arguments.

### Data impact

New tables only:

```text
<admin_catalog>.operations.execution_runs
<admin_catalog>.quality.data_quality_results
```

The existing GDP Bronze schema and historical data are not migrated or rewritten.

### Security / governance impact

Runtime access uses environment-scoped workload identities. Shared environments require explicit workload access to their data/admin catalogs. The target model is least privilege with runtime service-principal grants separated from catalog/schema ownership where supported. No sensitivity/PII classifications are invented by this feature.

### Main risks

- regression in the shared `BronzeWriter` — mitigated by an additive API and regression tests;
- duplicate Spark scans — mitigated by grouped evaluation plus checked-batch evidence reuse;
- Control Plane unavailable — protected write deliberately fails closed;
- incomplete cross-catalog status after a late failure — no distributed ACID is claimed; idempotent updates, `run_id`, stage and runtime logs provide recovery evidence;
- Data Quality growing into a generic framework — rule surface remains intentionally small and concrete.

## 6. Implementation Plan / checkpoints

1. Administrative contracts and idempotent Delta persistence.
2. Execution-run lifecycle tracking.
3. Lightweight reusable Data Quality core.
4. GDP rule contract.
5. `BronzeWriter.write_checked()` evidence-reuse path.
6. GDP end-to-end composition and failure semantics.
7. DAB/admin catalog/smoke wiring.
8. ADRs and operator/developer documentation.
9. Full CI and Databricks runtime validation.

All implementation checkpoints are complete for the GDP MVP.

## 7. Validation Evidence

### Repository CI

The final feature branch is validated by the repository gates:

```text
ruff
ty
pytest (237 passed)
deployment smoke contract validation
wheel build
isolated wheel installation
packaged GDP/CEMPRE entry-point checks
authenticated DAB validate dev/stg/prd
mkdocs / Documentation workflow
```

### Real DEV accepted execution

The GDP pilot was executed in DEV for period `2018`.

```text
run_id: 9893929e-8f1e-4e88-8792-8ca956b9b756
execution_status: SUCCEEDED
quality_status: PASSED
quality_rule_count: 8
bronze_2018_rows: 33420
bronze_2018_distinct_keys: 33420
bronze_2018_variable_combinations: 6
```

This proves the same run is represented in the Control Plane and that accepted data reaches `dev.bronze.ibge_municipality_gdp` with the expected 2018 natural-key uniqueness and requested variable coverage.

### Real DEV blocking-write proof

A deliberate duplicate-key batch was evaluated against an isolated temporary Bronze table.

```text
rejected_run_id: dq-runtime-rejected-b6eed530-eda4-44be-8f74-2812bb189099
blocking_rule: GDP-DQ03
blocking_rule_severity: ERROR
blocking_rule_status: FAIL
execution_status: REJECTED
quality_status: FAILED
records_written: 0
bronze_rows_before_rejection: 6
bronze_rows_after_rejection: 6
```

The protected table did not change after the rejection. The temporary runtime-validation job/table/resource files were removed after the proof; the correlated administrative evidence remains as the audit record.

### Shared-environment promotion proof

The same delivery was subsequently promoted through STG and PRD with retained deployment evidence.

```text
approved_stg_workflow_run: 33136649426
prd_workflow_run: 33137618230
main_commit: d12e82f57732b8329fbc1e2ebe39685a36808877
shared_workload_identity: olist-ci
```

For PRD, the workflow verified the approved STG artifact identity/digest, authenticated with the Databricks service principal, validated the PRD bundle, deployed the exact STG-approved wheel, passed production deployment smokes and retained production deployment evidence. The `olist-ci` workload identity was confirmed with the required runtime permissions on `prd` and `prd_admin` for this lab delivery.

The Data Quality Control Plane promotion is therefore validated through DEV -> STG -> PRD. The detailed accepted/rejected behavior proof remains the DEV evidence above; STG/PRD prove shared-environment deployment/runtime promotion.

## 8. Feature Definition of Done

In addition to the repository-wide Definition of Done:

- [x] repository CI is green;
- [x] legacy Bronze writer regression remains green;
- [x] GDP PASS and blocking-failure quality behavior are covered by tests;
- [x] administrative persistence is idempotent by logical key;
- [x] DAB validates all targets with `admin_catalog` resolution;
- [x] real `dev` GDP execution produces correlated execution and quality evidence;
- [x] STG promotion/runtime validation succeeded with retained evidence;
- [x] PRD exact-artifact promotion/runtime validation succeeded with retained evidence;
- [x] ADR-007 and ADR-008 reflect implemented behavior;
- [x] documentation and platform status reflect the delivered capability;
- [x] `/revisar` findings are resolved before merge/promotion.

## 9. Remaining operational boundary

- shared-environment grants required by this delivery are satisfied in the current lab using the confirmed `olist-ci` workload identity;
- least-privilege grant refinement and stronger per-environment workload-identity separation remain target architecture, not an active blocker for the completed Data Quality promotion;
- first-class Data Quality adoption beyond the currently migrated datasets remains future work and must be justified dataset by dataset;
- no deadline is assigned to further Data Quality expansion.
