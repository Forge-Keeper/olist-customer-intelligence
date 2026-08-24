# ADR-004 — Executable Dataset Contracts and Delta Table Lifecycle

- **Status:** Proposed
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Dataset contracts, Delta table lifecycle, Bronze write responsibility and schema evolution

## Context

The platform currently has a useful but narrow `BronzeDatasetConfig` containing logical keys, required columns, physical layout and write strategy. `BronzeWriter` validates batches and performs MERGE/FULL_REPLACE/reprocessing, but it also creates Delta tables and applies layout during creation.

Dataset-specific writers additionally contain Spark schema declarations. For IBGE GDP, the adapter has a transient `INPUT_SCHEMA`, while the persisted table contract is partially represented elsewhere. Table description, column comments, tags and explicit schema-drift behavior are not yet first-class platform concepts.

The DAB feature introduces isolated deployment environments and is the point at which persisted table definitions must become explicit enough to be validated consistently across `dev`, `stg` and `prd`.

A review of the mature SAFRA project confirmed the value of executable schema definitions and contract-versus-Unity-Catalog validation, but Olist should adopt those principles without copying SAFRA's heavier Task/orchestration framework.

## Decision

### 1. Adopt an executable dataset contract

Persisted datasets use an explicit `DatasetContract` composed from small declarative types.

At minimum, the contract represents:

- persisted columns;
- column data types;
- logical nullability;
- column descriptions;
- logical key columns;
- write strategy;
- clustering/partition layout;
- table description;
- approved tags;
- schema-evolution policy.

The contract is the authoritative declaration of the persisted table schema for managed datasets.

### 2. Keep platform-managed columns explicit in the resolved contract

Columns injected by platform behavior, beginning with `ingestion_timestamp`, are not hidden from the table contract.

They are declared once as platform-managed columns and composed into the dataset's resolved contract rather than manually repeated in every domain dataset.

### 3. Separate Delta lifecycle from Bronze write semantics

Introduce a reusable `DeltaTableLifecycle` responsibility for:

- create/ensure table;
- physical layout application/validation;
- table inspection;
- schema compatibility checks;
- metadata/comment/tag reconciliation;
- explicitly permitted schema evolution.

`BronzeWriter` remains responsible for:

- DataFrame preparation;
- platform-managed value injection;
- runtime batch validation;
- MERGE;
- FULL_REPLACE;
- explicit replaceWhere/reprocessing.

Table creation no longer belongs to `BronzeWriter`.

### 4. Fail on schema drift by default

Schema drift is not silently accepted.

The default dataset policy is:

```text
schema evolution disabled
```

A mismatch between the declared persisted contract and an existing table fails before normal write execution.

### 5. Allow controlled evolution only through explicit opt-in

Datasets may explicitly enable schema evolution, but the switch is not equivalent to unrestricted Spark/Delta `mergeSchema` behavior.

The first supported automatic schema change is intentionally conservative:

- additive nullable declared columns.

Breaking or ambiguous changes remain failures, including:

- non-nullable additions;
- removed/unexpected columns;
- type changes;
- nullability changes;
- key changes;
- partition/clustering changes.

Description, comment and approved tag changes are treated as reconcilable metadata rather than schema evolution.

### 6. Preserve adapter-specific transient schemas where technically necessary

Single persisted schema source of truth does not forbid transient adapter schemas.

For example, an IBGE writer may construct a temporary `payload_json` string before parsing it into the final persisted `VARIANT payload`. Only avoidable duplication of the persisted contract is removed.

### 7. Do not treat logical nullability as an automatically enforced UC constraint

The contract records nullability, but the first lifecycle implementation does not assume Delta/Unity Catalog nullable metadata provides full relational enforcement.

Existing runtime validation remains responsible for real application invariants such as non-null logical keys.

## Alternatives considered

### Keep the current `BronzeDatasetConfig` only

Rejected because it cannot become the authoritative persisted schema/metadata contract without accumulating unrelated concerns and becoming a god object.

### Put all lifecycle behavior into `BronzeWriter`

Rejected because table state/governance and write semantics evolve independently and are reusable outside Bronze.

### Adopt unrestricted `mergeSchema`

Rejected because silent or broad schema mutation weakens the contract boundary and makes production drift difficult to govern.

### Reproduce the SAFRA Task framework

Rejected for this project stage. SAFRA demonstrates useful principles, especially schema validation, but its automatic task discovery, dependency graph and generated resources solve a larger orchestration problem than this slice requires.

## Consequences

### Positive

- one authoritative persisted schema contract;
- reusable contract-to-Spark/Delta validation;
- explicit drift failures;
- safe opt-in evolution path;
- metadata becomes executable instead of documentation-only;
- clearer separation of responsibilities;
- foundation can extend to Silver/Gold without coupling them to BronzeWriter.

### Negative / cost

- generic BronzeWriter constructor/API may change;
- existing Bronze dataset configs may need mechanical migration;
- lifecycle requires new tests and workspace smoke validation;
- schema migration beyond additive nullable columns remains manual by design.

## Implementation constraints

- no generalized schema migration engine in this feature;
- no automatic YAML generation;
- no automatic dependency discovery;
- no hidden environment/catalog resolution in DatasetContract;
- all automatic evolution must be logged and testable.

## Validation

The decision is considered correctly implemented when:

1. GDP has an executable persisted contract;
2. table creation is delegated out of BronzeWriter;
3. compatible tables pass inspection;
4. drift fails with evolution disabled;
5. additive nullable evolution works only when explicitly enabled;
6. unsupported changes fail even when evolution is enabled;
7. metadata/comments/tags are reconciled safely;
8. existing Bronze write behavior remains green.
