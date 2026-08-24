# DAB + Platform Contracts — Impact Analysis

## Status

**Proposed — Impact Analysis gate.**

This document enumerates the expected code, deployment, test and documentation impact of the approved DAB + Platform Contracts requirements and proposed Technical Design.

## Impact summary

The feature is a focused platform refactor plus one deployment vertical slice. It intentionally does not migrate every job.

Primary impacted areas:

1. root bundle/deployment configuration;
2. Python packaging/entry point;
3. generic Delta contract/lifecycle abstractions;
4. existing BronzeWriter integration;
5. IBGE municipality GDP contract/writer;
6. tests for contracts/lifecycle/writer/GDP;
7. CI/CD workflow configuration;
8. development docs and ADRs.

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

`lifecycle.py` owns:

- `DeltaTableLifecycle`;
- table inspection;
- compatibility checks;
- explicit supported schema evolution;
- metadata reconciliation.

Avoid creating a deep package hierarchy until more lifecycle implementations exist.

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

Impact options:

**Preferred:** retain `WriteStrategy`, migrate dataset declarations toward the new generic `DatasetContract`, and remove/retire `BronzeDatasetConfig` once all current Bronze configs can be adapted without a compatibility burden.

**Safer incremental alternative:** make `BronzeDatasetConfig` a compatibility/narrow persistence object temporarily consumed by `DatasetContract`.

The implementation plan must choose one path and avoid maintaining two permanent competing contract models.

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

### `src/olist_data_platform/domains/bronze/ibge/municipality_gdp_bronze_config.py`

Impact:

- becomes the authoritative GDP `DatasetContract` declaration;
- declare persisted GDP columns with types/nullability/descriptions;
- declare logical key and `dt_base` clustering;
- declare table metadata/tags;
- schema evolution remains disabled by default.

Potential rename to a `*_contract.py` filename is architecturally cleaner but causes extra imports/test churn. Rename only if it materially improves clarity; otherwise keep the existing module name in this slice and change the object semantics.

### `src/olist_data_platform/domains/bronze/ibge/bronze_municipality_gdp_writer.py`

Current behavior contains a transient `INPUT_SCHEMA` with `payload_json` before conversion to final VARIANT payload.

Impact:

- preserve source adapter behavior;
- remove duplicated persisted-schema declarations where the DatasetContract can supply them;
- keep only transient construction schema fields genuinely required for JSON-to-VARIANT conversion;
- continue delegating persistence to generic `BronzeWriter`.

Risk: attempting to force the persisted VARIANT contract into the transient Python-row construction step can unnecessarily complicate the adapter. Technical Design explicitly allows a transient staging schema.

### `src/olist_data_platform/jobs/ibge_municipality_gdp_ingestion.py`

Impact expected to be small:

- remain the runtime application entrypoint;
- preserve `--target-table` and `--periods` CLI behavior;
- expose `main` via wheel entry point;
- no target-name/environment conditionals.

Existing tests around service orchestration should remain valid.

### Other Bronze dataset configs/writers

Even though only GDP is the DAB pilot, changing the `BronzeWriter` constructor/contract model may compile-time/runtime impact:

```text
src/olist_data_platform/domains/bronze/ibge/municipalities_bronze_config.py
src/olist_data_platform/domains/bronze/ibge/municipality_population_bronze_config.py
src/olist_data_platform/domains/bronze/ibge/bronze_municipalities_writer.py
src/olist_data_platform/domains/bronze/ibge/bronze_municipality_population_writer.py
src/olist_data_platform/domains/bronze/weather/*
src/olist_data_platform/domains/bronze/olist/*
```

This is the largest refactor risk.

Implementation should choose between:

- migrating all existing `BronzeDatasetConfig` declarations mechanically to the new contract so `BronzeWriter` has one clean API; or
- temporarily supporting the old config through a compatibility adapter while only GDP uses full metadata/schema capabilities.

Recommendation: migrate existing config declarations if the change is mechanical and tests are already strong; avoid a long-lived compatibility layer.

This is **contract migration**, not DAB migration. Other jobs remain undeployed by DAB in this slice.

### Exploration notebooks

Files:

```text
notebooks/exploration/ibge_bronze_validation.py
notebooks/exploration/ibge_gdp_bronze_validation.py
```

They currently hardcode `prd.bronze.*`.

Impact:

- remove or parameterize production catalog hardcodes if these notebooks remain active validation utilities;
- they do not become bundle deployment resources;
- official environment validation moves to the deployed job/contract smoke flow.

## 3. Existing tests likely affected

Known direct test owners from current repository structure include:

```text
tests/unit/platform/delta/bronze/test_config.py
tests/unit/platform/delta/bronze/test_writer.py
tests/unit/test_bronze_weather_writer.py
tests/unit/test_olist_closed_deals_bronze_config.py
```

Additionally, equivalent dataset-config/writer tests returned by the current unit suite must be updated if the generic contract constructor changes.

GDP-specific behavior to preserve includes tests around:

```text
tests/unit/test_ibge_municipality_gdp_extractor.py
tests/unit/test_ibge_municipality_gdp_ingestion_service.py
```

These should ideally need little or no modification because source extraction/service semantics are not changing.

## 4. Unity Catalog impact

New target namespaces:

```text
dev.bronze.ibge_municipality_gdp
stg.bronze.ibge_municipality_gdp
prd.bronze.ibge_municipality_gdp
```

Required permissions must exist for the appropriate developer/service-principal identities.

The lifecycle will begin materializing metadata on created/managed tables:

- table comment/description;
- column comments;
- approved tags;
- clustering metadata on creation.

No automatic migration or deletion of existing `prd` validation tables is included.

Potential operational risk: a pre-existing table may not match the newly authoritative contract. The default outcome is fail-fast; migration is not silently performed unless the exact change is in the approved evolution matrix and the dataset explicitly enables it.

## 5. Schema evolution impact

Introducing schema evolution changes the platform's failure semantics but not the default safety posture.

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
- GitHub protected environment or equivalent approval control for production.

Production promotion should require staging success plus manual/protected approval.

This is a repository/process change and should be documented in ADR-005 and developer docs.

## 7. Build/dependency impact

Current project uses setuptools and has no explicit `build` package in its dev group.

Implementation must choose one deterministic wheel-build command available both locally and in CI, for example:

```text
python -m build --wheel
```

with the corresponding development dependency, or a pinned/controlled `uv build` path.

Do not introduce multiple competing build mechanisms.

## 8. Runtime behavior that must not change

The following are regression guardrails:

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
- handling a failed schema compatibility check.

## 10. ADR impact

### ADR-004

Necessary because the feature changes a durable architectural responsibility boundary:

```text
DatasetContract -> definition
DeltaTableLifecycle -> table state/lifecycle
BronzeWriter -> write semantics
```

It also establishes fail-fast schema compatibility and controlled evolution policy.

### ADR-005

Necessary because `dev -> stg -> prd`, service-principal identities, production-mode protections and promotion-from-main become durable deployment governance, not merely implementation details.

## 11. Risk assessment

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Generic BronzeWriter change regresses existing datasets | High | migrate mechanically or use short-lived adapter; run full unit/integration suite |
| Contract and actual Spark VARIANT schema differ | High | dedicated GDP schema tests + workspace smoke validation |
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
- all catalog permission automation;
- schema migration engine;
- Silver/Gold dependency orchestration.

New needs discovered in these areas become separate backlog/features unless they block the accepted vertical slice.

## Impact Analysis exit criteria

The Impact gate is complete when:

1. impacted current files/classes/tests are accepted;
2. contract-migration strategy for non-GDP Bronze configs is selected;
3. deployment prerequisites are acknowledged;
4. no silent scope expansion remains;
5. Technical Design and ADRs can be reviewed as one coherent implementation boundary.
