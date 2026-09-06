# Olist Geolocation Bronze

## Objective

Land `olist_geolocation_dataset.csv` in Bronze while preserving the source snapshot exactly enough for later Silver geospatial and textual normalization.

## Source profiling

DEV source:

```text
/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_geolocation_dataset.csv
```

Observed columns:

- `geolocation_zip_code_prefix`
- `geolocation_lat`
- `geolocation_lng`
- `geolocation_city`
- `geolocation_state`

Databricks `read_files` also exposed `_rescued_data`; it was null in the inspected sample and is reader metadata, not a persisted Bronze source column.

Profiling result:

- rows: `1,000,163`
- distinct ZIP prefixes: `19,015`
- distinct full source rows: `738,332`
- null ZIP: `0`
- null latitude: `0`
- null longitude: `0`
- null city: `0`
- null state: `0`

The source therefore contains both repeated ZIP prefixes and exact duplicate observations. A sampled exact duplicate was also observed directly. ZIP prefix is not a row key and the complete source tuple is not unique.

## Identity decision

No artificial row identifier is created in Bronze.

Generating a hash would collapse exact duplicates, while adding an occurrence number would create an ordering-dependent identity for otherwise indistinguishable source rows. Both would invent semantics absent from the source.

The platform contract therefore allows an empty `key_columns` tuple only when the write strategy is `FULL_REPLACE`. MERGE and REPLACE_WHERE datasets still require explicit key columns.

This keeps the Geolocation snapshot keyless while preserving existing key guarantees for incremental datasets.

## Bronze contract

Target:

```text
${catalog}.bronze.olist_geolocation
```

Persisted source values remain strings:

- ZIP prefix: string
- latitude: string
- longitude: string
- city: string
- state: string
- `source_file`: string
- managed `ingestion_timestamp`: timestamp

Write strategy: `FULL_REPLACE`.

No partitioning or clustering is introduced for this snapshot in the initial Bronze contract.

## Data Quality

Blocking rules:

- `GEOLOCATION-DQ01`: snapshot is non-empty;
- `GEOLOCATION-DQ02`: all five source columns are non-null;
- `GEOLOCATION-DQ03`: ZIP prefix has numeric source shape;
- `GEOLOCATION-DQ04`: latitude/longitude parse to valid coordinate ranges.

Observation-only rule:

- `GEOLOCATION-DQ05`: count state values that are not two uppercase letters.

There is deliberately no uniqueness rule. Duplicate rows are source facts and must survive Bronze persistence.

## DEV runtime acceptance

Runtime acceptance was completed against `dev.bronze.olist_geolocation` after the feature was merged into `dev`.

First execution:

- Databricks job: `[dev bruno_cavi] olist_geolocation`;
- run ID: `788438005360116`;
- status: `SUCCESS`;
- source rows read: `1,000,163`;
- persisted rows: `1,000,163`;
- write strategy observed in runtime logs: `FULL_REPLACE`.

Post-write integrity check:

- rows: `1,000,163`;
- distinct ZIP prefixes: `19,015`;
- distinct full source rows: `738,332`;
- null `source_file`: `0`;
- null `ingestion_timestamp`: `0`.

The integrity result confirms that exact source duplicates remain present in Bronze rather than being collapsed.

Idempotence was then exercised with a second execution:

- run ID: `956084946863022`;
- status: `SUCCESS`;
- source rows read: `1,000,163`;
- persisted rows reported by the job: `1,000,163`;
- write strategy observed in runtime logs: `FULL_REPLACE`.

The same integrity query after the rerun returned exactly the same state:

- rows: `1,000,163`;
- distinct ZIP prefixes: `19,015`;
- distinct full source rows: `738,332`;
- null `source_file`: `0`;
- null `ingestion_timestamp`: `0`.

DEV acceptance is therefore complete for source fidelity, duplicate preservation, managed metadata completeness, and repeatable `FULL_REPLACE` behavior.

## Bronze non-goals

The Bronze job does not:

- deduplicate observations;
- collapse multiple coordinates per ZIP prefix;
- normalize `sao paulo` and `são paulo`;
- canonicalize city names or state codes;
- convert coordinates to numeric persisted types;
- choose a representative coordinate per ZIP prefix;
- join customers, sellers, IBGE, ANP, or other datasets.

Those are Silver or downstream modeling concerns.
