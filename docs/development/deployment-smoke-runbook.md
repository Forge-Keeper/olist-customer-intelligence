# Deployment Smoke Runbook

## Purpose

Deployment smoke tests are the post-deploy gate for production DAB workloads. They prove that every declared production job can execute its minimum representative path in STG before the same approved artifact is eligible for PRD.

They are deliberately smaller than a full regression suite.

## Source of truth

`deployment/smoke-jobs.yml` is the declarative smoke manifest.

Every job declared in `resources/*.job.yml` must have exactly one smoke contract in the manifest. CI runs:

```bash
python scripts/run_deployment_smokes.py --validate-only
```

and fails when a DAB job has no smoke contract or when the manifest references a job that no longer exists.

## Current smoke contracts

| DAB job | Runtime arguments |
| --- | --- |
| `ibge_municipality_gdp` | `--periods 2018` |
| `ibge_municipality_business_activity` | `--periods 2018` |

A single representative year is intentional. Deployment smoke verifies the operational path without turning promotion into a complete historical reload/regression.

## Runtime parameter semantics

Bundle variables such as `gdp_periods` and `cempre_periods` are resolved when the bundle is deployed. Setting `BUNDLE_VAR_*` only when calling an already-deployed job does not retroactively change the task parameters stored in that job.

For deployment smoke, bounded parameters are therefore passed as Python wheel task arguments at run time. The runner builds commands equivalent to:

```bash
databricks bundle run -t stg ibge_municipality_gdp -- --periods 2018
databricks bundle run -t stg ibge_municipality_business_activity -- --periods 2018
```

The normal deployed job configuration remains unchanged; only the smoke execution is bounded.

## Execution

STG executes the full manifest after `databricks bundle deploy -t stg`:

```bash
python scripts/run_deployment_smokes.py --target stg
```

PRD executes the same manifest after deploying the exact wheel retained by the approved STG run:

```bash
python scripts/run_deployment_smokes.py --target prd
```

The runner executes jobs sequentially and fail-fast.

## Evidence

Successful smoke results are written to:

```text
dist/deployment-smoke-results.txt
```

STG retains that file with the promoted wheel, SHA-256 and promotion manifest. PRD requires the staging smoke evidence to be present, preserves it as `staging-smoke-results.txt`, runs the production smoke contract, and retains both staging and production smoke evidence with the production promotion manifest.

GitHub Actions logs remain the detailed execution evidence, including the Databricks run output and run URLs.

## Adding or changing a DAB job

When adding a production job under `resources/*.job.yml`:

1. define the smallest safe representative execution for deployment smoke;
2. add the job key and bounded runtime arguments to `deployment/smoke-jobs.yml`;
3. use task arguments when the normal workload would be unnecessarily expensive;
4. run `python scripts/run_deployment_smokes.py --validate-only` locally or rely on CI;
5. update this runbook when the smoke semantics materially change.

A new job without a manifest entry must fail CI rather than silently bypass the deployment gate.

## Unsafe or expensive jobs

Do not encode a destructive or expensive full production workload as a deployment smoke merely to satisfy coverage. The manifest contract must remain explicit, but the safe bounded execution strategy should be designed for that job before promotion is allowed.

If a future job cannot be made safe enough for direct execution, treat that as a design decision and evolve the smoke contract deliberately rather than adding an implicit skip.

## Promotion invariant

The smoke change does not alter the existing artifact promotion invariant:

```text
main
  -> Deploy STG
  -> deploy bundle
  -> run declared STG smokes
  -> retain wheel + digest + manifest + smoke evidence
  -> approved Deploy PRD
  -> verify same Git SHA and wheel digest
  -> deploy exact approved staging wheel
  -> run the same declared PRD smokes
  -> retain production evidence
```

Full end-to-end regression of every pipeline remains outside the deployment smoke gate.
