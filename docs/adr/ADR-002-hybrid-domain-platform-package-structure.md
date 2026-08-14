# ADR-002 — Hybrid Domain and Platform Package Structure

- **Status:** Accepted
- **Date:** 2026-08-14
- **Decision owners:** Project maintainers
- **Scope:** Python package organization for `olist_data_platform`

## Context

The Olist Customer Intelligence project initially evolved around technical responsibilities such as:

```text
src/olist_data_platform/
├── common/
├── ingestion/
│   ├── api/
│   ├── parsers/
│   ├── services/
│   └── writers/
├── transformations/
├── quality/
├── features/
└── ml/
```

This structure was simple and appropriate while the project had few implemented pipelines, but it started to show scaling problems as responsibilities became more specialized.

Weather ingestion, for example, was distributed across different technical folders:

```text
ingestion/api/open_meteo_client.py
ingestion/parsers/weather_response_parser.py
ingestion/services/weather_ingestion_service.py
ingestion/writers/raw_weather_writer.py
ingestion/writers/bronze_weather_writer.py
```

As additional data sources and product capabilities are introduced, such as IBGE APIs, Olist datasets, Silver/Gold transformations, Data Quality, observability, and Customer Intelligence features, keeping components organized only by technical type would increasingly scatter related code across the repository.

A review of a mature professional Data Engineering architecture also reinforced the value of:

- explicit responsibility boundaries;
- reusable platform capabilities separated from domain-specific logic;
- domain-oriented organization for cohesive execution units;
- clear separation between application code and deployment resources.

The goal is to adopt those architectural principles without copying the structure, code, rules, datasets, or proprietary implementation of any third-party system.

## Decision

Adopt a **hybrid package structure** that separates:

1. **Platform capabilities** — reusable technical building blocks that do not depend on a specific business/data domain.
2. **Domains** — cohesive units of Data Engineering behavior and data lifecycle responsibility.
3. **Jobs** — orchestration/composition entrypoints.
4. **Resources** — Databricks deployment resources managed outside the Python application package.

The target direction is:

```text
src/olist_data_platform/
├── platform/
│   ├── http/
│   ├── logging/
│   ├── quality/
│   └── ...
│
├── domains/
│   ├── ingestion/
│   │   ├── weather/
│   │   └── olist/
│   ├── raw/
│   │   ├── weather/
│   │   └── olist/
│   ├── bronze/
│   │   ├── weather/
│   │   └── olist/
│   ├── silver/
│   ├── gold/
│   ├── customer_intelligence/
│   └── ml/
│
└── jobs/
```

Deployment resources remain outside the Python package:

```text
resources/
├── jobs/
└── pipelines/
```

## Current Placement Rules

### `platform/`

A component belongs in `platform/` when it is reusable across multiple domains and does not contain knowledge of a specific source or product domain.

Examples:

```text
platform/http/api_client.py
platform/logging/logger.py
```

`APIClient` belongs in `platform/http/` because the project is expected to integrate with multiple HTTP APIs, including Open-Meteo and IBGE.

A component should not be moved into `platform/` solely because it looks generic. There must be a real or clearly planned cross-domain use.

### `domains/ingestion/`

Contains source-specific acquisition, parsing, and orchestration behavior.

Example:

```text
domains/ingestion/weather/
├── open_meteo_client.py
├── weather_response_parser.py
└── weather_ingestion_service.py
```

`OpenMeteoClient` remains in the Weather ingestion domain because it knows the Open-Meteo contract, endpoints, parameters, and response semantics.

### `domains/raw/`

Contains persistence of original source data before structured Bronze processing.

Example:

```text
domains/raw/weather/
└── raw_weather_writer.py
```

RAW is treated as an explicit technical landing/preservation responsibility, distinct from Bronze.

### `domains/bronze/`

Contains Bronze-layer persistence and technical contracts.

Example:

```text
domains/bronze/weather/
└── bronze_weather_writer.py
```

Bronze remains responsible for structured ingestion data, explicit schema, technical metadata, idempotent persistence behavior, and table-layout configuration.

### `domains/customer_intelligence/`

Represents the primary data product domain of the repository.

This area will contain capabilities that belong to the Customer Intelligence product rather than to a specific ingestion source.

Examples may include:

```text
domains/customer_intelligence/
├── tables/
├── features/
└── quality/
```

Subdirectories should only be introduced when real implementation requires them.

## Architectural Principles

The package structure must follow these rules:

1. Prefer **high cohesion** inside each domain.
2. Keep **cross-domain technical capabilities** in `platform/`.
3. Do not create abstractions or folders before a concrete responsibility exists.
4. Do not treat every dataset as a business domain automatically.
5. Do not treat Medallion layers and business domains as the same concept.
6. Domain-specific clients, parsers, rules, and services stay with their domain.
7. Shared code should move to `platform/` only when reuse is real or clearly justified.
8. Tests should approximately mirror the source package structure.
9. Deployment configuration must remain separate from application logic.
10. Architectural evolution should optimize maintainability and explainability, not stack size.

## Alternatives Considered

### A. Keep the original layer-first technical structure

Example:

```text
ingestion/
├── api/
├── parsers/
├── services/
└── writers/
```

**Rejected because:**

- related domain behavior becomes scattered;
- navigation becomes harder as the number of pipelines grows;
- source-specific and reusable technical code tend to mix;
- a single domain requires traversing multiple repository areas.

### B. Fully domain-first by dataset

Example:

```text
domains/
├── orders/
├── customers/
├── products/
└── weather/
```

**Rejected because:**

- some datasets are sources/entities rather than true functional domains;
- cross-dataset products such as Customer Intelligence would become fragmented;
- Gold/data-product logic could span many source domains;
- this structure risks turning physical datasets into artificial architectural boundaries.

### C. Reproduce a large enterprise workflow/domain structure

**Rejected because:**

- the Olist project is smaller and has different requirements;
- copying a mature enterprise structure would introduce unnecessary complexity;
- folders such as `conditions`, `samples`, `slices`, `models`, or `exclusions` should only exist when the project actually needs those responsibilities;
- the portfolio must demonstrate original engineering decisions rather than architectural imitation.

### D. Hybrid `platform + domains`

**Accepted because:**

- it preserves reusable technical capabilities;
- it increases cohesion for domain-specific workflows;
- it scales better than the original flat technical structure;
- it supports multiple APIs and datasets cleanly;
- it creates a defensible architecture for interviews and documentation;
- it avoids premature enterprise-scale complexity.

## Consequences

### Positive

- Related Weather components are easier to locate and understand.
- Reusable HTTP and logging capabilities have explicit ownership.
- RAW and Bronze responsibilities are visible in the package structure.
- Future APIs such as IBGE can reuse `platform/http/APIClient`.
- The project is better prepared for additional domains and data products.
- Tests can mirror application architecture more clearly.
- Databricks Asset Bundle resources can remain independent from Python package organization.

### Negative

- The migration changes Python namespaces.
- Imports, mocks, patches, scripts, and tests must be updated when packages move.
- Developers need to understand the distinction between `platform`, data lifecycle domains, and product domains.
- The structure is slightly more complex than the original one.

The migration already demonstrated this cost: changing the package structure required updating production imports and the test suite before the repository returned to a fully passing state.

## Migration Guidance

Current mappings include:

```text
olist_data_platform.common.logging
→ olist_data_platform.platform.logging

olist_data_platform.ingestion.api.api_client
→ olist_data_platform.platform.http.api_client

olist_data_platform.ingestion.api.open_meteo_client
→ olist_data_platform.domains.ingestion.weather.open_meteo_client

olist_data_platform.ingestion.parsers.weather_response_parser
→ olist_data_platform.domains.ingestion.weather.weather_response_parser

olist_data_platform.ingestion.services.weather_ingestion_service
→ olist_data_platform.domains.ingestion.weather.weather_ingestion_service

olist_data_platform.ingestion.writers.raw_weather_writer
→ olist_data_platform.domains.raw.weather.raw_weather_writer

olist_data_platform.ingestion.writers.bronze_weather_writer
→ olist_data_platform.domains.bronze.weather.bronze_weather_writer
```

Any future structural migration must update:

- application imports;
- tests;
- `unittest.mock.patch` paths;
- scripts;
- package exports;
- documentation;
- CI/CD configuration if module paths are referenced there.

## Validation

This decision is considered successfully applied when:

- the source tree follows the `platform + domains` boundary;
- no obsolete namespaces remain in application code;
- no obsolete namespaces remain in tests;
- package imports are valid;
- all unit tests pass;
- all integration tests pass;
- Ruff/linting passes;
- new components are placed according to the rules in this ADR.

At the time this ADR was accepted, the migrated test suite was reported as fully passing.

## Follow-up

Future structural decisions should not automatically create new ADRs.

An ADR should be created only when a change introduces a durable architectural choice with meaningful alternatives and consequences.

Examples that may require separate ADRs:

- DAB versus Terraform responsibility boundaries;
- Job-based orchestration versus Lakeflow Spark Declarative Pipelines for a specific workflow;
- table-layout strategy changes;
- data contract strategy;
- data product ownership boundaries.

Simple file placement or routine package additions should follow this ADR without creating additional architectural records.
