# ADR-005 — DAB Environment and Promotion Boundary

- **Status:** Proposed
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Databricks Declarative Automation Bundle targets, environment isolation and promotion governance

## Context

Development and exploratory validation have materialized tables under the `prd` catalog even though production job entrypoints already accept fully qualified target tables externally. The project therefore lacks an explicit deployment/environment boundary.

The first DAB vertical slice must provide professional promotion semantics rather than only a local deployment convenience.

Current Databricks guidance distinguishes development deployments from production-safe deployments, supports dedicated run identities for staging/production, and recommends service-principal execution for production workflows.

## Decision

### 1. Use three Unity Catalog-backed environments

The project standard becomes:

```text
dev -> catalog dev
stg -> catalog stg
prd -> catalog prd
```

The Bronze schema remains `bronze` in each environment unless a future architectural decision changes the namespace convention.

Application/domain code does not infer or hardcode environment names. DAB target configuration resolves environment-specific values and passes fully qualified resources to jobs.

### 2. DAB target behavior

`dev`:

- `mode: development`;
- default developer target;
- uses developer identity;
- intended for isolated iteration and explicit test runs.

`stg`:

- shared pre-production target;
- fixed bundle root path;
- dedicated staging service-principal run identity;
- does not use development-mode presets;
- validates the artifact before production promotion.

`prd`:

- `mode: production`;
- fixed production root path;
- dedicated production service-principal run identity;
- production Git branch validation enabled against `main`;
- protected promotion only after staging success.

### 3. Promotion flow

The standard promotion path is:

```text
feature branch -> PR validation -> optional dev deployment
-> merge main -> stg deploy/run/verify
-> protected manual approval -> prd deploy/verify
```

Staging and production promote the same approved Git commit and corresponding wheel artifact.

### 4. Main is the shared promotion source

Feature branches are not normal production deployment sources.

The production target declares `git.branch: main`. Normal process does not use `--force` to bypass branch validation.

A tag/release-branch strategy may be introduced later if release governance requires it, but is out of scope for the first vertical slice.

### 5. Service-principal identities are environment-scoped

Staging and production execution must not depend on an individual developer account.

- staging service principal receives staging permissions only;
- production service principal receives production permissions only;
- production credentials/IDs/secrets are not committed;
- developer iteration does not run under the production identity.

### 6. Explicit resource YAML remains source controlled

The bundle owns explicit `databricks.yml` and `resources/**/*.yml` definitions.

No Python-driven DAB resource generator is introduced in this feature.

### 7. Use wheel packaging and serverless jobs for the pilot

The GDP pilot is deployed as a Python wheel task.

Serverless jobs compute is the selected default because Databricks recommends it for Python wheel jobs. Workspace capability and permissions are implementation prerequisites; if serverless is unavailable, a classic-jobs-compute fallback requires an explicit design adjustment rather than silent substitution.

## Alternatives considered

### Only `dev` and `prd`

Rejected because a shared staging boundary is valuable for validating the exact artifact and table contract before production.

### Treat `stg` as development mode

Rejected because personal naming/presets and development-oriented deployment behavior do not represent a shared pre-production environment.

### Deploy production directly from feature branches

Rejected because it weakens promotion traceability and bypasses the normal reviewed integration branch.

### Use developer identity in production

Rejected because workflow continuity and permissions should be decoupled from an individual's account.

### Automatically generate resource YAML from Python

Rejected for the first slice. Explicit YAML is easier to inspect and avoids premature framework complexity.

## Consequences

### Positive

- strong namespace isolation;
- lower risk of development writes to production;
- traceable `dev -> stg -> prd` promotion;
- production execution independent from developer identity;
- staging tests the same artifact that is promoted to production;
- uses Databricks-native deployment protections.

### Negative / prerequisites

- three catalogs and appropriate grants must exist;
- staging/production service principals and credentials must be provisioned;
- CI/CD secrets/authentication must be configured outside source code;
- protected production approval needs repository/environment governance;
- serverless workflows availability must be confirmed.

## Validation

The decision is correctly implemented when:

1. the same GDP application artifact targets all three environments without source changes;
2. `dev`, `stg` and `prd` resolve to their own catalogs;
3. shared staging deployment succeeds from the approved `main` commit;
4. production deployment is protected and uses production mode;
5. production cannot normally deploy from a feature branch;
6. staging and production use service-principal run identities;
7. production promotion occurs only after staging validation;
8. secrets and credentials remain outside the repository.
