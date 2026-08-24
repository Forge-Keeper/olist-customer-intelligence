# DAB + Platform Contracts — Impact Analysis

## Status

**Proposed — Impact Analysis gate.**

This document enumerates the expected code, deployment, test and documentation impact of the approved DAB + Platform Contracts requirements and proposed Technical Design.

## Impact summary

The feature is a focused platform refactor plus one deployment vertical slice. It intentionally does not migrate every job to DAB.

The contract migration strategy is **Option A: migrate all current Bronze dataset declarations to the new executable `DatasetContract` in this feature**. A compatibility layer between `BronzeDatasetConfig` and `DatasetContract` is not the target design.

Primary impacted areas:

1. root bundle/deployment configuration;
2. Python packaging/entry point;
3. generic Delta contract/lifecycle abstractions;
4. all current Bronze dataset contracts plus BronzeWriter integration;
5. IBGE municipality GDP DAB pilot;
6. table/column governance metadata support;
7. tests for contracts/lifecycle/writer/datasets/GDP;
8. CI/CD workflow configuration;
9. development docs and ADRs.

## 1. New files/directories

### DAB

```text
databricks.yml
resources/
└── jobs/
    └── ibge_municipality_gdp.job.yml
```

### Platform contract/lifecycle

Recommended new modules:

```text
src/olist_data_platform/platform/delta/
├── contract.py
└── lifecycle.py
```

`contract.py` owns small declarative types such as:

- `ColumnContract`;
- `DatasetContract`;
- `TableLayout`;
- `TableMetadata`;
- `SchemaEvolutionPolicy`;
- structured schema-diff types/helpers where cohesive.

`ColumnContract` must support column-level governance tags in addition to name/type/nullability/description. `TableMetadata` must support table-level governance tags.

`lifecycle.py` owns:

- `DeltaTableLifecycle`;
- table inspection;
- compatibility checks;
- explicit supported schema evolution;
- table description/comment reconciliation;
- table tag reconciliation;
- column tag reconciliation.

Avoid creating a deep package hierarchy until more lifecycle implementations exist.

### Future fine-grained governance extension

Do not create a generalized policy engine in this slice, but reserve a coherent extension point for future Gold governance such as:

```text
row filter policy references
column mask policy references
```

Unity Catalog does not attach metadata tags to individual rows. Row-level governance is implemented through row filters/ABAC policies. Therefore no fake `row_tags` abstraction should be introduced.

### Job metadata

Possible new module, only if justified by implementation:

```text
src/olist_data_platform/platform/jobs/definition.py
```

This is deferrable if the first slice would create a Python `JobDefinition` with no real consumer beyond duplicating YAML.

### CI/CD

The repository currently has no `.github/` directory on this branch. Professional promotion introduces, at minimum, repository-owned workflow definitions conceptually equivalent to:

```text
.github/workflows/ci.yml
.github/workflows/deploy-stg.yml
.github/workflows/deploy-prd.yml
```

Exact split may be consolidated during implementation if one workflow with protected environments is simpler and clearer.

### Tests

Likely new tests:

```text
tests/unit/platform/delta/test_contract.py
tests/unit/platform/delta/test_lifecycle.py
```

Additional integration coverage may be added under:

```text
tests/integration/platform/delta/
```

if the existing integration organization supports it.

## 2. Existing files requiring modification

### `pyproject.toml`

Impact:

- add wheel job entry point for `ibge_municipality_gdp_ingestion:main`;
- add/confirm build tooling needed by CI/bundle artifact build;
- preserve existing package discovery under `src`;
- no application dependency on Databricks SDK is required merely to run the wheel task.

Risk: changing distribution/entry-point naming incorrectly can break `python_wheel_task` resolution.

### `src/olist_data_platform/platform/delta/bronze/config.py`

Current owner: `BronzeDatasetConfig` and `WriteStrategy`.

Approved impact:

- retain `WriteStrategy` in the most cohesive platform location;
- replace/retire `BronzeDatasetConfig` as the dataset declaration model;
- migrate **all current Bronze dataset declarations** to the generic executable `DatasetContract` in this feature;
- do not keep two permanent competing contract models.

Tests directly impacted:

- `tests/unit/platform/delta/bronze/test_config.py`;
- dataset-specific config tests under `tests/unit/`.

### `src/olist_data_platform/platform/delta/bronze/writer.py`

Current responsibilities include both write semantics and table creation.

Required changes:

- consume the executable dataset contract;
- add/retain platform-managed `ingestion_timestamp` before lifecycle validation;
- delegate table creation/layout/metadata/schema compatibility to `DeltaTableLifecycle`;
- remove `_create_table()` responsibility;
- retain MERGE/FULL_REPLACE/replaceWhere semantics;
- preserve logical-key batch validation and non-empty FULL_REPLACE behavior.

Tests directly impacted:

- `tests/unit/platform/delta/bronze/test_writer.py`;
- other Bronze writer tests that construct `BronzeWriter` directly.

Regression risk: table-not-exists path currently performs creation plus initial write in one operation. New lifecycle design creates the empty table and then lets normal write semantics execute; tests must prove equivalent final data behavior.

### All current Bronze dataset configs/writers

Because Option A is approved, the contract migration affects the current Bronze declarations across IBGE, Weather and Olist, including at least:

```text
src/olist_data_platform/domains/bronze/ibge/municipalities_bronze_config.py
src/olist_data_platform/domains/bronze/ibge/municipality_population_bronze_config.py
src/olist_data_platform/domains/bronze/ibge/municipality_gdp_bronze_config.py
src/olist_data_platform/domains/bronze/ibge/bronze_municipalities_writer.py
src/olist_data_platform/domains/bronze/ibge/bronze_municipality_population_writer.py
src/olist_data_platform/domains/bronze/ibge/bronze_municipality_gdp_writer.py
src/olist_data_platform/domains/bronze/weather/*
src/olist_data_platform/domains/bronze/olist/*
```

The migration is intended to be mechanical where possible:

- convert required columns into explicit `ColumnContract` definitions;
- preserve key columns;
- preserve write strategy;
- preserve clustering/partitioning;
- add table/column descriptions based only on known semantics;
- add only justified governance tags;
- keep schema evolution disabled unless explicitly justified.

This is **contract migration**, not DAB migration. Other jobs remain undeployed by DAB in this slice.

### `src/olist_data_platform/domains/bronze/ibge/municipality_gdp_bronze_config.py`

Additional pilot impact:

- becomes the authoritative GDP `DatasetContract` declaration;
- declare persisted GDP columns with types/nullability/descriptions;
- declare logical key and `dt_base` clustering;
- declare table metadata/tags;
- support column tags structurally, without inventing classifications that the dataset does not justify;
- schema evolution remains disabled by default.

Potential rename to a `*_contract.py` filename is architecturally cleaner but causes extra imports/test churn. Rename only if it materially improves clarity; otherwise keep the existing module name in this slice and change the object semantics.

### `src/olist_data_platform/domains/bronze/ibge/bronze_municipality_gdp_writer.py`

Current behavior contains a transient `INPUT_SCHEMA` with `payload_json` before conversion to final VARIANT payload.

Impact:

- preserve source adapter behavior;
- remove duplicated persisted-schema declarations where the DatasetContract can supply them;
- keep only transient construction schema fields genuinely required for JSON-to-VARIANT conversion;
- continue delegating persistence to generic `BronzeWriter`.

### `src/olist_data_platform/jobs/ibge_municipality_gdp_ingestion.py`

Impact expected to be small:

- remain the runtime application entrypoint;
- preserve `--target-table` and `--periods` CLI behavior;
- expose `main` via wheel entry point;
- no target-name/environment conditionals.

### Exploration notebooks

Files:

```text
notebooks/exploration/ibge_bronze_validation.py
notebooks/exploration/ibge_gdp_bronze_validation.py
```

Impact:

- remove or parameterize production catalog hardcodes if these notebooks remain active validation utilities;
- they do not become bundle deployment resources;
- official environment validation moves to the deployed job/contract smoke flow.

## 3. Existing tests likely affected

Known direct test owners include:

```text
tests/unit/platform/delta/bronze/test_config.py
tests/unit/platform/delta/bronze/test_writer.py
tests/unit/test_bronze_weather_writer.py
tests/unit/test_olist_closed_deals_bronze_config.py
```

Equivalent dataset-config/writer tests must be updated because all Bronze contracts are migrated in one feature.

New governance tests must cover at least:

- valid/invalid table tag declarations;
- valid/invalid column tag declarations;
- lifecycle reconciliation of table tags;
- lifecycle reconciliation of column tags;
- metadata drift does not incorrectly become schema drift;
- no PII/sensitivity classification is synthesized by platform defaults.

GDP-specific source/service behavior should ideally need little or no modification.

## 4. Unity Catalog and governance impact

New target namespaces:

```text
dev.bronze.ibge_municipality_gdp
stg.bronze.ibge_municipality_gdp
prd.bronze.ibge_municipality_gdp
```

Required permissions must exist for the appropriate developer/service-principal identities.

The lifecycle will materialize/reconcile metadata on managed tables:

- table comment/description;
- column comments;
- table tags;
- column tags;
- clustering metadata on creation.

Governance direction:

- durable table and column tags are first-class contract state;
- governed tags should be used when the required account-level governed-tag definitions and permissions exist;
- the contract stores tag intent/assignments, but account-level governed-tag taxonomy creation is outside this feature unless required to unblock the pilot;
- future Gold fine-grained governance must be able to add ABAC row-filter and column-mask policy references without replacing `DatasetContract`;
- literal per-row tags are not modeled because rows are not Unity Catalog securable objects.

No automatic migration or deletion of existing `prd` validation tables is included.

## 5. Schema evolution impact

Default:

```text
schema evolution disabled -> drift fails
```

Opt-in v1:

```text
only additive nullable declared columns may be added automatically
```

Operational implications:

- deployment/run logs must surface evolution;
- breaking changes require a deliberate migration procedure;
- future schema-evolution capabilities can be added behind policy without changing the fail-fast default.

## 6. CI/CD and repository governance impact

New external configuration is required outside committed code:

- Databricks authentication for CI;
- staging service-principal identity/permissions;
- production service-principal identity/permissions;
- workspace host/profile information as appropriate;
- GitHub protected environment or equivalent approval control for production;
- Unity Catalog privileges necessary to apply/manage metadata and tags.

Production promotion should require staging success plus manual/protected approval.

## 7. Build/dependency impact

Current project uses setuptools and has no explicit `build` package in its dev group.

Implementation must choose one deterministic wheel-build command available both locally and in CI, for example:

```text
python -m build --wheel
```

with the corresponding development dependency, or a pinned/controlled `uv build` path.

Do not introduce multiple competing build mechanisms.

## 8. Runtime behavior that must not change

Regression guardrails:

- IBGE API/SIDRA extraction semantics;
- GDP `periods` behavior;
- logical primary-key validation;
- VARIANT payload preservation;
- MERGE idempotency;
- FULL_REPLACE safeguards;
- explicit replaceWhere semantics;
- request-id/logging behavior in ingestion services;
- Bronze AS-IS/source-preservation principle.

## 9. Documentation impact

Required new/updated docs:

```text
docs/development/dab-platform-discovery.md
docs/development/dab-platform-requirements.md
docs/development/dab-platform-technical-design.md
docs/development/dab-platform-impact-analysis.md
docs/adr/ADR-004-executable-dataset-contracts-and-delta-lifecycle.md
docs/adr/ADR-005-dab-environment-and-promotion-boundary.md
```

After implementation, add operational developer documentation for:

- local build;
- bundle validate;
- dev deploy/run;
- promotion behavior;
- contract declaration/evolution policy;
- table and column governance tag declaration;
- handling a failed schema compatibility check.

A later Gold/governance feature must document row-filter/column-mask policy authoring and ABAC policy ownership separately from the dataset contract itself.

## 10. ADR impact

### ADR-004

Necessary because the feature changes a durable architectural responsibility boundary and now also establishes governance metadata as executable contract state:

```text
DatasetContract -> schema + metadata/governance definition
DeltaTableLifecycle -> table state/lifecycle + metadata reconciliation
BronzeWriter -> write semantics
```

It establishes fail-fast schema compatibility, controlled evolution, table/column tags, and the future boundary for row/column access policies.

### ADR-005

Necessary because `dev -> stg -> prd`, service-principal identities, production-mode protections and promotion-from-main become durable deployment governance, not merely implementation details.

## 11. Risk assessment

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Generic BronzeWriter change regresses existing datasets | High | migrate all contracts mechanically; run full unit/integration suite |
| Contract and actual Spark VARIANT schema differ | High | dedicated GDP schema tests + workspace smoke validation |
| Incorrect tag taxonomy encodes false governance facts | High | only declare evidenced tags; no inferred PII/sensitivity |
| Governed-tag privileges/config unavailable | Medium | capability remains in contract; treat taxonomy/permissions as deployment prerequisite where used |
| Future row governance confused with row metadata tags | Medium | document row filters/ABAC as the correct extension point |
| Serverless unavailable in workspace | Medium | implementation prerequisite; explicit classic-compute redesign if blocked |
| Service principals/permissions unavailable | High for stg/prd | treat as deployment prerequisite; do not weaken production design silently |
| Schema evolution mutates tables unexpectedly | High | disabled by default; whitelist additive nullable only; logs/tests |
| DAB YAML and Python JobDefinition drift | Medium | keep Python model minimal; defer if no real consumer |
| CI rebuilds different artifact for production | Medium | promote same commit/artifact identity; protected workflow |
| Existing hardcoded `prd` validation paths cause accidental writes | High | parameterize/remove official use before acceptance |

## 12. Scope guardrail

This feature must not expand into:

- complete SAFRA parity;
- full job migration;
- generic data-platform framework generation;
- all environment infrastructure provisioning;
- account-wide governed-tag taxonomy management unless needed to unblock validated pilot metadata;
- generalized ABAC/row-filter/column-mask policy engine;
- schema migration engine;
- Silver/Gold dependency orchestration.

New needs discovered in these areas become separate backlog/features unless they block the accepted vertical slice.

## Impact Analysis exit criteria

The Impact gate is complete when:

1. impacted current files/classes/tests are accepted;
2. Option A full current-Bronze contract migration is accepted;
3. table/column governance tag capability and future Gold row-filter/column-mask extension are accepted;
4. deployment prerequisites are acknowledged;
5. no silent scope expansion remains;
6. Technical Design and ADRs form one coherent implementation boundary.
