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
- Table and column governed-tag assignments are first-class contract metadata.
- **Unity Catalog ABAC is the selected fine-grained governance direction.**
- ABAC v1 includes governed tags, centralized row-filter policies and centralized column-mask policies.
- ABAC policy definitions are separate from dataset contracts and have their own governance lifecycle.
- Synthetic/disposable `dev` objects prove ABAC behavior; GDP does not receive fabricated sensitivity metadata.
- ABAC GRANT policies remain out of scope because they are Beta.
- No YAML generator, dependency inference or full SAFRA parity.

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
tags / governed-tag assignments
```

`TableMetadata` must represent:

```text
description
tags / governed-tag assignments
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

Add tags only when justified. Minimum durable platform taxonomy may include:

```text
layer
domain
source_system
```

Do not infer PII/sensitivity/classification.

Governed column-tag capability must be present, but individual datasets only receive governed tags when there is a real governance fact to represent.

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
- column governed-tag assignment reconciliation;
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

### Governance assignment implementation

Implement table/column tag materialization using the supported Unity Catalog SQL/API mechanism.

The dataset contract represents tag assignments. Account-level governed-tag taxonomy creation and ownership remain explicit prerequisites unless the deployment identity has the required administrative authority.

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
- column governed tags;
- structured logs/observable evolution.

### Checkpoint 3

- lifecycle unit/integration tests green;
- no writes silently mutate unsupported schema;
- governance assignments are independently testable.

---

## Phase 4 — ABAC governance model and lifecycle

### Goal

Implement the first reusable platform abstraction for centralized Unity Catalog ABAC without putting policy logic inside every dataset contract.

### New modules

Recommended shallow package:

```text
src/olist_data_platform/platform/governance/
├── __init__.py
├── policy.py
└── lifecycle.py
```

### Policy model

Implement a small immutable `GovernancePolicyDefinition` (exact name may change) able to represent:

```text
key / name
policy_type = ROW_FILTER | COLUMN_MASK
scope = catalog | schema | table
tag condition / matching expression
UDF or inline policy expression reference
description
```

Do not model the full Databricks API. Only fields required by v1 ABAC policies belong here.

### Governance lifecycle

Implement a `GovernancePolicyLifecycle` responsible for:

- inspect current policy state;
- create/ensure a declared policy;
- validate policy scope/type/matching logic reference;
- reconcile supported policy definition changes;
- fail explicitly on unsupported/ambiguous drift;
- structured logs for policy create/update/validate/failure.

Use the supported Unity Catalog SQL or REST API based on what provides the clearest testable implementation in the actual workspace. Do not support both mechanisms without a concrete need.

### UDF boundary

Row filters and column masks may require Unity Catalog UDFs or supported inline SQL expressions. Policy definitions should reference those functions/expressions rather than embedding arbitrary Python execution.

UDFs used by policies must be version-controlled as SQL/application resources and have explicit ownership/EXECUTE prerequisites.

### Tests

Create:

```text
tests/unit/platform/governance/test_policy.py
tests/unit/platform/governance/test_lifecycle.py
```

Cover:

- valid/invalid policy definitions;
- ROW_FILTER and COLUMN_MASK types;
- valid catalog/schema/table scope;
- policy inspection/diff/reconcile;
- logging;
- unsupported drift failure;
- no coupling to BronzeWriter or domain code.

### Checkpoint 4

- governance abstractions are green independently of real workspace ABAC;
- policy definitions remain separate from DatasetContract;
- no generalized policy compiler or ABAC GRANT implementation appears.

---

## Phase 5 — BronzeWriter integration

### Changes

Refactor:

```text
src/olist_data_platform/platform/delta/bronze/writer.py
```

Target responsibility split:

```text
DatasetContract
    schema + metadata + governed object attributes

DeltaTableLifecycle
    create / inspect / validate / evolve / reconcile object metadata

GovernancePolicyLifecycle
    centralized ABAC policy state (not called by BronzeWriter)

BronzeWriter
    prepare / managed values / batch validation / write semantics
```

Remove `_create_table()` from `BronzeWriter`.

Flow:

1. validate incoming dataset fields;
2. add `ingestion_timestamp`;
3. validate logical key values/duplicates;
4. call Delta lifecycle `ensure/validate` using prepared schema;
5. perform MERGE/FULL_REPLACE/replaceWhere.

Preserve all current safeguards and semantics.

### Tests

Update:

```text
tests/unit/platform/delta/bronze/test_writer.py
```

and every domain writer affected by constructor/contract changes.

### Checkpoint 5

Run the **entire unit and integration suite**, not only new tests.

Must prove:

- existing MERGE behavior;
- idempotency;
- FULL_REPLACE protection;
- replaceWhere behavior;
- no source/domain behavior changed accidentally.

---

## Phase 6 — GDP contract validation and workspace lifecycle smoke

### Changes

Finalize GDP contract as the reference example for:

- explicit persisted schema;
- platform-managed timestamp;
- key columns;
- clustering;
- table description;
- truthful table tags;
- schema evolution disabled by default.

Keep transient `payload_json` staging behavior only where required before VARIANT conversion.

Do **not** add false sensitivity/PII governed tags to GDP merely to exercise ABAC.

### Workspace smoke before DAB

Against `dev` only:

- create/ensure GDP table through lifecycle;
- validate schema/layout;
- inspect comments/tags;
- run ingestion twice and prove idempotency;
- intentionally demonstrate contract drift failure in a disposable test object or controlled test path;
- demonstrate opt-in additive nullable evolution without making production GDP permissive.

### Checkpoint 6

Platform contract/lifecycle behavior is proven in the actual Databricks environment before adding deployment automation.

---

## Phase 7 — ABAC workspace validation in `dev`

### Goal

Prove the real Databricks governance behavior without contaminating business datasets with synthetic classifications.

### Prerequisites

Confirm current Databricks requirements before execution:

- Unity Catalog enabled;
- serverless or another supported runtime configuration;
- governed-tag CREATE/ASSIGN/APPLY TAG permissions as required;
- MANAGE/ownership on selected catalog/schema scope;
- EXECUTE on policy UDFs;
- test identities/groups sufficient to demonstrate differential access where possible.

If taxonomy creation permission is unavailable, stop and request/provision the required governed tags rather than falling back to ungoverned tags for the ABAC proof.

### Synthetic validation objects

Create disposable governance fixtures under a dedicated development schema, conceptually:

```text
dev.governance_validation.abac_people_demo
```

Synthetic rows may include only fake values such as region, access_segment, synthetic_identifier and synthetic_secret.

### Column-mask proof

1. assign a governed sensitivity tag to a synthetic column;
2. create/ensure a centralized COLUMN_MASK ABAC policy that matches that tag;
3. query as appropriate test caller contexts;
4. verify masked versus allowed behavior;
5. inspect/validate policy state through the governance lifecycle.

### Row-filter proof

1. use controlled synthetic row attributes such as `region` or `access_segment`;
2. create/ensure a ROW_FILTER ABAC policy at schema/catalog scope when safe;
3. verify different visible rows for controlled caller/group contexts;
4. inspect/validate policy state.

### Cleanup

Synthetic tables/policies/UDFs must be clearly named and either automatically removed after validation or documented as disposable test fixtures. Governed taxonomy objects may remain only if they are part of the approved durable taxonomy.

### Checkpoint 7

- real governed tag assignment proven;
- column masking proven;
- row filtering proven;
- policy inspection/validation proven;
- no false governance metadata added to GDP.

---

## Phase 8 — Wheel packaging

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

### Checkpoint 8

A reproducible wheel exists and GDP entry point resolves correctly.

---

## Phase 9 — DAB dev target and GDP pilot

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

### Checkpoint 9

End-to-end local/developer path is proven without any `prd` hardcode.

---

## Phase 10 — STG/PRD target validation and governance prerequisites

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
- approved governed-tag taxonomy and assignment permissions;
- ABAC policy MANAGE permissions at intended catalog/schema scopes;
- EXECUTE permission for governance UDFs where required;
- GitHub environment/secrets capability.

ABAC business policies are promoted only when backed by real governance requirements. The synthetic `dev` validation policy is not automatically promoted to `stg/prd`.

### Checkpoint 10

Targets validate and operational/governance prerequisites are known; no production deploy occurs merely because configuration validates.

---

## Phase 11 — CI/CD

Implement professional promotion gates.

### PR

- dependency install;
- Ruff;
- type gate;
- full pytest;
- wheel build;
- bundle validate targets;
- governance policy-definition unit validation.

### Main -> STG

- build/identify immutable artifact for commit;
- deploy `stg` using staging identity;
- run GDP smoke;
- verify table contract/data/governance assignments;
- validate any real declared ABAC policies intended for staging.

### STG -> PRD

- require protected/manual approval;
- use same approved commit/artifact;
- deploy `prd` with production identity;
- post-deploy contract verification;
- validate any real production ABAC policy state without deploying synthetic validation policies.

### Checkpoint 11

A failed test, contract validation, governance validation, staging smoke or approval prevents production promotion.

---

## Phase 12 — Documentation closeout

Before Done, update/accept:

```text
docs/development/dab-platform-*.md
docs/adr/ADR-004-*.md
docs/adr/ADR-005-*.md
docs/adr/ADR-006-unity-catalog-abac-governance.md
```

Add operator/developer instructions for:

- declaring a `DatasetContract`;
- declaring table/column governed tag assignments;
- governed-tag taxonomy prerequisites and permissions;
- declaring ROW_FILTER and COLUMN_MASK ABAC policies;
- governance UDF ownership/EXECUTE requirements;
- ABAC policy inspection and drift handling;
- contract drift failures;
- controlled schema evolution;
- local wheel build;
- bundle validate/deploy/run;
- dev -> stg -> prd promotion;
- rollback/recovery expectations supported by the implemented pipeline.

Document explicitly that ABAC GRANT policies are deferred and require a separate maturity decision.

## Commit/checkpoint strategy

Prefer small coherent commits after green checkpoints, conceptually:

1. `feat: add executable delta dataset contracts`
2. `refactor: migrate bronze dataset contracts`
3. `feat: add delta table lifecycle and governed tags`
4. `feat: add Unity Catalog ABAC policy lifecycle`
5. `refactor: delegate bronze lifecycle from writer`
6. `test: validate ABAC policies in dev`
7. `build: package GDP ingestion as wheel entry point`
8. `feat: add GDP Databricks bundle pilot`
9. `ci: add staging and production promotion flow`
10. `docs: finalize DAB platform and ABAC governance architecture`

Exact commits may be combined when changes are inseparable, but no commit should knowingly leave the branch with a broken test suite unless it is an explicitly temporary local step that is not pushed.

## Stop conditions / blockers

Stop and surface a decision instead of improvising if any of these occur:

- serverless jobs unavailable or incompatible;
- ABAC unsupported by available compute/runtime;
- required governed-tag taxonomy cannot be created/assigned;
- ABAC policy permissions or UDF execution privileges are unavailable;
- required Unity Catalog metadata/tag operation is unsupported by chosen SQL/API path;
- existing table state requires a breaking schema migration;
- service-principal creation/permissions unavailable;
- DAB wheel deployment requires a materially different packaging model;
- migration of a Bronze config exposes semantics not representable by the accepted `DatasetContract`.

## Final acceptance

The feature is Done only when:

- all current Bronze contracts are migrated;
- all tests/lint/type gates are green;
- `BronzeWriter` no longer owns table creation;
- lifecycle validates/reconciles schema, layout, comments, table tags and column governed tags;
- schema evolution is fail-fast by default and conservative when enabled;
- ABAC policy definitions/lifecycle support ROW_FILTER and COLUMN_MASK;
- synthetic `dev` validation proves governed tags, row filtering and column masking;
- GDP remains free of fabricated sensitivity metadata;
- GDP runs from the wheel through DAB;
- `dev`, `stg`, `prd` resolve isolated catalogs;
- staging promotion is successful;
- production promotion is protected and uses the same approved artifact;
- documentation/ADRs match implemented behavior;
- no production secret or identity is embedded in source;
- future Gold datasets can activate governed-tag-driven ABAC without redesigning the contract foundation.
