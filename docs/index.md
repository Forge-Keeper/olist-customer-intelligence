# Olist Customer Intelligence

This site is the living engineering reference for the Olist Customer Intelligence data platform.

Its purpose is to make architecture, delivery standards, platform contracts, governance decisions, operational runbooks and public Python APIs discoverable from one place while keeping GitHub as the source of truth.

## Platform status

The first platform foundation is now implemented and validated end to end:

- isolated Unity Catalog environments for `dev`, `stg` and `prd`;
- executable Delta dataset contracts and lifecycle management;
- controlled schema evolution and metadata reconciliation;
- Unity Catalog governance foundations, including ABAC smoke validation;
- Databricks Asset Bundles for repeatable deployment;
- immutable wheel promotion from staging to production;
- protected production deployment with retained evidence;
- environment-specific runtime hardcodes removed from application code;
- mandatory Git promotion path `topic branch -> dev -> main -> stg -> prd`;
- CI and documentation build gates.

The GDP ingestion pilot has been deployed and smoke-tested through staging and production, proving the delivery path with a real workload.

## Documentation model

```text
Code + docstrings
      |
      +-- mkdocstrings -> API Reference
      |
Markdown docs
      +-- architecture decisions
      +-- engineering and branch standards
      +-- feature specifications and delivery records
      +-- deployment and operational runbooks
      |
      v
Material for MkDocs
      |
      v
GitHub Pages
```

## Start here

For development workflow and promotion rules, read **Engineering -> Branch Governance**. For deployment and environment operations, use **Platform & Delivery -> Deployment Runbook**. For the implemented architectural decisions, use the **Architecture Decisions** section. The **Data Features** section records the delivered IBGE ingestion slices.

Documentation is treated as part of the engineering product: changes are versioned with the code, validated with `mkdocs build --strict`, and published from `main`.
