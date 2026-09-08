# Olist Customer Intelligence

Olist Customer Intelligence is a production-oriented Data Engineering portfolio built around the Olist public e-commerce dataset and justified external data sources.

The repository demonstrates not only ingestion code, but the platform boundaries needed to deliver and operate data workloads safely: executable contracts, Delta lifecycle management, governance metadata, first-class Data Quality, structured operational evidence, tests, Databricks Asset Bundles and controlled `dev -> stg -> prd` promotion.

## Source of truth

Use the project sources according to the question being answered:

1. **`main`** — implemented/executable baseline.
2. **Platform Status** — canonical human-readable checkpoint for delivered datasets, capabilities and environment readiness.
3. **GitHub Issues** — canonical backlog and future work.
4. **Accepted ADRs** — durable architectural decisions.
5. **README** — portfolio summary derived from the sources above.

Feature/gate documents remain valuable technical records, but may preserve historical `pending` / `in progress` wording from the time a delivery gate was written. They do not override Platform Status for current readiness.

## Start here

If you are evaluating the project as a portfolio, read these pages first:

1. **Platform Status** — what exists now, environment-by-environment evidence, limitations and current boundary.
2. **Architecture** — end-to-end system, Data Plane / Control Plane and delivery boundaries.
3. **Data Features** — detailed contracts, runtime behavior and feature-level evidence.

The remaining sections are the technical deep dive: ADRs, standards, runbooks, delivery records and generated API documentation.

## Delivered platform foundation

The current repository includes:

- hybrid Platform + Domains Python architecture;
- lightweight/source-faithful Bronze persistence;
- file-snapshot, HTTP/SIDRA and Azure PostgreSQL/JDBC ingestion paths;
- reusable HTTP/retry/logging foundations;
- executable Delta dataset contracts;
- `DeltaTableLifecycle` and `BronzeWriter` responsibility split;
- conservative schema evolution and metadata reconciliation;
- Unity Catalog governance metadata and ABAC policy foundations;
- lightweight first-class PySpark Data Quality contracts/rules/results;
- environment-isolated administrative Control Plane for execution and quality history;
- Databricks Asset Bundles for `dev`, `stg` and `prd` with separate data/admin catalogs;
- immutable staging-to-production wheel promotion;
- manifest-driven deployment-smoke coverage;
- dependency-aware smoke scheduling with bounded parallelism;
- GitHub Actions CI/CD and documentation gates;
- MkDocs Material documentation published from `main`.

The exact dataset inventory and the distinction between code presence, DEV runtime acceptance, STG smoke evidence and PRD readiness intentionally live in **Platform Status** rather than being duplicated here.

## Delivery evidence model

A feature is not publicly `DONE` merely because code was merged. Current readiness is established through accepted evidence and closeout:

```text
feature implementation
  -> runtime evidence appropriate to scope
  -> merge / promotion gates
  -> closeout
  -> Platform Status update
  -> DONE
```

The deployment-smoke plane is explicitly smaller than full runtime regression. Its current scheduler validates a manifest-driven DAG, runs independent nodes concurrently within a bounded worker limit, and preserves dependency/failure semantics. Full per-dataset runtime acceptance remains separate evidence.

## Documentation model

```text
Canonical current state
    |
    +-- Platform Status
    +-- main implementation
    +-- GitHub Issues
    +-- accepted ADRs
    |
    v
Portfolio surfaces
    +-- README
    +-- Architecture
    |
    v
Technical / historical detail
    +-- Engineering standards / DoD
    +-- Platform & Delivery records
    +-- Feature documentation
    +-- API Reference
```

Documentation is versioned with code, validated with `mkdocs build --strict`, and published from the stable `main` branch.
