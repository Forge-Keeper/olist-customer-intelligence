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

## Portfolio snapshot

- **Databricks / PySpark / Delta Lake** as the core execution and persistence stack;
- source-faithful Bronze ingestion across **Olist CSV, Open-Meteo and IBGE APIs / SIDRA**;
- executable dataset contracts, explicit logical keys and fail-fast schema-drift handling;
- first-class PySpark **Data Quality** with persisted rule evidence and blocking write gates;
- **Unity Catalog** metadata/governance foundation, ABAC policy lifecycle and justified Liquid Clustering;
- **Databricks Asset Bundles** with isolated `dev`, `stg` and `prd` targets;
- immutable wheel promotion from staging to production through **GitHub Actions**;
- real DEV evidence: **33,420 GDP rows**, **8 passing quality rules**, and a deliberate duplicate-key batch rejected with **0 records written**.

> **Current boundary:** the delivered scope is the Bronze/platform foundation. Silver, Gold and the final Customer Intelligence analytical product remain roadmap work and are not represented as completed implementations.

[📚 Full Engineering Documentation](https://forge-keeper.github.io/olist-customer-intelligence/)

## What is implemented

### Data ingestion and Bronze persistence

Implemented Bronze vertical slices:

- Weather / Open-Meteo;
- Olist Customers;
- Olist Closed Deals;
- IBGE Localidades / municipalities;
- IBGE municipality population;
- IBGE municipality GDP / VAB;
- IBGE CEMPRE municipal business activity for 2016–2018.

Bronze is intentionally lightweight and source-faithful: source semantics are preserved, technical metadata is explicit and business normalization is deferred to downstream analytical layers.

### Platform capabilities

- modular Python package using a hybrid **Platform + Domains** structure;
- reusable HTTP/retry/logging infrastructure;
- executable `DatasetContract` definitions;
- reusable `DeltaTableLifecycle`;
- `BronzeWriter` with explicit write strategies, idempotent behavior and checked-batch evidence reuse;
- lightweight first-class PySpark Data Quality contracts, rules and structured results;
- persisted `ERROR` / `WARNING` / `INFO` quality evidence;
- environment-isolated administrative Control Plane for execution history and Data Quality results;
- GDP pre-write Data Quality gate validated in real DEV runtime;
- controlled schema-evolution policy with fail-fast drift handling;
- metadata reconciliation for table/column descriptions and tags;
- Unity Catalog governance foundation and ABAC policy lifecycle;
- Liquid Clustering where justified by dataset access/layout needs;
- Databricks Asset Bundles with `dev`, `stg` and `prd` data/admin targets;
- immutable wheel promotion from staging to production;
- GitHub Actions quality, documentation and deployment workflows;
- MkDocs Material engineering portal published through GitHub Pages.

## Architecture

```text
Olist CSV        Open-Meteo         IBGE APIs / SIDRA
    \                |                    /
     +---------------+-------------------+
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

The GDP workload is the first consumer of the first-class Data Quality path. Existing non-migrated Bronze datasets retain their current contract/source/writer validations until a concrete migration is justified.

Deployment is a separate delivery plane:

```text
topic branch -> dev -> main -> stg -> prd
                                ^      ^
                                |      |
                         same validated wheel
```

`main` is the stable source for shared deployment. Staging validates the approved artifact before protected production promotion.

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
- use `MERGE` or `FULL_REPLACE` according to the source contract;
- use partitioning or Liquid Clustering only when justified;
- preserve semi-structured source payloads in `VARIANT` when this protects fidelity;
- fail on incompatible table drift rather than silently widening production state.

Relevant ADRs are under `docs/adr/`.

## Data Quality and operational evidence

`DataQualityContract` is intentionally separate from the persisted `DatasetContract`. Rules carry stable IDs, versions, categories and severities; evaluation produces structured PASS/FAIL evidence before the protected write.

For the GDP pilot:

- failed `ERROR` rules reject the Bronze write;
- `WARNING` and `INFO` do not block;
- quality evidence is persisted in `<admin_catalog>.quality.data_quality_results`;
- execution lifecycle is persisted in `<admin_catalog>.operations.execution_runs`;
- both are correlated by one platform `run_id`;
- passing key-integrity evidence can be consumed by `BronzeWriter.write_checked()` without repeating equivalent logical-key scans.

The real DEV proof for period 2018 produced 33,420 Bronze rows with 33,420 distinct natural keys and eight passing quality-rule results. A deliberate duplicate-key batch failed `GDP-DQ03`, recorded `REJECTED` / `FAILED` with `records_written = 0`, and left the isolated Bronze validation table unchanged.

## Data sources and delivered datasets

| Source | Delivered slices | Persistence behavior |
| --- | --- | --- |
| Olist | Customers, Closed Deals | authoritative CSV snapshots / `FULL_REPLACE` after validation |
| Open-Meteo | historical weather | idempotent `MERGE` |
| IBGE Localidades | municipalities | dated source snapshot / `MERGE` |
| IBGE SIDRA 6579 | municipality population | annual slices / `MERGE` |
| IBGE SIDRA 5938 | municipality GDP/VAB | bounded year × variable slices / `MERGE` with first-class pre-write DQ |
| IBGE SIDRA 1685 | CEMPRE municipal business activity | 2016–2018 year × variable slices / `MERGE` |

The reusable SIDRA stack includes `SidraClient`, `SidraQuery`, `SidraDataset` and `SidraParser`; dataset semantics remain in dedicated extractors/services/writers.

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

## Documentation

The MkDocs site is the public engineering portal. It contains:

- portfolio-oriented architecture and platform-status pages;
- engineering standards and Definition of Done;
- branch and deployment runbooks;
- DAB design/delivery records;
- Data Quality / Control Plane feature documentation;
- ADRs;
- generated API reference through `mkdocstrings`.

GitHub remains the source of truth for both code and documentation.

## Current boundary and roadmap

Delivered scope is currently centered on the Bronze/platform foundation, now including the first-class GDP Data Quality pilot and administrative Control Plane. Silver, Gold and the final Customer Intelligence analytical product remain future layers; their package boundaries exist but they are not represented as completed analytical implementations.

First-class Data Quality adoption beyond GDP, broader observability and shared-environment runtime hardening remain future work to be justified by concrete requirements. Full regression of every workload on every deployment is intentionally not part of the deployment smoke strategy; smoke coverage should remain targeted, cheap and explicit.

Future work must be selected from the current GitHub backlog rather than inferred from historical README checkpoints.

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
