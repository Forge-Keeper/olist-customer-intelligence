# DAB + Platform Contracts — Requirements

## Status

Requirements approved from Discovery and user decisions. Technical Design and Impact Analysis refine the implementation boundary. No implementation is authorized by this document alone.

## Objective

Deliver the first professional Databricks Asset Bundle vertical slice for Olist Customer Intelligence while introducing an executable dataset contract, an explicit Delta table lifecycle boundary, and a first-class Unity Catalog ABAC governance foundation.

The first DAB pilot is `ibge_municipality_gdp_ingestion`. All current Bronze dataset declarations will migrate to the executable contract model in this feature so the platform does not retain competing contract abstractions.

## Environment and deployment requirements

### R1 — Environment isolation

The solution must define three deployment targets backed by distinct Unity Catalog catalogs:

- `dev` -> catalog `dev`;
- `stg` -> catalog `stg`;
- `prd` -> catalog `prd`.

Runtime/domain code must not infer environment from target-name string checks and must not hardcode these catalogs.

### R2 — Databricks-native promotion flow

Deployment must follow a professional CI/CD promotion flow aligned with Databricks Declarative Automation Bundles practices:

- development execution and iteration occur in `dev`;
- validated deliverables are promoted through `stg` before `prd`;
- production deployment must use production-safe bundle behavior rather than treating `prd` as another development target;
- the exact branch-to-target mapping, deployment identity and automated/manual approval gates are Technical Design decisions.

### R3 — Explicit DAB resources

The first slice must use:

- root `databricks.yml`;
- explicit, versioned YAML resources under `resources/`;
- no automatic YAML/resource generator.

### R4 — Environment-specific configuration

The DAB target configuration must own environment-specific values such as catalog/schema and the resolved target table. Domain code must receive fully resolved runtime values.

### R5 — Pilot job

The first deployed job is `src/olist_data_platform/jobs/ibge_municipality_gdp_ingestion.py`.

The same Python code must run against `dev`, `stg` and `prd` without source changes.

## Dataset contract requirements

### R6 — Single schema source of truth

Managed datasets must have one declarative source of truth for stable persisted column contract information.

Each declared column must contain at least:

- name;
- data type;
- nullable flag;
- description/comment.

The design should eliminate avoidable duplication between Spark `StructType` declarations and `required_columns`-style lists.

### R7 — Executable schema contract

The declared column contract must be usable to produce and/or validate a Spark schema.

At minimum, validation must identify:

- missing declared columns;
- unexpected runtime/table columns;
- incompatible data types.

Nullability handling must be explicitly defined in Technical Design because existing Delta/Spark behavior may differ between in-memory input validation and catalog metadata comparison.

### R8 — Dataset persistence contract

The dataset contract must continue to declare the persistence semantics already represented by the platform, including:

- logical key columns;
- write strategy;
- physical layout through clustering and/or partitioning.

The first design should remain small. New wrapper classes are introduced only where they clarify real responsibility boundaries.

### R9 — Dataset metadata and governed-tag assignments

The contract must support at least:

- table description;
- column comments;
- table-level tags;
- column-level tags;
- explicit governed-tag assignments compatible with Unity Catalog ABAC.

Tags are executable governance metadata, not documentation-only fields. The lifecycle must be able to reconcile intended tag assignments with Unity Catalog state when the required feature and permissions are available.

The first pilot may declare durable table facts such as `layer=bronze`, `domain=ibge` and source-system information. PII/classification/sensitivity tags must not be invented without evidence.

## ABAC governance requirements

### R10 — ABAC as the default fine-grained governance direction

Unity Catalog Attribute-Based Access Control (ABAC) is the selected strategic mechanism for scalable fine-grained governance.

The platform must be designed to use governed tags as object attributes and centralized policies rather than implementing per-table custom access logic whenever ABAC can represent the requirement.

### R11 — Separate dataset attributes from policy definitions

`DatasetContract` owns data-object facts and assignments, including table/column governed tags.

ABAC policy definitions are separate platform governance objects because policies can attach at catalog/schema/table scope and apply to many datasets automatically.

The architecture must therefore separate:

```text
DatasetContract
    -> table/column governed tag assignments

GovernancePolicyDefinition
    -> policy scope
    -> policy type
    -> tag matching condition
    -> UDF / policy expression reference
```

A dataset contract must not embed a complete duplicated policy definition for every table.

### R12 — Column mask policy support

The governance platform must be able to represent, deploy/ensure and validate ABAC column-mask policies driven by governed column tags.

This capability must support future sensitive Gold columns without requiring a redesign of `DatasetContract`.

### R13 — Row filter policy support

The governance platform must be able to represent, deploy/ensure and validate ABAC row-filter policies.

Rows are not modeled as tagged securable objects. Row-level restrictions are policy behavior evaluating row values, object governed tags and caller identity/context.

If a classification attribute is stored per row, it is an ordinary data-model column consumed by policy logic, not a Unity Catalog row tag.

### R14 — Policy scope and centralization

Policy definitions must support at least catalog and schema scope, with table scope available where a genuinely local exception is required.

Default preference is the broadest safe reusable scope so new tagged datasets inherit policy behavior automatically.

### R15 — Governance policy reconciliation

Governance lifecycle/tooling must be able to inspect and reconcile declared ABAC policy state, including:

- policy existence;
- scope;
- policy type;
- referenced governed tags;
- referenced UDF/policy expression;
- observable drift/failure.

Policy changes must be logged and testable.

### R16 — Governed-tag taxonomy is controlled

Governed tags are account-level governed objects with explicit allowed values and assignment permissions.

The project may declare the taxonomy it requires, but account-level creation/ownership and permissions are deployment/governance prerequisites unless the implementation has the required administrative authority.

Tag names/values/descriptions must never contain personal or secret data.

### R17 — ABAC validation slice

Because the Bronze GDP pilot does not contain a legitimate sensitive-data use case, ABAC row-filter and column-mask behavior must be proven in `dev` using disposable/synthetic governance test objects rather than adding false sensitivity metadata to GDP.

The validation must demonstrate at least:

1. a governed tag assignment on a column;
2. a centralized column-mask ABAC policy matching that tag;
3. a row-filter ABAC policy using controlled test data;
4. policy behavior from at least two caller/group contexts when workspace permissions make that feasible;
5. policy drift/inspection or explicit validation of the declared policy state.

No synthetic governance object is promoted as production business data.

### R18 — ABAC GRANT policies

Dynamic ABAC GRANT policies are currently Beta and are not required for the first implementation slice.

The governance model should not preclude them, but row-filter and column-mask policies are the required v1 capabilities. Promotion of GRANT policies into scope requires a separate explicit decision.

## Delta lifecycle requirements

### R19 — Lifecycle separation

Physical table lifecycle must be separated from Bronze write semantics.

A reusable Delta lifecycle boundary must be responsible for capabilities such as:

- ensure/create table;
- apply or validate table layout;
- materialize description/comments;
- materialize/reconcile table and column tags;
- inspect current table state;
- validate contract compatibility;
- coordinate explicitly allowed schema evolution.

ABAC policy lifecycle remains a separate governance responsibility so `DeltaTableLifecycle` does not become a god object.

### R20 — BronzeWriter responsibility

`BronzeWriter` must remain focused on batch/dataframe preparation and persistence semantics, including the currently supported behaviors:

- MERGE;
- FULL_REPLACE;
- explicit reprocessing / `replaceWhere`.

It must not become the owner of table governance or ABAC policy concerns.

## Schema evolution requirements

### R21 — Fail-fast default

Incompatible schema drift must fail explicitly by default.

A dataset for which schema evolution has not been explicitly enabled must never silently mutate the table definition to accommodate an incompatible schema.

### R22 — Explicit evolution opt-in

The dataset contract must provide an explicit way to declare that supported schema evolution is allowed for that dataset.

This opt-in is a policy switch, not unrestricted `mergeSchema` behavior.

### R23 — Controlled evolution behavior

When evolution is enabled, the lifecycle component must distinguish supported changes from breaking changes.

The first supported matrix is conservative: additive nullable columns may be eligible for automatic evolution; type changes, column removals, key changes, nullability changes and incompatible layout changes remain explicit migrations.

### R24 — Observable evolution

Any automatic schema evolution that is allowed and applied must be visible in logs and must be testable. Silent mutation is not acceptable.

## Contract migration requirements

### R25 — Single contract model after this feature

All current `BronzeDatasetConfig` dataset declarations must be migrated to the executable `DatasetContract` model in this feature.

Only GDP is migrated to DAB deployment. Migrating the other Bronze contracts does not imply migrating their jobs to DAB.

A long-lived compatibility layer between old and new dataset contract models is not accepted as the target architecture.

## Job definition requirements

### R26 — Minimal declarative job definition

The platform should introduce a small job-definition capability able to represent at least:

- job key/name;
- Python entrypoint;
- parameters;
- optional explicit dependencies.

### R27 — Dependency scope

Dependencies must be representable but remain shallow in this slice.

Out of scope:

- automatic dependency detection;
- DAG compilation;
- dependency graph planning;
- generalized Silver/Gold orchestration.

## Packaging and compute requirements

### R28 — Deployable Python artifact

The pilot must use a repeatable deployment mechanism for the existing Python package. Wheel packaging is the selected direction and must be validated during implementation.

### R29 — Compute compatibility

The pilot design targets serverless jobs compute, subject to actual workspace availability, Unity Catalog permissions and required outbound access to IBGE.

ABAC policy validation requires supported compute. Current Databricks requirements must be verified during implementation; serverless is acceptable and avoids depending on an older unsupported runtime.

## Validation and acceptance criteria

The first vertical slice is accepted only when all of the following are demonstrated:

1. Bundle configuration validates successfully.
2. The same job artifact/configuration model can target `dev`, `stg` and `prd` without Python source changes.
3. `dev` resolves to `dev.bronze...`, `stg` to `stg.bronze...`, and `prd` to `prd.bronze...`.
4. Non-production execution cannot write to the `prd` catalog through a hardcoded runtime path in the GDP pilot.
5. GDP can be deployed and run through the approved promotion path.
6. All current Bronze dataset declarations use the executable contract model.
7. The dataset contract is the authoritative declaration of stable persisted schema information.
8. The lifecycle can create/ensure the table and materialize approved metadata.
9. Table-level tags can be declared and reconciled.
10. Column-level governed-tag assignments can be declared and reconciled.
11. No sensitivity/PII governance fact is invented by platform defaults.
12. A synthetic `dev` validation proves ABAC column masking.
13. A synthetic `dev` validation proves ABAC row filtering.
14. ABAC policy state is inspectable/validatable and policy changes are observable.
15. The lifecycle can detect schema drift.
16. Drift fails by default when evolution is disabled.
17. A dataset explicitly marked as evolution-enabled can apply only supported evolution changes.
18. Unsupported/breaking changes still fail even when evolution is enabled.
19. Any applied evolution is logged.
20. Existing GDP MERGE/idempotency behavior remains valid.
21. Existing unit/integration/lint gates remain green.
22. Documentation is updated and durable architectural decisions are captured in ADRs.

## Documentation requirements

### DR1 — Development documentation

The feature documentation must describe:

- bundle targets and promotion path;
- configuration boundaries;
- pilot job;
- contract model;
- lifecycle behavior;
- table/column governed tags;
- ABAC policy model and supported v1 policy types;
- row-filter and column-mask validation;
- schema evolution policy;
- validation/deployment commands once finalized.

### DR2 — ADR: executable contracts and lifecycle

Maintain `ADR-004-executable-dataset-contracts-and-delta-lifecycle.md` for executable contracts, metadata, lifecycle and schema evolution.

### DR3 — ADR: deployment/environment boundary

Maintain `ADR-005-dab-environment-and-promotion-boundary.md` for the durable `dev -> stg -> prd` DAB environment/promotion boundary.

### DR4 — ADR: ABAC governance

Create a dedicated ADR for the durable decision to use Unity Catalog ABAC as the fine-grained governance model and to separate dataset governed-tag assignments from centralized policy definitions.

Candidate: `ADR-006-unity-catalog-abac-governance.md`.

## Explicit non-goals

The first slice does not include:

- DAB migration of all existing jobs;
- automatic YAML generation;
- automatic job/task discovery;
- dependency inference or DAG compiler;
- generalized table migration engine;
- unrestricted schema evolution;
- production-sensitive policy assignments invented for demonstration;
- ABAC GRANT policies Beta;
- full Silver/Gold orchestration;
- Terraform;
- MLOps framework parity with SAFRA.

## Open implementation/design details

The following implementation details remain to be validated against the actual Databricks workspace:

1. exact service-principal identities/permissions;
2. GitHub protected-environment/approval configuration;
3. exact wheel build/install command;
4. serverless workflow availability and egress permissions;
5. exact `DatasetContract`/`ColumnContract` Python field shapes;
6. exact SQL/REST mechanism used to reconcile governed tags;
7. exact SQL/REST mechanism used to create/alter/inspect ABAC policies;
8. governed-tag taxonomy creation/permissions in the connected account;
9. lifecycle API details and BronzeWriter injection seam;
10. exact synthetic ABAC smoke dataset and caller/group identities;
11. whether a minimal Python `JobDefinition` has a real first-slice consumer or should be deferred.

## Gate

Requirements are approved. Technical Design, ADRs and Implementation Plan must reflect ABAC as a first-class v1 governance capability before implementation begins.
