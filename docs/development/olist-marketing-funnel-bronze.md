# Olist Marketing Funnel Bronze

## Scope

This feature completes the Olist Marketing Funnel Bronze domain without moving
funnel business logic into Bronze.

The source directory is:

```text
/Volumes/<catalog>/bronze/raw_storage/raw/olist/funnel/
```

It contains:

- `olist_marketing_qualified_leads_dataset.csv`
- `olist_closed_deals_dataset.csv`

Both Funnel slices are complete. MQL and Closed Deals use the same first-class
Data Quality, execution tracking, DAB and smoke-delivery pattern and have been
validated successfully in DEV.

## Discovery evidence

The physical source inventory found 8,000 MQL rows and four source columns:

- `mql_id`
- `first_contact_date`
- `landing_page_id`
- `origin`

Observed MQL properties:

| Check | Evidence |
| --- | --- |
| Natural-key candidate | 8,000 non-null `mql_id`, 8,000 distinct |
| Duplicate `mql_id` | 0 |
| `first_contact_date` nulls | 0 |
| `landing_page_id` nulls | 0 |
| `origin` nulls | 60 (0.75%) |
| `first_contact_date` parse failures | 0 |
| Date range | 2017-06-14 through 2018-05-31 |

The relationship check against Closed Deals found all 842 Closed Deals `mql_id`
values in MQL, with 7,158 MQLs having no Closed Deal. That relationship is a
Silver discovery; Bronze persists each source independently.

## Persisted contracts

### Marketing qualified leads

The MQL Bronze table keeps source values as strings and adds platform-managed
technical metadata:

| Column | Type | Nullable |
| --- | --- | --- |
| `mql_id` | STRING | no |
| `first_contact_date` | STRING | no |
| `landing_page_id` | STRING | no |
| `origin` | STRING | yes |
| `source_file` | STRING | yes |
| `ingestion_timestamp` | TIMESTAMP | managed |

Natural key: `mql_id`.

Persistence strategy: `FULL_REPLACE`.

### Closed Deals

The existing Closed Deals DatasetContract remains unchanged by the uplift. The
source columns stay source-faithful strings, `source_file` remains technical
source metadata, and `ingestion_timestamp` remains platform-managed.

Natural key: `mql_id`.

Persistence strategy: `FULL_REPLACE`.

Neither Funnel table is partitioned or clustered because both sources are small,
authoritative CSV snapshots.

## First-class Data Quality

Both Funnel datasets use the platform Data Quality path before the protected
Bronze write:

1. snapshot read;
2. execution evidence start;
3. Data Quality evaluation;
4. quality-result persistence;
5. `BronzeWriter.write_checked()`;
6. execution evidence completion.

MQL blocking rules:

- `MQL-DQ01`: snapshot is non-empty;
- `MQL-DQ02`: `mql_id` is not null;
- `MQL-DQ03`: `mql_id` is unique;
- `MQL-DQ04`: `first_contact_date` and `landing_page_id` are not null;
- `MQL-DQ05`: `first_contact_date` parses as `yyyy-MM-dd`.

`origin` is intentionally nullable because the source contains 60 null values.
No Bronze allow-list is imposed on origin values.

Closed Deals blocking rules:

- `CLOSED-DEALS-DQ01`: snapshot is non-empty;
- `CLOSED-DEALS-DQ02`: `mql_id` is not null;
- `CLOSED-DEALS-DQ03`: `mql_id` is unique.

No Bronze cross-table foreign-key rule is added between Closed Deals and MQL.
Their discovered relationship is preserved for Silver design rather than used as
a Bronze write blocker.

## Delivery

The Databricks Asset Bundle jobs resolve source Volumes and destination tables
from the deployment target catalog. DEV, STG and PRD therefore use the same code
with environment-isolated paths.

Both deployment smokes execute their complete snapshots because the Funnel
sources are small and use bounded `FULL_REPLACE` writes.

The bundle wheel build removes stale wheel artifacts before normal DEV/STG builds
and requires exactly one resulting wheel. Production exact-artifact promotion
keeps its separate prebuilt-wheel path and never rebuilds the approved artifact.
CI installs the built wheel in an isolated environment and verifies both
`olist-mql` and `olist-closed-deals` packaged entry points.

## MQL DEV validation evidence

The MQL job completed successfully in DEV on 2026-08-28 with run ID
`fc1a93ae-3151-437b-bd39-b3d1ee977787`.

Observed runtime evidence:

| Check | Result |
| --- | --- |
| Execution status | `SUCCEEDED` |
| Quality status | `PASSED` |
| Records extracted | 8,000 |
| Records evaluated | 8,000 |
| Records written | 8,000 |
| Target rows | 8,000 |
| Distinct `mql_id` | 8,000 |
| Required-column nulls | 0 |
| Invalid `first_contact_date` values | 0 |
| Blocking DQ rules | `MQL-DQ01` through `MQL-DQ05` all `PASS` |

Target table: `dev.bronze.olist_marketing_qualified_leads`.

## Closed Deals DEV validation evidence

The Closed Deals job completed successfully in DEV on 2026-08-28 with run ID
`bd971f31-4082-4c41-ac28-7234b783a931`.

Observed runtime evidence:

| Check | Result |
| --- | --- |
| Job status | `TERMINATED SUCCESS` |
| Records read | 842 |
| Records written | 842 |
| Target rows | 842 |
| Distinct `mql_id` | 842 |
| Null `mql_id` | 0 |
| Write strategy | `FULL_REPLACE` |
| Blocking DQ rules | all three rules passed before protected write |

Target table: `dev.bronze.olist_closed_deals`.

Because `BronzeWriter.write_checked()` is only reached after the first-class DQ
report has no blocking failures, the successful protected write also validates
that `CLOSED-DEALS-DQ01` through `CLOSED-DEALS-DQ03` passed for this run.

## Status

The Olist Marketing Funnel Bronze domain is `DONE`.

Both MQL and Closed Deals have completed Discovery/contract confirmation,
first-class Data Quality, execution tracking, DAB delivery, deployment smoke
coverage, automated tests, DEV runtime execution and post-write validation.

Silver keeps the discovered funnel relationship as a downstream design input:
all 842 Closed Deals map to MQL while 7,158 MQL records have no Closed Deal.
Bronze intentionally does not enforce that relationship as a cross-table rule.
