# Definition of Done

A feature is Done only when its accepted scope is implemented, validated, documented, operable and reflected in the canonical project status. Passing tests or merging code alone is not sufficient.

## Core Definition of Done

### Scope and decisions

- Accepted requirements and non-goals are satisfied.
- No proposal is represented as a confirmed decision.
- New scope discovered during implementation is either explicitly approved or captured as backlog.
- Relevant ADRs are accepted/updated when a durable architectural decision changed.

### Code quality

- Code respects the package/responsibility boundaries documented in `engineering-standards.md`.
- New/materially changed public classes, functions and methods have useful docstrings.
- Names follow project conventions and reveal responsibility.
- No known dead compatibility layer remains unless explicitly approved as transitional debt.
- No environment-specific secret, credential or production identifier is embedded in source.

### Tests and static gates

- Unit tests cover new invariants and failure paths.
- Integration tests cover cross-component behavior where meaningful.
- Existing regression tests remain green.
- Ruff/type/static checks configured for the repository are green.
- Build/package validation is green when the feature changes deployable code.

### Data/platform changes

When applicable:

- schema/data contracts are updated;
- table lifecycle/migration behavior is explicit;
- schema drift behavior is tested;
- governance metadata/tags are based on real approved facts;
- ABAC/access policy behavior is validated when in scope;
- idempotency/reprocessing behavior is preserved or deliberately changed and documented;
- environment isolation is demonstrated.

### Deployment and operations

When applicable:

- deployment configuration validates for intended targets;
- `dev -> stg -> prd` promotion behavior is documented and tested at the appropriate stage;
- production deployment is protected by the accepted approval model;
- deployment smoke and runtime acceptance are not treated as interchangeable evidence;
- operational logs expose meaningful lifecycle/failure information;
- rollback/recovery expectations are documented.

### Documentation

- Discovery/Requirements/Technical Design/Impact/Implementation Plan reflect the implemented result or are clearly retained as historical gate records.
- Developer/operator instructions exist for new recurring workflows.
- Public API documentation has been reviewed for all touched APIs.
- Naming/convention changes are reflected in `engineering-standards.md` when they establish a reusable rule.
- README is updated only when the durable portfolio narrative or architecture changes; routine readiness updates belong in `docs/platform-status.md`.

### Public status and closeout

A feature may not be represented publicly as `DONE` solely because its code was merged.

The default closeout flow is:

```text
feature implementation
  -> runtime evidence appropriate to the accepted scope
  -> merge / promotion gates
  -> closeout
  -> Platform Status update
  -> DONE
```

The exact order of environment evidence may vary when STG/PRD can only execute after promotion, but the final `DONE` claim still requires closeout and a Platform Status update.

Before marking a feature Done:

- `docs/platform-status.md` records the feature/capability and the exact readiness stage reached;
- Code, DEV, STG and PRD are distinguished rather than collapsed into one vague `implemented` state;
- missing or intentionally unavailable environment evidence is represented explicitly rather than inferred;
- the closeout points to accepted runtime/deployment evidence when such evidence is in scope;
- historical feature documents do not override the canonical current status;
- GitHub Issues contain any deferred work that remains future scope.

### Delivery

- CI checks required by the repository are green on the PR/commit.
- PR description reflects actual scope and major decisions.
- No unresolved blocker or known high-severity defect remains hidden.
- Source of truth is GitHub and the final branch/PR state is auditable.
- The public status checkpoint is consistent with the delivered evidence before the feature is called Done.

## Feature-level Definition of Done

Each feature specification may add acceptance items beyond this global baseline. It may not silently weaken this baseline; an exception must be explicit and justified in the feature documentation.

## Documentation review checklist

Before marking a feature Done, inspect every public API created or materially changed by the feature and ask:

1. Can another engineer understand what this abstraction owns?
2. Is the important boundary (what it does not own) clear?
3. Are non-obvious side effects and fail-fast behaviors documented?
4. Are arguments/returns already obvious from types, or does the docstring add useful semantics?
5. Would a future implementation agent know how to use it without reconstructing design decisions from Git history?
6. Does Platform Status state the feature's current readiness without relying on stale README or gate-document wording?

If the answer to an important item is no, the feature is not Done.
