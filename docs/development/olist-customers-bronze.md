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
- Implementation Plan: complete.
- Implementation: complete.
- Runtime Validation: complete in DEV.
- Promotion: pending PR approval and the normal delivery flow.

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

The principal migration risk was replacing the legacy direct write path with the
checked-batch path. The delivered implementation mitigates that risk by reusing
the established platform pattern, automated tests, deployment-smoke validation,
a successful DEV runtime execution and a controlled DEV rejection proving that
a blocking DQ failure cannot replace the valid Bronze target.

## Implementation result

The delivered feature includes:

1. Customers first-class DQ contract and tests;
2. execution tracking and persisted rule-level DQ evidence;
3. protected checked-batch `FULL_REPLACE` writing;
4. packaged `olist-customers` entry point;
5. DAB Customers job and deployment-smoke coverage;
6. packaged-entry-point CI validation;
7. strengthened Databricks post-write validation;
8. real DEV positive-path and controlled rejection evidence.

## DEV runtime validation

### Authoritative snapshot

The deployed DEV Customers job completed successfully with logical run ID:

```text
1e270fd6-b768-4bc6-8b76-9412048126e7
```

Persisted execution evidence:

```text
status=SUCCEEDED
quality_status=PASSED
records_extracted=99441
records_evaluated=99441
records_written=99441
last_stage=COMPLETE
```

All five Customers DQ rules persisted `PASS`. The resulting Bronze table also
proved:

```text
row_count=99441
distinct_customer_ids=99441
null_customer_ids=0
required_attribute_null_rows=0
invalid_zip_rows=0
leading_zero_zip_rows=23995
partitionColumns=[]
clusteringColumns=[]
```

### Controlled write-gate proof

A temporary DEV target was first seeded through a valid two-row Customers batch.
The baseline logical run ID was:

```text
521e646a-10fd-42cb-9435-cabcc7652c37
```

Its persisted execution evidence was:

```text
status=SUCCEEDED
quality_status=PASSED
records_extracted=2
records_evaluated=2
records_written=2
last_stage=COMPLETE
```

A subsequent deliberately invalid batch duplicated `customer_id`. The canonical
rejection evidence used for this feature is logical run ID:

```text
8d00ca97-0661-4852-8903-b24687c9ab0d
```

The Control Plane persisted:

```text
status=REJECTED
quality_status=FAILED
records_extracted=2
records_evaluated=2
records_written=0
last_stage=QUALITY
error_stage=QUALITY
error_type=DataQualityRejectedError
error_message=Blocking Data Quality rules failed: CUSTOMERS-DQ03
```

`CUSTOMERS-DQ03` persisted `FAIL` with one duplicate group and one duplicate
excess row, while the other four rules persisted `PASS`. After rejection, the
temporary target still contained exactly the original two distinct customer IDs,
proving that the blocking failure occurred before the protected write.

A repeated controlled rejection produced the same terminal state and was not
needed as the canonical acceptance record.

## Acceptance criteria

DEV implementation and runtime validation are complete:

- repository CI is green for the implementation checkpoint;
- DAB validates for DEV/STG/PRD;
- the Customers job exists in the bundle and packaged wheel;
- the authoritative DEV run finished successfully;
- exactly 99,441 source rows were evaluated and written for the validated
  snapshot;
- `customer_id` remained complete and unique;
- all five blocking Customers DQ rules passed on the authoritative snapshot;
- 23,995 leading-zero ZIP rows remained representable as strings;
- target layout remained unpartitioned and unclustered;
- `execution_runs` and `data_quality_results` contain the positive-path evidence;
- a controlled duplicate-key batch was persisted as `REJECTED` with
  `records_written=0`;
- the controlled target remained unchanged after rejection.

Promotion beyond the feature branch remains a separate delivery decision and
must follow repository branch governance and approval gates.
