# ADR-006 — Unity Catalog ABAC Governance

- **Status:** Proposed
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Fine-grained access governance, governed tags, row filters and column masks

## Context

Olist Customer Intelligence is evolving from dataset-local metadata toward a reusable data-platform governance model. The platform already plans executable table/column metadata in `DatasetContract`, but Gold datasets will require scalable fine-grained access controls that should not be reimplemented independently per table.

Unity Catalog Attribute-Based Access Control (ABAC) uses governed tags as securable-object attributes and centrally managed policies to apply row filters and column masks dynamically. Policies can be attached at catalog, schema or table scope and can apply automatically to matching tagged objects.

The platform therefore needs to distinguish two responsibilities:

1. **dataset attributes** — facts about tables and columns, represented by governed tag assignments;
2. **access policies** — centralized rules that interpret those attributes and caller/row context.

Rows are not tagged securable objects. Row-level security is implemented through row-filter policy logic that evaluates row values together with governed object attributes and caller context.

## Decision

### 1. ABAC is the default scalable fine-grained governance mechanism

For use cases that can be expressed through Unity Catalog ABAC, the platform will prefer centralized ABAC policies over table-by-table custom masks or filters.

This does not replace normal Unity Catalog privileges/ownership. ABAC is an additional fine-grained governance layer.

### 2. Governed tags are first-class executable metadata

`DatasetContract` and `ColumnContract` may declare governed-tag assignments for tables and columns.

The contract represents the intended attributes of a dataset. It does not define all access-control policy behavior inline.

Examples of future governed taxonomies may include data classification, sensitivity class, business domain or access profile, but no taxonomy value is invented without governance truth.

Tag names, values and descriptions must not contain secrets or personal data.

### 3. Policy definitions are separate platform governance objects

Introduce a governance policy model independent of `DatasetContract`, conceptually capable of representing:

```text
GovernancePolicyDefinition
├── key/name
├── policy_type
│   ├── ROW_FILTER
│   └── COLUMN_MASK
├── scope
│   ├── catalog
│   ├── schema
│   └── table
├── tag condition / matching expression
├── UDF or inline policy expression reference
└── description
```

This prevents duplicating the same centralized policy across every dataset contract.

### 4. Column-mask policies are a v1 capability

The first governance implementation must be able to create/ensure, inspect and validate a centralized ABAC column-mask policy driven by governed tags.

The policy must be exercised in `dev` using synthetic/disposable data unless a legitimate business dataset already requires masking.

### 5. Row-filter policies are a v1 capability

The first governance implementation must be able to create/ensure, inspect and validate an ABAC row-filter policy.

The validation must use controlled synthetic data and caller/group contexts where the workspace permits.

Literal row tags are explicitly rejected. Any per-row business attribute used by a policy is a regular data column.

### 6. Prefer reusable catalog/schema scope

Policies should attach at the broadest safe reusable scope, normally catalog or schema, so newly tagged objects inherit governance automatically.

Table-level scope is allowed only for genuine local exceptions or when required by a platform limitation.

### 7. Governance policy lifecycle is separate from Delta table lifecycle

`DeltaTableLifecycle` owns table state, schema, layout and table/column metadata assignments.

A separate governance responsibility owns policy state, conceptually:

```text
GovernancePolicyLifecycle
├── ensure_policy
├── inspect_policy
├── validate_policy
├── reconcile_policy
└── structured logging
```

This keeps ABAC policy management from turning `DeltaTableLifecycle` into a god object.

### 8. Governed-tag taxonomy management is an explicit boundary

The repository may declare required governed-tag keys/allowed values as specification, but account-level governed-tag creation and `ASSIGN` permissions require appropriate administrative authority.

If CI/deployment does not have that authority, taxonomy provisioning is an external prerequisite rather than a hidden manual assumption.

Dataset/table/column assignment still requires the appropriate Unity Catalog privileges.

### 9. Compute/runtime prerequisites are validated

ABAC row-filter and column-mask policies require supported compute. The implementation must validate current Databricks requirements before workspace smoke tests.

The selected serverless direction is compatible with this requirement when available.

### 10. ABAC GRANT policies are deferred

Dynamic ABAC GRANT policies are currently Beta and are not part of v1.

The governance model must not preclude them, but their adoption requires a separate explicit decision after evaluating maturity, supported securables and operational implications.

## Alternatives considered

### Per-table masks and row filters only

Rejected as the default platform pattern because it scales poorly and duplicates governance logic across tables.

### Put policies directly inside every `DatasetContract`

Rejected because centralized ABAC policies can apply to many datasets and should remain independently governed/versioned.

### Model row sensitivity using row tags

Rejected because Unity Catalog tags apply to securable objects, not individual rows. Row-level security belongs in row-filter policy logic.

### Implement all ABAC features including GRANT policies immediately

Rejected because GRANT policies are Beta and are not needed to prove the first fine-grained governance foundation.

## Consequences

### Positive

- governed tags become actionable attributes rather than decorative metadata;
- Gold can add sensitive datasets without redesigning the contract foundation;
- row/column protection can be centralized and inherited by newly tagged objects;
- separation of dataset facts from access policies remains clear;
- policy drift can be validated and tested like other platform state.

### Negative / cost

- requires governed-tag taxonomy and permissions at the Databricks account/workspace level;
- introduces policy/UDF lifecycle in addition to table lifecycle;
- realistic validation requires multiple identities/groups or equivalent workspace test context;
- ABAC-protected objects impose runtime compatibility requirements on readers.

## Implementation constraints

- do not add false sensitive tags to public IBGE GDP data;
- prove row-filter and column-mask policies using disposable/synthetic `dev` objects;
- policy mutation must be observable/logged;
- policy definitions must remain separate from dataset contracts;
- do not implement a generalized policy compiler beyond the two required v1 policy types;
- do not adopt ABAC GRANT policies in this feature.

## Validation

This decision is considered implemented when:

1. governed table/column tag assignments are representable and materializable;
2. a reusable ABAC policy definition/lifecycle exists;
3. a synthetic `dev` column-mask policy is deployed and behavior validated;
4. a synthetic `dev` row-filter policy is deployed and behavior validated;
5. declared policy state can be inspected/validated;
6. policy changes/failures are observable;
7. GDP remains free of fabricated sensitivity metadata;
8. developer documentation explains taxonomy, permissions, policy declaration and validation.
