# Engineering Standards and Naming Conventions

## Purpose

This document defines the default engineering conventions for Olist Customer Intelligence. The goal is consistency without ceremony: names should reveal ownership and responsibility, public APIs should explain their contract, and feature work should leave enough durable context for another engineer or agent to continue safely.

These conventions apply to new code and to existing code materially changed by a feature. They do not require repository-wide cleanup unrelated to the current scope.

## 1. Responsibility and package boundaries

Use the repository architecture as the first naming signal.

- `domains/`: business/source-specific behavior and adapters.
- `platform/`: reusable cross-domain technical capabilities.
- `jobs/`: executable composition/entrypoints. Jobs orchestrate collaborators; they do not become business-logic owners.
- `resources/`: deployment/orchestration declarations such as Databricks job resources.
- `docs/adr/`: durable architectural decisions.
- `docs/development/`: discovery, requirements, design, impact, implementation and operational documentation.

A class or module must have one clear owner. If a capability is reusable across domains, it belongs under `platform/`. If it contains IBGE/Olist/Weather-specific semantics, it belongs under the appropriate domain.

## 2. Python naming conventions

Follow PEP 8 naming with additional project semantics.

### Modules and files

Use `snake_case.py`.

Prefer names describing responsibility rather than implementation mechanism:

```text
contract.py
lifecycle.py
writer.py
csv_snapshot_reader.py
municipality_gdp_bronze_config.py
```

Avoid generic names such as `utils.py`, `helpers.py`, `common.py` unless the module truly has a narrow, durable responsibility that cannot be named more precisely.

### Classes

Use `PascalCase` and a responsibility suffix when it improves meaning:

- `DatasetContract`: declarative persisted-data contract.
- `DeltaTableLifecycle`: owns managed Delta table state/lifecycle.
- `BronzeWriter`: owns Bronze write semantics.
- `OlistCsvSnapshotReader`: source reader/adapter.
- `MunicipalityPopulationIngestionService`: domain application service.

Suffix guidance:

| Suffix | Meaning |
| --- | --- |
| `Contract` | declarative, executable invariant/metadata definition |
| `Policy` | configurable decision/allow-list; no orchestration |
| `Lifecycle` | inspect/create/reconcile/evolve state of an external managed object |
| `Writer` | persistence/write semantics |
| `Reader` / `Client` | external/source access boundary |
| `Parser` / `Extractor` | deterministic transformation/extraction |
| `Service` | application/domain orchestration with business/source semantics |
| `Definition` | declarative execution/deployment metadata |

Do not use a suffix merely because another project uses it. The class behavior must match the semantic contract.

### Functions and methods

Use verbs in `snake_case`:

```text
validate_contract()
ensure_table()
apply_metadata()
replace_where()
build_parser()
```

Boolean methods/properties should read as predicates when practical:

```text
can_add_nullable_columns
is_compatible
has_drift
```

Private methods use a leading underscore only when they are implementation details of the owning abstraction.

### Constants

Use `UPPER_SNAKE_CASE` for module/class constants and immutable dataset declarations:

```text
BRONZE_INGESTION_TIMESTAMP
IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG
```

Existing `*_CONFIG` symbols may remain while filenames/import churn would add no value, but new declarations should prefer names that reveal actual semantics (`*_CONTRACT`) when practical.

## 3. Data/platform naming conventions

### Environments

Canonical targets:

```text
dev
stg
prd
```

Do not introduce `prod`, `production`, `stage`, or environment aliases in runtime/domain code.

### Unity Catalog object names

Use lowercase `snake_case` object names. Environment belongs in the catalog, not embedded into the table name.

```text
dev.bronze.ibge_municipality_gdp
stg.bronze.ibge_municipality_gdp
prd.bronze.ibge_municipality_gdp
```

### Dataset layers

Canonical layer vocabulary:

```text
bronze
silver
gold
```

### Governance tags

Tag keys must be lowercase `snake_case` and represent durable governance facts. Initial taxonomy should remain intentionally small.

Examples:

```text
layer=bronze
domain=ibge
source_system=ibge_sidra
managed_by=olist_data_platform
```

Do not invent `pii`, `sensitive`, classification, retention or business-owner values without evidence/decision.

Governed tags intended for ABAC must use the account-approved taxonomy. Dataset code assigns approved tags; it does not silently create governance truth.

## 4. Public API documentation standard

### What must have a docstring

Required for code introduced or materially changed by a feature:

1. public classes;
2. public functions;
3. public methods whose purpose, side effects or failure behavior are not trivial;
4. public dataclasses/value objects that establish a platform/domain contract.

Private methods require docstrings only when they contain a non-obvious invariant, algorithm, side effect or architectural rule.

### What a useful docstring contains

Document the contract, not the syntax.

For a public class, explain:

- responsibility;
- important ownership boundary / what it deliberately does not own;
- externally visible side effects when relevant.

For a public method, explain as needed:

- purpose;
- non-obvious arguments;
- return semantics;
- significant exceptions/fail-fast behavior;
- external side effects.

Avoid noise such as:

```python
 def write(...):
     """Writes data."""
```

Prefer:

```python
 def write(self, dataframe: DataFrame) -> None:
     """Persist one validated Bronze batch using the dataset write strategy.

     The writer injects platform-managed values and validates batch-level keys.
     Delta table creation, schema evolution and governance reconciliation belong
     to the table lifecycle collaborator rather than this method.
     """
```

### Style

Use concise PEP 257-compatible docstrings. Add structured `Args`, `Returns`, `Raises`, or `Side Effects` sections only when they convey information that type hints and the method name do not already make clear.

## 5. Logging conventions

Operational log events should be stable, machine-searchable names followed by explicit fields.

```text
bronze_write_started | target_table=... | strategy=...
schema_evolution_applied | target_table=... | added_columns=...
```

Use lowercase `snake_case` event names. Include identifiers needed to investigate the operation (`target_table`, `request_id`, job/dataset key, changed fields) without logging secrets or raw sensitive payloads.

## 6. Test naming conventions

Use behavior-oriented tests:

```text
test_should_reject_duplicate_columns
test_should_fail_on_type_drift_when_evolution_disabled
test_should_reconcile_column_tags
```

A test name should make the expected behavior understandable without reading its body.

Platform abstractions require tests for invariants and failure semantics, not just happy paths.

## 7. Feature documentation convention

A feature that changes architecture or cross-domain behavior follows the repository gates:

```text
Discovery
  -> Requirements
  -> Technical Design
  -> Impact Analysis
  -> Implementation Plan
  -> Implementation / Validation
  -> Done
```

Use the feature template under `docs/templates/feature-specification-template.md` as the starting point. Separate confirmed decisions from proposals and open questions.

Durable architectural decisions receive an ADR using `docs/templates/adr-template.md`.

## 8. Scope rule for legacy code

When a feature touches an existing public API:

- bring that API up to the current documentation/naming standard when the change is local and safe;
- do not perform unrelated repository-wide renames or documentation cleanup;
- capture larger cleanup as backlog rather than silently expanding scope.

## 9. Enforcement

The Definition of Done requires documentation coverage for new/materially changed public APIs.

CI may progressively enforce docstring/naming rules once the existing touched surface is compliant. Enforcement should target public APIs first; requiring documentation for every private helper is explicitly not a goal.
