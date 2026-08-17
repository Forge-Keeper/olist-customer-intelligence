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
    │   │   └── weather/
    │   ├── bronze/
    │   │   └── weather/
    │   └── customer_intelligence/
    └── jobs/
```

`platform/` contains reusable technical capabilities. `domains/` contains cohesive Data Engineering responsibilities and source/product-specific behavior.

The Weather vertical slice is evolving to:

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

Primary keys represent both logical row identity and the idempotency key used by the Bronze writer.

Normal ingestion uses `MERGE`, so repeated ingestion of the same logical observations does not create duplicate rows.

Reprocessing is an explicit operation with an explicit geographic/date scope. It uses selective replacement rather than overloading normal ingestion with an `overwrite` boolean.

If a reprocessing request produces zero daily observations, it fails before replacement and preserves the existing Bronze scope.

## Data Sources

### Olist

The public Olist Brazilian e-commerce dataset is the primary analytical source and foundation for the Customer Intelligence data product.

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
- Table Contracts;
- Data Quality framework;
- Silver architecture;
- Gold/data-product architecture;
- richer backfill/replay policies;
- observability;
- governance and Unity Catalog.

Databricks remains the project's primary specialization, but the portfolio is intentionally not limited to the Databricks ecosystem.
