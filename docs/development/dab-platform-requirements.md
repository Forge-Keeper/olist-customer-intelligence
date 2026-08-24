# DAB + Platform Contracts — Requirements

## Status

Requirements approved from Discovery and user decisions. Technical Design and Impact Analysis refine the implementation boundary. No implementation is authorized by this document alone.

## Objective

Deliver the first professional Databricks Asset Bundle vertical slice for Olist Customer Intelligence while introducing an executable dataset contract and an explicit Delta table lifecycle boundary.

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

### R9 — Dataset metadata and governance

The contract must support at least:

- table description;
- column comments;
- table-level tags;
- column-level tags;
- a small durable tag vocabulary based on platform/source/governance truth.

Tags are executable governance metadata, not documentation-only fields. The lifecycle must be able to reconcile intended tag assignments with Unity Catalog state when the required feature and permissions are available.

The first pilot may declare durable table facts such as `layer=bronze`, `domain=ibge` and source-system information. PII/classification/sensitivity tags must not be invented without evidence.

Where account-level governed tags are available, the platform design must be compatible with them so tag assignments can participate in centralized Unity Catalog governance/ABAC policies.

### R10 — Future Gold fine-grained governance compatibility

The contract/lifecycle architecture must preserve an explicit extension path for Gold datasets that require fine-grained governance.

Required future capabilities include:

- column-level governed tag assignments;
- column mask policy references;
- row filter policy references;
- compatibility with Unity Catalog ABAC policy-driven governance.

The platform must **not** invent literal per-row metadata tags. Rows are governed through row-filter policies evaluating row values and object attributes. If a business dataset needs a classification attribute stored per row, that is a data-model column and not a Unity Catalog tag.

A generalized ABAC policy engine is outside this first slice, but the executable contract must not require redesign to add these policy references later.

## Delta lifecycle requirements

### R11 — Lifecycle separation

Physical table lifecycle must be separated from Bronze write semantics.

A reusable Delta lifecycle boundary must be responsible for capabilities such as:

- ensure/create table;
- apply or validate table layout;
- materialize description/comments;
- materialize/reconcile table and column tags;
- inspect current table state;
- validate contract compatibility;
- coordinate explicitly allowed schema evolution.

### R12 — BronzeWriter responsibility

`BronzeWriter` must remain focused on batch/dataframe preparation and persistence semantics, including the currently supported behaviors:

- MERGE;
- FULL_REPLACE;
- explicit reprocessing / `replaceWhere`.

It must not become the owner of all table governance/lifecycle concerns.

## Schema evolution requirements

### R13 — Fail-fast default

Incompatible schema drift must fail explicitly by default.

A dataset for which schema evolution has not been explicitly enabled must never silently mutate the table definition to accommodate an incompatible schema.

### R14 — Explicit evolution opt-in

The dataset contract must provide an explicit way to declare that supported schema evolution is allowed for that dataset.

This opt-in is a policy switch, not unrestricted `mergeSchema` behavior. Technical Design must define the supported evolution matrix before implementation.

### R15 — Controlled evolution behavior

When evolution is enabled, the lifecycle component must distinguish supported changes from breaking changes.

The first supported matrix is conservative: additive nullable columns may be eligible for automatic evolution; type changes, column removals, key changes, nullability changes and incompatible layout changes remain explicit migrations.

### R16 — Observable evolution

Any automatic schema evolution that is allowed and applied must be visible in logs and must be testable. Silent mutation is not acceptable.

## Contract migration requirements

### R17 — Single contract model after this feature

All current `BronzeDatasetConfig` dataset declarations must be migrated to the executable `DatasetContract` model in this feature.

Only GDP is migrated to DAB deployment. Migrating the other Bronze contracts does not imply migrating their jobs to DAB.

A long-lived compatibility layer between old and new dataset contract models is not accepted as the target architecture.

## Job definition requirements

### R18 — Minimal declarative job definition

The platform should introduce a small job-definition capability able to represent at least:

- job key/name;
- Python entrypoint;
- parameters;
- optional explicit dependencies.

### R19 — Dependency scope

Dependencies must be representable but remain shallow in this slice.

Out of scope:

- automatic dependency detection;
- DAG compilation;
- dependency graph planning;
- generalized Silver/Gold orchestration.

## Packaging and compute requirements

### R20 — Deployable Python artifact

The pilot must use a repeatable deployment mechanism for the existing Python package. Wheel packaging is the selected direction and must be validated during implementation.

### R21 — Compute decision

The pilot design targets serverless jobs compute, subject to actual workspace availability, Unity Catalog permissions and required outbound access to IBGE. If those prerequisites are unavailable, an explicit classic-compute redesign is required rather than a silent substitution.

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
10. Column-level tags can be declared and reconciled.
11. No sensitivity/PII governance fact is invented by platform defaults.
12. The lifecycle can detect schema drift.
13. Drift fails by default when evolution is disabled.
14. A dataset explicitly marked as evolution-enabled can apply only supported evolution changes.
15. Unsupported/breaking changes still fail even when evolution is enabled.
16. Any applied evolution is logged.
17. Existing GDP MERGE/idempotency behavior remains valid.
18. Existing unit/integration/lint gates remain green.
19. Documentation is updated and durable architectural decisions are captured in ADRs.
20. The contract model has a documented future extension point for row-filter and column-mask policy references without introducing fictional row tags.

## Documentation requirements

### DR1 — Development documentation

The feature documentation must describe:

- bundle targets and promotion path;
- configuration boundaries;
- pilot job;
- contract model;
- lifecycle behavior;
- table/column governance tags;
- schema evolution policy;
- validation/deployment commands once finalized.

### DR2 — ADR: executable contracts and lifecycle

Maintain an ADR for the durable architectural decision to:

- use executable dataset contracts;
- separate Delta table lifecycle from write semantics;
- treat table/column governance metadata as executable contract state;
- preserve the future ABAC row-filter/column-mask extension path;
- fail on schema drift by default;
- allow explicit, controlled schema evolution;
- keep environment resolution outside the dataset contract.

`ADR-004-executable-dataset-contracts-and-delta-lifecycle.md`.

### DR3 — ADR: deployment/environment boundary

Maintain a separate ADR for the durable `dev -> stg -> prd` DAB environment/promotion boundary.

`ADR-005-dab-environment-and-promotion-boundary.md`.

## Explicit non-goals

The first slice does not include:

- DAB migration of all existing jobs;
- automatic YAML generation;
- automatic job/task discovery;
- dependency inference or DAG compiler;
- generalized table migration engine;
- unrestricted schema evolution;
- generalized ABAC policy authoring/management;
- row-filter or column-mask implementation for Bronze GDP;
- full Silver/Gold orchestration;
- Terraform;
- MLOps framework parity with SAFRA.

## Open implementation/design details

The following implementation details remain to be finalized in the implementation plan or validated against the actual Databricks workspace:

1. exact service-principal identities/permissions;
2. GitHub protected-environment/approval configuration;
3. exact wheel build/install command;
4. serverless workflow availability and egress permissions;
5. exact `DatasetContract`/`ColumnContract` Python field shapes;
6. exact SQL/API mechanism used to reconcile table and column tags;
7. whether governed-tag taxonomy already exists or must be treated as an external prerequisite;
8. lifecycle API details and BronzeWriter injection seam;
9. whether a minimal Python `JobDefinition` has a real first-slice consumer or should be deferred.

## Gate

Requirements are approved. Technical Design and Impact Analysis incorporate the selected full Bronze contract migration and governance direction. Proceed to Implementation Plan only after those design amendments are accepted.
