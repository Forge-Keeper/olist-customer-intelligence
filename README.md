# Olist Customer Intelligence

End-to-end Data Engineering project built around the Olist public e-commerce dataset and external data sources.

## Current Architecture

The Python package follows a hybrid **Platform + Domains** structure.

```text
src/
└── olist_data_platform/
    ├── platform/
    │   ├── delta/
    │   │   └── bronze/
    │   ├── http/
    │   └── logging/
    ├── domains/
    │   ├── ingestion/
    │   │   ├── olist/
    │   │   └── weather/
    │   ├── bronze/
    │   │   ├── olist/
    │   │   └── weather/
    │   └── customer_intelligence/
    └── jobs/
        ├── olist_customers_ingestion.py
        ├── olist_closed_deals_ingestion.py
        └── weather_ingestion.py
```

`platform/` contains reusable technical capabilities. `domains/` contains cohesive Data Engineering responsibilities and source/product-specific behavior. `jobs/` contains executable application composition entrypoints; deployment and orchestration remain separate concerns.

The Weather vertical slice is:

```text
Open-Meteo API
      ↓
OpenMeteoClient
      ↓
WeatherIngestionService
      ↓
WeatherDailyExtractor
      ↓
BronzeWeatherWriter
      ↓
BronzeWriter
      ↓
Delta Bronze
```

Bronze is the first persistent landing layer for this flow. Each Weather row represents one observation day and stores:

- `dt_base` as `DATE`;
- source data for that day in a `VARIANT` payload;
- request metadata;
- ingestion metadata.

There is no separate RAW persistence layer in the new design. Semantic typing, normalization, Data Quality, and business interpretation are deferred to downstream processing.

Olist file-based authoritative snapshots now share this vertical slice:

```text
Olist CSV in Unity Catalog Volume
      ↓
OlistCsvSnapshotReader
      ↓
OlistSnapshotIngestionService
      ↓
BronzeWriter
      ↓
Delta Bronze
```

`OlistCsvSnapshotReader` preserves business values as `STRING`, keeps additional source columns, validates each dataset's minimum required columns, and adds `source_file` from file metadata. `OlistSnapshotIngestionService` provides the common read/count/log/write workflow while each job keeps its own source contract and Bronze configuration.

Olist Customers and Olist Closed Deals are both treated as authoritative full snapshots. Business typing is intentionally deferred to Silver. Technical metadata includes `source_file` and `ingestion_timestamp`.

See:

- `docs/adr/ADR-001-liquid-clustering-bronze-weather.md`;
- `docs/adr/ADR-002-hybrid-domain-platform-package-structure.md`;
- `docs/adr/ADR-003-bronze-landing-with-variant.md`.

## Bronze Persistence Contract

Reusable Bronze persistence is configured per dataset.

Each dataset declares:

- primary-key columns;
- required columns;
- clustering columns;
- partition columns;
- normal write strategy.

For Weather:

```text
PRIMARY KEY
(dt_base, requested_latitude, requested_longitude)

NORMAL WRITE
MERGE

CLUSTER BY
(dt_base)

PARTITION BY
none
```

For Olist Customers:

```text
PRIMARY KEY
(customer_id)

NORMAL WRITE
FULL_REPLACE

CLUSTER BY
none

PARTITION BY
none
```

For Olist Closed Deals:

```text
PRIMARY KEY
(mql_id)

NORMAL WRITE
FULL_REPLACE

CLUSTER BY
none

PARTITION BY
none
```

Primary keys represent both logical row identity and the idempotency key used by the Bronze writer.

Weather normal ingestion uses `MERGE`, so repeated ingestion of the same logical observations does not create duplicate rows.

Olist file-based snapshots use `FULL_REPLACE` because each source file represents the complete authoritative snapshot. A validated non-empty snapshot replaces the existing Bronze table and may evolve the schema through new source columns. An empty snapshot fails before replacement and preserves the existing table.

Weather reprocessing is an explicit operation with an explicit geographic/date scope. It uses selective replacement rather than overloading normal ingestion with an `overwrite` boolean.

If a Weather reprocessing request produces zero daily observations, it fails before replacement and preserves the existing Bronze scope.

## Job Entrypoints

### Weather

The Weather entrypoint is:

```text
olist_data_platform.jobs.weather_ingestion
```

It composes Spark, the Open-Meteo client, the Weather Bronze writer, and the ingestion service. Deployment and scheduling are intentionally out of scope here and remain in the Databricks Asset Bundles backlog.

Example normal ingestion:

```powershell
uv run python -m olist_data_platform.jobs.weather_ingestion `
  --operation ingest `
  --target-table prd.bronze.weather_daily `
  --latitude -23.5505 `
  --longitude -46.6333 `
  --start-date 2018-01-01 `
  --end-date 2018-01-31 `
  --timezone America/Sao_Paulo
```

Example explicit reprocessing:

```powershell
uv run python -m olist_data_platform.jobs.weather_ingestion `
  --operation reprocess `
  --target-table prd.bronze.weather_daily `
  --latitude -23.5505 `
  --longitude -46.6333 `
  --start-date 2018-01-01 `
  --end-date 2018-01-31 `
  --timezone America/Sao_Paulo
```

Optional daily variables can be supplied as a comma-separated list with `--daily-variables`.

### Olist Customers

The Olist Customers entrypoint is:

```text
olist_data_platform.jobs.olist_customers_ingestion
```

Example:

```powershell
uv run python -m olist_data_platform.jobs.olist_customers_ingestion `
  --target-table prd.bronze.olist_customers
```

The source defaults to the Olist Customers CSV in the configured Unity Catalog Volume and can be overridden with `--source-path`.

### Olist Closed Deals

The Olist Closed Deals entrypoint is:

```text
olist_data_platform.jobs.olist_closed_deals_ingestion
```

Example:

```powershell
uv run python -m olist_data_platform.jobs.olist_closed_deals_ingestion `
  --target-table prd.bronze.olist_closed_deals
```

The source defaults to the Closed Deals CSV in the Olist funnel Unity Catalog Volume and can be overridden with `--source-path`.

## Data Sources

### Olist

The public Olist Brazilian e-commerce dataset is the primary analytical source and foundation for the Customer Intelligence data product. Olist file-based Bronze tables preserve source values as strings unless a source-specific contract requires otherwise; semantic typing belongs downstream.

### Open-Meteo

Open-Meteo is the first external API integrated into the platform. The integration demonstrates reusable HTTP communication, source-specific extraction, semi-structured Bronze landing, request metadata, idempotent Delta persistence, explicit reprocessing, and Liquid Clustering.

Additional sources should only be introduced when they solve a concrete data or product requirement.

## Development Environment

### Requirements

- Python 3.11+
- Java 17+
- `uv`

Java 17 or newer is required for local PySpark integration tests.

Databricks validation of the Bronze Weather table requires a runtime compatible with the features used by the table. `VARIANT` support in Delta requires Databricks Runtime 15.4 LTS or newer.

```powershell
python --version
java -version
uv --version
```

## Dependency Management with uv

The project uses `uv` for dependency and environment management.

Synchronize the environment:

```powershell
uv sync
```

Runtime and development dependencies are resolved from `pyproject.toml` and locked in `uv.lock`. The lockfile should be committed to Git.

Project commands should normally be executed through `uv run`; manually activating `.venv` is optional.

## Testing

### Unit tests

```powershell
uv run pytest tests/unit -q
```

### Integration tests

```powershell
uv run pytest tests/integration -q
```

Local integration tests require Java 17+ and are intentionally separated because starting Spark is heavier than running the unit suite.

Some Databricks-specific behaviors, including Delta `VARIANT` support and the managed-table clustering configuration, require validation on Databricks rather than only local OSS Spark.

### Full suite

```powershell
uv run pytest -q
```

## Linting and Type Checking

```powershell
uv run ruff check .
uv run ty check
```

Current Ruff rule families include `E`, `F`, `I`, `UP`, and `B`.

Before committing a completed change, run the cheapest useful validations first and finish with the full relevant suite.

## Engineering Principles

1. Architecture should solve real project problems rather than maximize the technology stack.
2. Reusable abstractions should emerge from concrete reuse.
3. Source-specific behavior stays close to its domain.
4. Shared technical capabilities belong in `platform/`.
5. Bronze, Silver, and Gold have distinct responsibilities; a separate RAW layer is not mandatory when Bronze already fulfills the required landing/preservation role.
6. Schemas and persistence behavior should be explicit.
7. Tests are part of the architecture.
8. Data Quality and observability should become first-class capabilities.
9. Durable architectural decisions with meaningful alternatives should be documented as ADRs.
10. Professional architectures may inspire principles, but third-party code, rules, datasets, or intellectual property must not be copied into the portfolio.

## Near-term Roadmap

- finish Bronze landing validation on Databricks;
- Databricks Asset Bundles deployment/orchestration;
- Table Contracts;
- Data Quality framework;
- Silver architecture;
- Gold/data-product architecture;
- richer backfill/replay policies;
- observability;
- governance and Unity Catalog.

Databricks remains the project's primary specialization, but the portfolio is intentionally not limited to the Databricks ecosystem.
