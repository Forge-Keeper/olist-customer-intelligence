# Databricks Asset Bundles --- Development & Deployment Guide

## Purpose

This document defines how the Olist Customer Intelligence project will
introduce and use Databricks Asset Bundles (DAB).

DAB is being added to make Databricks deployment configuration
versioned, reproducible, environment-aware, and suitable for CI/CD.

This is a development and deployment practice document, not an
Architecture Decision Record. If future work introduces a durable
architectural boundary --- for example, deciding which resources belong
to DAB versus Terraform --- that decision should be evaluated separately
for an ADR.

## Goals

The initial DAB implementation should:

1.  make Databricks resource configuration part of the repository;
2.  support explicit deployment targets;
3.  externalize environment-specific values;
4.  provide a repeatable `validate → deploy → run` workflow;
5.  automate one small end-to-end workflow before expanding scope;
6.  create a clean path toward GitHub Actions CI/CD.

## Non-Goals

The first iteration will not:

-   migrate every Databricks resource at once;
-   introduce Terraform without an infrastructure requirement;
-   add cloud services only to increase the visible technology stack;
-   duplicate configuration between documentation and Bundle YAML;
-   treat Bundle variables and Job/Task runtime parameters as the same
    concern.

## Proposed Repository Structure

``` text
olist-customer-intelligence/
├── databricks.yml
├── resources/
│   └── jobs.yml
├── src/
│   └── olist_data_platform/
├── tests/
├── docs/
│   ├── adr/
│   └── development/
│       └── databricks-asset-bundles.md
├── pyproject.toml
└── README.md
```

This structure is a target for the DAB implementation and should be
adjusted only when the actual resource model requires it.

## Responsibility Boundaries

### Application code

`src/olist_data_platform/` owns reusable Data Engineering logic:

-   ingestion;
-   parsing;
-   transformations;
-   writers;
-   Data Quality;
-   logging;
-   feature engineering;
-   ML-related components.

Application logic should not contain deployment-environment details that
belong to Bundle configuration.

### Bundle configuration

`databricks.yml` and `resources/*.yml` own Databricks deployment
configuration such as:

-   Bundle identity;
-   targets;
-   Databricks resources;
-   deployment-time variables;
-   environment-specific overrides;
-   resource references.

The YAML configuration is the source of truth for what the Bundle
deploys.

### Runtime parameters

Job and Task parameters communicate values needed by a particular
execution.

They are not a replacement for Bundle variables.

A useful distinction is:

``` text
Bundle configuration
    → where/how resources are deployed

Job / Task parameters
    → values required by a particular execution
```

## Targets

The initial target model is:

### `dev`

Used for active development, validation, and manual execution.

Expected responsibilities:

-   developer-oriented resource naming;
-   development catalog/schema configuration;
-   safe iteration;
-   manual `bundle deploy` and `bundle run`.

### `prod`

Represents the production deployment boundary.

The target should exist only with configuration that can be defended
architecturally. A production target does not imply that the current
Databricks environment can or should execute a complete production
deployment immediately.

Production automation should be introduced only after authentication and
environment constraints are validated.

## Variables

Environment-dependent values should be externalized where appropriate.

Candidate values include:

-   catalog;
-   schema;
-   resource naming prefixes/suffixes;
-   environment identifier;
-   paths or locations that genuinely vary by environment.

Variables should not be created merely because DAB supports variables.
Stable application constants should remain in the appropriate
application configuration.

## First Bundle Scope

The first Bundle should deliberately cover a small vertical slice.

Target:

``` text
ingestion
   ↓
Bronze write
   ↓
validation
```

The exact Job entrypoint must be selected from the implemented Olist
workflow before creating the final resource definition.

This keeps the first milestone focused on learning and validating
deployment mechanics instead of converting the entire project at once.

## Implementation Sequence

### 1. Verify local prerequisites

Confirm:

-   Databricks CLI availability;
-   CLI version compatible with current Asset Bundles;
-   authentication against the intended workspace;
-   repository tests passing before deployment work begins.

### 2. Create the Bundle root

Add:

``` text
databricks.yml
```

Start with the smallest valid configuration.

Do not model all future resources in the first commit.

### 3. Add targets

Define:

``` text
dev
prod
```

Keep environment differences explicit.

### 4. Externalize deployment configuration

Move environment-dependent deployment values into Bundle
variables/target overrides where appropriate.

Do not move runtime business parameters into Bundle variables merely for
centralization.

### 5. Define the first Databricks resource

Create the first Job under `resources/`.

The resource should invoke an existing, tested entrypoint rather than
embedding business logic in YAML.

### 6. Validate

Run:

``` bash
databricks bundle validate -t dev
```

A successful validation is the first acceptance criterion.

### 7. Deploy to development

Run:

``` bash
databricks bundle deploy -t dev
```

Confirm that the expected resource is created or updated in the intended
development scope.

### 8. Execute

Run the configured resource:

``` bash
databricks bundle run <resource-key> -t dev
```

Verify:

-   execution succeeds;
-   parameters resolve correctly;
-   expected tables/data are produced;
-   rerunning the same logical input preserves idempotency.

### 9. Expand tests around deployment-sensitive behavior

DAB does not replace application testing.

Before CI/CD, maintain the existing quality gates:

``` bash
ruff check .
pytest
databricks bundle validate -t dev
```

### 10. Integrate CI

Initial Pull Request validation target:

``` text
PR
 ↓
ruff
 ↓
pytest
 ↓
bundle validate
```

Deployment should remain a separate concern until authentication and
environment rules are explicit.

### 11. Evaluate automated deployment

Only after manual deployment is stable, decide:

-   what event triggers deployment;
-   which target can be deployed automatically;
-   how CI authenticates;
-   what approval boundary protects production;
-   what Databricks Free Edition or workspace limitations apply.

## Local Development Workflow

Expected developer loop:

``` bash
ruff check .
pytest
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run <resource-key> -t dev
```

Not every code change should require deployment. Unit tests and linting
remain the fastest feedback loop.

## CI/CD Boundary

DAB solves Databricks resource packaging/deployment concerns.

It should not automatically become responsible for every piece of
infrastructure surrounding Databricks.

A future infrastructure tool such as Terraform should only be added when
a concrete requirement exists, such as managing cloud resources or
platform infrastructure outside the appropriate DAB boundary.

If that boundary becomes a durable architectural decision, create an ADR
at that point.

## Documentation Rules

Keep responsibilities separated:

### `README.md`

Explains:

-   what the project is;
-   architecture at a high level;
-   engineering capabilities;
-   how DAB fits into the development/deployment model;
-   where detailed documentation lives.

### `docs/development/databricks-asset-bundles.md`

Explains:

-   how DAB is used;
-   targets;
-   variables;
-   development workflow;
-   deployment workflow;
-   CI/CD integration;
-   operational conventions.

### `databricks.yml` and `resources/*.yml`

Define the actual deployable configuration.

Do not duplicate every YAML value in Markdown.

### `docs/adr/`

Records durable architectural decisions and their trade-offs.

DAB adoption alone does not currently require an ADR.

## Acceptance Criteria --- First DAB Milestone

The milestone is complete when:

-   [ ] `databricks.yml` exists and validates;
-   [ ] `dev` target is usable;
-   [ ] `prod` boundary is represented without pretending unsupported
    production capability;
-   [ ] environment-specific configuration is not hard-coded into
    application logic;
-   [ ] at least one existing Olist workflow is represented as a Bundle
    resource;
-   [ ] `databricks bundle deploy -t dev` succeeds;
-   [ ] the resource can be executed through `databricks bundle run`;
-   [ ] the execution preserves the project's idempotency requirements;
-   [ ] `ruff` passes;
-   [ ] `pytest` passes;
-   [ ] Bundle validation is ready to become a CI quality gate;
-   [ ] README points to this document.

## Follow-up Milestones

After the first Bundle works:

1.  expand resource coverage incrementally;
2.  integrate `bundle validate` into GitHub Actions;
3.  define secure CI authentication;
4.  evaluate automated `dev` deployment;
5.  define the production promotion/approval model;
6.  evaluate whether any infrastructure requirement justifies Terraform;
7.  keep deployment conventions synchronized with the actual Bundle
    configuration.

## Architectural Guardrail

For every technology added around DAB, ask:

1.  What problem does it solve?
2.  What competency does it demonstrate?
3.  Is there an architectural justification?
4.  Can the decision be defended in an interview?
5.  Is the technology being added only to increase stack breadth?

If the answer to the last question is yes, do not add it.
