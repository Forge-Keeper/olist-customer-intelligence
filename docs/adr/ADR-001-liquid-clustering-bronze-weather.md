# ADR-001: Use Liquid Clustering Instead of Hive-Style Partitioning for Bronze Weather Data

- **Status:** Accepted
- **Date:** 2026-08-12
- **Decision owners:** Olist Customer Intelligence
- **Scope:** `prd.bronze.weather_daily`

## Context

The Open-Meteo ingestion pipeline stores daily weather observations in the Bronze layer.

Each Bronze row represents one calendar day for a requested geographic location. The table includes a daily reference column named `dt_base`, stored as `DATE`.

An earlier design considered physically partitioning the Delta table by `dt_base`. Because `dt_base` has daily granularity, this approach would continuously increase the number of partitions as historical data grows while many partitions could contain little data.

Another alternative considered changing `dt_base` to the first day of each month and partitioning monthly. This was rejected because it would change the semantic meaning of the column solely to accommodate a physical storage decision.

The project uses Databricks and Delta Lake. ADR-003 later changed the Bronze payload representation and normal write strategy, but it did not change the daily grain or this layout decision.

## Decision

`prd.bronze.weather_daily` uses **Liquid Clustering** instead of Hive-style `PARTITION BY`.

The initial clustering key is:

```sql
CLUSTER BY (dt_base)
```

The table does not use:

```sql
PARTITION BY (dt_base)
```

`dt_base` preserves the actual daily date represented by the observation. It is not converted to the first day of its month for storage optimization.

If monthly semantics are required later, a separate derived column such as `reference_month` can be introduced downstream.

## Rationale

### Preserve data semantics

Physical optimization must not redefine the business meaning of a column. `dt_base` represents the date of the weather observation and therefore remains daily and typed as `DATE`.

### Avoid excessive partition cardinality

Daily Hive-style partitioning would create an increasing number of physical partitions even though the expected table size does not justify that layout.

### Allow the physical layout to evolve

Liquid Clustering provides a more flexible organization strategy than fixed Hive-style partitions. The clustering strategy can evolve as actual query patterns become known without redesigning the logical meaning of `dt_base`.

### Align with the Databricks platform

The project intentionally uses Databricks as its primary specialization. Liquid Clustering demonstrates a modern Delta table-layout decision rather than applying `PARTITION BY` by convention.

## Initial Clustering Key

The first explicit clustering key is:

```text
dt_base
```

The current justification is temporal filtering, historical reprocessing, date-range validation, and incremental ingestion control.

Geographic fields such as `requested_latitude` and `requested_longitude` are not included initially. Although they are part of the Weather primary key, logical identity alone is not sufficient justification for making them physical clustering keys.

The Bronze `payload` column introduced by ADR-003 is `VARIANT` and must not be used as a clustering or partition column.

Additional clustering keys should only be introduced after observing real query patterns and table growth.

## Automatic Liquid Clustering

`CLUSTER BY AUTO` is not adopted in this phase.

The project initially uses an explicit clustering key so that the physical design decision is intentional, explainable, deterministic, and testable.

Automatic Liquid Clustering can be evaluated later when the table has sufficient workload history and the project reaches its performance and platform-optimization phase.

## Write and Reprocessing Strategy

Liquid Clustering is a **table-layout property**, not a write-mode property.

When the Bronze table is first created, the writer defines the clustering configuration. Subsequent writes preserve the existing table layout.

ADR-003 supersedes the earlier normal-write behavior that relied on selective `replaceWhere` writes:

```text
normal ingestion
    -> MERGE by declared Weather primary key

explicit scoped reprocessing
    -> replaceWhere by coordinates + date interval
```

The writer must not combine Liquid Clustering with Hive-style partitioning for this table.

## Consequences

### Positive

- `dt_base` keeps its correct daily semantics.
- No proliferation of daily Hive-style partitions.
- Physical organization can evolve as workload patterns become clearer.
- The architecture aligns with modern Databricks/Delta Lake capabilities.
- The table layout remains independent from the chosen normal write strategy.
- Scoped reprocessing can still use selective replacement without redefining clustering.

### Negative / Trade-offs

- Liquid Clustering introduces a stronger dependency on Databricks/Delta capabilities than generic Hive-style partitioning.
- Local OSS Spark integration tests cannot fully validate Databricks managed-table clustering behavior.
- The selected clustering key may need to evolve as query patterns change.
- Clustering effectiveness must eventually be validated using actual table size and workload characteristics.

## Testing Impact

Local tests should validate:

- `dt_base` is represented as `datetime.date` before Spark DataFrame creation;
- Bronze contract requires `dt_base`;
- the writer requests clustering by `dt_base` when creating the table;
- the writer does not call `partitionBy` for Weather;
- existing-table writes do not attempt to redefine clustering;
- scoped reprocessing predicates use `DATE` literals and `dt_base`.

Databricks integration validation should confirm:

- the table is Delta;
- `partitionColumns` is empty;
- Liquid Clustering is enabled;
- `dt_base` is the configured clustering key;
- normal MERGE ingestion remains idempotent;
- selective reprocessing behaves correctly.

## Alternatives Considered

### 1. Daily `PARTITION BY (dt_base)`

Rejected. The expected table size does not justify a physical partition for every calendar day, and the layout would become increasingly fragmented and rigid.

### 2. Monthly `PARTITION BY` using `dt_base`

Rejected. Changing `dt_base` to the first day of the month would corrupt its intended semantics.

### 3. Separate monthly partition column

Not selected at this stage. A dedicated column such as `reference_month` would preserve semantics, but there is currently no demonstrated workload or table volume that justifies Hive-style monthly partitioning.

### 4. No partitioning and no clustering

Viable for a small table, but not selected. The project intentionally wants to demonstrate an explicit Databricks table-layout decision while retaining the ability to evolve clustering based on real workload patterns.

### 5. `CLUSTER BY AUTO`

Deferred. Automatic clustering may become preferable after sufficient workload history exists, but explicit `CLUSTER BY (dt_base)` provides a clearer architectural decision during the current development phase.

## Revisit Criteria

Review this ADR if:

- `weather_daily` grows substantially beyond the expected project scale;
- query patterns become predominantly geographic rather than temporal;
- a stable geographic key such as `location_id` is introduced;
- automatic liquid clustering becomes preferable based on observed workload;
- performance metrics show insufficient data skipping or excessive rewrite cost;
- the table moves away from Databricks/Delta Lake.

## Related Decisions

- ADR-003: Bronze as first persistent landing layer with `VARIANT` payloads and explicit reprocessing.
