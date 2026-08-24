# ADR-003: Use Bronze as the First Persistent Landing Layer with VARIANT Payloads

- **Status:** Accepted
- **Date:** 2026-08-17
- **Decision owners:** Olist Customer Intelligence
- **Scope:** Bronze ingestion architecture for semi-structured API sources

## Context

The Weather ingestion flow previously persisted the original Open-Meteo response in a dedicated RAW table and then parsed the same in-memory response into a rigid, typed Bronze table.

That design preserved source payloads, but it duplicated persistence responsibilities and coupled the first Bronze write to a closed schema containing known source metrics.

The same concern applies to IBGE APIs. SIDRA and Localidades expose source-owned structures whose business attributes should not be normalized or strongly typed before the first persistent landing layer.

The project needs a Bronze contract that:

- remains as close as practical to source data;
- preserves semi-structured fields without requiring a table schema change for every new source attribute;
- keeps one row per natural ingestion grain;
- supports idempotent writes and explicit reprocessing where justified;
- extracts only the technical fields required for row identity, time semantics, layout, and operations;
- can be reused by future datasets without embedding source-specific field semantics in platform code.

## Decision

The project will not maintain a separate RAW persistence layer for these ingestion paths.

Bronze becomes the first persistent landing layer.

Each semi-structured API Bronze row contains:

- a source payload stored as `VARIANT`;
- `dt_base` with an explicit dataset-specific technical meaning;
- the minimum source-derived columns required for logical identity;
- request/ingestion metadata.

The payload remains as close as practical to the source representation. Semantic typing, normalization, Data Quality rules, historical reconstruction, and business interpretation are deferred to downstream processing.

### Weather

For daily Weather data, each row represents one source observation day and contains:

- `dt_base` as the observation date;
- `payload` as `VARIANT`;
- `request_id`;
- requested coordinates;
- `ingestion_timestamp`.

The only structural transformation required before persistence is splitting the multi-day response into the established daily grain and extracting the observation date.

### IBGE municipality population

For SIDRA municipality population, each row represents one municipality, reference year, and SIDRA variable. Bronze contains:

- `municipality_code` as source identity;
- `reference_year` preserved as a source string;
- `variable_code` as source identity;
- `dt_base` as January 1 of the reference year, used only as the annual technical competence date;
- the decoded SIDRA row preserved in `payload` as `VARIANT`;
- `request_id` and `ingestion_timestamp`.

Source values such as `Valor`, variable names, units, and territorial labels remain inside the payload in their source representation. Numeric typing and semantic interpretation belong downstream.

### IBGE Localidades

The Localidades endpoint is treated as a current source snapshot. Each row contains:

- `municipality_code` as source identity;
- `dt_base` as the snapshot capture date;
- the municipality object preserved in `payload` as `VARIANT`;
- `request_id` and `ingestion_timestamp`.

Bronze must not fabricate historical copies of the current Localidades response. Historical municipality modeling for analytical years belongs downstream.

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

For IBGE municipality population:

```text
PRIMARY KEY
(municipality_code, reference_year, variable_code)

CLUSTER BY
(dt_base)

PARTITION BY
none

NORMAL WRITE STRATEGY
MERGE
```

For IBGE Localidades:

```text
PRIMARY KEY
(municipality_code, dt_base)

CLUSTER BY
(dt_base)

PARTITION BY
none

NORMAL WRITE STRATEGY
MERGE
```

The application validates non-null and non-duplicated primary keys inside the incoming batch. Catalog primary-key constraints, if introduced later, are not relied upon for enforcement.

## Normal Ingestion

Normal ingestion is idempotent within the declared logical key.

Existing rows are matched by the declared primary key and updated; new keys are inserted.

For current-snapshot datasets such as Localidades, a later `dt_base` intentionally creates a new snapshot. Re-execution for the same snapshot date updates the same logical rows.

## Explicit Reprocessing

Reprocessing requires the caller to explicitly provide the scope to rebuild.

For Weather, the scope contains requested coordinates and a date interval and uses selective replacement with `replaceWhere`.

IBGE population and Localidades currently rely on idempotent `MERGE`; no separate reprocessing API is introduced until a concrete replay requirement justifies one.

The Bronze table is not used as the source of truth for deciding a historical universe to reconstruct.

## VARIANT

`payload` uses the Databricks `VARIANT` type so source attributes can evolve without turning every source field into a top-level Bronze column.

The payload is created from JSON with `parse_json`.

The project requires Databricks Runtime 15.4 LTS or newer for reading and writing Delta tables with `VARIANT` support.

`payload` must not be configured as a partitioning or clustering column. Physical layout must use extracted typed columns such as `dt_base`.

Enabling `VARIANT` on a Delta table upgrades the Delta table writer protocol, so compatibility with external Delta clients must be considered if such clients are introduced later.

## Generic Bronze Infrastructure

Reusable persistence behavior belongs to `platform/delta/bronze`.

Source-specific extraction of technical identity and time metadata remains in the source domain. Business normalization remains downstream.

The platform layer must not know Weather, SIDRA, or Localidades field semantics.

## Alternatives Considered

### Keep RAW + structured Bronze

Rejected for the current architecture because it maintains two first-stage persistence responsibilities and requires the initial Bronze contract to evolve whenever source fields change.

### Fully normalize API responses in Bronze

Rejected because it moves semantic typing and source interpretation into the landing layer, increases schema coupling, and loses fidelity to source-owned structures.

### Materialize historical Localidades rows from the current endpoint

Rejected because the endpoint is a current snapshot. Repeating that snapshot for historical analytical years creates derived data that does not belong in Bronze.

### Store entire API responses as one Bronze row

Rejected when the established natural grain is smaller than the response envelope. Weather is daily; SIDRA population is municipality/year/variable; Localidades is municipality/snapshot date.

### Use JSON STRING as the Bronze payload

Viable and simpler, but not selected because the project specializes in Databricks and `VARIANT` provides native semi-structured storage and downstream query capabilities without closing the schema.

### Use STRUCT or MAP as the Bronze payload

Rejected for the first landing layer because those representations introduce a stronger schema contract than required at this stage.

## Consequences

### Positive

- removes duplicate RAW persistence responsibility;
- preserves new source attributes inside `payload`;
- keeps the first persistent schema small and stable;
- separates source extraction from generic Delta persistence;
- makes logical identity and idempotency explicit;
- prevents historical or business modeling from leaking into Bronze;
- creates reusable Bronze infrastructure for future SIDRA datasets such as municipal GDP.

### Negative / Trade-offs

- stronger dependency on Databricks because `VARIANT` is platform-specific;
- local Spark tests cannot fully validate Databricks Delta `VARIANT` behavior;
- some technical fields are still extracted from source payloads to support identity and layout;
- consumers must perform explicit downstream parsing and typing;
- current Localidades snapshots alone do not provide authoritative historical municipality state.

## Testing

Local tests should validate:

- preservation of unexpected source fields;
- dataset-specific `dt_base` semantics;
- Bronze configuration validation;
- non-null and non-duplicated primary-key validation;
- generic MERGE condition generation;
- source-specific writers delegate persistence to generic Bronze infrastructure;
- source values intended to remain AS-IS are not prematurely typed.

Databricks validation should confirm:

- `payload` is physically stored as `VARIANT`;
- `dt_base` is `DATE`;
- the tables have no Hive partition columns;
- Liquid Clustering matches each dataset contract;
- repeated ingestion of the same logical scope is idempotent through `MERGE`;
- IBGE population retains the requested historical coverage;
- Localidades is persisted as real current snapshots rather than fabricated historical rows.

## Migration

Development Bronze tables affected by a contract change may be dropped/recreated and source data re-ingested before the feature is declared complete.

No production migration guarantee is implied while the portfolio project remains in active development.

## Revisit Criteria

Review this decision if:

- a canonical source-coverage configuration is introduced;
- an authoritative-empty reprocessing policy is required;
- a second Bronze representation becomes justified before Silver;
- external Delta clients require a compatibility profile that conflicts with the VARIANT table feature;
- a source demonstrates that its natural grain cannot be represented with a small stable technical envelope plus `VARIANT` payload;
- authoritative historical Localidades data becomes available and changes the downstream modeling strategy.
