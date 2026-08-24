# Olist Customer Intelligence

End-to-end Data Engineering project built around the Olist public e-commerce dataset and justified external data sources.

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
    │   │   ├── ibge/
    │   │   ├── olist/
    │   │   └── weather/
    │   ├── bronze/
    │   │   ├── ibge/
    │   │   ├── olist/
    │   │   └── weather/
    │   └── customer_intelligence/
    └── jobs/
        ├── ibge_municipalities_ingestion.py
        ├── ibge_municipality_population_ingestion.py
        ├── ibge_municipality_gdp_ingestion.py
        ├── olist_customers_ingestion.py
        ├── olist_closed_deals_ingestion.py
        └── weather_ingestion.py
```

`platform/` contains reusable technical capabilities. `domains/` contains cohesive source/product-specific behavior. `jobs/` contains executable application composition entrypoints; deployment and orchestration remain separate concerns.

## Bronze Design

Bronze is the first persistent landing layer. There is no separate RAW persistence layer in the current design.

Core rules:

- preserve source semantics / AS-IS values;
- keep business typing and normalization downstream;
- use explicit schemas and technical metadata;
- define natural keys/idempotency keys explicitly;
- use `MERGE` or full-replace semantics according to the source contract;
- choose partitioning or Liquid Clustering based on the dataset/use case;
- preserve semi-structured source payloads in `VARIANT` where that protects source fidelity.

See:

- `docs/adr/ADR-001-liquid-clustering-bronze-weather.md`;
- `docs/adr/ADR-002-hybrid-domain-platform-package-structure.md`;
- `docs/adr/ADR-003-bronze-landing-with-variant.md`.

## Implemented Bronze Vertical Slices

### Weather / Open-Meteo

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

Natural key:

```text
(dt_base, requested_latitude, requested_longitude)
```

Write strategy: `MERGE`.

Layout: Liquid Clustering by `dt_base`.

### Olist authoritative CSV snapshots

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

Implemented datasets:

- Olist Customers;
- Olist Closed Deals.

These sources are treated as authoritative full snapshots. Source values are preserved as strings unless a source-specific contract requires otherwise. `source_file` and `ingestion_timestamp` provide technical lineage.

Write strategy: `FULL_REPLACE` after validation of a non-empty snapshot.

### IBGE Localidades

```text
IBGE Localidades API
      ↓
LocalitiesClient
      ↓
MunicipalitiesIngestionService
      ↓
BronzeMunicipalitiesWriter
      ↓
BronzeWriter
      ↓
Delta Bronze
```

Bronze keeps:

- `municipality_code`;
- capture-date `dt_base`;
- full source object in `payload VARIANT`;
- request/ingestion metadata.

Natural key:

```text
(municipality_code, dt_base)
```

The current Localidades endpoint is treated as a current snapshot. Historical municipality snapshots are not fabricated from the current response.

### IBGE Municipality Population

SIDRA table `6579`, variable `9324`.

```text
SIDRA API
   ↓
SidraClient / SidraQuery / SidraDataset
   ↓
SidraParser
   ↓
MunicipalityPopulationExtractor
   ↓
MunicipalityPopulationIngestionService
   ↓
BronzeMunicipalityPopulationWriter
   ↓
Delta Bronze
```

Production scope currently covers 2016, 2017 and 2018.

Natural key:

```text
(municipality_code, reference_year, variable_code)
```

`dt_base` is January 1 of the reference year. `Valor` remains source-like inside `payload VARIANT`.

To reduce SIDRA timeout/retry blast radius, periods are requested independently and accumulated into one logical Bronze write.

### IBGE Municipality GDP

SIDRA table `5938`.

Production scope:

- years: 2016, 2017, 2018;
- territorial level: municipality (`6`);
- variables: `37`, `498`, `513`, `517`, `525`, `6575`.

The selected variables cover GDP at current prices plus total and sector gross value added. Participation/share variables are intentionally outside the current production contract.

Natural key:

```text
(municipality_code, reference_year, variable_code)
```

Bronze contract:

- `municipality_code STRING`;
- `reference_year STRING`;
- `variable_code STRING`;
- `dt_base DATE`;
- `payload VARIANT`;
- `request_id STRING`;
- `ingestion_timestamp TIMESTAMP`.

Write strategy: idempotent `MERGE`.

Layout: Liquid Clustering by `dt_base`.

GDP requests are bounded to one `year × variable × all municipalities` slice. The current 3-year × 6-variable scope therefore executes 18 SIDRA requests under one ingestion request context and performs one logical Bronze write.

Final Databricks validation for this feature produced:

- `100260` rows total;
- 18 year × variable combinations;
- `5570` rows / `5570` unique municipalities in every combination;
- `special_value_rows = 0` for the approved scope;
- key uniqueness, payload preservation, annual `dt_base`, municipality-code compatibility, clustering and idempotent re-execution all validated.

The `5570` GDP cardinality is observed source evidence for this SIDRA table/scope, not a permanent contract. It differs from the `5571` municipality cardinality observed in the population/Localidades validations.

See `docs/development/ibge-municipality-gdp.md` for the complete feature contract and validation evidence.

## Reusable SIDRA Infrastructure

IBGE SIDRA ingestion shares:

- `SidraClient` — transport;
- `SidraQuery` — query contract;
- `SidraDataset` — logical dataset configuration;
- `SidraParser` — source header decoding;
- common HTTP timeout/retry/backoff/logging capabilities.

Dataset-specific semantics remain in their own extractor/service/writer/configuration code. New SIDRA datasets should reuse this stack rather than create a parallel transport/parser implementation.

## Job Entrypoints

### Weather

```text
olist_data_platform.jobs.weather_ingestion
```

### Olist Customers

```text
olist_data_platform.jobs.olist_customers_ingestion
```

### Olist Closed Deals

```text
olist_data_platform.jobs.olist_closed_deals_ingestion
```

### IBGE Localidades

```text
olist_data_platform.jobs.ibge_municipalities_ingestion
```

### IBGE Municipality Population

```text
olist_data_platform.jobs.ibge_municipality_population_ingestion
```

### IBGE Municipality GDP

```text
olist_data_platform.jobs.ibge_municipality_gdp_ingestion
```

Deployment and scheduling remain separate from Python application composition and are part of the deployment/orchestration roadmap.

## Data Sources

### Olist

The public Olist Brazilian e-commerce dataset is the primary analytical source and foundation for the Customer Intelligence data product.

### Open-Meteo

Open-Meteo provides historical weather enrichment and demonstrates reusable API communication, semi-structured Bronze landing, request metadata, idempotent Delta persistence, explicit reprocessing and Liquid Clustering.

### IBGE

IBGE provides municipality/locality and socioeconomic enrichment.

Current implemented API datasets:

- Localidades municipalities;
- SIDRA municipality population;
- SIDRA municipality GDP / gross value added.

Additional IBGE datasets should only be added when a concrete analytical or engineering requirement justifies them.

## Development Environment

Requirements:

- Python 3.11+
- Java 17+
- `uv`

Java 17 or newer is required for local PySpark integration tests.

Databricks validation of Bronze `VARIANT` and managed-table clustering behavior requires a compatible Databricks Runtime.

Synchronize dependencies:

```powershell
uv sync
```

Runtime and development dependencies are resolved from `pyproject.toml` and locked in `uv.lock`.

## Testing

Unit tests:

```powershell
uv run pytest tests/unit -q
```

Integration tests:

```powershell
uv run pytest tests/integration -q
```

Full suite:

```powershell
uv run pytest -q
```

Lint/type checks:

```powershell
uv run ruff check .
uv run ty check
```

Some behaviors, including Databricks Delta `VARIANT` and managed Liquid Clustering metadata, are validated in Databricks notebooks in addition to local tests.

## Engineering Principles

1. Architecture should solve real project problems rather than maximize the technology stack.
2. Reusable abstractions should emerge from concrete reuse.
3. Source-specific behavior stays close to its domain.
4. Shared technical capabilities belong in `platform/`.
5. Bronze, Silver and Gold have distinct responsibilities.
6. Schemas and persistence behavior should be explicit.
7. Idempotency and controlled reprocessing are first-class requirements.
8. Tests are part of the architecture.
9. Data Quality and observability should become first-class capabilities.
10. Durable architectural decisions with meaningful alternatives should be documented as ADRs.
11. Professional architectures may inspire principles, but third-party code, rules, datasets or intellectual property must not be copied into the portfolio.

## Development Gates

Relevant features follow:

```text
Discovery
→ Requirements
→ Technical Design
→ Impact Analysis
→ Approved Plan
→ Implementation
→ Validation
→ Done
```

Completed feature scope must not silently expand after `Done`; a material extension starts a new feature/gate cycle.

## Current State

Completed and merged into `dev`:

- Weather Bronze;
- Olist Customers Bronze;
- Olist Closed Deals Bronze;
- IBGE Localidades Bronze;
- IBGE municipality population Bronze;
- IBGE municipality GDP Bronze.

The municipality GDP feature was merged through PR #6 on 2026-08-24, merge commit `cff34e52179ff532e1c9bd2567ee85325b334e1b`.

## Near-term Roadmap

The next feature is intentionally **not selected in this README**. Before implementation, re-evaluate the current `dev` branch and backlog and choose the next work item explicitly.

Durable candidates/capabilities include:

- additional justified Bronze/source ingestion;
- Table Contracts;
- reusable Delta table lifecycle management;
- explicit table-layout strategy;
- Data Quality framework;
- Silver architecture/modeling;
- Gold/data-product architecture;
- incremental processing, backfill and replay;
- Databricks Asset Bundles deployment/orchestration;
- observability;
- governance / Unity Catalog.

Databricks remains the project's primary specialization, but the portfolio is intentionally not limited to the Databricks ecosystem.
