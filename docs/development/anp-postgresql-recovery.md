# ANP PostgreSQL / Bronze recovery

## Objective

Recover the previously validated ANP fuel-price ingestion path into the current repository lineage without merging the stale historical branch wholesale.

## Historical source

Recovered selectively from `feature/tools-postgresql`:

- PostgreSQL Docker/bootstrap migrations;
- generic `platform.postgres` client/config/bootstrap utilities;
- generic `platform.jdbc` reader/config utilities;
- ANP CSV to PostgreSQL loader with SHA-256 idempotency and ingestion control;
- ANP PostgreSQL to Databricks Bronze reader and job;
- historical PostgreSQL/JDBC/ANP operational documentation.

The historical branch had diverged substantially from current `dev`, so it is retained as evidence only and is not a merge source.

## Current-platform adaptations

The recovered Bronze dataset now uses the current `DatasetContract`, `TableLayout`, `TableMetadata`, `BRONZE_INGESTION_TIMESTAMP`, and `WriteStrategy.REPLACE_WHERE` APIs.

The shared persisted contract parser was extended to support `decimal(p,s)` with Spark-compatible validation. This is required to preserve PostgreSQL `NUMERIC` values without coercing fuel prices to floating point.

The recovered ANP contract keeps:

- technical key: `id`;
- `dt_base = data_coleta`;
- clustering: `dt_base`;
- explicit bounded `replaceWhere` reprocessing;
- `source_file` lineage;
- `source_system = azure_postgresql`.

## Historical runtime evidence

The historical implementation documentation records a successful reprocessing validation for `2016-01-04` through `2016-06-30` with:

- 486,897 rows;
- 486,897 distinct IDs;
- no null `source_file` values;
- final `source_file = ca-2016-01.csv`;
- repeated execution preserving the same final state.

This evidence is historical. The recovery PR must pass the current CI/static gates, and current-environment runtime validation remains a separate deployment gate.

## Explicit non-goals of the recovery PR

- do not merge the stale historical branch;
- do not restore unrelated Weather/Olist code from that branch;
- do not invent PostgreSQL credentials, hosts, firewall rules, or deployment secrets;
- do not claim current DEV/STG/PRD runtime validation until it is executed again.
