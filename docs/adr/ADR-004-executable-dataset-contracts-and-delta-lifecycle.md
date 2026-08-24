# ADR-004 — Executable Dataset Contracts and Delta Table Lifecycle

- **Status:** Proposed
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Dataset contracts, Delta table lifecycle, governance metadata, Bronze write responsibility and schema evolution

## Context

The platform currently has a useful but narrow `BronzeDatasetConfig` containing logical keys, required columns, physical layout and write strategy. `BronzeWriter` validates batches and performs MERGE/FULL_REPLACE/reprocessing, but it also creates Delta tables and applies layout during creation.

Dataset-specific writers additionally contain Spark schema declarations. For IBGE GDP, the adapter has a transient `INPUT_SCHEMA`, while the persisted table contract is partially represented elsewhere. Table description, column comments, tags and explicit schema-drift behavior are not yet first-class platform concepts.

The DAB feature introduces isolated deployment environments and is the point at which persisted table definitions must become explicit enough to be validated consistently across `dev`, `stg` and `prd`.

A review of the mature SAFRA project confirmed the value of executable schema definitions and contract-versus-Unity-Catalog validation, but Olist should adopt those principles without copying SAFRA's heavier Task/orchestration framework.

Unity Catalog governance also introduces a durable requirement beyond table-level metadata. Governed tags can be applied to securable objects, including columns, and can participate in ABAC policies. Row-level governance is represented through row-filter policies rather than literal metadata tags attached to individual rows. The platform contract must therefore evolve toward table/column governed tags plus explicit row/column access-policy declarations, without encoding a false concept of row tags.

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
- approved table tags;
- approved column tags;
- schema-evolution policy.

The contract is the authoritative declaration of the persisted table schema and governance metadata for managed datasets.

### 2. Keep platform-managed columns explicit in the resolved contract

Columns injected by platform behavior, beginning with `ingestion_timestamp`, are not hidden from the table contract.

They are declared once as platform-managed columns and composed into the dataset's resolved contract rather than manually repeated in every domain dataset.

### 3. Separate Delta lifecycle from Bronze write semantics

Introduce a reusable `DeltaTableLifecycle` responsibility for:

- create/ensure table;
- physical layout application/validation;
- table inspection;
- schema compatibility checks;
- table description/comment reconciliation;
- table and column tag reconciliation;
- explicitly permitted schema evolution.

`BronzeWriter` remains responsible for:

- DataFrame preparation;
- platform-managed value injection;
- runtime batch validation;
- MERGE;
- FULL_REPLACE;
- explicit replaceWhere/reprocessing.

Table creation no longer belongs to `BronzeWriter`.

### 4. Treat governance metadata as executable contract state

Governance is not documentation-only.

The platform contract and lifecycle must support the capability to declare and reconcile:

- table-level tags;
- column-level tags;
- table descriptions;
- column comments.

The first slice only materializes tags that represent real durable facts. It must not invent PII, classification or sensitivity metadata merely to demonstrate functionality.

Where Unity Catalog governed tags are available and administratively configured, the platform should be able to reference/apply those governed tag assignments rather than relying only on free-form tags.

### 5. Preserve a future path to Gold row- and column-level governance

The contract model must not block future Gold requirements for fine-grained access control.

The intended future model is:

```text
DatasetContract
├── table tags
├── column tags
├── column mask policy references (future)
└── row filter policy references (future)
```

Literal "row tags" are not introduced because rows are not Unity Catalog securable objects that receive tags. Row-level governance is represented by row-filter/ABAC policies that evaluate row values and governed object attributes.

This feature does **not** implement a generalized ABAC policy engine. It establishes the metadata model and lifecycle boundary so a later Gold/governance feature can add policy references without redesigning the dataset contract.

### 6. Fail on schema drift by default

Schema drift is not silently accepted.

The default dataset policy is:

```text
schema evolution disabled
```

A mismatch between the declared persisted contract and an existing table fails before normal write execution.

### 7. Allow controlled evolution only through explicit opt-in

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

### 8. Preserve adapter-specific transient schemas where technically necessary

Single persisted schema source of truth does not forbid transient adapter schemas.

For example, an IBGE writer may construct a temporary `payload_json` string before parsing it into the final persisted `VARIANT payload`. Only avoidable duplication of the persisted contract is removed.

### 9. Do not treat logical nullability as an automatically enforced UC constraint

The contract records nullability, but the first lifecycle implementation does not assume Delta/Unity Catalog nullable metadata provides full relational enforcement.

Existing runtime validation remains responsible for real application invariants such as non-null logical keys.

## Alternatives considered

### Keep the current `BronzeDatasetConfig` only

Rejected because it cannot become the authoritative persisted schema/metadata contract without accumulating unrelated concerns and becoming a god object.

### Put all lifecycle behavior into `BronzeWriter`

Rejected because table state/governance and write semantics evolve independently and are reusable outside Bronze.

### Adopt unrestricted `mergeSchema`

Rejected because silent or broad schema mutation weakens the contract boundary and makes production drift difficult to govern.

### Model row-level governance as row tags

Rejected because Unity Catalog tags apply to securable objects such as catalogs, schemas, tables and columns, not individual rows. Row-level access should use row filters/ABAC policies.

### Reproduce the SAFRA Task framework

Rejected for this project stage. SAFRA demonstrates useful principles, especially schema validation, but its automatic task discovery, dependency graph and generated resources solve a larger orchestration problem than this slice requires.

## Consequences

### Positive

- one authoritative persisted schema contract;
- reusable contract-to-Spark/Delta validation;
- explicit drift failures;
- safe opt-in evolution path;
- table and column governance metadata becomes executable instead of documentation-only;
- future Gold row-filter/column-mask policy support has an explicit extension point;
- clearer separation of responsibilities;
- foundation can extend to Silver/Gold without coupling them to BronzeWriter.

### Negative / cost

- generic BronzeWriter constructor/API may change;
- all existing Bronze dataset configs must be mechanically migrated to the new contract model;
- lifecycle requires new tests and workspace smoke validation;
- governed-tag application depends on Unity Catalog account/workspace configuration and permissions;
- schema migration beyond additive nullable columns remains manual by design.

## Implementation constraints

- migrate all current `BronzeDatasetConfig` declarations in this feature; no compatibility layer is kept as the target design;
- no generalized schema migration engine in this feature;
- no generalized ABAC/row-filter/column-mask policy engine in this feature;
- no automatic YAML generation;
- no automatic dependency discovery;
- no hidden environment/catalog resolution in DatasetContract;
- all automatic evolution must be logged and testable;
- governance metadata reconciliation must be logged and testable.

## Validation

The decision is considered correctly implemented when:

1. all current Bronze datasets use the executable contract model;
2. GDP has a complete executable persisted contract;
3. table creation is delegated out of BronzeWriter;
4. compatible tables pass inspection;
5. drift fails with evolution disabled;
6. additive nullable evolution works only when explicitly enabled;
7. unsupported changes fail even when evolution is enabled;
8. table descriptions/comments/tags are reconciled safely;
9. column tags can be declared and reconciled by the lifecycle;
10. governance metadata support does not require a Gold-specific redesign later;
11. existing Bronze write behavior remains green.
