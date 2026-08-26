# Olist Customer Intelligence

Production-oriented Data Engineering portfolio built around the Olist public e-commerce dataset and justified external data sources.

The project has evolved from isolated ingestion pipelines into a small Databricks-oriented data platform foundation with explicit contracts, Delta lifecycle management, governance metadata, CI/CD and controlled environment promotion.

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
- `BronzeWriter` with explicit write strategies and idempotent behavior;
- controlled schema-evolution policy with fail-fast drift handling;
- metadata reconciliation for table/column descriptions and tags;
- Unity Catalog governance foundation and ABAC policy lifecycle;
- Liquid Clustering where justified by dataset access/layout needs;
- Databricks Asset Bundles with `dev`, `stg` and `prd` targets;
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
             Bronze adapters/writers
                     |
                     v
               BronzeWriter
                     |
          +----------+-----------+
          |                      |
          v                      v
   DatasetContract       DeltaTableLifecycle
          |                      |
          +----------+-----------+
                     |
                     v
          Delta tables / Unity Catalog
                     |
                     v
        metadata + governance / ABAC
```

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

## Data sources and delivered datasets

| Source | Delivered slices | Persistence behavior |
| --- | --- | --- |
| Olist | Customers, Closed Deals | authoritative CSV snapshots / `FULL_REPLACE` after validation |
| Open-Meteo | historical weather | idempotent `MERGE` |
| IBGE Localidades | municipalities | dated source snapshot / `MERGE` |
| IBGE SIDRA 6579 | municipality population | annual slices / `MERGE` |
| IBGE SIDRA 5938 | municipality GDP/VAB | bounded year × variable slices / `MERGE` |
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

Some Databricks-specific behaviors such as managed Delta metadata, `VARIANT`, clustering, Unity Catalog governance and deployment are validated in workspace smoke tests in addition to local tests.

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

DAB provides distinct Unity Catalog targets:

- `dev` -> development catalog;
- `stg` -> shared pre-production catalog;
- `prd` -> production catalog.

The staging-approved wheel is retained with integrity metadata and reused for production promotion; production is not rebuilt from materially different source after staging acceptance.

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
- feature documentation;
- ADRs;
- generated API reference through `mkdocstrings`.

GitHub remains the source of truth for both code and documentation.

## Current boundary and roadmap

Delivered scope is currently centered on the Bronze/platform foundation. Silver, Gold and the final Customer Intelligence analytical product remain future layers; their package boundaries exist but they are not represented as completed analytical implementations.

Known near-term technical debt is tracked in GitHub issues. Full regression of every workload on every deployment is intentionally not part of the deployment smoke strategy; smoke coverage should remain targeted, cheap and explicit.

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
