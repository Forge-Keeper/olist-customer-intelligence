# Environment Hardcode Audit

## Purpose

Audit runtime and deployment code for values that silently bind execution to a
specific Olist environment, then move those values to explicit runtime or DAB
configuration.

The governing rule is:

> Application/domain code does not infer or embed `dev`, `stg` or `prd` resources.
> Environment selection is explicit at the deployment/runtime boundary.

## Findings and migrations

### 1. Validation notebooks embedded production table names

Affected notebooks:

- `notebooks/exploration/ibge_bronze_validation.py`
- `notebooks/exploration/ibge_gdp_bronze_validation.py`

Previous behavior used fully qualified `prd.bronze.*` table literals.

Migration:

- both notebooks now require an explicit Databricks `catalog` widget;
- table names are composed with `platform.naming.qualified_table_name`;
- the helper validates simple Unity Catalog identifiers;
- no default environment is selected by the notebook.

This mirrors the DAB model, where `${var.catalog}` is resolved by the selected
target and passed to deployed resources.

### 2. Olist CSV jobs embedded production Volume paths

Affected jobs:

- `jobs/olist_customers_ingestion.py`
- `jobs/olist_closed_deals_ingestion.py`

Previous behavior defaulted `--source-path` to `/Volumes/prd/...`.

Migration:

- `--source-path` is now required;
- `--target-table` remains required;
- callers/deployment resources own both source and target resolution.

When these jobs are migrated to DAB, their environment-specific source paths
should be supplied by bundle variables or job parameters according to whether the
value changes per deployment or per run.

### 3. DAB configuration embedded the Free Edition service-principal application ID

Previous behavior declared concrete defaults for staging and production
`run_as` identities in `databricks.yml`.

Migration:

- one required bundle variable, `run_as_service_principal`, now represents the
  deployment run identity;
- staging and production both reference `${var.run_as_service_principal}`;
- GitHub workflows inject `BUNDLE_VAR_run_as_service_principal` from the
  environment-scoped `DATABRICKS_CLIENT_ID` variable;
- the service-principal application ID is no longer committed to bundle config.

The laboratory still reuses one service principal in `stg` and `prd` because of
Free Edition constraints. Separate identities remain the intended enterprise
architecture.

### 4. Tests used production-qualified fixtures

Tests that only verify argument forwarding or composition previously used
`prd.bronze.*` literals. They now use neutral `test_catalog.*` fixtures. Tests for
Olist CSV jobs also verify that source paths are explicitly required.

## Guardrails added

`tests/unit/platform/test_naming.py` now protects the boundary by checking that:

- runtime Python under `src/` and `notebooks/` does not embed quoted
  `dev.*`, `stg.*` or `prd.*` object names;
- runtime Python does not embed `/Volumes/dev/`, `/Volumes/stg/` or
  `/Volumes/prd/` paths;
- `databricks.yml` does not embed a literal UUID in
  `service_principal_name`.

The naming helper is separately tested for explicit catalog composition and
unsafe identifier rejection.

## Intentional environment declarations that remain

The following are not treated as defects:

- DAB target names `dev`, `stg`, `prd`;
- each target's `catalog: dev|stg|prd` mapping, because this is the explicit
  environment boundary itself;
- GitHub Environment names (`ci`, `olist-stg`, `olist-prd`);
- stable architecture names such as schema `bronze` and logical table names;
- concrete object names retained in ADRs, historical discovery documents and
  deployment evidence when they describe what was actually tested or deployed.

The goal is not to remove every occurrence of the words `dev`, `stg` and `prd`.
The goal is to prevent runtime behavior from being silently bound to one of them.

## Result

After this migration, environment-specific runtime values have a single clear
ownership boundary:

```text
GitHub Environment / local operator
        -> DAB variable or explicit job/notebook parameter
        -> fully qualified runtime resource
        -> application/domain code
```

No application/domain component chooses production by default.
