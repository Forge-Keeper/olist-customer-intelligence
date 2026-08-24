# DAB + Platform Contracts — Implementation Plan

## Status

**Proposed — Implementation Plan gate.**

This plan implements the approved Requirements and the selected Technical Design direction. It does not itself authorize code changes until reviewed/approved.

## Approved scope decisions

- DAB targets: `dev`, `stg`, `prd`.
- First DAB pilot: `ibge_municipality_gdp_ingestion`.
- Promotion path: feature/PR -> `dev` -> `stg` -> protected `prd`.
- Wheel artifact; same commit/artifact promoted from staging to production.
- Serverless jobs compute is the preferred pilot compute, subject to workspace prerequisites.
- Executable `DatasetContract` becomes the single current Bronze contract model.
- **Option A:** migrate all current Bronze dataset declarations in this feature; only GDP is migrated to DAB.
- `DeltaTableLifecycle` owns table lifecycle/state; `BronzeWriter` owns write semantics.
- Schema drift fails by default; only explicitly enabled, supported evolution is automatic.
- Initial automatic evolution: additive nullable columns only.
- Table and column governance tags are first-class contract metadata.
- Future Gold fine-grained governance uses Unity Catalog/ABAC row filters and column masks; literal per-row metadata tags are not introduced.
- No YAML generator, dependency inference, generalized ABAC engine or full SAFRA parity.

## Execution strategy

Implement from the lowest-level contract primitives outward. Keep every checkpoint independently testable so a regression can be isolated before DAB deployment work begins.

---

## Phase 1 — Executable contract foundation

### Changes

Create the generic Delta contract module, initially under:

```text
src/olist_data_platform/platform/delta/contract.py
```

Implement small immutable types for:

- `ColumnContract`;
- `TableLayout`;
- `TableMetadata`;
- `SchemaEvolutionPolicy`;
- `DatasetContract`;
- schema/metadata diff value objects where cohesive.

`ColumnContract` must represent:

```text
name
data_type
nullable
description
tags
```

`TableMetadata` must represent:

```text
description
tags
```

Add the reusable platform-managed Bronze declaration for `ingestion_timestamp` and contract resolution (`columns + managed_columns`).

### Invariants

Validate at construction time:

- unique persisted/resolved column names;
- valid/non-empty names/descriptions;
- parsable Spark DDL type;
- key columns exist;
- layout columns exist;
- clustering/partition conflicts do not exist;
- tag keys/values are valid and non-empty;
- managed columns cannot be redeclared by a dataset;
- evolution policy values are internally valid.

### Tests first/alongside

Create/update:

```text
tests/unit/platform/delta/test_contract.py
```

Cover success/failure cases for all invariants, Spark schema generation/parsing, managed columns, table tags and column tags.

### Checkpoint 1 — definition of done

- contract unit tests green;
- no production writer behavior changed yet;
- Ruff/type gates green.

---

## Phase 2 — Migrate all current Bronze contracts (Option A)

### Changes

Convert every current `BronzeDatasetConfig` declaration to `DatasetContract` across:

```text
domains/bronze/ibge/
domains/bronze/weather/
domains/bronze/olist/
```

Preserve exactly the existing:

- logical keys;
- write strategy;
- clustering/partitioning;
- persisted column semantics.

Add explicit type/nullability/description metadata using existing source/code truth only.

Add table tags only when justified. Minimum durable platform taxonomy may include:

```text
layer
domain
source_system
```

Do not infer PII/sensitivity/classification.

Column tag capability must be present, but individual datasets only receive column tags when there is a real governance fact to represent.

Retire `BronzeDatasetConfig` as a dataset declaration model once all callers are migrated. Retain/move `WriteStrategy` to the most cohesive platform module.

### Tests

Update all dataset config tests and generic contract tests.

### Checkpoint 2

- no `BronzeDatasetConfig` dataset declaration remains;
- all existing Bronze contract tests green;
- full unit suite green before touching table lifecycle.

---

## Phase 3 — Delta table lifecycle

### Changes

Create:

```text
src/olist_data_platform/platform/delta/lifecycle.py
```

Implement a small `DeltaTableLifecycle` with explicit responsibilities:

- table existence/inspection;
- create/ensure empty Delta table;
- physical layout application/validation;
- schema diff;
- fail-fast compatibility validation;
- controlled schema evolution;
- table description reconciliation;
- column comment reconciliation;
- table tag reconciliation;
- column tag reconciliation;
- structured lifecycle logging.

### Schema diff

At minimum classify:

```text
missing_columns
unexpected_columns
type_mismatches
layout_mismatch
```

Metadata/tag drift is separate from breaking schema drift.

### Evolution v1

Only:

```text
contract adds nullable column
AND schema_evolution.enabled == true
=> ALTER TABLE ADD COLUMN
```

Everything else remains explicit failure/migration.

### Governance implementation

Implement table/column tag materialization using the Databricks/Unity Catalog mechanism available in the workspace/runtime.

The contract represents tag assignments. Account-level governed-tag taxonomy creation and ownership are external governance prerequisites unless required to unblock a demonstrated pilot tag.

Do not implement row filters or column masks in this phase; preserve the documented extension boundary for Gold.

### Tests

Create:

```text
tests/unit/platform/delta/test_lifecycle.py
```

and integration tests where local Spark/Delta allows.

Cover:

- creation;
- compatible existing table;
- each drift category;
- evolution disabled;
- nullable additive evolution enabled;
- unsupported evolution failures;
- table metadata reconciliation;
- table tags;
- column tags;
- structured logs/observable evolution.

### Checkpoint 3

- lifecycle unit/integration tests green;
- no writes silently mutate unsupported schema;
- governance metadata reconciliation is independently testable.

---

## Phase 4 — BronzeWriter integration

### Changes

Refactor:

```text
src/olist_data_platform/platform/delta/bronze/writer.py
```

Target responsibility split:

```text
DatasetContract
    schema + metadata + governance intent

DeltaTableLifecycle
    create / inspect / validate / evolve / reconcile

BronzeWriter
    prepare / managed values / batch validation / write semantics
```

Remove `_create_table()` from `BronzeWriter`.

Flow:

1. validate incoming dataset fields;
2. add `ingestion_timestamp`;
3. validate logical key values/duplicates;
4. call lifecycle `ensure/validate` using prepared schema;
5. perform MERGE/FULL_REPLACE/replaceWhere.

Preserve all current safeguards and semantics.

### Tests

Update:

```text
tests/unit/platform/delta/bronze/test_writer.py
```

and every domain writer affected by constructor/contract changes.

### Checkpoint 4

Run the **entire unit and integration suite**, not only new tests.

Must prove:

- existing MERGE behavior;
- idempotency;
- FULL_REPLACE protection;
- replaceWhere behavior;
- no source/domain behavior changed accidentally.

---

## Phase 5 — GDP contract validation and workspace lifecycle smoke

### Changes

Finalize GDP contract as the reference example for:

- explicit persisted schema;
- platform-managed timestamp;
- key columns;
- clustering;
- table description;
- table tags;
- supported column-tag declaration capability;
- schema evolution disabled by default.

Keep transient `payload_json` staging behavior only where required before VARIANT conversion.

### Workspace smoke before DAB

Against `dev` only:

- create/ensure GDP table through lifecycle;
- validate schema/layout;
- inspect comments/tags;
- run ingestion twice and prove idempotency;
- intentionally demonstrate contract drift failure in a disposable test object or controlled test path;
- demonstrate opt-in additive nullable evolution without making production GDP permissive.

### Checkpoint 5

Platform contract/lifecycle behavior is proven in the actual Databricks environment before adding deployment automation.

---

## Phase 6 — Wheel packaging

### Changes

Update `pyproject.toml` with a deterministic GDP wheel entry point.

Choose **one** build mechanism for local + CI, for example `uv build` or `python -m build --wheel`; do not maintain two competing build paths.

Validate locally:

```text
build wheel
inspect artifact
install/import entry point
execute parser/help path
```

### Checkpoint 6

A reproducible wheel exists and GDP entry point resolves correctly.

---

## Phase 7 — DAB dev target and GDP pilot

### Changes

Create:

```text
databricks.yml
resources/jobs/ibge_municipality_gdp.job.yml
```

Configure variables for catalog/schema/table resolution.

Targets:

```text
dev -> dev.bronze.ibge_municipality_gdp
stg -> stg.bronze.ibge_municipality_gdp
prd -> prd.bronze.ibge_municipality_gdp
```

`dev` uses development-mode behavior. GDP job receives the fully qualified target table from DAB rather than deriving environment inside Python.

Use serverless wheel task if prerequisite validation succeeds. If unavailable, stop and approve a compute redesign before continuing.

### Validation

```text
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev <gdp_job_key>
```

Then verify contract/table/data in `dev`.

### Checkpoint 7

End-to-end local/developer path is proven without any `prd` hardcode.

---

## Phase 8 — STG/PRD target validation and promotion configuration

### Changes

Complete shared target configuration:

- `stg` shared root/identity;
- `prd` production mode/protections;
- service principal/run-as setup references;
- `main` branch production guard;
- same artifact identity across promotion.

No secrets committed.

### Validate config before deployment

```text
databricks bundle validate -t stg
databricks bundle validate -t prd
```

### External prerequisites

Confirm before deployment:

- catalogs/schemas exist or creation ownership is explicitly decided;
- serverless availability;
- IBGE outbound access;
- service principals;
- UC write/metadata/tag permissions;
- governed-tag taxonomy/assignments if governed tags are exercised;
- GitHub environment/secrets capability.

### Checkpoint 8

Targets validate and operational prerequisites are known; no production deploy occurs merely because configuration validates.

---

## Phase 9 — CI/CD

Implement professional promotion gates.

### PR

- dependency install;
- Ruff;
- type gate;
- full pytest;
- wheel build;
- bundle validate targets.

### Main -> STG

- build/identify immutable artifact for commit;
- deploy `stg` using staging identity;
- run GDP smoke;
- verify table contract/data/governance metadata.

### STG -> PRD

- require protected/manual approval;
- use same approved commit/artifact;
- deploy `prd` with production identity;
- post-deploy contract verification.

### Checkpoint 9

A failed test, contract validation, staging smoke or approval prevents production promotion.

---

## Phase 10 — Documentation closeout

Before Done, update/accept:

```text
docs/development/dab-platform-*.md
docs/adr/ADR-004-*.md
docs/adr/ADR-005-*.md
```

Add operator/developer instructions for:

- declaring a `DatasetContract`;
- table and column tag assignments;
- contract drift failures;
- controlled schema evolution;
- local wheel build;
- bundle validate/deploy/run;
- dev -> stg -> prd promotion;
- rollback/recovery expectations supported by the implemented pipeline.

Document explicitly that future Gold row-level governance uses row filters/ABAC and future column protection uses governed tags/column masks.

## Commit/checkpoint strategy

Prefer small coherent commits after green checkpoints, conceptually:

1. `feat: add executable delta dataset contracts`
2. `refactor: migrate bronze dataset contracts`
3. `feat: add delta table lifecycle and governance metadata`
4. `refactor: delegate bronze lifecycle from writer`
5. `build: package GDP ingestion as wheel entry point`
6. `feat: add GDP Databricks bundle pilot`
7. `ci: add staging and production promotion flow`
8. `docs: finalize DAB platform architecture and operations`

Exact commits may be combined when changes are inseparable, but no commit should knowingly leave the branch with a broken test suite unless it is an explicitly temporary local step that is not pushed.

## Stop conditions / blockers

Stop and surface a decision instead of improvising if any of these occur:

- serverless jobs unavailable or incompatible;
- required Unity Catalog metadata/tag operation is unsupported by chosen runtime/API;
- existing table state requires a breaking schema migration;
- governed-tag taxonomy/permissions conflict with the proposed contract capability;
- service-principal creation/permissions unavailable;
- DAB wheel deployment requires a materially different packaging model;
- migration of a Bronze config exposes semantics not representable by the accepted `DatasetContract`.

## Final acceptance

The feature is Done only when:

- all current Bronze contracts are migrated;
- all tests/lint/type gates are green;
- `BronzeWriter` no longer owns table creation;
- lifecycle validates/reconciles schema, layout, comments, table tags and column tags;
- schema evolution is fail-fast by default and conservative when enabled;
- GDP runs from the wheel through DAB;
- `dev`, `stg`, `prd` resolve isolated catalogs;
- staging promotion is successful;
- production promotion is protected and uses the same approved artifact;
- documentation/ADRs match implemented behavior;
- no production secret or identity is embedded in source;
- future Gold row-filter/column-mask governance can extend the model without redesigning the contract foundation.
