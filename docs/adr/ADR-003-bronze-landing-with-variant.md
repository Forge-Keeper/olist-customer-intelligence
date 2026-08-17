# ADR-003: Use Bronze as the First Persistent Landing Layer with VARIANT Payloads

- **Status:** Accepted
- **Date:** 2026-08-17
- **Decision owners:** Olist Customer Intelligence
- **Scope:** Bronze ingestion architecture and the Weather vertical slice

## Context

The Weather ingestion flow previously persisted the original Open-Meteo response in a dedicated RAW table and then parsed the same in-memory response into a rigid, typed Bronze table.

That design preserved source payloads, but it duplicated persistence responsibilities and coupled the first Bronze write to a closed schema containing known weather metrics.

The project needs a Bronze contract that:

- remains close to source data;
- preserves semi-structured fields without requiring a table schema change for every new source attribute;
- keeps one row per natural ingestion grain;
- supports idempotent writes and explicit reprocessing;
- can be reused by future datasets without embedding Weather-specific keys or layout rules in platform code.

## Decision

The project will not maintain a separate RAW layer for this ingestion path.

Bronze becomes the first persistent landing layer.

For daily Weather data, each Bronze row represents one source observation day and contains:

- `dt_base` as `DATE`;
- `payload` as `VARIANT`;
- `request_id`;
- `requested_latitude`;
- `requested_longitude`;
- `ingestion_timestamp`.

The daily payload remains as close as practical to the source representation. The only structural transformation required before the first persistence is splitting the multi-day API response into one payload per day and extracting `dt_base`.

Semantic typing, normalization, Data Quality rules, and business interpretation are deferred to downstream processing.

## Dataset Contract

Bronze datasets declare their persistence contract through a typed configuration object.

The contract includes:

- primary key columns;
- required columns;
- clustering columns;
- partition columns;
- normal write strategy.

Primary key columns represent the logical identity of a Bronze row and are also the idempotency key used by the ingestion infrastructure.

For Weather:

```text
PRIMARY KEY
(dt_base, requested_latitude, requested_longitude)

CLUSTER BY
(dt_base)

PARTITION BY
none

NORMAL WRITE STRATEGY
MERGE
```

The application validates non-null and non-duplicated primary keys inside the incoming batch. Catalog primary-key constraints, if introduced later, are not relied upon for enforcement.

## Normal Ingestion

Normal ingestion is idempotent.

Existing rows are matched by the declared primary key and updated; new keys are inserted.

```text
source API
    |
    v
WeatherDailyExtractor
    |
    v
Bronze payload + metadata
    |
    v
MERGE by declared primary key
```

The previous `overwrite` boolean is removed from normal ingestion because reprocessing is a separate operational intent.

## Explicit Reprocessing

Reprocessing requires the caller to explicitly provide the scope to rebuild.

For Weather, the scope contains requested coordinates and a date interval.

Scoped reprocessing uses selective replacement with `replaceWhere`.

The Bronze table is not used as the source of truth for deciding the historical universe to rebuild. A future canonical coverage configuration may enable a parameterless full-reprocess operation, but that is outside this decision.

If a reprocessing request returns zero daily records, the operation fails before replacement and preserves the existing Bronze scope.

A future policy may allow an authoritative empty response to clear a scope, but the initial behavior intentionally favors data preservation.

## VARIANT

`payload` uses the Databricks `VARIANT` type so source attributes can evolve without turning every source field into a top-level Bronze column.

The payload is created from JSON with `parse_json`.

The project requires Databricks Runtime 15.4 LTS or newer for reading and writing Delta tables with `VARIANT` support.

`payload` must not be configured as a partitioning or clustering column. Physical layout must use extracted typed columns such as `dt_base`.

Enabling `VARIANT` on a Delta table upgrades the Delta table writer protocol, so compatibility with external Delta clients must be considered if such clients are introduced later.

## Generic Bronze Infrastructure

Reusable persistence behavior belongs to `platform/delta/bronze`.

Source-specific extraction and metadata enrichment remain in their domain.

The platform layer must not know Weather field names or Open-Meteo semantics.

The initial implementation supports a configurable write-strategy contract while implementing only strategies justified by current use cases.

## Alternatives Considered

### Keep RAW + structured Bronze

Rejected for the current architecture because it maintains two first-stage persistence responsibilities and requires the initial Bronze contract to evolve whenever source fields change.

### Store the entire API response as one Bronze row

Rejected because the established Weather grain and `dt_base` semantics are daily. One API response can contain many observation days.

### Use JSON STRING as the Bronze payload

Viable and simpler, but not selected because the project specializes in Databricks and `VARIANT` provides native semi-structured storage and downstream query capabilities without closing the schema.

### Use STRUCT or MAP as the Bronze payload

Rejected for the first landing layer because those representations introduce a stronger schema contract than required at this stage.

### Continue using `overwrite=True` for reprocessing

Rejected because a boolean mixes normal idempotent ingestion with the separate intent of rebuilding an explicit scope.

## Consequences

### Positive

- removes the duplicate RAW persistence layer;
- preserves new source attributes inside `payload`;
- keeps the first persistent schema small and stable;
- separates source extraction from generic Delta persistence;
- makes logical identity and idempotency explicit;
- makes reprocessing intent explicit instead of overloading normal ingestion;
- creates reusable Bronze infrastructure for future datasets.

### Negative / Trade-offs

- stronger dependency on Databricks because `VARIANT` is a platform-specific capability;
- local Spark tests cannot fully validate Databricks Delta `VARIANT` behavior;
- a daily payload is structurally reconstructed from the original multi-day API response rather than persisted byte-for-byte;
- full historical rebuild still requires the caller to supply the intended universe;
- `MERGE` and scoped replacement semantics require careful primary-key and scope definitions.

## Testing

Local tests should validate:

- daily extraction and preservation of unexpected source fields;
- `dt_base` parsing and required-grain behavior;
- Bronze configuration validation;
- non-null and non-duplicated primary-key validation;
- generic MERGE condition generation;
- explicit scoped-reprocess predicate generation;
- empty reprocess responses fail before a replacement is attempted;
- Weather code delegates persistence to the generic Bronze infrastructure.

Databricks validation should confirm:

- `payload` is physically stored as `VARIANT`;
- the Delta table supports VARIANT;
- `dt_base` is `DATE`;
- the table has no Hive partition columns;
- Liquid Clustering is configured on `dt_base`;
- repeated normal ingestion is idempotent through MERGE;
- scoped reprocessing replaces only the explicitly supplied scope.

## Migration

No migration of the existing development Bronze schema is required.

Any existing Bronze table for the affected dataset will be dropped/recreated and source data will be ingested again using the new contract.

## Revisit Criteria

Review this decision if:

- a canonical source-coverage configuration is introduced;
- an authoritative-empty reprocessing policy is required;
- a second Bronze representation becomes justified before Silver;
- external Delta clients require a compatibility profile that conflicts with the VARIANT table feature;
- another source demonstrates that the current Bronze dataset contract is insufficient.
