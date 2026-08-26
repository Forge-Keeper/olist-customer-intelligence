# ADR-006 — Unity Catalog ABAC Governance

- **Status:** Accepted
- **Date:** 2026-08-24
- **Decision owners:** Project maintainers
- **Scope:** Fine-grained access governance, governed tags, row filters and column masks

## Context

Olist Customer Intelligence required a scalable governance model that separates dataset attributes from centralized access policies. Unity Catalog governed tags can describe securable objects such as tables and columns, while row/column protection belongs to policy logic rather than dataset-specific ad-hoc code.

Rows are not tagged securable objects. Row-level security is implemented through row-filter policy logic that evaluates row values together with governed object attributes and caller context.

## Decision

### 1. ABAC is the preferred scalable fine-grained governance mechanism

Where a use case can be expressed through Unity Catalog ABAC, centralized policies are preferred over duplicating local masks/filters on each table. Normal Unity Catalog privileges and ownership still provide the base access-control layer.

### 2. Governed tags are first-class dataset metadata

`DatasetContract` and `ColumnContract` may declare approved governed-tag assignments for tables and columns. Tags represent dataset facts; they do not embed the full access-control policy.

No taxonomy value is invented without governance truth, and tag names/values/descriptions must not contain secrets or personal data.

### 3. Policy definitions are separate governance objects

Governance policy definitions remain independent from `DatasetContract` and support row-filter and column-mask policy types, reusable scope and explicit matching/policy expressions.

### 4. Column-mask and row-filter policies are first-class capabilities

The platform governance lifecycle can represent, create/ensure, inspect and validate centralized ABAC column-mask and row-filter policies. Synthetic/disposable development objects are used when a real business dataset does not justify masking/filtering.

### 5. Prefer the broadest safe reusable scope

Policies should attach at reusable catalog/schema scope when safe. Table-level scope remains available for legitimate local exceptions or platform limitations.

### 6. Governance policy lifecycle is separate from Delta table lifecycle

`DeltaTableLifecycle` owns table state, schema, layout and metadata assignments. `GovernancePolicyLifecycle` owns policy state. This keeps both responsibilities independently testable and prevents lifecycle abstractions from becoming god objects.

### 7. Governed-tag taxonomy provisioning is an explicit external boundary

The repository may specify expected taxonomy, but account/workspace-level governed-tag creation and assignment authority depend on appropriate Databricks administrative privileges. Missing authority is an explicit prerequisite, not a hidden application behavior.

### 8. Runtime prerequisites are explicit

ABAC-protected objects require supported Databricks compute/runtime capabilities. Workspace smoke tests validate applicable behavior in the target environment.

### 9. ABAC GRANT policies remain deferred

Dynamic ABAC GRANT policies are not part of this decision's implemented v1 boundary and require a separate future decision when maturity and operational requirements justify them.

## Alternatives considered

### Per-table masks and row filters only

Rejected as the default because it duplicates policy logic and scales poorly.

### Put policies directly inside every dataset contract

Rejected because one centralized policy can apply to many tagged datasets and has its own governance lifecycle.

### Model row sensitivity using row tags

Rejected because rows are not securable objects that receive Unity Catalog tags.

### Implement all ABAC capabilities immediately

Rejected to avoid broadening the first governance foundation beyond concrete needs.

## Consequences

### Positive

- dataset attributes and policy behavior remain distinct;
- governed tags become actionable rather than decorative metadata;
- row/column protection can be centralized and inherited;
- governance state is testable and observable;
- later Gold datasets can use the foundation without redesigning dataset contracts.

### Costs / prerequisites

- taxonomy and permission management require appropriate Unity Catalog administration;
- governance policy lifecycle is an additional operational component;
- realistic behavior validation may require appropriate identities/groups and supported compute.

## Implementation evidence

The current platform implements the accepted foundation:

- governed table/column metadata is represented by contract types;
- governance policy definitions and lifecycle exist under the platform governance boundary;
- row-filter and column-mask policy types are represented separately from dataset contracts;
- governance lifecycle behavior has unit coverage;
- a Databricks ABAC smoke job exists for controlled development validation;
- public GDP data remains free of fabricated sensitivity metadata;
- ABAC GRANT policies remain outside the implemented boundary.

Account-level taxonomy provisioning and permissions continue to be environment prerequisites rather than source-controlled secrets or hidden assumptions.
