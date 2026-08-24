# DAB + Platform Contracts — Technical Design

## Status

**Proposed — Technical Design gate.**

This document translates the approved Discovery and Requirements into an implementation design. It does not authorize implementation until reviewed and approved.

## Design goals

The first vertical slice must prove, with `ibge_municipality_gdp_ingestion`, that the project can:

1. build one deployable Python artifact;
2. deploy the same code through `dev -> stg -> prd` without source changes;
3. resolve environment-specific Unity Catalog namespaces through Declarative Automation Bundle targets;
4. use an executable dataset contract as the authoritative table contract;
5. separate Delta table lifecycle from Bronze write semantics;
6. fail on schema drift by default while supporting conservative, explicit schema evolution;
7. keep job/dependency definitions intentionally small and avoid recreating SAFRA's full orchestration framework.

## 1. Deployment architecture

### 1.1 Bundle targets

The bundle will expose exactly three targets:

| Target | Catalog | Deployment behavior | Run identity |
| --- | --- | --- | --- |
| `dev` | `dev` | `mode: development`; default target; personal/iterative deployment | developer identity |
| `stg` | `stg` | staging target with fixed shared bundle root; no development presets | staging service principal |
| `prd` | `prd` | `mode: production`; fixed root; protected production deployment | production service principal |

This follows the Databricks pattern in which development uses `mode: development`, staging has its own shared deployment identity/root, and production uses `mode: production` with a service-principal run identity.

`stg` intentionally does **not** use `mode: development`. It is a shared pre-production validation environment and must not inherit personal resource naming, paused schedules or unlocked deployment behavior intended for developer iteration.

### 1.2 Namespace resolution

Bundle variables provide environment-specific values:

```text
catalog
bronze_schema
```

For the first slice:

```text
dev -> dev.bronze.ibge_municipality_gdp
stg -> stg.bronze.ibge_municipality_gdp
prd -> prd.bronze.ibge_municipality_gdp
```

The target table supplied to the Python job is assembled by bundle configuration. Python/domain code receives only the resolved fully qualified table name and has no `if target == ...` environment logic.

### 1.3 Promotion flow

The professional promotion model is:

```text
feature branch
    |
    v
PR validation
    - unit/integration tests
    - lint/type checks
    - wheel build
    - bundle validate
    |
    v
optional/on-demand dev deploy + run
    |
    v
merge to main
    |
    v
build immutable wheel for commit
    |
    v
automatic stg deployment
    - bundle deploy -t stg
    - pilot smoke/run validation
    - contract/table verification
    |
    v
manual protected approval
    |
    v
prd deployment from the SAME commit/artifact
    - bundle deploy -t prd
    - post-deploy validation
```

`stg` and `prd` must promote the same Git commit and wheel artifact. Production must not rebuild materially different application code after staging acceptance.

### 1.4 Git policy

- feature branches: development and PR validation;
- `main`: promotion source for shared `stg` and `prd` deployments;
- `prd` target specifies `git.branch: main` so production-mode branch validation can reject accidental production deploys from feature branches;
- bypassing production branch validation with `--force` is not part of the normal deployment procedure.

A release-tag flow may be introduced later if release cadence or rollback governance requires it; it is not needed for the first slice.

### 1.5 Deployment identities

- `dev`: current developer identity is acceptable;
- `stg`: dedicated staging service principal;
- `prd`: dedicated production service principal;
- production job execution is decoupled from the individual who deploys the bundle.

Service-principal application IDs, credentials and workspace permission grants are deployment secrets/configuration and must not be committed to source control.

## 2. Bundle structure

Target repository structure:

```text
databricks.yml
resources/
└── jobs/
    └── ibge_municipality_gdp.job.yml
src/
└── olist_data_platform/
    ├── jobs/
    ├── platform/
    └── domains/
```

The root bundle owns:

- bundle name;
- artifact build;
- resource includes;
- common variables;
- target configuration.

The explicit job YAML owns the Databricks job resource. No Python-to-YAML generator is introduced.

## 3. Packaging

### 3.1 Wheel artifact

The existing setuptools project becomes the deployable artifact.

`pyproject.toml` will expose a console/entry point for the GDP job so the DAB job can use a `python_wheel_task` instead of relying on notebook `sys.path` bootstrapping.

Conceptual mapping:

```text
Python distribution: olist-customer-intelligence
entry point: ibge-municipality-gdp-ingestion
function: olist_data_platform.jobs.ibge_municipality_gdp_ingestion:main
```

The bundle artifact build produces a wheel under `dist/` and the job installs/references that artifact.

### 3.2 Artifact immutability

CI must retain or reproducibly identify the wheel built for a commit. `stg` and `prd` promotion must use the artifact corresponding to the same approved commit SHA.

## 4. Compute model

The pilot design chooses **Databricks serverless jobs compute** for the Python wheel task, because Databricks recommends serverless compute for Python wheel jobs and the pilot requires ordinary Spark/Delta/Unity Catalog access plus outbound HTTP to IBGE.

The resource therefore uses a serverless `environment_key` rather than defining a classic job cluster.

Implementation prerequisite: the target workspace/account must have serverless workflows enabled and the required egress/Unity Catalog permissions. If this prerequisite is not met, the feature stops at the implementation gate and a classic jobs-compute fallback must be designed explicitly rather than silently substituted.

## 5. Executable dataset contract

### 5.1 Contract model

Introduce a small reusable contract under the platform Delta boundary. Proposed public model:

```python
@dataclass(frozen=True)
class ColumnContract:
    name: str
    data_type: str
    nullable: bool
    description: str

@dataclass(frozen=True)
class TableLayout:
    clustering_columns: tuple[str, ...] = ()
    partition_columns: tuple[str, ...] = ()

@dataclass(frozen=True)
class TableMetadata:
    description: str
    tags: Mapping[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class SchemaEvolutionPolicy:
    enabled: bool = False
    allow_add_nullable_columns: bool = True

@dataclass(frozen=True)
class DatasetContract:
    columns: tuple[ColumnContract, ...]
    managed_columns: tuple[ColumnContract, ...]
    key_columns: tuple[str, ...]
    write_strategy: WriteStrategy
    layout: TableLayout
    metadata: TableMetadata
    schema_evolution: SchemaEvolutionPolicy = SchemaEvolutionPolicy()
```

This is the target shape, not a commitment to these exact module names or syntax if Python implementation constraints require a minor adjustment.

### 5.2 Why DDL strings for `data_type`

`ColumnContract.data_type` uses Spark SQL/DDL type strings such as `string`, `date`, `timestamp` and `variant`.

Reasons:

- they map directly to Unity Catalog/ALTER TABLE statements;
- they are stable to serialize/log/test;
- they avoid leaking environment-specific schema instances into metadata declarations;
- a helper can parse them into Spark `DataType`/`StructField` objects when a `StructType` is needed.

Invalid DDL types must fail contract validation.

### 5.3 Managed columns

`ingestion_timestamp` is a platform-managed Bronze column.

It remains added by `BronzeWriter`, but it becomes part of the authoritative resolved table contract through `managed_columns` rather than being manually repeated in every dataset declaration.

The platform owns a reusable declaration equivalent to:

```text
name: ingestion_timestamp
type: timestamp
nullable: false
description: Timestamp at which the row was persisted by the ingestion platform.
```

`DatasetContract.resolved_columns` conceptually returns:

```text
columns + managed_columns
```

Duplicate names between dataset and managed columns are invalid.

### 5.4 Contract invariants

Contract construction validates at least:

- unique column names;
- non-empty descriptions for persisted columns;
- key columns exist in resolved columns;
- layout columns exist in resolved columns;
- no column is both partitioned and clustered;
- supported write strategy;
- valid schema-evolution policy;
- durable metadata/tag keys and non-empty values.

## 6. Spark schema semantics

### 6.1 Final table schema versus adapter staging schema

The `DatasetContract` is authoritative for the **persisted table schema**.

A source/domain adapter may still have a transient construction schema when technically necessary. The current GDP writer, for example, constructs `payload_json` as a string before converting it to final `VARIANT payload`. That transient field is not part of the persisted contract and does not violate single-source-of-truth semantics.

Avoidable duplication of the final persisted fields must be removed.

### 6.2 Nullability

Spark/Delta catalog nullability metadata is not treated as a fully enforced database constraint in the first slice.

The contract stores nullability because it is part of the logical schema and is needed when constructing schemas and documenting columns. Table drift comparison normalizes/does not fail solely on Delta's nullable representation when the platform cannot rely on it as an enforced UC invariant.

Explicit runtime checks, such as non-null logical keys, remain application validation.

## 7. Delta table lifecycle

Introduce a reusable collaborator under `platform/delta/`, conceptually:

```python
class DeltaTableLifecycle:
    def ensure_table(self, dataframe: DataFrame) -> None: ...
    def inspect(self) -> TableState: ...
    def validate_contract(self) -> SchemaDiff: ...
    def apply_metadata(self) -> None: ...
    def evolve_if_allowed(self, diff: SchemaDiff) -> None: ...
```

### 7.1 Creation path

When the target does not exist:

1. validate prepared DataFrame against the resolved dataset contract;
2. create an **empty Delta table** using the prepared DataFrame schema;
3. apply clustering/partitioning from the contract;
4. materialize table description, column comments and approved tags;
5. inspect and validate the resulting table against the contract;
6. return control to `BronzeWriter`, which performs the configured write strategy.

Creating an empty table first prevents lifecycle creation from also becoming the initial write operation.

### 7.2 Existing-table path

When the table exists:

1. inspect actual schema/layout/metadata;
2. compute a structured diff against the contract;
3. fail immediately on breaking drift;
4. if the only schema drift is explicitly supported and evolution is enabled, apply it;
5. reconcile safe metadata changes;
6. re-inspect and assert compatibility;
7. return control to the writer.

### 7.3 Schema diff model

The lifecycle should expose a testable diff containing categories such as:

```text
missing_columns        # declared by contract, absent from table
unexpected_columns     # present in table, absent from contract
type_mismatches
layout_mismatch
```

Metadata drift is tracked independently because description/comment/tag updates are reconcilable metadata rather than schema evolution.

## 8. Schema evolution matrix

Default for every dataset: `schema_evolution.enabled = false`.

First-slice behavior:

| Change | Evolution disabled | Evolution enabled | First-slice action |
| --- | --- | --- | --- |
| Add nullable declared column | FAIL | ALLOW | `ALTER TABLE ADD COLUMN` then metadata reconcile |
| Add non-nullable declared column | FAIL | FAIL | explicit migration required |
| Column removed from contract / unexpected table column | FAIL | FAIL | explicit migration required |
| Data type change | FAIL | FAIL | explicit migration required |
| Nullability tightening | FAIL | FAIL | explicit migration required |
| Nullability loosening | FAIL | FAIL | explicit migration required in v1 |
| Key change | FAIL | FAIL | contract/migration decision required |
| Partition/clustering change | FAIL | FAIL | explicit physical migration required |
| Table description change | RECONCILE | RECONCILE | update metadata |
| Column comment change | RECONCILE | RECONCILE | update metadata |
| Approved tag change | RECONCILE | RECONCILE | update metadata |

This deliberately avoids general `mergeSchema` behavior.

All applied evolution must produce structured logs containing target table and changed columns.

## 9. BronzeWriter integration

`BronzeWriter` receives a lifecycle collaborator or creates the default lifecycle from its Spark session, target table and dataset contract.

Target responsibility split:

```text
DatasetContract
    defines persisted contract

DeltaTableLifecycle
    ensure/create/inspect/evolve/metadata/layout

BronzeWriter
    prepare dataframe
    add platform-managed columns
    runtime batch validation
    MERGE / FULL_REPLACE / replaceWhere
```

`BronzeWriter._create_table()` is removed. Table creation is delegated to lifecycle.

No domain-specific behavior enters the lifecycle.

## 10. GDP pilot contract

`IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG` evolves into, or is replaced by, the GDP dataset contract that declares the existing persisted fields plus platform-managed ingestion timestamp.

Durable initial metadata:

```text
layer = bronze
domain = ibge
source_system = ibge_sidra
```

No PII tag is added because this public aggregate dataset does not justify it.

Schema evolution for the GDP pilot remains **disabled by default**. A dedicated unit/integration test contract may enable it to prove the supported additive-nullable behavior without making GDP permissive merely for demonstration.

## 11. Minimal JobDefinition

Introduce only enough Python-side job metadata to represent future composition needs without generating YAML:

```python
@dataclass(frozen=True)
class JobDefinition:
    key: str
    entrypoint: str
    parameters: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
```

For the first slice, the GDP definition has no dependencies.

The DAB YAML remains deployment source of truth. `JobDefinition` is application/platform metadata for reuse/testing and must not become a parallel complete Databricks Job API model.

If this object creates duplication without a second real consumer during implementation, its introduction may be deferred; dependency representation is a requirement, but premature framework construction is not.

## 12. Testing strategy

### Unit tests

Add tests for:

- `ColumnContract` and DDL parsing;
- `DatasetContract` invariants and resolved managed columns;
- `TableLayout` invariants;
- schema diff classification;
- fail-fast default;
- additive nullable evolution opt-in;
- rejection of non-null additions/type/removal/layout changes;
- metadata reconciliation commands/behavior;
- BronzeWriter delegation to lifecycle;
- GDP contract contents;
- GDP job parser/entrypoint behavior remains valid.

### Integration tests

Using local Spark/Delta capabilities where available:

- create table through lifecycle;
- verify contract-compatible schema;
- verify MERGE idempotency remains intact;
- prove incompatible drift fails;
- prove allowed additive nullable evolution succeeds when explicitly enabled.

Workspace smoke validation covers features that local Spark cannot faithfully prove, especially Unity Catalog comments/tags and actual DAB deployment.

### Bundle validation

CI/local gates include:

```text
databricks bundle validate -t dev
databricks bundle validate -t stg
databricks bundle validate -t prd
```

Deployment/run occurs only at the appropriate promotion stage.

## 13. CI/CD design

Introduce GitHub Actions workflows or an equivalent repository-owned pipeline with these logical gates:

### PR / CI

- install environment;
- Ruff;
- type check if current project gate requires it;
- pytest unit/integration;
- build wheel;
- validate bundle configuration.

### Staging promotion

On approved merge to `main`:

- use the commit SHA as promotion identity;
- obtain Databricks credentials through GitHub secrets/OIDC-compatible setup supported by the environment;
- deploy `stg`;
- run GDP smoke job;
- verify expected table/contract state.

### Production promotion

After staging success and protected manual approval:

- deploy the exact approved commit/artifact to `prd`;
- production target branch validation must pass;
- run post-deploy verification;
- no source modification occurs between staging approval and production deployment.

Secrets, service-principal IDs and workspace credentials are never committed.

## 14. Observability

New lifecycle operations log at least:

- target table;
- lifecycle action (`create`, `validate`, `metadata_reconcile`, `schema_evolve`);
- schema diff summary on failure;
- exact automatically added nullable columns when evolution occurs.

Existing ingestion `request_id` behavior remains unchanged.

## 15. Security and permissions

- `dev`, `stg`, `prd` use distinct catalogs to provide the primary namespace boundary;
- service principals receive only the catalog/schema permissions needed by their environment;
- staging identity must not receive production write permission;
- production identity must not be used for ordinary developer iteration;
- DAB/environment configuration must not embed credentials.

## 16. Documentation deliverables

Implementation must update:

- this Technical Design with any approved deviations;
- deployment/run documentation with concrete commands;
- dataset-contract usage documentation/examples;
- ADR-004 for executable contracts/lifecycle;
- ADR-005 for DAB environment/promotion boundary;
- README only where the new standard developer workflow changes repository onboarding/usage.

## 17. Explicitly deferred

- generalized migration engine;
- schema widening/type migration;
- drop/rename automation;
- job discovery;
- YAML generation;
- DAG compiler;
- schedule framework;
- generic CI framework comparable to SAFRA;
- migration of all six jobs;
- Silver/Gold orchestration.

## Technical Design exit criteria

Technical Design can advance when:

1. this design is approved;
2. ADR-004 and ADR-005 are accepted;
3. Impact Analysis is reviewed;
4. serverless workflows and service-principal prerequisites are confirmed during implementation readiness;
5. no unresolved design question changes the public contract or promotion model.
