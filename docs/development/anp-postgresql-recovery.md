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

## Current DEV runtime wiring

The current Azure PostgreSQL DEV endpoint was revalidated from the Azure resource overview:

```text
pg-olist-ci-dev.postgres.database.azure.com
```

The PostgreSQL database remains `olist`.

The Databricks secret scope `olist-jdbc` was also revalidated and contains the expected `username` and `password` keys. Secret values are not stored in GitHub.

The ANP Bronze Databricks job resource reads the non-sensitive host/database from bundle configuration and resolves JDBC username/password at runtime through `dbutils.secrets`. The recovered job no longer depends on developer shell `JDBC_*` environment variables when executed in Databricks.

Only DEV has a configured PostgreSQL hostname. STG and PRD intentionally keep the bundle hostname variable empty until their PostgreSQL sources are explicitly defined, preventing accidental cross-environment reads from the DEV database.

The bundle-level `run_as_service_principal` variable now defaults to an empty value so local DEV validation/deployment does not require a STG/PRD service-principal identifier. STG/PRD deployment automation continues to inject the identifier explicitly.

## Fresh DEV runtime evidence

The recovered DAB job was deployed and executed successfully in DEV against Azure PostgreSQL.

Validation interval:

```text
2016-01-04 through 2016-06-30
```

First execution:

- Databricks run ID: `226465764660636`;
- target: `dev.bronze.anp_combustiveis_precos`;
- result: SUCCESS;
- source/write row count: 486,897;
- exact bounded predicate: `dt_base >= DATE '2016-01-04' AND dt_base <= DATE '2016-06-30'`.

Post-write integrity validation:

- rows: 486,897;
- distinct `id`: 486,897;
- minimum `dt_base`: 2016-01-04;
- maximum `dt_base`: 2016-06-30;
- null `source_file`: 0.

Idempotency rerun:

- Databricks run ID: `31438430709540`;
- result: SUCCESS;
- row count after bounded reprocessing: 486,897;
- final state preserved for the same interval.

This fresh DEV evidence matches the historical comparator of 486,897 rows and proves that the recovered Azure PostgreSQL -> JDBC -> Databricks Bronze path is operational and idempotent in DEV.

## Historical runtime evidence

The historical implementation documentation records a successful reprocessing validation for `2016-01-04` through `2016-06-30` with:

- 486,897 rows;
- 486,897 distinct IDs;
- no null `source_file` values;
- final `source_file = ca-2016-01.csv`;
- repeated execution preserving the same final state.

The historical evidence is retained as a comparator. Fresh DEV runtime validation is now complete. STG/PRD runtime validation remains intentionally unclaimed and blocked on explicit environment-specific PostgreSQL configuration and promotion decisions.

## Explicit non-goals of the recovery work

- do not merge the stale historical branch;
- do not restore unrelated Weather/Olist code from that branch;
- do not commit PostgreSQL passwords or Databricks secret values;
- do not configure STG/PRD PostgreSQL endpoints without explicit environment evidence;
- do not promote ANP to STG/PRD automatically from DEV recovery evidence.
