# ADR-007 — Platform Administrative Control Plane

- **Status:** Accepted
- **Date:** 2026-08-27
- **Decision owners:** Project maintainers
- **Scope:** Operational execution metadata and administrative platform data

## Context

Olist Customer Intelligence needs durable operational evidence for ingestion runs and Data Quality evaluations. These records are not business datasets and do not belong to the Bronze/Silver/Gold data plane.

Application logs already exist in runtime systems, but logs alone do not provide a stable relational history for answering questions such as which dataset ran, which scope was requested, how many rows were processed, whether Data Quality rejected the run, and which rule failed.

The platform already isolates `dev`, `stg` and `prd` data catalogs and resolves environment-specific names at the Databricks Asset Bundle boundary rather than in domain code. The administrative plane must preserve the same isolation principle.

## Decision

Introduce a separate administrative Control Plane alongside the business Data Plane.

Each environment has its own administrative Unity Catalog catalog:

```text
dev  -> dev_admin
stg  -> stg_admin
prd  -> prd_admin
```

The initial Control Plane contains only the capabilities required by the current feature:

```text
<admin_catalog>
├── operations
│   └── execution_runs
└── quality
    └── data_quality_results
```

`operations.execution_runs` has one row per logical platform execution. `quality.data_quality_results` has one row per evaluated rule and scope. Both are correlated by the same platform `run_id`.

Runtime/application logs, Spark executor logs and CI logs remain in their native logging systems. The Control Plane stores structured operational facts, not a second logging platform.

Catalog and schema provisioning remain an infrastructure prerequisite. Application code may create and reconcile its managed Delta tables through existing `DatasetContract` and `DeltaTableLifecycle` capabilities, but it does not silently create catalogs or schemas.

Environment-specific catalog names are injected at deployment/execution boundaries. Domain code must not branch on `dev`, `stg` or `prd`.

Runtime identities follow least privilege. Development may temporarily use a developer identity, while shared environments should use workload service principals. Catalog/schema ownership should remain separate from routine runtime write privileges when the target account supports that model.

## Alternatives considered

### Store administrative tables inside each data catalog

Rejected because operational metadata is not a Bronze/Silver/Gold product and would mix platform-control concerns with business datasets.

### Use one global administrative catalog for all environments

Deferred because it creates cross-environment permissions and a larger blast radius. Per-environment isolation is simpler and matches the existing deployment model.

### Persist all application logs in Delta

Rejected. Runtime log systems remain the correct owner for unstructured/technical logs; only structured operational facts are persisted in the Control Plane.

## Consequences

### Positive

- business data and platform-control data have explicit boundaries;
- execution and Data Quality evidence are queryable with SQL;
- one `run_id` correlates source, quality and write stages;
- environment isolation remains consistent with the Data Plane;
- the administrative model can later support additional workloads without changing Bronze/Silver/Gold semantics.

### Negative / cost

- every environment requires an additional catalog and the required schemas;
- workload identities require privileges on both the Data Plane and Control Plane;
- updates across data and administrative catalogs are not one distributed ACID transaction.

### Operational implications

- `dev_admin`, `stg_admin` and `prd_admin` plus `operations` and `quality` schemas must exist before workloads use them;
- write/update operations are idempotent so interrupted runs can be reconciled safely;
- a failure to persist mandatory administrative evidence before a protected Bronze write fails closed;
- a failure after the data-plane write can leave the last operational status stale and must remain diagnosable through `run_id`, stage and runtime logs.

## Implementation constraints

- preserve per-environment administrative catalogs unless this ADR is superseded;
- do not embed concrete environment catalog names in domain/application logic;
- do not treat raw application logs as Control Plane rows;
- keep `execution_runs` at one row per logical run;
- correlate related quality evidence through the same `run_id`;
- prefer least-privilege workload identities and keep ownership/admin authority separate when practical;
- do not invent governance classifications or sensitive-data tags without evidence.

## Validation

The decision is considered correctly implemented when:

1. DAB resolves a distinct `admin_catalog` for `dev`, `stg` and `prd`;
2. an execution can persist and update one `execution_runs` row idempotently;
3. Data Quality results persist in the corresponding environment administrative catalog;
4. no environment-specific admin catalog name exists in GDP domain logic;
5. runtime smoke evidence demonstrates the Data Plane and Control Plane can be correlated through one `run_id`.

## Supersession

None.
