# ADR-004 — Executable Dataset Contracts and Delta Table Lifecycle

- **Status:** Accepted
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Dataset contracts, Delta table lifecycle, governance metadata, Bronze write responsibility and schema evolution

## Context

The platform needed to evolve beyond the narrow `BronzeDatasetConfig` model without turning `BronzeWriter` into a god object. Persisted schema, layout, descriptions, tags and drift behavior needed an explicit executable contract that could be validated consistently across `dev`, `stg` and `prd`.

Unity Catalog governance also required a durable distinction between table/column attributes and later access-policy behavior. Rows are not tagged securable objects; row-level security belongs to row-filter policy logic.

## Decision

### 1. Adopt an executable dataset contract

Persisted datasets use `DatasetContract` composed from small declarative contract types. The contract is authoritative for persisted columns, data types, logical nullability, descriptions, logical keys, write strategy, table layout, table/column metadata and schema-evolution policy.

### 2. Keep platform-managed columns explicit

Platform-managed fields such as `ingestion_timestamp` are part of the resolved table contract rather than hidden implementation details.

### 3. Separate table lifecycle from write semantics

`DeltaTableLifecycle` owns table creation/inspection, layout validation, schema compatibility, metadata reconciliation and explicitly supported schema evolution.

`BronzeWriter` owns DataFrame preparation, platform-managed value injection, runtime batch validation and write semantics such as `MERGE`, `FULL_REPLACE` and explicit reprocessing.

### 4. Treat governance metadata as executable state

Table descriptions, column comments and approved table/column tags are contract state and are reconciled through the lifecycle. Metadata must represent real facts; public datasets must not receive fabricated sensitivity classifications solely to demonstrate governance.

### 5. Preserve a path to fine-grained governance

The contract model supports table/column governed-tag assignments while row-filter and column-mask policy definitions remain separate governance objects. Literal row tags are not introduced.

### 6. Fail on schema drift by default

Schema evolution is disabled by default. Incompatible table drift fails before normal write execution.

### 7. Allow only conservative explicit evolution

The first automatic evolution supported is an explicitly enabled additive nullable column. Type changes, removals, non-null additions, key changes and layout changes remain explicit migration concerns.

Description/comment/tag updates are reconcilable metadata rather than schema evolution.

### 8. Preserve transient adapter schemas where necessary

A source adapter may use transient construction fields, for example creating `payload_json` before conversion to persisted `VARIANT payload`. The single source of truth applies to the persisted contract, not every transient transformation shape.

### 9. Logical nullability is not assumed to be a fully enforced UC constraint

The contract records nullability, while runtime validations continue to enforce application invariants such as non-null logical keys where required.

## Alternatives considered

### Keep `BronzeDatasetConfig` as the only contract

Rejected because it could not become the authoritative persisted schema/metadata contract without absorbing unrelated responsibilities.

### Put lifecycle behavior into `BronzeWriter`

Rejected because table state/governance and write semantics evolve independently and must remain reusable outside Bronze.

### Use unrestricted `mergeSchema`

Rejected because broad automatic schema mutation weakens the production contract boundary.

### Model row-level governance as row tags

Rejected because Unity Catalog tags apply to securable objects, not individual rows.

### Reproduce a larger orchestration/task framework

Rejected because the project only needed the reusable contract/lifecycle principles, not a generalized orchestration framework.

## Consequences

### Positive

- one authoritative persisted schema contract;
- explicit and testable drift behavior;
- safe opt-in schema evolution boundary;
- executable table/column metadata;
- clear separation between lifecycle and write semantics;
- reusable foundation for later Silver/Gold datasets.

### Costs

- existing Bronze declarations required migration;
- lifecycle logic and tests became explicit platform code;
- governed-tag application depends on Unity Catalog configuration and permissions;
- schema changes beyond additive nullable columns remain manual by design.

## Implementation evidence

The decision is implemented in the current platform:

- current Bronze datasets use executable `DatasetContract` declarations;
- `DeltaTableLifecycle` exists as a dedicated platform boundary;
- `BronzeWriter` delegates table lifecycle rather than owning creation/state reconciliation;
- schema drift and supported additive-nullable evolution are covered by tests;
- table physical layout validation is implemented;
- table/column metadata and governance assignments are represented by the contract/lifecycle model;
- GDP and later CEMPRE workloads execute on the same platform foundation;
- generated API reference exposes Contracts, Lifecycle and BronzeWriter separately.

Future generalized migration behavior and analytical-layer policy needs remain separate scope.
