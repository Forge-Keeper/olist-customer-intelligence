# DAB + Platform Contracts — Discovery Checkpoint

## Status

Discovery complete. Inventory and boundaries are captured below. No implementation decisions beyond these Discovery findings are approved yet.

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

## Discovery inventory

### Current runnable jobs

The repository currently exposes six production-style Python entrypoints under `src/olist_data_platform/jobs/`:

| Job | Required runtime parameters | Defaults / optional parameters | Environment coupling observed |
| --- | --- | --- | --- |
| `ibge_municipalities_ingestion.py` | `--target-table` | none | target is externally supplied |
| `ibge_municipality_population_ingestion.py` | `--target-table` | `--periods=2016,2017,2018` | target is externally supplied |
| `ibge_municipality_gdp_ingestion.py` | `--target-table` | `--periods=2016,2017,2018` | target is externally supplied |
| `olist_customers_ingestion.py` | `--target-table` | `--source-path=/Volumes/prd/bronze/raw_storage/raw/olist/e_commerce/olist_customers_dataset.csv` | default source path hardcodes `prd` |
| `olist_closed_deals_ingestion.py` | `--target-table` | `--source-path=/Volumes/prd/bronze/raw_storage/raw/olist/funnel/olist_closed_deals_dataset.csv` | default source path hardcodes `prd` |
| `weather_ingestion.py` | `--target-table`, `--latitude`, `--longitude`, `--start-date`, `--end-date` | `--operation=ingest`, `--timezone=auto`, optional `--daily-variables` | target is externally supplied |

### Pilot job decision candidate

`ibge_municipality_gdp_ingestion.py` remains the minimum viable DAB pilot identified in the original Discovery direction because:

- it is already a clean Python entrypoint;
- the target table is already supplied externally;
- it has only one environment-sensitive resource to inject (`target-table`);
- the only business/runtime parameter in the first slice is `periods`;
- it exercises the current generic `BronzeWriter` through a domain adapter without requiring source-volume configuration.

This is still a Design decision to confirm at the next gate, not an implementation approval.

### Hardcoded catalog/schema/environment references

Confirmed hardcodes that must be removed from development execution paths or isolated as environment-specific configuration:

- `notebooks/exploration/ibge_bronze_validation.py`
  - `prd.bronze.ibge_municipalities`
  - `prd.bronze.ibge_municipality_population`
- `notebooks/exploration/ibge_gdp_bronze_validation.py`
  - `prd.bronze.ibge_municipality_gdp`
  - `prd.bronze.ibge_municipalities`
- `src/olist_data_platform/jobs/olist_customers_ingestion.py`
  - default source volume path begins with `/Volumes/prd/bronze/...`
- `src/olist_data_platform/jobs/olist_closed_deals_ingestion.py`
  - default source volume path begins with `/Volumes/prd/bronze/...`

The IBGE production job entrypoints do not hardcode catalog/schema/table names; they already require `--target-table` and are therefore ready to receive a fully qualified target from DAB configuration.

The exploratory API notebook is source-contract discovery and does not currently define production table targets; it should not become a deployment resource.

### Environment configuration boundary

Discovery indicates the following split:

**DAB target/deployment configuration candidates**

- catalog name;
- Bronze schema name;
- fully qualified pilot target table derived from target variables;
- source volume/root for jobs whose raw source lives in Unity Catalog Volumes;
- job compute/deployment configuration;
- package artifact reference.

**Runtime/business parameters**

- IBGE `periods`;
- weather operation, coordinates, dates, timezone and requested daily variables;
- explicit source path override when a caller intentionally wants a non-default dataset location.

The environment must not be inferred inside domain code from `dev`/`prod` string checks.

### Existing Bronze / Delta abstractions

`BronzeDatasetConfig` currently owns the narrow declarative data/write contract:

- `primary_key_columns`;
- `required_columns`;
- `clustering_columns`;
- `partition_columns`;
- `write_strategy` (`MERGE`, `REPLACE_WHERE`, `FULL_REPLACE`).

It validates column lists, primary-key membership in required columns and clustering/partition conflicts. It has no metadata, table-description, column-comment, tag, constraint or environment responsibilities today.

`BronzeWriter` currently owns both write semantics and physical table creation:

- validates required/layout columns;
- adds `ingestion_timestamp`;
- validates null/duplicate logical primary keys;
- creates a Delta table when absent;
- applies `clusterBy` or `partitionBy` at creation;
- executes MERGE or full replacement;
- supports explicit `replaceWhere` reprocessing.

The relevant architectural seam is therefore concrete: `_create_table()` currently mixes table lifecycle/layout creation with persistence behavior. This is the point from which a reusable Delta lifecycle collaborator can be extracted without changing the domain adapters' responsibilities.

IBGE-specific Bronze writers are thin adapters around `BronzeWriter`: they translate source records into a typed Spark DataFrame / VARIANT payload and delegate persistence. This boundary should remain intact.

### Metadata and constraint findings

The current codebase provides enough truth to declare only a conservative first metadata slice:

- table description: safe when sourced from the dataset's actual purpose;
- column comments: safe for stable technical/source semantics already represented by code contracts;
- tags: start only with durable platform facts such as `layer=bronze`, `domain=ibge`, `source_system=ibge`; classification/PII tags require dataset-specific evidence;
- primary keys in `BronzeDatasetConfig` are currently logical validation/merge keys, not evidence of an enforced relational primary-key constraint in Unity Catalog;
- non-null and duplicate checks are runtime write-contract validation today and must not automatically be converted into table constraints without a separate contract decision.

### Job dependency representation

No current Bronze entrypoint requires another repository job to complete first in order to execute its own ingestion. The minimum useful representation is therefore an optional explicit dependency list in a job definition model, defaulting to empty.

Discovery does not justify automatic DAG inference, dependency scanning or orchestration planning.

### Packaging / deployment finding

The repository is already organized as a Python package under `src/olist_data_platform` with `pyproject.toml`. Wheel packaging is therefore the preferred candidate for the first DAB design because it provides an explicit deployable artifact and avoids relying on Databricks Repo path bootstrapping used only by exploration notebooks.

Direct source-file deployment remains a fallback to evaluate during Technical Design if wheel execution introduces disproportionate friction for the first vertical slice.

### Compute model

No repository evidence currently mandates a specific compute model. The first Bundle job needs ordinary Spark + Delta/Unity Catalog access and outbound HTTP access to IBGE. The exact DAB job compute configuration remains pending for Technical Design and must be selected based on the available Databricks workspace/runtime constraints rather than invented during Discovery.

## Discovery answers

1. **Which jobs exist / pilot?** Six runnable entrypoints exist. IBGE municipality GDP is the preferred pilot candidate; mass migration is out of scope.
2. **Parameters?** Inventoried above. All jobs accept externally supplied target tables; Olist snapshot jobs additionally contain `prd`-coupled default source paths.
3. **Hardcodes?** Confirmed in two IBGE validation notebooks and two Olist source-path defaults.
4. **Target variables vs runtime params?** Catalog/schema/source-root/compute/package belong to deployment configuration; periods/dates/coordinates/operation remain runtime/business inputs.
5. **Compute model?** Pending Technical Design; no repository evidence supports choosing one yet.
6. **Source vs wheel?** Wheel is preferred candidate; validate feasibility in Design.
7. **Metadata safely declarable now?** Dataset/table descriptions, stable column comments and a small set of durable platform/source tags.
8. **Constraints vs runtime validation?** Current PK/non-null/duplicate semantics are application/write contracts; do not promote them automatically to UC constraints.
9. **Lifecycle separation?** Extract table ensure/create/layout/metadata/inspection behind a Delta lifecycle collaborator; keep `BronzeWriter` responsible for preparation and write semantics.
10. **Minimum dependency model?** Explicit optional dependency names/keys, empty by default; no inference or DAG compiler.

## Discovery exit criteria

Discovery is considered complete when this checkpoint is reviewed and approved. The next mandatory gates are:

1. Requirements — convert these findings into explicit functional/non-functional requirements and acceptance criteria.
2. Technical Design — define DAB structure, variable resolution, pilot resource, packaging/compute choice, lifecycle contract and minimum job definition model.
3. Impact — enumerate affected files/classes/tests and migration boundaries.
4. Implementation Plan — ordered changes only after the prior gates are approved.

No DAB implementation should begin before approval to proceed beyond Discovery.
