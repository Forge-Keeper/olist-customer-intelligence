# DAB + Platform Contracts — Discovery Checkpoint

## Status

Discovery started. No implementation decisions beyond the boundaries below are approved yet.

## Objective

Introduce Databricks Asset Bundles as the deployment/environment boundary for the Olist Customer Intelligence project while evolving the platform toward explicit table lifecycle and job definitions.

This feature is motivated by a real architectural gap: development/validation workflows have materialized tables under the `prd` catalog, while the runtime jobs themselves are already capable of receiving target tables externally. The next step is to formalize `dev` and `prod` targets and stop coupling development execution to production namespaces.

## Current direction

### Environment boundary

Target model:

- `dev` target writes to the development catalog/namespace.
- `prod` target writes to the production catalog/namespace.
- Runtime jobs must receive catalog/table information from deployment configuration rather than hardcoding environment names.
- Existing `prd` validation tables are not automatically dropped or moved as part of Discovery; migration/cleanup is a separate decision after the new boundary exists.

### Databricks Asset Bundles

Initial Bundle scope:

- `databricks.yml`;
- resource YAML files under `resources/`;
- targets `dev` and `prod`;
- environment-specific variables such as catalog/schema;
- first pilot job: IBGE municipality GDP ingestion;
- package/deployment approach to be evaluated, with wheel packaging as the current preferred candidate because the repository already contains a real Python package.

The first vertical slice should demonstrate:

`local validation -> bundle validate -> bundle deploy(dev) -> run job -> verify data in dev namespace`

Full CI/CD promotion is not part of the first slice unless explicitly approved later.

## Platform abstraction direction

Do not turn `BronzeWriter` or `BronzeDatasetConfig` into a god object.

Keep responsibilities separated:

### Table / dataset contract

A dataset/table definition should be able to describe, progressively:

- required columns;
- logical primary key;
- write strategy;
- clustering / partitioning;
- table description;
- column comments;
- tags;
- declarative constraints;
- other table metadata/lifecycle information where justified.

The existing `BronzeDatasetConfig` remains a valid narrow contract and should evolve through smaller reusable metadata objects rather than absorbing every concern directly.

### Table lifecycle

Introduce a reusable Delta table lifecycle boundary when the design is validated. Candidate responsibility:

- create/ensure table;
- apply table layout;
- apply description/comments;
- apply constraints;
- apply tags;
- inspect/validate table state.

`BronzeWriter` should remain focused on batch preparation/validation and write semantics such as MERGE, FULL_REPLACE and explicit reprocessing.

### Job definition

Introduce a small declarative job definition capability with fields such as:

- job name;
- Python entrypoint;
- parameters;
- compute/deployment configuration where appropriate;
- optional dependencies.

Dependency semantics should be representable but remain intentionally shallow in this slice. Bronze jobs are expected to have no dependencies in most cases. Silver and Gold will require explicit dependencies later, but automatic dependency detection, DAG compilation and dependency resolution are out of scope for now.

### DAB resource ownership

Do not build an automatic YAML generator in the first slice.

Keep `databricks.yml` and `resources/*.yml` explicit and versioned. If meaningful duplication later appears between Python definitions and Bundle YAML, evaluate generation only then.

## Metadata/governance scope to investigate

The feature should evaluate support for:

- table descriptions;
- column comments;
- a small durable tag vocabulary (for example layer, domain, source system, data classification, PII where applicable);
- logical/Unity Catalog constraints where they represent real contracts;
- table inspection/validation after creation.

Do not add metadata or constraints merely for demonstration. They must represent source, platform or governance truth.

## Explicit non-goals for the first slice

- automatic dependency detection;
- DAG compiler/planner;
- full Silver/Gold orchestration;
- automatic generation of all Bundle YAML;
- complex schedules;
- Terraform;
- full CI/CD promotion pipeline;
- migration of all existing jobs at once.

## Discovery questions

Before implementation, answer:

1. Which current jobs should be represented in the Bundle, and which one is the minimum viable pilot?
2. What parameters does each current job require?
3. Where are catalog/schema/table names currently hardcoded, especially in notebooks and validation assets?
4. Which environment variables belong in DAB targets versus runtime parameters?
5. What compute model should the first Bundle job use?
6. Should the first deployment package source files directly or build/install a wheel?
7. Which table metadata can be declared safely now?
8. Which constraints are true contracts versus only runtime validation rules?
9. How should table lifecycle responsibilities be separated from write semantics?
10. What is the minimum job-dependency representation needed now without prematurely implementing orchestration logic?

## Next gate

Complete Discovery by inventorying the current jobs, parameters, hardcoded environment references and the existing Bronze/Delta abstractions. Then produce Requirements and Technical Design before implementation.
