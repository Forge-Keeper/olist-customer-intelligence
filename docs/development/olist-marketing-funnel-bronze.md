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

The MQL slice is implemented first. The existing Closed Deals slice remains a
separate uplift step before the Marketing Funnel can be declared Bronze-complete.

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

## Persisted contract

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

The source is an authoritative, small CSV snapshot. No partitioning or
clustering is configured.

## First-class Data Quality

MQL adopts the platform Data Quality path before the protected Bronze write:

1. snapshot read;
2. execution evidence start;
3. Data Quality evaluation;
4. quality-result persistence;
5. `BronzeWriter.write_checked()`;
6. execution evidence completion.

Blocking rules:

- `MQL-DQ01`: snapshot is non-empty;
- `MQL-DQ02`: `mql_id` is not null;
- `MQL-DQ03`: `mql_id` is unique;
- `MQL-DQ04`: `first_contact_date` and `landing_page_id` are not null;
- `MQL-DQ05`: `first_contact_date` parses as `yyyy-MM-dd`.

`origin` is intentionally nullable because the source contains 60 null values.
No Bronze allow-list is imposed on origin values.

## Delivery

The Databricks Asset Bundle job resolves both the source Volume and destination
table from the deployment target catalog. DEV, STG and PRD therefore use the
same code with environment-isolated paths.

The deployment smoke executes the full 8,000-row MQL snapshot because the source
is small and the write is a bounded `FULL_REPLACE`.

The bundle wheel build removes stale wheel artifacts before normal DEV/STG builds
and requires exactly one resulting wheel. Production exact-artifact promotion
keeps its separate prebuilt-wheel path and never rebuilds the approved artifact.
The CI wheel-isolation gate also executes the `olist-mql` packaged entry point.

## DEV validation evidence

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

## Status

The MQL Bronze slice is `DONE`: Discovery, contract, implementation, first-class
Data Quality, DAB delivery, runtime execution and DEV validation are complete.
Closed Deals still requires its first-class DQ/DAB/smoke uplift before the Olist
Marketing Funnel domain can be declared Bronze-complete.
