# Olist Customer Intelligence

Olist Customer Intelligence is a production-oriented Data Engineering portfolio built around the Olist public e-commerce dataset and justified external data sources.

The repository demonstrates not only ingestion code, but the platform boundaries needed to deliver and operate data workloads safely: executable contracts, Delta lifecycle management, governance metadata, first-class Data Quality, structured operational evidence, tests, Databricks Asset Bundles and controlled `dev -> stg -> prd` promotion.

## Start here

If you are evaluating the project as a portfolio, read these pages first:

1. **Architecture** — end-to-end system, Data Plane / Control Plane and delivery boundaries.
2. **Platform Status** — what is delivered, what remains intentionally out of scope and known technical debt.
3. **Data Features** — concrete datasets implemented on top of the platform.

The remaining sections are the technical deep dive: ADRs, standards, runbooks, delivery records and generated API documentation.

## Delivered platform foundation

The current repository implements and validates:

- hybrid Platform + Domains Python architecture;
- lightweight/source-faithful Bronze persistence;
- reusable HTTP/retry/logging foundations;
- executable Delta dataset contracts;
- `DeltaTableLifecycle` and `BronzeWriter` responsibility split;
- conservative schema evolution and metadata reconciliation;
- Unity Catalog governance metadata and ABAC policy foundations;
- lightweight first-class PySpark Data Quality contracts/rules/results;
- environment-isolated administrative Control Plane for execution and quality history;
- GDP pre-write Data Quality gate with persisted evidence and checked-batch key reuse;
- Databricks Asset Bundles for `dev`, `stg` and `prd` with separate data/admin catalogs;
- immutable staging-to-production wheel promotion;
- GitHub Actions CI/CD and documentation gates;
- MkDocs Material documentation published from `main`.

The GDP Data Quality pilot has real DEV runtime evidence for both an accepted 2018 execution and a deliberately rejected duplicate-key batch that left Bronze unchanged. Earlier GDP deployment work also proved the shared promotion path through staging and production. CEMPRE remains another DAB-managed workload and the broader deployment smoke-coverage gap is tracked separately as technical debt.

## Delivered data slices

- Weather / Open-Meteo;
- Olist Customers;
- Olist Closed Deals;
- IBGE Localidades / municipalities;
- IBGE municipality population;
- IBGE municipality GDP / VAB;
- IBGE CEMPRE municipal business activity, 2016–2018.

## Documentation model

```text
Portfolio entry pages
    |
    +-- Architecture
    +-- Platform Status
    |
    v
Technical deep dive
    +-- Engineering standards / DoD
    +-- Platform & Delivery records
    +-- Feature documentation
    +-- ADRs
    +-- API Reference
```

Documentation is versioned with the code, validated with `mkdocs build --strict`, and published from the stable `main` branch. GitHub remains the source of truth.
