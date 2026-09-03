# Olist Products Bronze

## Scope

This feature adds production-grade Bronze ingestion for
`olist_products_dataset.csv` while preserving the physical source values and
reusing the existing Olist CSV snapshot ingestion path.

Source path pattern:

```text
/Volumes/<catalog>/bronze/raw_storage/raw/olist/e_commerce/olist_products_dataset.csv
```

Target table pattern:

```text
<catalog>.bronze.olist_products
```

## Gate status

- Discovery: complete.
- Requirements: complete.
- Technical Design: complete.
- Impact Analysis: complete.
- Implementation Plan: approved through feature autopilot.
- Implementation: complete locally; validation in progress.
- Runtime Validation: pending DEV.
- STG Promotion: pending.
- PRD Promotion: pending.
- Feature status: IN PROGRESS.

No new platform abstraction or ADR is required.

## Discovery evidence

Read-only discovery ran against the physical DEV source snapshot:

```text
path=dbfs:/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_products_dataset.csv
row_count=32951
size_bytes=2379446
column_count=9
all_source_types=string
missing_expected_columns=[]
unexpected_columns=[]
```

The source columns are:

```text
product_id
product_category_name
product_name_lenght
product_description_lenght
product_photos_qty
product_weight_g
product_length_cm
product_height_cm
product_width_cm
```

The source spelling `lenght` is retained deliberately in Bronze.

### Grain and duplicate evidence

`product_id` is complete and unique in the observed snapshot:

```text
distinct_product_id=32951
product_id_nulls=0
product_id_blanks=0
duplicate_groups=0
duplicate_excess=0
non_hex_32_product_ids=0
```

No exact duplicate rows were observed. The accepted Bronze grain is one row
per `product_id`.

Deterministic content signature:

```text
row_count=32951
distinct_row_hashes=32951
row_hash_sum=-11340715477652328362
```

### Completeness evidence

No blank strings or trim differences were found. Nulls are present and must be
preserved:

| Source attributes | Null rows | Rate | Pattern |
|---|---:|---:|---|
| category, name length, description length, photos | 610 each | 1.8512% | 609 rows share only this missing descriptive set; one row also lacks every physical measure |
| weight, length, height, width | 2 each | 0.0061% | the four physical fields are missing together |

The second physical-null row has category `bebes` and complete descriptive
attributes. These observations do not establish that descriptive or physical
completeness is a Bronze validity requirement.

### Numeric-source evidence

All seven numeric-named columns contain only integer-form text when present.
No negative, fractional or non-parseable values were observed.

| Column | Min | P50 | P95 | Max | Zero rows |
|---|---:|---:|---:|---:|---:|
| `product_name_lenght` | 5 | 51 | 60 | 76 | 0 |
| `product_description_lenght` | 4 | 595 | 2063 | 3992 | 0 |
| `product_photos_qty` | 1 | 1 | 6 | 20 | 0 |
| `product_weight_g` | 0 | 700 | 10850 | 40425 | 4 |
| `product_length_cm` | 7 | 25 | 65 | 105 | 0 |
| `product_height_cm` | 2 | 13 | 44 | 105 | 0 |
| `product_width_cm` | 6 | 20 | 47 | 118 | 0 |

The four zero-weight rows are all `cama_mesa_banho` products with non-zero
dimensions. Zero weight is suspicious but not proven impossible, so it is
observed rather than rejected.

### Category and encoding evidence

There are 73 non-null raw categories. Raw and trimmed/lowercase cardinalities
are equal; no trim differences or basic mojibake markers were detected. Bronze
does not normalize or translate categories.

### Relationship evidence

The sibling Order Items snapshot has 112,650 rows and exactly 32,951 distinct
`product_id` values:

```text
order_item_product_ids_missing_from_products=0
products_not_used_by_order_items=0
```

The translation snapshot has 71 distinct categories. Two Products categories
have no translation:

```text
pc_gamer
portateis_cozinha_e_preparadores_de_alimentos
```

These are downstream Silver/Gold considerations. Bronze does not introduce
cross-dataset foreign-key or translation-coverage write gates.

One static CSV does not prove a business date, cadence or incremental delivery
model. No `dt_base`, partitioning, clustering or incremental assumption is
introduced.

## Requirements

### Functional

1. Read the nine Products source columns as strings.
2. Preserve source column names and values, including `lenght` spellings.
3. Persist `source_file` plus the platform-managed ingestion timestamp.
4. Use one row per `product_id` and protect key completeness and uniqueness.
5. Preserve source nulls and zero-weight values.
6. Reject present numeric attributes that no longer have non-negative integer
   text shape.
7. Persist non-blocking observations for incomplete descriptive attributes,
   incomplete physical attributes and zero weights.
8. Persist first-class DQ and execution lifecycle evidence.
9. Expose Products as a packaged CLI entry point and DAB job for DEV/STG/PRD.
10. Add targeted deployment smoke coverage.

### Non-goals

- no type casting or business-data normalization in Bronze;
- no imputation, correction or removal of null or zero values;
- no category translation;
- no join to Order Items or category translation during ingestion;
- no blocking cross-dataset relationship rule;
- no source cadence, `dt_base`, partitioning or clustering assumption;
- no new shared platform abstraction.

## Technical Design

### Dataset contract

All nine business columns and `source_file` remain strings. `product_id` is the
logical key; the other source fields remain nullable. The platform adds
`ingestion_timestamp`.

Write strategy: `FULL_REPLACE`.

Physical layout: no partition columns and no clustering columns.

### Data Quality contract

| Rule | Evidence | Severity | Failure impact | Write gate |
|---|---|---|---|---|
| `PRODUCTS-DQ01` snapshot non-empty | authoritative snapshot has 32,951 rows | ERROR | replacement with empty snapshot | blocks |
| `PRODUCTS-DQ02` `product_id` non-null | 0 nulls observed; key grain | ERROR | unidentified product row | blocks |
| `PRODUCTS-DQ03` `product_id` unique | 32,951 distinct IDs; 0 duplicates | ERROR | ambiguous product grain | blocks |
| `PRODUCTS-DQ04` present numeric attributes are non-negative integer text | 0 malformed, negative or fractional values | ERROR | source-shape drift breaks downstream numeric interpretation | blocks |
| `PRODUCTS-DQ05` incomplete descriptive set count | 610 rows observed | INFO | descriptive completeness metric | observes only |
| `PRODUCTS-DQ06` incomplete physical set count | 2 rows observed | INFO | physical completeness metric | observes only |
| `PRODUCTS-DQ07` zero weight count | 4 rows observed | INFO | suspicious-value metric | observes only |

### Runtime composition

```text
OlistCsvSnapshotReader
  -> OlistSnapshotIngestionService
     -> DataQualityRunner / QualityResultWriter
     -> BronzeWriter.write_checked()
     -> ExecutionRunTracker
```

The job receives explicit source, target and Control Plane table arguments.

## Impact Analysis

Changes are local to the Products vertical slice and deployment registration:

- Products DatasetContract and DataQualityContract;
- executable Products ingestion job;
- DAB job resource, package entry point and deployment smoke entry;
- unit/integration tests and Databricks validation script;
- read-only discovery notebook and feature documentation.

No existing table schema, platform API, shared abstraction or architectural
boundary changes.

### Risks

- future source-shape drift is rejected before `FULL_REPLACE`;
- null descriptive/physical attributes must remain source-faithful;
- zero weight may be a source anomaly and is monitored without blocking;
- the two untranslated categories require explicit downstream handling;
- source files must exist in STG/PRD before promotion smokes can pass.

## Implementation Plan

1. Record Discovery, requirements, design and impact evidence.
2. Add Products persisted and DQ contracts.
3. Compose the Products job from existing Olist snapshot components.
4. Add unit/integration coverage for contracts, observations and write gates.
5. Register the package entry point, DAB job and deployment smoke.
6. Run repository static, test, build and bundle validation.
7. Run the authoritative DEV positive path and validate the persisted target.
8. Run a controlled malformed numeric batch and prove `records_written=0`
   with the protected target unchanged.
9. Open the topic-branch PR to `dev`; merge only after explicit approval.
10. Promote the approved immutable artifact through STG and PRD gates.
11. Publish runtime evidence and closeout on `main`.
