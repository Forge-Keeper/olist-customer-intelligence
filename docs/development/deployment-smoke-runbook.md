# Deployment Smoke Runbook

## Purpose

Deployment smoke tests are the post-deploy gate for production DAB workloads. They prove that every declared production job can execute its representative path in STG before the same approved artifact is eligible for PRD.

The smoke contract is deployment-oriented. It is not the source of truth for per-dataset runtime acceptance or full regression evidence.

## Source of truth

`deployment/smoke-jobs.yml` is the declarative smoke manifest.

Every job declared in `resources/*.job.yml` must have exactly one smoke contract in the manifest. CI runs:

```bash
python scripts/run_deployment_smokes.py --validate-only
```

and fails when:

- a DAB job has no smoke contract;
- the manifest references a job that no longer exists;
- a dependency references an unknown smoke node;
- the dependency graph contains a cycle.

Each smoke node declares:

- `arguments`: complete runtime arguments for the representative execution;
- `depends_on`: upstream smoke nodes that must succeed before this node becomes runnable.

The dependency graph is intentionally layer-agnostic. It can represent Bronze -> Silver -> Gold dependencies and future Gold -> Gold dependencies without forcing fixed execution waves.

## Current smoke contracts

The current manifest covers every declared DAB job. The Bronze-only graph currently has no inter-job execution dependencies, so those nodes are eligible to run concurrently.

`${target}` is resolved by the smoke runner to `stg` or `prd` before invoking the Databricks CLI.

For IBGE workloads, the representative smoke is explicitly bounded to the 2018 period. Other jobs retain their declared representative runtime contract from the manifest.

## Runtime parameter semantics

Bundle variables such as `gdp_periods` and `cempre_periods` are resolved when the bundle is deployed. Setting `BUNDLE_VAR_*` only when calling an already-deployed job does not retroactively change the task parameters stored in that job.

For Python wheel tasks, runtime arguments passed after the Databricks CLI `--` separator replace the task's complete parameter list for that run. The smoke contract must therefore include every required task argument, not only the value being bounded.

The runner builds commands equivalent to:

```bash
databricks bundle run -t stg ibge_municipality_gdp -- --target-table stg.bronze.ibge_municipality_gdp --periods 2018
```

The normal deployed job configuration remains unchanged; only the smoke execution contract is applied.

## DAG scheduling and bounded parallelism

STG executes the manifest after `databricks bundle deploy -t stg`:

```bash
python scripts/run_deployment_smokes.py --target stg
```

PRD executes the same manifest after deploying the exact wheel retained by the approved STG run:

```bash
python scripts/run_deployment_smokes.py --target prd
```

The runner is dependency-aware:

1. validate the complete DAG before starting Databricks execution;
2. mark a node runnable as soon as all of its own `depends_on` nodes are `SUCCESS`;
3. execute independent runnable nodes concurrently;
4. enforce bounded concurrency with `--max-workers` (default: `4`);
5. mark a node `BLOCKED` when any required upstream node is `FAILED` or `BLOCKED`;
6. allow unrelated branches of the DAG to continue;
7. fail the overall smoke command when any node ends as `FAILED` or `BLOCKED`.

This is not a fixed layer barrier. A future Silver node may start as soon as its required Bronze dependencies succeed even while unrelated Bronze work is still running.

To override the concurrency bound deliberately:

```bash
python scripts/run_deployment_smokes.py --target stg --max-workers 2
```

Concurrency should remain bounded because Databricks job startup, shared administrative tables, workspace quotas and cloud compute are finite resources.

## Result states and evidence

Per-node terminal states are:

- `SUCCESS` — the Databricks smoke command completed successfully;
- `FAILED` — the smoke command failed;
- `BLOCKED` — execution was skipped because a required upstream node failed or was blocked.

Smoke results are written to:

```text
dist/deployment-smoke-results.txt
```

The result artifact records a terminal status for every node, including failed and blocked nodes.

STG retains that file with the promoted wheel, SHA-256 and promotion manifest. PRD requires the staging smoke evidence to be present, preserves it as `staging-smoke-results.txt`, runs the production smoke contract, and retains both staging and production smoke evidence with the production promotion manifest.

GitHub Actions logs remain the detailed execution evidence, including Databricks run output and run URLs.

## Adding or changing a DAB job

When adding a production job under `resources/*.job.yml`:

1. define the smallest safe representative execution for deployment smoke;
2. add the job key and complete runtime argument list to `deployment/smoke-jobs.yml`;
3. declare every required upstream smoke node in `depends_on` and no unrelated dependency;
4. include all required Python wheel task arguments because runtime overrides replace the complete parameter list;
5. use `${target}` when a target-dependent table or resource must resolve consistently in STG and PRD;
6. run `python scripts/run_deployment_smokes.py --validate-only` locally or rely on CI;
7. update this runbook when smoke semantics materially change.

A new job without a manifest entry, with an unknown dependency, or participating in a cycle must fail CI before deployment.

## Dependency examples

A future layered graph may be represented as:

```json
{
  "jobs": {
    "olist_orders": {
      "depends_on": [],
      "arguments": []
    },
    "olist_order_items": {
      "depends_on": [],
      "arguments": []
    },
    "silver_orders": {
      "depends_on": ["olist_orders", "olist_order_items"],
      "arguments": []
    },
    "gold_sales": {
      "depends_on": ["silver_orders"],
      "arguments": []
    }
  }
}
```

Independent nodes can run in parallel while the scheduler preserves the declared vertical dependency chain.

## Unsafe or expensive jobs

Do not encode a destructive or unnecessarily expensive full production workload as a deployment smoke merely to satisfy coverage. The manifest contract must remain explicit, but the safe representative execution strategy should be designed for that job before promotion is allowed.

If a future job cannot be made safe enough for direct execution, treat that as a design decision and evolve the smoke contract deliberately rather than adding an implicit skip.

## Promotion invariant

The DAG scheduler does not alter the existing artifact promotion invariant:

```text
main
  -> Deploy STG
  -> deploy bundle
  -> run declared STG smoke DAG with bounded concurrency
  -> retain wheel + digest + manifest + smoke evidence
  -> approved Deploy PRD
  -> verify same Git SHA and wheel digest
  -> deploy exact approved staging wheel
  -> run the same declared PRD smoke DAG
  -> retain production evidence
```

Full runtime acceptance and broader regression remain separate evidence concerns and must not be inferred solely from a green deployment smoke workflow.
