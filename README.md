# Olist Customer Intelligence

End-to-end Data Engineering platform built with the public Olist
Brazilian E-Commerce dataset.

The project is designed as a portfolio-grade data platform to
demonstrate how a data product can be designed, tested, deployed,
operated, and evolved using modern Data Engineering practices.

## Objectives

The project progressively demonstrates:

-   Databricks and Apache Spark / PySpark
-   Delta Lake and Medallion Architecture
-   Unity Catalog and data governance
-   REST API ingestion
-   explicit schemas and idempotent data processing
-   Data Quality and observability
-   automated tests
-   CI/CD and deployment automation
-   performance and table layout decisions
-   feature engineering and MLflow
-   architecture documentation and engineering trade-offs

The goal is not to maximize the number of technologies in the stack. New
tools are introduced only when they solve a concrete engineering problem
and their architectural role can be explained and defended.

## Current Architecture

The source code is organized under `src/olist_data_platform/`.

``` text
src/olist_data_platform/
├── common/
│   └── logging/
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

Current responsibilities include:

-   `ingestion/api` --- external API clients, including Open-Meteo
-   `ingestion/parsers` --- conversion of API payloads into structured
    records
-   `ingestion/services` --- ingestion workflow coordination
-   `ingestion/writers` --- persistence into Delta Bronze tables
-   `common/logging` --- shared structured logging
-   `transformations` --- Silver/Gold transformations
-   `quality` --- Data Quality capabilities
-   `features` --- analytical and ML feature engineering
-   `ml` --- machine-learning-related components

The architecture is evolving incrementally. Components listed above may
be at different implementation stages.

## Data Architecture

The project follows a Medallion-oriented architecture:

``` text
Sources
   │
   ├── Olist public dataset
   └── External APIs
          │
          ▼
       Bronze
          │
          ▼
       Silver
          │
          ▼
        Gold
          │
          ├── Analytics
          └── Feature Engineering / ML
```

Bronze preserves source semantics while enforcing technical contracts
such as explicit schemas and technical metadata. Business
transformations belong to downstream layers.

Delta table layout decisions are treated as architectural decisions. The
current direction for managed Delta tables is Liquid Clustering rather
than Hive-style partitioning; see the ADRs under `docs/adr/`.

## Engineering Principles

-   Idempotency is a first-class requirement.
-   Bronze uses explicit schemas instead of schema inference.
-   Reprocessing should be selective rather than full-table overwrite
    when possible.
-   Business transformations do not belong in Bronze.
-   Structured logging follows consistent event and `key=value`
    conventions.
-   Changes in persistence behavior require corresponding tests.
-   Native Spark, Delta, Lakeflow, and Unity Catalog capabilities are
    preferred over unnecessary custom implementations.
-   Architecture choices should be documented when the trade-off is
    non-trivial.

## Tests and Code Quality

The project uses:

-   `pytest` for unit and integration tests
-   local Spark fixtures for integration tests where Spark behavior must
    be exercised
-   `ruff` for linting
-   Python 3.11+
-   explicit type annotations

Install development dependencies:

``` bash
pip install -e ".[dev]"
```

Run the test suite:

``` bash
pytest
```

Run only unit tests:

``` bash
pytest tests/unit
```

Run linting:

``` bash
ruff check .
```

## Deployment Automation

Databricks Asset Bundles (DAB) are being introduced as the deployment
and Databricks resource configuration mechanism for the project.

The intended lifecycle is:

``` text
code
  ↓
tests + lint
  ↓
bundle validate
  ↓
bundle deploy
  ↓
bundle run
```

The first implementation will remain intentionally small: establish a
valid Bundle, externalize environment-specific configuration, define
development/production targets, and automate one vertical workflow
before expanding Bundle coverage.

Detailed implementation and operating guidance lives in:

`docs/development/databricks-asset-bundles.md`

DAB configuration itself remains the source of truth for deployed
Databricks resources; documentation explains how and why the project
uses that configuration.

## Environments

The deployment model is being prepared around explicit Bundle targets:

-   `dev` --- active development and validation
-   `prod` --- production-oriented configuration and deployment boundary

Environment-specific values such as catalogs, schemas, resource names,
and execution configuration should be externalized instead of hard-coded
into application logic.

Bundle deployment variables and runtime Job/Task parameters are treated
as separate concerns.

## CI/CD Direction

The planned CI/CD flow is:

``` text
Pull Request
   ↓
Ruff
   ↓
pytest
   ↓
databricks bundle validate
   ↓
merge
   ↓
deployment
```

Automated deployment will only be enabled after authentication,
environment boundaries, and the available Databricks environment have
been validated.

Terraform is not being introduced merely to increase stack breadth. Its
role will be evaluated later if infrastructure requirements emerge that
are not appropriately owned by Databricks Asset Bundles.

## Documentation

``` text
docs/
├── adr/          # durable architectural decisions and trade-offs
└── development/  # development, deployment, and operational practices
```

ADRs are reserved for decisions whose rationale and consequences need to
survive beyond the implementation itself.

Operational tooling such as Databricks Asset Bundles is documented under
`docs/development/` unless its adoption introduces a separate
architectural decision that warrants an ADR.

## Roadmap

Near-term engineering milestones include:

1.  Introduce Databricks Asset Bundles.
2.  Define environment-aware deployment configuration.
3.  Automate an initial Databricks workflow.
4.  Integrate Bundle validation into CI/CD.
5.  Continue evolving Data Quality and observability.
6.  Expand Silver/Gold processing and analytical outputs.
7.  Evaluate cloud integration where it solves a real architectural or
    learning objective.

A focused AWS S3 + Databricks lab is also planned to build practical
S3/IAM experience and revisit Unity Catalog external storage concepts
without artificially introducing unrelated AWS services.

## Architectural Decisions

Architectural Decision Records are stored in:

`docs/adr/`

The repository currently includes the decision covering Liquid
Clustering for the Bronze weather data path.

## Dataset

The project uses the public Olist Brazilian E-Commerce dataset as its
primary business dataset and external public APIs where they add a
meaningful Data Engineering use case.

## Status

Active development.

The repository is intentionally evolving in small, explainable
increments so that each feature represents an engineering problem, an
implementation decision, and a testable capability rather than a
collection of disconnected technologies.
