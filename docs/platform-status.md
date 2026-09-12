# Platform Status

This page is the canonical human-readable checkpoint for the current delivered state of Olist Customer Intelligence.

## Source-of-truth hierarchy

Use the project sources in this order according to the question being answered:

1. **`main`** — executable truth: implemented code, deployment resources and tests.
2. **Platform Status** — canonical human-readable truth for delivered datasets, capabilities and environment readiness.
3. **GitHub Issues** — canonical backlog and future work.
4. **Accepted ADRs** — durable architectural decisions and their rationale.
5. **README** — portfolio-oriented summary derived from the sources above.
6. **Feature/gate documents** — detailed technical and historical delivery records. They may contain wording that was accurate at the time a gate was written and do not override this page for current readiness.

A code merge alone does not change public feature readiness. Status changes require closeout evidence and an update to this page.

## Readiness semantics

The environment columns deliberately distinguish code existence from runtime/deployment evidence:

| Symbol | Meaning |
| --- | --- |
| ✅ | accepted evidence for that stage is recorded |
| ◐ | representative deployment smoke evidence exists, but this is not full runtime acceptance |
| ? | implementation exists, but canonical closeout evidence for this environment has not yet been normalized here |
| — | intentionally unavailable / not configured / not applicable |

A green deployment smoke proves the declared representative deployment path. It does **not** automatically prove full runtime acceptance, idempotence, data reconciliation or complete regression for the dataset.

## Dataset readiness matrix

| Dataset / layer | Code | DEV | STG | PRD | Evidence / current interpretation |
| --- | :---: | :---: | :---: | :---: | --- |
| Olist Customers Bronze | ✅ | ✅ | ✅ | ✅ | first-class DQ and execution tracking accepted end-to-end; controlled DEV rejection proved protected target behavior |
| Olist Sellers Bronze | ✅ | ✅ | ✅ | ✅ | first-class DQ and execution tracking accepted end-to-end; controlled DEV rejection proved protected target behavior |
| Olist Marketing Qualified Leads Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted; current DAB job covered by the STG deployment-smoke DAG |
| Olist Closed Deals Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted; current DAB job covered by the STG deployment-smoke DAG |
| Olist Products Bronze | ✅ | ✅ | ✅ | ✅ | explicit Products closeout records DEV -> STG -> PRD and exact-artifact promotion |
| Olist Product Category Name Translation Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted; current DAB job covered by the STG deployment-smoke DAG; older gate wording is historical |
| Olist Geolocation Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted including repeatable `FULL_REPLACE`; current DAB job covered by the STG deployment-smoke DAG |
| Olist Orders Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted including repeatable `FULL_REPLACE`; current DAB job covered by the STG deployment-smoke DAG |
| Olist Order Items Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted including repeatable `FULL_REPLACE`; current DAB job covered by the STG deployment-smoke DAG |
| Olist Order Payments Bronze | ✅ | ✅ | ◐ | ? | DEV runtime accepted including repeatable `FULL_REPLACE`; current DAB job covered by the STG deployment-smoke DAG |
| Olist Order Reviews Bronze | ✅ | ✅ | ◐ | ? | two successful DEV `FULL_REPLACE` executions preserve 99,224 semantic rows; current DAB job covered by the STG deployment-smoke DAG |
| Olist Customers Silver | ✅ | ✅ | ? | ? | first Silver slice accepted in DEV: 99,441 rows / 99,441 distinct `customer_id`, 96,096 distinct `customer_unique_id`, deterministic rerun, explicit lineage and blocking DQ |
| Olist Orders Silver | ✅ | ✅ | ? | ? | first Silver slice accepted in DEV: 99,441 rows / 99,441 distinct `order_id`, zero Orders -> Customers orphans, typed lifecycle timestamps, warnings for 1,359 carrier-before-approval and 23 delivered-before-carrier observations, controlled DQ rejection preserved the target |
| ANP Azure PostgreSQL/JDBC Bronze | ✅ | ✅ | — | — | DEV runtime recovery accepted with bounded `REPLACE_WHERE`; STG/PRD PostgreSQL sources intentionally unconfigured |
| IBGE municipality GDP / VAB Bronze | ✅ | ✅ | ✅ | ✅ | first-class DQ gate and deployment path accepted end-to-end; deliberate DEV rejection proved protected target behavior |
| IBGE CEMPRE municipal business activity Bronze | ✅ | ? | ◐ | ? | implementation is present; current DAB job covered by STG deployment smoke; environment closeout evidence remains to be normalized |
| IBGE Localidades / municipalities | ✅ | ? | ? | ? | implementation is present; historical environment evidence has not yet been normalized into this checkpoint |
| IBGE municipality population | ✅ | ? | ? | ? | implementation is present; historical environment evidence has not yet been normalized into this checkpoint |
| Weather / Open-Meteo | ✅ | ? | ? | ? | implementation is present; historical environment evidence has not yet been normalized into this checkpoint |
| Gold / Customer Intelligence | — | — | — | — | roadmap only; no completed analytical product is claimed |

Olist Bronze CSV code coverage is complete for the current public Olist source set represented by this repository. The first Olist Silver slice is now delivered for Customers + Orders in DEV. Environment readiness is intentionally shown separately above rather than inferred from implementation alone.

## Platform capability readiness

| Capability | Code | DEV | STG | PRD | Evidence / current interpretation |
| --- | :---: | :---: | :---: | :---: | --- |
| Platform + Domains package architecture | ✅ | ✅ | ✅ | ✅ | exercised by delivered workloads across the promotion path |
| Dataset contracts / Delta lifecycle / Bronze write strategies | ✅ | ✅ | ✅ | ✅ | reused by delivered Bronze workloads |
| Silver typed contracts + protected full-snapshot writes | ✅ | ✅ | ? | ? | Customers + Orders DEV acceptance proves explicit typed schemas, blocking/non-blocking DQ, deterministic reruns and target preservation on blocking rejection |
| First-class Data Quality + administrative Control Plane | ✅ | ✅ | ✅ | ✅ | GDP, Customers and Sellers provide accepted cross-environment evidence; Silver Customers + Orders add accepted DEV evidence; adoption still varies by dataset |
| DAB environment targets and exact-wheel promotion | ✅ | ✅ | ✅ | ✅ | `dev`, `stg`, `prd` targets with retained staging-approved artifact for production |
| Manifest-driven deployment smoke coverage | ✅ | ✅ | ✅ | ? | every current declared DAB job has one smoke contract; current STG evidence is complete |
| DAG-aware bounded smoke scheduler | ✅ | ✅ | ✅ | ? | STG Deploy #37 validated `max_workers=4`, 13/13 `SUCCESS`, no `FAILED`/`BLOCKED`, no observed shared-control-plane conflict |
| Unity Catalog metadata / ABAC foundation | ✅ | ✅ | ? | ? | capability exists; exact environment-specific governance readiness remains subject to workspace/account permissions and explicit evidence |

### DAG-aware deployment evidence

GitHub Issue #92 records the accepted runtime closeout for the parallel deployment-smoke scheduler:

- Deploy STG #37, run `34251706046` on `main` commit `44196c6e81691e089c20564ca5bc5c11f800636d`;
- all 13 declared DAB smoke nodes completed `SUCCESS`;
- bounded concurrency was observed with `max_workers=4`;
- no `FAILED` or `BLOCKED` nodes;
- no observed Delta/shared-Control-Plane concurrency conflict;
- smoke wall-clock fell from approximately 59 minutes in the preceding sequential deployment to approximately 14m23s, a reduction of about 76% and roughly 4.1x speedup for that observed comparison.

This evidence validates the scheduler and the representative STG smoke graph. It is not a claim that every dataset has full STG runtime acceptance.

## Delivered platform foundation

The implemented foundation includes:

- reusable HTTP, retry/backoff and logging infrastructure;
- source-faithful Bronze landing;
- executable `DatasetContract` model;
- `DeltaTableLifecycle` for table state and metadata lifecycle;
- `BronzeWriter` for explicit write semantics and checked-batch evidence reuse;
- fail-fast schema drift with conservative explicit evolution;
- table/column metadata and tag reconciliation;
- Unity Catalog governance / ABAC policy foundation;
- first-class PySpark Data Quality contracts, rules and structured results;
- persisted Data Quality evidence with `ERROR`, `WARNING` and `INFO` policy semantics;
- administrative Control Plane with environment-isolated `execution_runs` and `data_quality_results` history;
- explicit Silver Customers + Orders contracts with typed lifecycle fields, referential DQ, lineage, deterministic `FULL_REPLACE` and protected writes;
- DAB targets for `dev`, `stg` and `prd`, with separate Data Plane and administrative catalogs;
- GitHub Actions CI/CD;
- same staging-approved wheel artifact promotion to production;
- DAG-aware deployment smokes with bounded concurrency and retained per-node evidence;
- MkDocs Material documentation and GitHub Pages workflow.

## Current evidence highlights

- **Silver Customers + Orders DEV:** Customers contains 99,441 rows at unique `customer_id` grain and preserves 96,096 longitudinal `customer_unique_id` values. Orders contains 99,441 unique `order_id` rows with zero Orders -> Customers orphans and typed lifecycle timestamps. Bidirectional `EXCEPT ALL` after a rerun returned `0/0` for both datasets when excluding the expected processing timestamp. A controlled one-orphan rejection persisted `OLIST-SILVER-ORDERS-DQ05` as `ERROR/FAIL` with `invalid_row_count=1` and left the protected target unchanged (`0/0` bidirectional comparison).
- **Order Reviews DEV:** two successful `FULL_REPLACE` executions of the same 99,224-row source snapshot. The target contains 99,224 rows and 99,224 distinct `(review_id, order_id)` keys with complete `source_file` and `ingestion_timestamp` lineage.
- **ANP DEV:** bounded Azure PostgreSQL/JDBC reprocessing is accepted only in DEV; absence of STG/PRD readiness is intentional, not an implied failure.
- **Products:** explicit closeout records DEV -> STG -> PRD and exact staging-wheel reuse in production.
- **Deployment smokes:** the current manifest covers every declared DAB job and the DAG-aware STG execution is accepted with bounded parallelism.

## Known limitations / technical debt

- first-class Data Quality adoption and runtime evidence vary by dataset;
- several earlier source slices have implementation history but their environment-specific evidence has not yet been normalized into this matrix; `?` is intentional until evidence is reconciled rather than guessed;
- a successful STG deployment/smoke is not equivalent to full STG runtime acceptance for every dataset;
- full regression of every pipeline during deployment is intentionally out of scope;
- Silver delivery currently covers only Customers + Orders in DEV; remaining Silver domains and all Gold analytical products are not yet delivered;
- account/workspace-level governance taxonomy provisioning remains subject to external Unity Catalog permissions/capabilities;
- shared-environment grants required by the Data Quality Control Plane delivery were validated with the shared `olist-ci` workload identity in the lab STG/PRD environments; stronger per-environment identity separation remains target architecture rather than current-state fact;
- repository server-side branch protection may depend on account/plan capabilities, so process and CI guardrails remain important.

## Closeout governance

A feature is not publicly `DONE` merely because its code was merged.

The default evidence flow is:

```text
feature implementation
  -> runtime evidence appropriate to the accepted scope
  -> merge / promotion gates
  -> closeout
  -> Platform Status update
  -> DONE
```

If a feature does not require a particular environment or runtime gate, closeout records that stage as not applicable or intentionally unavailable instead of implying readiness.

The README should be updated only when the portfolio narrative or durable architecture changes. Routine feature readiness changes belong here so the README does not become an operational ledger.

## Roadmap boundary

Future work is selected from GitHub Issues. Historical Discovery, Requirements, Technical Design, Impact Analysis and Implementation Plan documents are not a live backlog.

Likely capability families remain:

- remaining Silver modeling and harmonization;
- Gold / Customer Intelligence products;
- broader observability where concrete use cases justify it;
- incremental processing/backfill/replay where required;
- additional justified source datasets;
- deployment and operational hardening driven by concrete gaps.

## Historical delivery records

Feature and platform gate documents are retained as engineering records of the state and reasoning at the time each gate was written. They may therefore contain historical phrases such as `pending` or `in progress` after later delivery has advanced.

For current-state questions, use this page first, inspect `main` when implementation proof is needed, use GitHub Issues for future work, and consult ADRs when the architectural rationale matters.
