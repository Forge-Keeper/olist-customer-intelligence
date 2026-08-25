# Branch Governance

## Decision

The repository uses a mandatory promotion path:

```text
topic branch -> dev -> main
```

`main` is the stable promotion source for staging and production. Work must not move directly from a feature/fix/chore/docs branch into `main`.

## Roles

- topic branches (`feature/**`, `fix/**`, `chore/**`, `docs/**`): isolated implementation work;
- `dev`: shared integration branch and mandatory validation boundary before `main`;
- `main`: stable release/promotion branch consumed by the automatic staging deployment;
- DAB `dev`: Databricks development target. This is an environment target and is distinct from the Git branch named `dev`.

## Required flow

1. Create the topic branch from the current `dev` branch.
2. Implement and validate on the topic branch.
3. Open a PR from the topic branch into `dev`.
4. Merge only after required CI/documentation gates are green and human approval is recorded when required.
5. Open a promotion PR from `dev` into `main`.
6. Merge `dev -> main` only after the integration state is approved.
7. A successful `main` merge triggers the staging deployment path.
8. Production remains a separate protected promotion after staging success.

Conceptually:

```text
feature/fix/chore/docs
        |
        v
       dev          Git integration branch
        |
        v
       main         stable Git promotion branch
        |
        v
       stg          DAB / Unity Catalog target
        |
        v
       prd          protected DAB / Unity Catalog target
```

## CI guardrail

The CI workflow rejects pull requests into `main` unless their head branch is `dev`. Pull requests into `dev` must originate from a topic branch.

Repository branch protection/rulesets should additionally prevent direct pushes to `dev` and `main` and require the relevant status checks. CI is a second line of defense; it is not a substitute for server-side branch protection.

## Recovery rule

If `dev` and `main` drift because the governance path was bypassed, do not silently discard history. First preserve the old ref, then reconcile/synchronize deliberately and record the correction.

The stale pre-realignment `dev` ref from 2026-08-24 is retained as:

```text
archive/dev-pre-resync-20260824
```

This checkpoint exists only for historical recovery and is not an active development branch.
