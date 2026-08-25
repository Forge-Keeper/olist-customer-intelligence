# ADR-005 — DAB Environment and Promotion Boundary

- **Status:** Accepted
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Databricks Declarative Automation Bundle targets, environment isolation and promotion governance

## Context

Development and exploratory validation had materialized tables under the `prd` catalog even though production job entrypoints already accepted fully qualified target tables externally. The project therefore needed an explicit deployment/environment boundary.

The first DAB vertical slice was required to provide professional promotion semantics rather than only a local deployment convenience.

## Decision

### 1. Use three Unity Catalog-backed environments

The project standard is:

```text
dev -> catalog dev
stg -> catalog stg
prd -> catalog prd
```

The Bronze schema remains `bronze` in each environment unless a future architectural decision changes the namespace convention.

Application/domain code does not infer or hardcode environment names. DAB target configuration or explicit runtime parameters resolve environment-specific values and pass fully qualified resources to jobs.

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
- validates the exact artifact before production promotion.

`prd`:

- `mode: production`;
- fixed production root path;
- dedicated production service-principal run identity;
- production Git branch validation enabled against `main`;
- protected promotion only after staging success.

### 3. Git and environment promotion flow

The mandatory integration and promotion path is:

```text
topic branch -> PR into dev -> validation -> merge dev
-> PR dev into main -> validation -> merge main
-> automatic stg deploy/run/verify
-> protected manual approval -> prd deploy/verify
```

`dev` is both the Git integration branch and the name of the developer DAB target; these are distinct concepts even though they share the name.

Staging and production promote the same approved Git commit and corresponding wheel artifact.

### 4. Main is the shared deployment source

Topic branches do not deploy directly to staging or production. `main` is the shared promotion source after changes have passed through `dev`.

The production target declares `git.branch: main`. Normal process does not use `--force` to bypass branch validation.

### 5. Service-principal identities are environment-scoped

Staging and production execution must not depend on an individual developer account.

- staging service principal receives staging permissions only;
- production service principal receives production permissions only;
- credentials are stored outside source code;
- developer iteration does not run under the production identity.

### 6. Explicit resource YAML remains source controlled

The bundle owns explicit `databricks.yml` and `resources/**/*.yml` definitions. No Python-driven DAB resource generator is introduced in this slice.

### 7. Use wheel packaging and serverless jobs for the pilot

The GDP pilot is deployed as a Python wheel task. The wheel built and validated for staging is retained with integrity metadata and reused for production promotion.

## Alternatives considered

### Only `dev` and `prd`

Rejected because a shared staging boundary is valuable for validating the exact artifact and table contract before production.

### Treat `stg` as development mode

Rejected because development-oriented presets do not represent a shared pre-production environment.

### Deploy production directly from topic branches

Rejected because it weakens promotion traceability and bypasses the integration branch and reviewed `main` boundary.

### Use developer identity in production

Rejected because workflow continuity and permissions should be decoupled from an individual's account.

### Automatically generate resource YAML from Python

Rejected for the first slice. Explicit YAML is easier to inspect and avoids premature framework complexity.

## Consequences

### Positive

- strong namespace isolation;
- lower risk of development writes to production;
- traceable `topic -> dev -> main -> stg -> prd` promotion;
- production execution independent from developer identity;
- staging tests the same artifact promoted to production;
- environment selection is explicit rather than hidden in application code.

### Costs / prerequisites

- three catalogs and appropriate grants must exist;
- staging/production service principals and credentials must be provisioned;
- GitHub Environments own deployment credentials and protection;
- production approval remains an explicit human gate.

## Validation evidence

The decision has been implemented and validated:

1. the same GDP application artifact targets `dev`, `stg` and `prd` without source changes;
2. each target resolves to its own Unity Catalog namespace;
3. staging deployment and GDP smoke tests succeed from approved `main` commits;
4. production deployment is manual/protected and uses the retained staging artifact;
5. runtime hardcodes for environment-specific tables, Volumes and identities are guarded by tests;
6. staging and production use service-principal run identities;
7. GitHub CI enforces PRs to `main` coming from `dev`;
8. secrets and credentials remain outside the repository.
