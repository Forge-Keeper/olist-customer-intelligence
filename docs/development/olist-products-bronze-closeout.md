# Olist Products Bronze — Closeout

## Final status

Olist Products Bronze completed the full delivery path:

```text
Discovery -> Requirements -> Technical Design -> Impact Analysis -> Implementation Plan -> Implementation -> DEV Validation -> STG -> PRD -> Closeout
```

Feature status: **DONE**, subject to merge of this closeout record into `main`.

The detailed Discovery, requirements, design, implementation and DEV evidence remains in `docs/development/olist-products-bronze.md`. This closeout record is the canonical evidence for the final STG/PRD gates.

## Promotion identity

The approved production identity is:

```text
git_sha=da781d7d3a74b37de0ee133af3b272dbb4452e75
wheel=olist_customer_intelligence-0.1.1.dev181+gda781d7d3-py3-none-any.whl
wheel_sha256=f9ac8a49dcf15e5ae39778be19d5021bebb5ff533a0466b07ff19a2e8125ca96
```

The production workflow reused the exact wheel retained by the successful STG run rather than rebuilding the application artifact.

## STG validation

GitHub Actions `Deploy STG` run:

```text
run_id=33794895863
status=completed
conclusion=success
git_sha=da781d7d3a74b37de0ee133af3b272dbb4452e75
```

The workflow completed successfully through:

- staging bundle validation;
- staging bundle deployment;
- deployment smoke coverage;
- promoted wheel manifest capture;
- staging promotion artifact retention.

The retained staging artifact is:

```text
artifact=stg-promotion-da781d7d3a74b37de0ee133af3b272dbb4452e75
artifact_id=9909768010
```

The Products STG deployment smoke completed successfully against:

```text
source_path=/Volumes/stg/bronze/raw_storage/raw/olist/e_commerce/olist_products_dataset.csv
target_table=stg.bronze.olist_products
row_count=32951
strategy=full_replace
```

## PRD validation

GitHub Actions `Deploy PRD` run:

```text
run_id=33813877400
status=completed
conclusion=success
stg_run_id=33794895863
prd_git_sha=da781d7d3a74b37de0ee133af3b272dbb4452e75
```

Before deployment, the production workflow successfully:

1. required dispatch from `main`;
2. downloaded the approved STG promotion artifact;
3. verified the staging manifest and current Git commit identity;
4. verified the wheel SHA-256 digest;
5. copied the approved wheel into the production deployment path;
6. validated the production Databricks bundle.

Production then deployed the approved staging wheel and completed the full deployment smoke suite successfully.

The Products PRD smoke completed successfully:

```text
source_path=/Volumes/prd/bronze/raw_storage/raw/olist/e_commerce/olist_products_dataset.csv
target_table=prd.bronze.olist_products
row_count=32951
logical_run_id=9ce5097b-a9c4-4731-9a83-9b497091c5c0
strategy=full_replace
```

Production deployment evidence was retained as:

```text
artifact=prd-deployment-da781d7d3a74b37de0ee133af3b272dbb4452e75
artifact_id=9916527301
artifact_sha256=49ac370da448ffc6cfa0a54f3e3ac094a5a38e880a1716fa226a548b4f8cecea
```

## Acceptance criteria

The feature is complete across DEV -> STG -> PRD:

- the accepted source-faithful Products contract is implemented;
- all nine source columns remain source-shaped strings and retain the source `lenght` spellings;
- authoritative DEV ingestion completed with 32,951 rows and 32,951 distinct non-null `product_id` values;
- all blocking Products DQ rules passed on the authoritative snapshot;
- non-blocking observations remained aligned with Discovery evidence: 610 incomplete descriptive rows, 2 incomplete physical rows and 4 zero-weight rows;
- no partitioning or clustering was introduced;
- controlled malformed numeric input was rejected by `PRODUCTS-DQ04` before the protected write, with zero records written and the validation target unchanged;
- STG deployment and Products smoke completed successfully;
- the exact STG-approved wheel was verified by commit identity and SHA-256 before PRD deployment;
- PRD Products smoke completed successfully with 32,951 rows;
- final STG and PRD artifacts are retained in GitHub Actions.

## Closeout

Olist Products Bronze is **DONE** once this documentation-only closeout PR is merged into `main`.

Future changes to Products Bronze require a new explicitly scoped backlog item rather than reopening this delivery record.
