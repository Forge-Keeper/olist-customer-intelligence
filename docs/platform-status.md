# Platform Status

This page is the public checkpoint for delivered capability versus future scope. GitHub code, workflows, issues and ADRs remain the authoritative implementation records.

## Delivered

### Platform

- modular Platform + Domains Python package;
- reusable HTTP, retry/backoff and logging infrastructure;
- source-faithful Bronze landing;
- executable `DatasetContract` model;
- `DeltaTableLifecycle` for table state and metadata lifecycle;
- `BronzeWriter` for write semantics;
- fail-fast schema drift with conservative explicit evolution;
- table/column metadata and tag reconciliation;
- Unity Catalog governance / ABAC policy foundation;
- DAB targets for `dev`, `stg` and `prd`;
- GitHub Actions CI/CD;
- same staging-approved wheel artifact promoted to production;
- deployment runbook and retained deployment evidence;
- MkDocs Material documentation and GitHub Pages workflow.

### Data features

- Weather / Open-Meteo;
- Olist Customers;
- Olist Closed Deals;
- IBGE Localidades / municipalities;
- IBGE municipality population;
- IBGE municipality GDP / VAB;
- IBGE CEMPRE municipal business activity for 2016–2018.

## Known limitations / technical debt

- deployment smoke coverage is narrower than the current set of DAB workloads; GDP is the proven deployment pilot and CEMPRE exposes the coverage gap tracked in GitHub Issue #21;
- full regression of every pipeline during deployment is intentionally out of scope;
- Silver/Gold analytical products are not yet delivered;
- account/workspace-level governance taxonomy provisioning remains subject to external Unity Catalog permissions/capabilities;
- repository server-side branch protection may depend on account/plan capabilities, so process and CI guardrails remain important.

## Roadmap boundary

Future work must be selected explicitly from the current GitHub backlog. The repository does not treat historical proposal documents as a live backlog.

Likely capability families include:

- Silver modeling and harmonization;
- Gold / Customer Intelligence products;
- first-class data quality and observability expansion;
- incremental processing/backfill/replay where required;
- additional justified source datasets;
- deployment and operational hardening driven by concrete gaps.

## Historical delivery records

The DAB Discovery, Requirements, Technical Design, Impact Analysis and Implementation Plan pages are retained as engineering records of the gate process. Their proposed wording describes the state at the time each gate was written; the implemented/accepted outcome is represented by the current code, runbook, ADRs and this status page.

The current public narrative therefore distinguishes:

- **current state** — this page, Architecture, README and accepted ADRs;
- **historical design record** — gate documents retained for traceability.
