# Olist Product Category Name Translation Bronze

## Scope

Production-grade Bronze ingestion for the physical source:

```text
product_category_name_translation.csv
```

Source path pattern:

```text
/Volumes/<catalog>/bronze/raw_storage/raw/olist/e_commerce/product_category_name_translation.csv
```

Target table pattern:

```text
<catalog>.bronze.olist_product_category_name_translation
```

## Gate status

- Discovery: complete.
- Requirements: complete.
- Technical Design: complete.
- Impact Analysis: complete.
- Implementation Plan: complete.
- Implementation: complete and merged through the governed promotion path.
- CI/static validation: complete.
- DEV runtime validation: complete.
- PR to `dev`: complete; PR #66 merged.
- Promotion `dev -> main`: complete; PR #67 merged.
- STG: complete; Deploy STG run `33915255555` succeeded.
- PRD: complete; Deploy PRD run `33923138081` succeeded.
- Closeout: operational evidence complete; documentation closeout pending human review/merge.

No new shared abstraction or ADR is required.

## Discovery evidence

Read-only Discovery ran against the physical DEV snapshot:

```text
path=dbfs:/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/product_category_name_translation.csv
row_count=71
size_bytes=2613
column_count=2
```

Observed schema:

```text
product_category_name:string
product_category_name_english:string
```

Both columns are complete in the observed snapshot:

| Column | Nulls | Blanks | Distinct raw | Distinct trim/lower | Trim differences |
|---|---:|---:|---:|---:|---:|
| `product_category_name` | 0 | 0 | 71 | 71 | 0 |
| `product_category_name_english` | 0 | 0 | 71 | 71 | 0 |

`product_category_name` is complete and unique:

```text
distinct_count=71
null_count=0
blank_count=0
duplicate_group_count=0
duplicate_row_excess=0
```

No exact duplicate rows or basic encoding/mojibake indicators were observed.

Deterministic content signature:

```text
row_count=71
distinct_row_hashes=71
row_hash_sum=24255282855097946299
```

### Relationship evidence

The physical DEV Products source has 73 distinct non-null categories, while the
translation source has 71. The two Products categories without translation are:

```text
pc_gamer
portateis_cozinha_e_preparadores_de_alimentos
```

There are no translation-only categories relative to the observed Products
snapshot.

Architecture decision: this referential incompleteness is **not a Bronze
validity concern**. Bronze owns source-faithful ingestion and internal source
integrity. Resolving coverage between Products and the translation mapping is a
Silver responsibility. Therefore the Bronze runtime does not read Products and
does not define a cross-dataset DQ rule.

### Snapshot semantics

One physical CSV snapshot does not prove a business date, cadence or incremental
model. No `dt_base`, partitioning or clustering is introduced.

## Requirements

### Functional

1. Read exactly the two physical business columns as strings.
2. Preserve source column names and values without normalization or translation logic.
3. Persist `source_file` plus platform-managed `ingestion_timestamp`.
4. Accept one row per `product_category_name` as the Bronze logical grain.
5. Protect snapshot non-emptiness, key completeness, key uniqueness and English-translation completeness.
6. Reject blank values in either business column before the protected write.
7. Persist first-class DQ results and execution lifecycle evidence in the Control Plane.
8. Use the existing Olist CSV snapshot runtime and `BronzeWriter.write_checked()` path.
9. Expose the dataset as a packaged CLI entry point and DAB job for DEV/STG/PRD.
10. Add deployment smoke coverage and a Databricks persisted-table validation script.

### Non-goals

- no join to Products during Bronze ingestion;
- no translation-coverage write gate;
- no fabrication/imputation of the two missing translations;
- no trimming, lowercasing, renaming or business normalization;
- no inferred `dt_base`, cadence or incremental semantics;
- no partitioning or clustering;
- no new shared platform abstraction.

## Technical Design

### Dataset contract

Business columns:

```text
product_category_name:string NOT NULL
product_category_name_english:string NOT NULL
```

Platform columns:

```text
source_file:string
ingestion_timestamp:timestamp
```

Logical key:

```text
product_category_name
```

Write strategy: `FULL_REPLACE`.

Physical layout: no partition columns and no clustering columns.

### Data Quality contract

| Rule | Evidence | Purpose | Severity | Behavior / failure impact |
|---|---|---|---|---|
| `CATEGORY-TRANSLATION-DQ01` snapshot non-empty | 71 rows observed | prevent replacing a valid target with an empty snapshot | ERROR | blocking; `records_written=0` |
| `CATEGORY-TRANSLATION-DQ02` key non-null | 0 null keys observed; accepted grain | prevent unidentified mapping rows | ERROR | blocking; `records_written=0` |
| `CATEGORY-TRANSLATION-DQ03` key unique | 71 distinct keys / 0 duplicates | prevent ambiguous source-category mappings | ERROR | blocking; `records_written=0` |
| `CATEGORY-TRANSLATION-DQ04` English translation non-null | 0 null translations observed; translation is the file payload | prevent unusable mapping rows | ERROR | blocking; `records_written=0` |
| `CATEGORY-TRANSLATION-DQ05` both values non-blank | 0 blanks observed | detect lexical completeness drift not covered by null checks | ERROR | blocking; `records_written=0` |

No rule evaluates relationship coverage against Products.

### Runtime composition

```text
OlistCsvSnapshotReader
  -> OlistSnapshotIngestionService
     -> DataQualityRunner / QualityResultWriter
     -> BronzeWriter.write_checked()
     -> ExecutionRunTracker
```

Runtime dataset identifier:

```text
olist_product_category_name_translation
```

## Impact Analysis

Changes are isolated to this vertical slice and deployment registration:

- DatasetContract;
- DataQualityContract;
- executable ingestion job;
- package entry point;
- DAB resource;
- deployment smoke manifest;
- unit tests;
- Databricks persisted-table validation script;
- Discovery notebook and feature documentation.

No existing table schema, platform API, shared runtime abstraction or architectural
boundary is changed.

### Risks

- source schema drift will fail before persistence through the existing reader/contract path;
- duplicate, null or blank mapping rows will block `FULL_REPLACE`;
- the two untranslated Products categories remain a known Silver concern;
- STG/PRD promotion requires the physical source file to exist in the respective environment volumes.

## Implementation Plan

1. Close Discovery and architecture boundary decisions.
2. Add persisted DatasetContract and DQ contract.
3. Compose the ingestion job entirely from existing Olist snapshot runtime components.
4. Register CLI and DAB job.
5. Register deployment smoke coverage.
6. Add unit tests and Databricks persisted-table validation.
7. Run CI/static/build/bundle validation.
8. Deploy/run authoritative DEV positive path and validate target plus Control Plane evidence.
9. Run one controlled DQ rejection and prove the protected target is unchanged.
10. Open PR to `dev`; merge remains a human gate.
11. After merge and later main promotion, execute STG and human-authorized PRD gates.

## Implementation

Implemented on `feature/olist-product-category-translation-bronze`:

```text
src/olist_data_platform/domains/bronze/olist/product_category_name_translation_bronze_config.py
src/olist_data_platform/domains/bronze/olist/product_category_name_translation_quality.py
src/olist_data_platform/jobs/olist_product_category_name_translation_ingestion.py
resources/olist_product_category_name_translation.job.yml
scripts/validate_olist_product_category_name_translation_bronze_databricks.py
tests/unit/test_olist_product_category_name_translation_bronze_config.py
tests/unit/test_olist_product_category_name_translation_quality.py
tests/unit/test_olist_product_category_name_translation_ingestion_job.py
```

Deployment/packaging registration also updates:

```text
pyproject.toml
.github/workflows/ci.yml
deployment/smoke-jobs.yml
```

## DEV validation

Authoritative DEV validation is complete.

### Positive path and persisted target

The production-like DEV job completed successfully against the canonical source
snapshot. The persisted target `dev.bronze.olist_product_category_name_translation`
was validated after the write, confirming the expected Bronze contract and the
source-faithful snapshot persisted through the protected `FULL_REPLACE` path.

The successful execution also confirmed the Control Plane path for the dataset:
DQ evaluation completed before persistence and execution lifecycle evidence was
recorded for the run.

### Controlled negative path

A controlled duplicate-key fixture was executed against an isolated validation
source path. The run was rejected by:

```text
CATEGORY-TRANSLATION-DQ03
```

The rule correctly blocked the write with zero records written for the rejected
execution.

Target protection was explicitly verified: the previously valid persisted target
remained unchanged after the failed negative-path run. This proves that a duplicate
`product_category_name` cannot replace a healthy Bronze snapshot.

### DEV gate conclusion

DEV acceptance criteria are satisfied:

- positive path succeeds;
- persisted target is valid;
- DQ03 rejects duplicate logical keys;
- rejected execution does not mutate the protected target;
- branch CI `quality` check is green.

## Promotion and closeout evidence

The feature completed the governed Git and deployment path:

```text
feature/olist-product-category-translation-bronze
  -> PR #66 -> dev
  -> PR #67 -> main
  -> STG
  -> PRD
```

The stable production promotion commit is:

```text
20d995734f4c9f0d4bfab68fa8248940af041cec
```

### STG

Deploy STG run `33915255555` completed successfully for that commit. The workflow
validated and deployed the staging bundle, ran deployment smokes, captured the
promoted wheel manifest and retained the promotion artifact.

Retained STG artifact:

```text
stg-promotion-20d995734f4c9f0d4bfab68fa8248940af041cec
```

### PRD

The human-authorized Deploy PRD run `33923138081` completed successfully against
the same `main` commit and approved STG artifact. The workflow verified artifact
identity and digest, validated the production bundle, deployed the approved staging
wheel, ran production deployment smokes and retained production evidence.

Retained PRD artifact:

```text
prd-deployment-20d995734f4c9f0d4bfab68fa8248940af041cec
```

### Final conclusion

The Product Category Name Translation Bronze vertical slice is operationally
complete across DEV, STG and PRD. Source integrity protections, protected
`FULL_REPLACE`, deployment smokes and promotion evidence all completed successfully.

The known two-category translation coverage gap remains intentionally deferred to
Silver and is not a Bronze defect.
