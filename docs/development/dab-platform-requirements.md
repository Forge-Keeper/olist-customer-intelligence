# DAB + Platform Contracts — Requirements

## Status

Requirements drafted from the approved Discovery and user decisions. Technical Design and Impact Analysis are the next gates. No implementation is authorized by this document alone.

## Objective

Deliver the first professional Databricks Asset Bundle vertical slice for Olist Customer Intelligence while introducing an executable dataset contract and an explicit Delta table lifecycle boundary.

The first pilot is `ibge_municipality_gdp_ingestion`.

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
- the exact branch-to-target mapping, deployment identity and automated/manual approval gates are Technical Design decisions and must not be invented at Requirements.

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

The pilot dataset must have one declarative source of truth for stable column contract information.

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

### R9 — Dataset metadata

The contract must support at least:

- table description;
- column comments;
- a small durable set of tags based on platform/source truth.

The first pilot may declare durable facts such as `layer=bronze`, `domain=ibge` and source-system information. PII/classification tags must not be invented without evidence.

## Delta lifecycle requirements

### R10 — Lifecycle separation

Physical table lifecycle must be separated from Bronze write semantics.

A reusable Delta lifecycle boundary must be responsible for capabilities such as:

- ensure/create table;
- apply or validate table layout;
- materialize description/comments/tags;
- inspect current table state;
- validate contract compatibility;
- coordinate explicitly allowed schema evolution.

### R11 — BronzeWriter responsibility

`BronzeWriter` must remain focused on batch/dataframe preparation and persistence semantics, including the currently supported behaviors:

- MERGE;
- FULL_REPLACE;
- explicit reprocessing / `replaceWhere`.

It must not become the owner of all table governance/lifecycle concerns.

## Schema evolution requirements

### R12 — Fail-fast default

Incompatible schema drift must fail explicitly by default.

A dataset for which schema evolution has not been explicitly enabled must never silently mutate the table definition to accommodate an incompatible schema.

### R13 — Explicit evolution opt-in

The dataset contract must provide an explicit way to declare that supported schema evolution is allowed for that dataset.

This opt-in is a policy switch, not unrestricted `mergeSchema` behavior. Technical Design must define the supported evolution matrix before implementation.

### R14 — Controlled evolution behavior

When evolution is enabled, the lifecycle component must distinguish supported changes from breaking changes.

The first supported matrix should be conservative. Candidate evolution classes to evaluate in Technical Design include additive nullable columns and metadata/comment changes. Type changes, column removals, key changes, nullability tightening and incompatible layout changes must not be assumed safe.

### R15 — Observable evolution

Any automatic schema evolution that is allowed and applied must be visible in logs and must be testable. Silent mutation is not acceptable.

## Job definition requirements

### R16 — Minimal declarative job definition

The platform should introduce a small job-definition capability able to represent at least:

- job key/name;
- Python entrypoint;
- parameters;
- optional explicit dependencies.

### R17 — Dependency scope

Dependencies must be representable but remain shallow in this slice.

Out of scope:

- automatic dependency detection;
- DAG compilation;
- dependency graph planning;
- generalized Silver/Gold orchestration.

## Packaging and compute requirements

### R18 — Deployable Python artifact

The pilot must use a repeatable deployment mechanism for the existing Python package. Wheel packaging remains the preferred candidate and must be validated in Technical Design.

### R19 — Compute decision

The first job compute model must be explicitly designed based on the actual workspace constraints and the pilot needs:

- Spark + Delta / Unity Catalog access;
- outbound HTTP access to IBGE;
- compatibility with the selected package deployment mechanism.

No compute SKU/runtime/policy is fixed at Requirements.

## Validation and acceptance criteria

The first vertical slice is accepted only when all of the following are demonstrated:

1. Bundle configuration validates successfully.
2. The same job artifact/configuration model can target `dev`, `stg` and `prd` without Python source changes.
3. `dev` resolves to `dev.bronze...`, `stg` to `stg.bronze...`, and `prd` to `prd.bronze...`.
4. Non-production execution cannot write to the `prd` catalog through a hardcoded runtime path in the GDP pilot.
5. GDP can be deployed and run through the approved promotion path.
6. The dataset contract is the authoritative declaration of stable schema information for the pilot.
7. The lifecycle can create/ensure the table and materialize approved metadata.
8. The lifecycle can detect schema drift.
9. Drift fails by default when evolution is disabled.
10. A dataset explicitly marked as evolution-enabled can apply only supported evolution changes.
11. Unsupported/breaking changes still fail even when evolution is enabled.
12. Any applied evolution is logged.
13. Existing GDP MERGE/idempotency behavior remains valid.
14. Existing unit/integration/lint gates remain green.
15. Documentation is updated and architectural decisions are captured in ADRs when durable trade-offs are introduced.

## Documentation requirements

### DR1 — Development documentation

The feature documentation must describe:

- bundle targets and promotion path;
- configuration boundaries;
- pilot job;
- contract model;
- lifecycle behavior;
- schema evolution policy;
- validation/deployment commands once finalized.

### DR2 — ADR: executable contracts and lifecycle

Create an ADR for the durable architectural decision to:

- use executable dataset contracts;
- separate Delta table lifecycle from write semantics;
- fail on schema drift by default;
- allow explicit, controlled schema evolution;
- keep environment resolution outside the dataset contract.

Candidate: `ADR-004-executable-dataset-contracts-and-delta-lifecycle.md`.

### DR3 — ADR: deployment/environment boundary

Technical Design must determine whether DAB environment/promotion policy deserves its own ADR. Given the durable `dev -> stg -> prd` boundary and production deployment behavior, the current recommendation is to create a separate ADR rather than bury the decision in implementation documentation.

Candidate: `ADR-005-dab-environment-and-promotion-boundary.md`.

## Explicit non-goals

The first slice does not include:

- migration of all existing jobs;
- automatic YAML generation;
- automatic job/task discovery;
- dependency inference or DAG compiler;
- generalized table migration engine;
- unrestricted schema evolution;
- full Silver/Gold orchestration;
- Terraform;
- MLOps framework parity with SAFRA.

## Open Technical Design decisions

The following items are intentionally unresolved and must be closed at the next gate:

1. exact DAB `mode`/presets for `dev`, `stg` and `prd`;
2. Git branch/ref promotion policy per target;
3. service-principal/run identity strategy for `prd` and possibly `stg`;
4. CI/CD approval/manual promotion boundaries;
5. wheel build/install mechanism inside the bundle;
6. compute configuration for the pilot;
7. exact `DatasetContract`, `ColumnContract`, layout/metadata types and package placement;
8. contract-to-`StructType` mapping rules;
9. exact schema drift comparison semantics;
10. exact allowed schema-evolution matrix and how approved changes are applied;
11. treatment of the platform-added `ingestion_timestamp` within the authoritative table contract;
12. lifecycle API and BronzeWriter integration seam;
13. minimum `JobDefinition` API without duplicating DAB YAML unnecessarily.

## Gate

Requirements are ready for review. After approval, proceed to Technical Design and Impact Analysis before implementation.
