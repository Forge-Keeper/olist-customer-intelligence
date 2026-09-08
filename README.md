# Olist Customer Intelligence

<p align="center">
  <strong>Production-oriented Databricks data platform portfolio</strong><br/>
  PySpark · Delta Lake · Unity Catalog · Data Quality · Databricks Asset Bundles · GitHub Actions
</p>

<p align="center">
  <a href="https://github.com/Forge-Keeper/olist-customer-intelligence/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Forge-Keeper/olist-customer-intelligence/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/Forge-Keeper/olist-customer-intelligence/actions/workflows/docs.yml"><img alt="Documentation" src="https://github.com/Forge-Keeper/olist-customer-intelligence/actions/workflows/docs.yml/badge.svg?branch=main"></a>
  <a href="https://forge-keeper.github.io/olist-customer-intelligence/"><img alt="Engineering documentation" src="https://img.shields.io/badge/docs-engineering%20portal-0969da"></a>
</p>

A small data platform foundation built around the Olist public e-commerce dataset and justified external sources to demonstrate production Data Engineering concerns: explicit contracts, idempotent persistence, Data Quality, operational evidence, governance, CI/CD and controlled environment promotion.

> **Source of truth**
>
> `main` represents the implemented code baseline.  
> [Platform Status](docs/platform-status.md) is the canonical human-readable view of delivered datasets, capabilities and environment readiness.  
> [GitHub Issues](https://github.com/Forge-Keeper/olist-customer-intelligence/issues) are the canonical backlog.  
> [ADRs](docs/adr/) record accepted architectural decisions.  
> This README is a portfolio overview and may intentionally summarize those sources.

## Portfolio snapshot

- **Databricks / PySpark / Delta Lake** as the core execution and persistence stack;
- source-faithful Bronze ingestion across file snapshots, HTTP APIs / SIDRA and an Azure PostgreSQL/JDBC path;
- executable dataset contracts, explicit logical keys and fail-fast schema-drift handling;
- first-class PySpark **Data Quality** with persisted rule evidence and blocking write gates;
- **Unity Catalog** metadata/governance foundation, ABAC policy lifecycle and justified Liquid Clustering;
- **Databricks Asset Bundles** with isolated `dev`, `stg` and `prd` targets;
- immutable wheel promotion from staging to production through **GitHub Actions**;
- dependency-aware deployment smokes with bounded parallelism and retained per-job evidence.

> **Current boundary:** the delivered scope is the Bronze/platform foundation. Silver, Gold and the final Customer Intelligence analytical product remain roadmap work and are not represented as completed implementations.

[📚 Full Engineering Documentation](https://forge-keeper.github.io/olist-customer-intelligence/)

## What is implemented

### Data ingestion and Bronze persistence

Current delivered sources include authoritative Olist CSV snapshots, Open-Meteo, IBGE APIs / SIDRA and a DEV-validated Azure PostgreSQL/JDBC path for ANP fuel prices.

The exact dataset list and environment readiness matrix intentionally live in [Platform Status](docs/platform-status.md) rather than being duplicated here.

Bronze is intentionally lightweight and source-faithful: source semantics are preserved, technical metadata is explicit and business normalization is deferred to downstream analytical layers.

### Platform capabilities

- modular Python package using a hybrid **Platform + Domains** structure;
- reusable HTTP/retry/logging infrastructure;
- reusable PostgreSQL and JDBC access infrastructure for operational-source ingestion;
- executable `DatasetContract` definitions;
- reusable `DeltaTableLifecycle`;
- `BronzeWriter` with explicit write strategies, idempotent behavior and checked-batch evidence reuse;
- lightweight first-class PySpark Data Quality contracts, rules and structured results;
- persisted `ERROR` / `WARNING` / `INFO` quality evidence;
- environment-isolated administrative Control Plane for execution history and Data Quality results;
- controlled schema-evolution policy with fail-fast drift handling;
- metadata reconciliation for table/column descriptions and tags;
- Unity Catalog governance foundation and ABAC policy lifecycle;
- Liquid Clustering where justified by dataset access/layout needs;
- Databricks Asset Bundles with `dev`, `stg` and `prd` data/admin targets;
- immutable wheel promotion from staging to production;
- manifest-driven deployment smoke coverage with a DAG-aware scheduler and bounded concurrency;
- GitHub Actions quality, documentation and deployment workflows;
- MkDocs Material engineering portal published through GitHub Pages.

## Architecture

```text
Olist CSV      ANP / Azure PostgreSQL      Open-Meteo      IBGE APIs / SIDRA
    \                   |                       |                  /
     +------------------+-----------------------+-----------------+
                                |
                                v
                       Domain ingestion services
                                |
                                v
                        source/domain adapters
                                |
                                v
                        DataQualityRunner
                         /             \
                        v               v
             quality evidence      checked batch
                        |               |
                        v               v
              Admin Control Plane   BronzeWriter
                        |               |
                        |       +-------+--------+
                        |       |                |
                        |       v                v
                        | DatasetContract  DeltaTableLifecycle
                        |       |                |
                        |       +-------+--------+
                        |               |
                        v               v
                execution_runs /      business Delta tables
                data_quality_results      / Unity Catalog
```

The ANP path enters the platform from Azure PostgreSQL through JDBC. Its accepted environment readiness is intentionally narrower than the file/API paths; consult [Platform Status](docs/platform-status.md) for the current matrix rather than inferring readiness from code presence.

The GDP workload was the first consumer of the first-class Data Quality path. Adoption now varies by dataset and is tracked as an explicit capability/readiness concern instead of being inferred from Bronze delivery alone.

Deployment is a separate delivery plane:

```text
topic branch -> dev -> main -> stg -> protected prd
                                |
                                v
                   manifest-driven smoke DAG
                   bounded parallel execution
```

`main` is the stable executable baseline for shared deployment. Staging validates the approved artifact before protected production promotion, and the same retained wheel is reused for PRD.

For the complete architecture and delivery boundary, use the documentation site pages **Architecture** and **Platform Status**.

## Package structure

```text
src/olist_data_platform/
├── platform/
│   ├── delta/
│   ├── governance/
│   ├── http/
│   ├── logging/
│   ├── operations/
│   └── quality/
├── domains/
│   ├── ingestion/
│   │   ├── ibge/
│   │   ├── olist/
│   │   └── weather/
│   ├── bronze/
│   │   ├── ibge/
│   │   ├── olist/
│   │   └── weather/
│   ├── silver/
│   ├── gold/
│   └── customer_intelligence/
└── jobs/
```

`platform/` owns reusable technical capabilities. `domains/` owns source/product-specific behavior. `jobs/` owns executable application composition. Deployment/orchestration stays in repository-owned DAB and GitHub Actions configuration rather than application code.

## Bronze design

Core rules:

- preserve source semantics / AS-IS values;
- use explicit persisted schemas and technical metadata;
- make logical keys and idempotency explicit;
- use `MERGE`, `FULL_REPLACE` or bounded reprocessing according to the source contract;
- use partitioning or Liquid Clustering only when justified;
- preserve semi-structured source payloads in `VARIANT` when this protects fidelity;
- fail on incompatible table drift rather than silently widening production state.

Relevant ADRs are under `docs/adr/`.

## Data Quality and operational evidence

`DataQualityContract` is intentionally separate from the persisted `DatasetContract`. Rules carry stable IDs, versions, categories and severities; evaluation produces structured PASS/FAIL evidence before protected writes where the first-class path is adopted.

- failed `ERROR` rules reject the protected write;
- `WARNING` and `INFO` do not block;
- quality evidence is persisted in `<admin_catalog>.quality.data_quality_results`;
- execution lifecycle is persisted in `<admin_catalog>.operations.execution_runs`;
- both are correlated by one platform `run_id`;
- passing key-integrity evidence can be consumed by `BronzeWriter.write_checked()` without repeating equivalent logical-key scans.

Exact per-dataset rule sets and accepted runtime evidence belong to feature documentation and [Platform Status](docs/platform-status.md), not this portfolio summary.

## Testing and quality gates

```powershell
uv sync
uv run ruff check .
uv run ty check
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest -q
```

Some Databricks-specific behaviors such as managed Delta metadata, `VARIANT`, clustering, Unity Catalog governance, Data Quality persistence/write-gate behavior and deployment are validated in workspace/runtime checks in addition to local tests.

Documentation is validated with:

```powershell
uv run mkdocs build --strict
```

## Delivery and environments

The mandatory Git path is:

```text
topic branch -> PR into dev -> merge dev
-> PR dev into main -> merge main
-> automatic staging deployment/validation
-> protected production promotion
```

DAB provides distinct Unity Catalog Data Plane and Control Plane targets:

- `dev` -> `dev` + `dev_admin`;
- `stg` -> `stg` + `stg_admin`;
- `prd` -> `prd` + `prd_admin`.

The staging-approved wheel is retained with integrity metadata and reused for production promotion; production is not rebuilt from materially different source after staging acceptance. Workload identities require explicit least-privilege access to the relevant data and administrative catalogs before execution.

## Governance

The platform separates dataset facts from access policies:

- `DatasetContract` / `ColumnContract` represent persisted schema and metadata, including approved table/column tags;
- `DeltaTableLifecycle` reconciles table state and metadata;
- governance policy definitions/lifecycle own centralized ABAC row-filter and column-mask policies;
- public datasets are not assigned fabricated sensitivity metadata merely to demonstrate governance capabilities.

Project status follows a separate evidence rule: a merge does not by itself make a feature publicly `DONE`. Closeout evidence must update [Platform Status](docs/platform-status.md) with the stage actually reached.

## Documentation

The MkDocs site is the public engineering portal. It contains:

- portfolio-oriented architecture and platform-status pages;
- engineering standards and Definition of Done;
- branch and deployment runbooks;
- DAB design/delivery records;
- Data Quality / Control Plane feature documentation;
- ADRs;
- generated API reference through `mkdocstrings`.

Historical feature/gate documents are retained for traceability and may describe the state at the time they were written. They do not override the current readiness recorded in Platform Status.

## Current boundary and roadmap

Delivered scope is currently centered on the Bronze/platform foundation. Silver, Gold and the final Customer Intelligence analytical product remain future layers; their package boundaries exist but they are not represented as completed analytical implementations.

First-class Data Quality adoption, runtime acceptance depth and operational hardening vary by dataset and must be justified by concrete requirements. Full regression of every workload on every deployment is intentionally not part of the deployment smoke strategy.

Future work is selected from GitHub Issues rather than inferred from README wording or historical feature plans.

## Engineering principles

1. Solve concrete project problems before adding abstractions.
2. Reuse should emerge from demonstrated repetition.
3. Keep source-specific behavior close to its domain.
4. Keep shared technical capabilities in `platform/`.
5. Treat idempotency, contracts and failure behavior as first-class concerns.
6. Keep environment resolution outside domain/application logic.
7. Treat tests and documentation as delivery artifacts.
8. Record durable architectural decisions as ADRs.
9. Do not add technologies merely to inflate the visible stack.
