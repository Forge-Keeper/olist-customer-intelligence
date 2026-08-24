# <Feature Name> — Feature Specification

> Copy this template into `docs/development/` and split it into separate files when the feature becomes large. Keep confirmed decisions, proposals and open questions visibly distinct.

## 0. Status

- Owner: <pending>
- Branch: <pending>
- Current gate: Discovery
- Decision status: Proposed / Approved / Implemented

## 1. Objective

Describe the business/technical outcome in one paragraph.

### Expected result

State what must be observably true when the feature is complete.

### Non-goals

List scope explicitly excluded from this feature.

## 2. Discovery

### Current state

- Existing components/classes/jobs/tables:
- Current behavior:
- Known pain/problem:

### Stakeholders / consumers

- <role/system> — <need>

### Inputs and sources

- Source systems/files/APIs:
- Expected volume/frequency:
- Data ownership:

### Constraints

- Runtime/platform constraints:
- Security/governance constraints:
- Cost/performance constraints:
- Compatibility constraints:

### Open questions

- [ ] <question>

### Discovery gate

- [ ] Source of truth inspected.
- [ ] Current behavior inventoried.
- [ ] Unknowns and assumptions separated.
- [ ] Scope/non-goals agreed.

## 3. Requirements

Use stable IDs.

| ID | Requirement | Priority | Acceptance evidence |
| --- | --- | --- | --- |
| R1 | <requirement> | P0/P1/P2 | <test/run/artifact> |

### Functional requirements

- R...

### Non-functional requirements

Cover applicable dimensions:

- reliability/idempotency;
- performance/volumetry;
- security/LGPD/governance;
- observability;
- operability/recovery;
- maintainability/testability;
- cost;
- environment isolation;
- compatibility/evolution.

### Data contract requirements

- schema/types/nullability;
- keys;
- write strategy;
- layout;
- metadata/tags;
- quality rules;
- schema evolution policy;
- consumer compatibility.

### Deployment requirements

- targets/environments;
- packaging;
- compute;
- permissions/identity;
- promotion gates.

### Requirements gate

- [ ] P0 requirements accepted.
- [ ] Acceptance criteria observable/testable.
- [ ] No invented deadline/owner.
- [ ] Open requirements marked pending.

## 4. Technical Design

### Architecture

Describe component boundaries and data/control flow.

```text
<Component A>
    -> <Component B>
    -> <External object>
```

### Public APIs / contracts

```python
class Example:
    ...
```

Explain responsibility and non-responsibility of each new abstraction.

### Data model / schema

Include relevant tables/columns/types/keys/layout and evolution behavior.

### Governance and security

Cover applicable:

- table/column governed tags;
- Unity Catalog privileges;
- ABAC row filters;
- ABAC column masks;
- service principals;
- secrets;
- sensitive-data handling.

### Failure behavior

Define fail-fast vs retry/recovery/evolution semantics.

### Observability

Define logs, metrics, run identifiers, alerts or audit evidence.

### Alternatives considered

1. <alternative> — rejected/selected because...

### ADRs required

- [ ] ADR-XXX — <decision>

## 5. Impact Analysis

### Code impact

| Area/file | Change | Risk |
| --- | --- | --- |
| <path> | <change> | Low/Medium/High |

### Data/table impact

- tables/contracts affected;
- schema migrations;
- backfill/reprocessing;
- compatibility.

### Job/deployment impact

- jobs/resources;
- scheduling/dependencies;
- DAB targets;
- CI/CD.

### Test impact

- unit;
- integration;
- workspace smoke;
- regression.

### Documentation impact

- feature docs;
- ADRs;
- runbooks/developer docs;
- public API docstrings;
- standards/templates if reusable rules changed.

### Risks and mitigations

| Risk | Severity | Mitigation |
| --- | --- | --- |
| <risk> | High/Medium/Low | <mitigation> |

## 6. Implementation Plan

Keep checkpoints independently testable.

### Phase 1 — <name>

Changes:
- ...

Validation:
- ...

Definition of checkpoint:
- [ ] ...

### Phase N — Documentation closeout

- reconcile specifications with actual implementation;
- update ADR status;
- document public APIs;
- update operator/developer instructions;
- verify global Definition of Done.

## 7. Validation Plan

### Local/CI

```text
lint
static/type checks
unit tests
integration tests
build
bundle validate (when applicable)
```

### Workspace/runtime

- <smoke test>

### Negative tests

- <intentional drift/failure test>

## 8. Definition of Done

Inherit `docs/development/definition-of-done.md` and add feature-specific acceptance:

- [ ] <feature-specific item>

## 9. Handoff Package

Before implementation can be delegated end-to-end, this package should allow another engineer/agent to proceed without reconstructing intent.

Required context:

- objective/non-goals;
- approved requirements;
- approved technical design;
- impact analysis;
- implementation order/checkpoints;
- ADRs;
- acceptance/validation commands;
- unresolved blockers explicitly marked.

### Implementation prompt template

```text
Implement <feature> in repository <owner/repo>.

GitHub is the source of truth. Read these specifications before changing code:
- <requirements>
- <technical-design>
- <impact-analysis>
- <implementation-plan>
- <ADRs>
- docs/development/engineering-standards.md
- docs/development/definition-of-done.md

Mandatory workflow:
Discovery verification -> Requirements verification -> Design/Impact verification -> implement one approved checkpoint at a time -> run CI/tests -> document actual behavior -> final validation.

Do not invent requirements, owners, deadlines, migrations, governance classifications or environment configuration. Stop and surface a blocker when implementation would require violating an approved decision or expanding scope.

The task is complete only when the feature-specific acceptance criteria and repository Definition of Done are satisfied.
```
