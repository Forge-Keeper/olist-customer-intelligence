# Platform Status

This page is the public checkpoint for delivered capability versus future scope. GitHub code, workflows, issues and ADRs remain the authoritative implementation records.

## Delivered

### Platform

- modular Platform + Domains Python package;
- reusable HTTP, retry/backoff and logging infrastructure;
- reusable PostgreSQL and JDBC access infrastructure for operational-source ingestion;
- source-faithful Bronze landing;
- executable `DatasetContract` model;
- `DeltaTableLifecycle` for table state and metadata lifecycle;
- `BronzeWriter` for write semantics, including checked-batch evidence reuse;
- fail-fast schema drift with conservative explicit evolution;
- table/column metadata and tag reconciliation;
- Unity Catalog governance / ABAC policy foundation;
- first-class PySpark Data Quality contracts, rules and structured results;
- persisted Data Quality evidence with `ERROR`, `WARNING` and `INFO` policy semantics;
- administrative Control Plane with environment-isolated `execution_runs` and `data_quality_results` history;
- GDP pre-write Data Quality gate validated end-to-end through DEV -> STG -> PRD, with a deliberate DEV rejected batch proving Bronze remains unchanged on blocking failure;
- Olist Customers pre-write Data Quality and execution tracking validated end-to-end through DEV -> STG -> PRD, including a deliberate DEV duplicate-key rejection with `records_written=0` and an unchanged protected target;
- Olist Sellers pre-write Data Quality and execution tracking validated end-to-end through DEV -> STG -> PRD, including a deliberate DEV duplicate-key rejection with `records_written=0` and an unchanged protected target;
- DAB targets for `dev`, `stg` and `prd`, with separate data-plane and administrative catalogs;
- GitHub Actions CI/CD;
- same staging-approved wheel artifact promoted to production;
- deployment runbook and retained deployment evidence;
- MkDocs Material documentation and GitHub Pages workflow.

### Data features

Implemented Bronze vertical slices currently represented in the repository:

- Weather / Open-Meteo;
- ANP fuel prices from Azure PostgreSQL through JDBC into Databricks Bronze, with DEV runtime validation and bounded `REPLACE_WHERE` reprocessing;
- Olist Customers;
- Olist Sellers;
- Olist Products;
- Olist Product Category Name Translation;
- Olist Geolocation;
- Olist Orders;
- Olist Marketing Qualified Leads;
- Olist Closed Deals;
- IBGE Localidades / municipalities;
- IBGE municipality population;
- IBGE municipality GDP / VAB;
- IBGE CEMPRE municipal business activity for 2016–2018.

The remaining core Olist e-commerce Bronzes are backlog work. Current implementation evidence does not yet include Order Items, Order Payments or Order Reviews.

## Known limitations / technical debt

- the first-class Data Quality path is not yet uniform across every historical Bronze workload; adoption remains dataset-specific and should follow concrete feature work rather than a bulk rewrite;
- deployment smoke coverage is intentionally targeted rather than a full regression suite, although the current smoke manifest now includes the implemented Olist Customers, Sellers, Products, Product Category Name Translation, Geolocation, Orders and Marketing Funnel workloads alongside selected IBGE jobs;
- the recovered ANP PostgreSQL/JDBC runtime is intentionally configured only for DEV; STG/PRD PostgreSQL endpoints remain undefined until separately configured and validated;
- full regression of every pipeline during deployment is intentionally out of scope;
- Silver/Gold analytical products are not yet delivered;
- account/workspace-level governance taxonomy provisioning remains subject to external Unity Catalog permissions/capabilities;
- shared-environment grants required by the Data Quality Control Plane delivery were validated with the `olist-ci` workload identity in the lab STG/PRD environments; least-privilege and stronger per-environment identity separation remain target architecture rather than an active blocker for that completed promotion;
- repository server-side branch protection may depend on account/plan capabilities, so process and CI guardrails remain important.

## Roadmap boundary

Future work must be selected explicitly from the current GitHub backlog. The repository does not treat historical proposal documents as a live backlog.

Likely capability families include:

- completion of remaining Olist Bronze datasets;
- Silver modeling and harmonization;
- Gold / Customer Intelligence products;
- broader Data Quality and observability adoption where concrete use cases justify it;
- incremental processing/backfill/replay where required;
- additional justified source datasets;
- deployment and operational hardening driven by concrete gaps.

## Historical delivery records

The DAB and feature Discovery, Requirements, Technical Design, Impact Analysis and Implementation Plan pages are retained as engineering records of the gate process. Their proposed wording describes the state at the time each gate was written; the implemented/accepted outcome is represented by the current code, runtime evidence, ADRs and this status page.

The current public narrative therefore distinguishes:

- **current state** — this page, Architecture, README and accepted ADRs;
- **historical design record** — gate documents retained for traceability.
