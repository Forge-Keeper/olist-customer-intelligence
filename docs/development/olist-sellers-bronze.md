# Olist Sellers Bronze

## Scope

This feature adds production-grade Bronze ingestion for `olist_sellers_dataset.csv` while preserving source values and reusing the existing Olist CSV snapshot ingestion path.

Source path pattern:

```text
/Volumes/<catalog>/bronze/raw_storage/raw/olist/e_commerce/olist_sellers_dataset.csv
```

Target table pattern:

```text
<catalog>.bronze.olist_sellers
```

## Gate status

- Discovery: complete.
- Requirements: complete.
- Technical Design: complete.
- Impact Analysis: complete.
- Implementation Plan: approved.
- Implementation: in progress.
- Runtime Validation: pending.
- STG Promotion: pending.
- PRD Promotion: pending.

No new platform architecture or ADR is required.

## Discovery evidence

Read-only discovery ran against the DEV source snapshot.

Observed source:

```text
row_count=3095
columns=seller_id,seller_zip_code_prefix,seller_city,seller_state
all_source_types=string
size_bytes=174703
```

All four columns had zero nulls, zero blanks and zero trim differences.

### Grain and key evidence

`seller_id` is complete and unique in the authoritative snapshot:

```text
distinct_seller_id=3095
seller_id_nulls=0
seller_id_blanks=0
duplicate_groups=0
duplicate_excess=0
```

The accepted Bronze grain is one row per `seller_id`, with `seller_id` as the logical key.

### ZIP and text evidence

`seller_zip_code_prefix` is source text, not a numeric measure:

```text
distinct_zip_prefix=2246
leading_zero_rows=1027
non_digit_rows=0
non_5_char_rows=0
```

ZIP must remain `string` so leading zeroes are preserved.

`seller_city` had 611 distinct raw values and `seller_state` had 23. Neither showed trim differences or basic encoding symptoms. Bronze does not normalize these values.

### Duplicate and snapshot evidence

No exact duplicate rows were observed.

Deterministic content signature:

```text
row_count=3095
distinct_row_hashes=3095
row_hash_sum=178364510235517853568
```

One static CSV does not prove refresh cadence, so no business date or cadence assumption is introduced.

### Relationship evidence

The sibling `olist_order_items_dataset.csv` contained 112,650 rows and 3,095 distinct `seller_id` values. Discovery observed:

```text
order_item_seller_ids_missing_from_sellers=0
seller_ids_not_used_by_order_items=0
```

This is descriptive relationship evidence for downstream modeling only. Bronze does not add a blocking cross-dataset foreign-key rule.

## Requirements

### Functional

1. Read the Sellers CSV source as strings.
2. Require the four discovered source columns.
3. Preserve source values without city/state normalization.
4. Persist `source_file` plus the platform-managed Bronze ingestion timestamp.
5. Use one row per `seller_id` and enforce `seller_id` completeness/uniqueness before write.
6. Preserve five-character ZIP strings including leading zeroes.
7. Persist first-class Data Quality evidence and execution lifecycle evidence in the environment-specific Control Plane.
8. Reject blocking DQ failures before the protected Bronze write.
9. Expose Sellers as a packaged CLI entry point and DAB job for DEV/STG/PRD.
10. Add targeted deployment smoke coverage.

### Non-goals

- no Silver normalization or deduplication;
- no city/state canonicalization;
- no join to geolocation or order items during Bronze ingestion;
- no cross-dataset FK blocking rule;
- no `dt_base` or inferred source cadence;
- no partitioning or clustering for this bounded 3,095-row snapshot;
- no new shared platform abstraction.

## Technical Design

### Dataset contract

Business columns remain strings:

- `seller_id` — non-null logical key;
- `seller_zip_code_prefix` — source string;
- `seller_city` — source string;
- `seller_state` — source string;
- `source_file` — source file metadata;
- platform-managed `ingestion_timestamp`.

Write strategy: `FULL_REPLACE`.

Physical layout: no partition columns and no clustering columns.

### Data Quality contract

All accepted Sellers rules are blocking `ERROR` rules:

- `SELLERS-DQ01` — snapshot must be non-empty;
- `SELLERS-DQ02` — `seller_id` must not be null;
- `SELLERS-DQ03` — `seller_id` must be unique;
- `SELLERS-DQ04` — ZIP, city and state must not be null;
- `SELLERS-DQ05` — ZIP prefix must match exactly five decimal digits.

No uniqueness requirement applies to ZIP, city or state.

### Runtime composition

Reuse the existing components:

```text
OlistCsvSnapshotReader
  -> OlistSnapshotIngestionService
     -> DataQualityRunner / QualityResultWriter
     -> BronzeWriter.write_checked()
     -> ExecutionRunTracker
```

The executable job owns composition only and receives explicit source, target and Control Plane table arguments.

## Impact Analysis

Expected changes are local to the Sellers vertical slice plus deployment registration:

- new Sellers DatasetContract;
- new Sellers DataQualityContract;
- new Sellers ingestion job;
- new DAB job resource;
- new unit/integration tests;
- new deployment smoke manifest entry;
- new package entry point;
- CI packaged-entrypoint verification;
- Sellers discovery and delivery documentation.

No existing table schema, platform API or architectural boundary changes.

### Risks

- malformed or incomplete future snapshots must be rejected before replacement;
- source ZIP conversion to numeric would destroy leading zeroes, so source and persisted type remain string;
- cross-dataset relationship evidence may change independently and is intentionally not a Bronze write gate;
- environment source files must exist in STG/PRD before their deployment smokes can pass.

## Implementation Plan

1. Record Discovery and approved design gates.
2. Add Sellers persisted DatasetContract.
3. Add Sellers first-class blocking DQ contract.
4. Add executable Sellers job using existing Olist snapshot components.
5. Add unit and integration tests for contract, DQ and job composition.
6. Register package entry point, DAB job and deployment smoke.
7. Update CI packaged entrypoint verification.
8. Run repository CI/static/build validation.
9. Execute authoritative DEV positive-path runtime validation.
10. Execute controlled DEV rejection proving `records_written=0` and unchanged protected target.
11. Promote through DEV -> STG -> PRD using the repository immutable-artifact path.
12. Record final runtime evidence and mark the feature DONE.

## Acceptance criteria

The feature can be marked DONE only when:

- accepted contracts and non-goals are implemented;
- local/CI validation is green;
- DAB validates for intended targets;
- authoritative DEV Sellers ingestion succeeds;
- all five blocking DQ rules pass on the authoritative snapshot;
- target contains the expected source-faithful Sellers rows and preserves ZIP leading zeroes;
- a controlled duplicate-key batch is persisted as rejected with zero records written and leaves the protected target unchanged;
- STG deployment smoke executes Sellers successfully;
- PRD promotion uses the exact staging-approved wheel and Sellers production smoke succeeds;
- final evidence is recorded in GitHub.
