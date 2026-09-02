# Olist Customers Bronze

## Scope

This feature modernizes the existing Olist Customers Bronze snapshot without
moving Silver business logic into Bronze.

The source is the authoritative CSV snapshot:

```text
/Volumes/<catalog>/bronze/raw_storage/raw/olist/e_commerce/olist_customers_dataset.csv
```

The feature reuses the platform's existing file-snapshot ingestion, first-class
Data Quality, administrative Control Plane, Databricks Asset Bundle and
deployment-smoke patterns.

## Gate status

- Discovery: complete.
- Requirements: complete.
- Technical Design: complete.
- Impact Analysis: complete.
- Implementation Plan: accepted for implementation.
- Implementation: pending at this checkpoint.
- Runtime Validation: pending.

No new platform architecture or ADR is required.

## Discovery evidence

Discovery was executed read-only against the DEV source snapshot.

| Check | Evidence |
| --- | --- |
| Source rows | 99,441 |
| Source columns | 5 expected, no missing or unexpected columns |
| Source types | all five columns read as `STRING` |
| `customer_id` | 99,441 non-null, 99,441 distinct, 0 duplicate groups |
| `customer_unique_id` | 96,096 distinct |
| Repeat-customer evidence | 2,997 unique IDs map to multiple `customer_id` values |
| Maximum `customer_id` values per `customer_unique_id` | 17 |
| Exact duplicate rows | 0 |
| Null values | 0 across all five source columns |
| Blank/whitespace-only values | 0 across all five source columns |
| Leading-zero ZIP prefixes | 23,995 rows |
| Non-digit ZIP prefixes | 0 |
| ZIP prefixes not exactly 5 characters | 0 |
| Distinct states | 27 |
| City/state trim differences | 0 |
| Basic city/state encoding symptoms | 0 |
| Distinct content hashes | 99,441 |

The deterministic snapshot signature observed during Discovery was:

```text
row_count=99441
distinct_row_hashes=99441
row_hash_sum=-595971771399300285112
```

One static CSV does not prove source refresh frequency. No ingestion cadence is
inferred from file modification time.

## Requirements

1. Bronze remains source-faithful: source business values stay `STRING`.
2. The persisted grain is one source row per `customer_id`.
3. `customer_id` remains the Bronze key and must be non-null and unique.
4. `customer_unique_id` must not be used as the Bronze key and must not be
   deduplicated: repeat identities are valid downstream evidence for Silver.
5. `customer_zip_code_prefix` must remain a string so leading zeroes are
   preserved.
6. The authoritative snapshot continues to use `FULL_REPLACE` semantics.
7. Empty or structurally invalid snapshots fail before the protected Bronze
   write.
8. Customers adopts first-class pre-write Data Quality and persists quality
   evidence to the administrative Control Plane.
9. The ingestion run persists execution evidence and records extracted,
   evaluated and written counts.
10. Runtime source, target and administrative tables are explicit deployment
    parameters; application code must not hardcode DEV/STG/PRD object names.
11. No synthetic `dt_base`, business date or source-frequency assumption is
    introduced in Bronze.
12. No partitioning or clustering is introduced for this bounded 99k-row
    authoritative snapshot.

## Data Quality contract

The implementation uses blocking `ERROR` rules for discovered technical
invariants:

- `CUSTOMERS-DQ01`: authoritative snapshot is non-empty;
- `CUSTOMERS-DQ02`: `customer_id` is not null;
- `CUSTOMERS-DQ03`: `customer_id` is unique;
- `CUSTOMERS-DQ04`: `customer_unique_id`, `customer_zip_code_prefix`,
  `customer_city` and `customer_state` are not null;
- `CUSTOMERS-DQ05`: `customer_zip_code_prefix` contains exactly five decimal
  digits.

There is intentionally no uniqueness rule on `customer_unique_id`: Discovery
found 2,997 repeated identities, with as many as 17 source customer IDs for one
unique customer ID.

There is also no Bronze normalization, deduplication by `customer_unique_id`,
city/state standardization or cross-dataset relationship rule.

## Technical Design

The runtime flow is:

1. DAB resolves source and destination object names from the deployment target;
2. a run ID and JSON execution scope are created;
3. `ExecutionRunTracker` starts the administrative execution record;
4. `OlistCsvSnapshotReader` reads the authoritative CSV and attaches source-file
   lineage;
5. `DataQualityRunner` evaluates the Customers DQ contract;
6. `QualityResultWriter` persists rule-level evidence;
7. blocking DQ failures reject the run and prevent the write;
8. accepted batches reach `BronzeWriter.write_checked()` using the existing
   Customers `DatasetContract` and `FULL_REPLACE` strategy;
9. the execution run is completed with written-record metrics.

The existing Customers persisted contract remains source-faithful and the
feature does not add a physical layout. The DQ layer owns the newly formalized
source-value invariants rather than introducing Silver transformations.

## Impact Analysis

### Code

- add a Customers-specific `DataQualityContract`;
- modernize `olist_customers_ingestion.py` to use the first-class DQ and Control
  Plane path;
- keep the shared reader, ingestion service and `BronzeWriter` unchanged.

### Delivery

- add an `olist-customers` packaged entry point;
- add a Databricks Asset Bundle Customers job;
- add Customers to deployment-smoke coverage;
- verify the packaged entry point in CI.

### Tests

- unit-test the Customers DQ contract;
- integration-test valid, duplicate-key, missing-value and malformed-ZIP
  behavior;
- update job-composition tests for the Control Plane/DQ dependencies;
- rely on existing shared service/writer tests for write-gate behavior.

### Data and contracts

- no business-column type conversion;
- no key change;
- no new source columns;
- no partition/clustering change;
- no Silver/Gold model change;
- no new ADR.

### Operational risk

The principal migration risk is replacing the legacy direct write path with the
checked-batch path. This is mitigated by reusing the already delivered MQL and
Closed Deals pattern, automated tests, deployment-smoke validation and a DEV
runtime execution before promotion.

## Implementation plan

1. add the Customers DQ contract and tests;
2. wire the Customers job to execution tracking and persisted DQ results;
3. add packaging, DAB resource and smoke configuration;
4. extend CI packaged-entry-point validation;
5. run the repository CI suite;
6. deploy/run the Customers job in DEV;
7. validate target table and Control Plane evidence;
8. only after runtime evidence is green, mark the feature `DONE` and promote via
   the normal topic-branch -> `dev` -> `main` path.

## Acceptance criteria

Implementation is complete when:

- repository CI is green;
- DAB validates for DEV/STG/PRD;
- the Customers job exists in the bundle and packaged wheel;
- a DEV run finishes successfully;
- exactly 99,441 source rows are evaluated and written for the current snapshot;
- `customer_id` remains complete and unique;
- all five blocking Customers DQ rules pass;
- 23,995 leading-zero ZIP rows remain representable as strings;
- target layout remains unpartitioned and unclustered;
- `execution_runs` and `data_quality_results` contain the run evidence.

Runtime evidence is intentionally not predeclared as successful in this design
record; it must be captured from an actual DEV run.
