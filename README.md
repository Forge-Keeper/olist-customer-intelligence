# Olist Customer Intelligence

End-to-end Data Engineering project built around the Olist public e-commerce dataset and external data sources.

## Current Architecture

The Python package follows a hybrid **Platform + Domains** structure.

```text
src/
└── olist_data_platform/
    ├── platform/
    │   ├── http/
    │   └── logging/
    ├── domains/
    │   ├── ingestion/
    │   │   └── weather/
    │   ├── raw/
    │   │   └── weather/
    │   ├── bronze/
    │   │   └── weather/
    │   └── customer_intelligence/
    └── jobs/
```

`platform/` contains reusable technical capabilities. `domains/` contains cohesive Data Engineering responsibilities and source/product-specific behavior.

The current Weather vertical slice is:

```text
Open-Meteo API
      ↓
OpenMeteoClient
      ↓
WeatherIngestionService
      ↓
RawWeatherWriter
      ↓
WeatherResponseParser
      ↓
BronzeWeatherWriter
```

RAW preserves the original API response and request metadata. Bronze converts the response into a structured, explicitly typed dataset with technical metadata and controlled persistence behavior.

See `docs/adr/ADR-002-hybrid-domain-platform-package-structure.md` for the architectural decision.

## Data Sources

### Olist

The public Olist Brazilian e-commerce dataset is the primary analytical source and foundation for the Customer Intelligence data product.

### Open-Meteo

Open-Meteo is the first external API integrated into the platform. The integration demonstrates reusable HTTP communication, source-specific ingestion, RAW payload preservation, structured Bronze ingestion, request metadata, reprocessing controls, Delta persistence, and Liquid Clustering.

Additional sources should only be introduced when they solve a concrete data or product requirement.

## Development Environment

### Requirements

- Python 3.11+
- Java 17+
- `uv`

Java 17 or newer is required for local PySpark integration tests.

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

Fast tests that do not require a real Spark session:

```powershell
uv run pytest tests/unit -q
```

Current validated baseline: **143 unit tests passing**.

### Integration tests

Tests using real local PySpark DataFrames:

```powershell
uv run pytest tests/integration -q
```

They require Java 17+ and are intentionally separated because starting Spark is heavier than running the unit suite.

### Full suite

```powershell
uv run pytest -q
```

Current validated baseline: **158 tests passing**.

## Linting with Ruff

Run:

```powershell
uv run ruff check .
```

Current rule families:

```toml
[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors: style and structural errors
    "F",   # Pyflakes: invalid/unused imports, undefined variables, etc.
    "I",   # isort: import organization and ordering
    "UP",  # pyupgrade: modern Python syntax
    "B",   # flake8-bugbear: bug-prone patterns and common bad practices
]
```

Safe automatic fixes can be applied with:

```powershell
uv run ruff check . --fix
```

Review changes before committing them. Additional rule families should only be enabled when they provide clear engineering value.

## Recommended Development Workflow

Normal development:

```powershell
uv sync
uv run ruff check .
uv run pytest tests/unit -q
```

When changing Spark-dependent code:

```powershell
uv run pytest tests/integration -q
```

Before committing a completed change:

```powershell
uv run ruff check .
uv run pytest -q
```

> Run the cheapest useful validation first.

## Engineering Principles

1. Architecture should solve real project problems rather than maximize the technology stack.
2. Reusable abstractions should emerge from concrete reuse.
3. Source-specific behavior stays close to its domain.
4. Shared technical capabilities belong in `platform/`.
5. RAW, Bronze, Silver, and Gold have distinct responsibilities.
6. Schemas and persistence behavior should be explicit.
7. Tests are part of the architecture.
8. Data Quality and observability should become first-class capabilities.
9. Durable architectural decisions with meaningful alternatives should be documented as ADRs.
10. Professional architectures may inspire principles, but third-party code, rules, datasets, or intellectual property must not be copied into the portfolio.

## Near-term Roadmap

- Table Contracts
- reusable Delta table lifecycle management
- explicit table layout strategy (`partition_by` or `cluster_by`)
- Data Quality framework
- Silver architecture
- Gold/data-product architecture
- backfill and replay
- observability
- governance and Unity Catalog

Databricks remains the project's primary specialization, but the portfolio is intentionally not limited to the Databricks ecosystem.

## Current Status

- Olist dataset as the primary analytical source
- Open-Meteo external API ingestion
- RAW and Bronze Weather flow
- reusable HTTP and logging platform capabilities
- hybrid Platform + Domains package structure
- Liquid Clustering for Weather Bronze
- local PySpark integration tests
- `uv` dependency/environment management
- Ruff linting
- **158-test validated baseline**

The next architectural evolution is focused on **Table Contracts and reusable Delta table lifecycle management**.
