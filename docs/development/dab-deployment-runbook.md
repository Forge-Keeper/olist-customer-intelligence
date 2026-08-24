# DAB Deployment Runbook

## Purpose

This runbook records the operational path proven by the first Olist Declarative Automation Bundle vertical slice. It is intended to make the workflow reproducible without relying on manual Databricks Job configuration.

The first proven resource is the IBGE municipality GDP ingestion job.

## Mental model

```text
Python source
  -> wheel artifact
  -> databricks.yml + resources/*.yml
  -> target resolution (dev/stg/prd)
  -> bundle validate
  -> bundle deploy
  -> bundle summary
  -> bundle run
```

Application/domain code does not infer the environment. Bundle targets resolve environment-specific catalog names and inject fully qualified resources through job parameters.

## Prerequisites

- Databricks CLI installed.
- A valid CLI authentication profile for the target workspace.
- Serverless Jobs enabled for the workspace used by the pilot.
- Unity Catalog catalogs/schemas and permissions required by the target job.
- `uv` installed for wheel builds.

Check available Databricks profiles:

```powershell
databricks auth profiles
```

Verify the selected profile before working with a bundle:

```powershell
databricks current-user me --profile olist-ci-main
```

Do not type placeholder notation such as `<profile>` literally in PowerShell; `<` and `>` are shell syntax.

## 1. Validate bundle targets

Validation resolves the local bundle configuration and consults the Databricks workspace. It therefore requires working authentication.

```powershell
databricks bundle validate -t dev --profile olist-ci-main
databricks bundle validate -t stg --profile olist-ci-main
databricks bundle validate -t prd --profile olist-ci-main
```

Expected result:

```text
Validation OK!
```

Production-mode targets must declare a deterministic `workspace.root_path`. The current bundle uses the authenticated workspace user in the path so each target has a stable deployment location.

## 2. Deploy to dev

A deploy builds the declared artifact, uploads bundle files and creates or updates Databricks resources. It does not execute the job.

```powershell
databricks bundle deploy -t dev --profile olist-ci-main
```

Expected high-level output:

```text
Building default...
Uploading dist/<wheel>.whl...
Uploading bundle files...
Deploying resources...
Updating deployment state...
Deployment complete!
```

The wheel version is derived from Git through `setuptools-scm`, so a development artifact is traceable to source history rather than every commit producing the same `0.1.0` filename.

## 3. Inspect deployed resources

```powershell
databricks bundle summary -t dev --profile olist-ci-main
```

The resource key used by bundle commands is not necessarily the same as the visual Job name.

For the pilot:

```text
resource key: ibge_municipality_gdp
visual name:  [dev <user>] olist_ibge_municipality_gdp
```

Development mode adds a user-specific prefix automatically.

## 4. Execute the pilot job

```powershell
databricks bundle run -t dev ibge_municipality_gdp --profile olist-ci-main
```

The CLI prints the Databricks run URL and waits for completion by default.

A successful run proves the complete path from Git-managed configuration through wheel installation and Databricks serverless execution.

## Serverless wheel dependency rule

For serverless Jobs, do not configure a task-level `libraries:` section. The task points to an `environment_key`, and wheel dependencies belong to the corresponding serverless environment.

Conceptual shape:

```yaml
tasks:
  - task_key: ingest_gdp
    environment_key: default
    python_wheel_task:
      ...

environments:
  - environment_key: default
    spec:
      environment_version: "4"
      dependencies:
        - ../dist/*.whl
```

Classic/job-cluster tasks and serverless tasks have different dependency configuration boundaries.

## Wheel development workflow

The Python distribution exposes the GDP job as a package entry point. To prove the artifact independently of the repository source tree:

```powershell
uv build --wheel
uv venv .venv-wheel-test --python 3.12
uv pip install --python .venv-wheel-test\Scripts\python.exe "pyspark>=4.2.0" dist\*.whl
.venv-wheel-test\Scripts\olist-ibge-gdp.exe --help
```

Expected CLI arguments include:

```text
--target-table
--periods
```

Use the executable inside the test virtual environment explicitly. Relying only on shell activation can accidentally resolve a globally installed executable on Windows.

PySpark is a development/test dependency rather than a normal wheel runtime dependency because Databricks supplies Spark/PySpark in the execution environment.

## Proven troubleshooting cases

### Invalid access token

Symptom:

```text
403 Invalid access token
```

Action:

1. run `databricks auth profiles`;
2. select a profile marked valid for the intended host;
3. confirm with `databricks current-user me --profile <name>`;
4. rerun bundle validation with that profile.

### Production target root path error

Symptom:

```text
target with 'mode: production' must set 'workspace.root_path'
```

Action: declare a stable production-mode root path in the target configuration.

### Serverless libraries field error

Symptom:

```text
Libraries field is not supported for serverless task
```

Action: remove task-level `libraries:` and put the wheel in `environments[].spec.dependencies`.

### Source file imports work locally but fail in Databricks

Do not solve production packaging by adding repository-specific `sys.path` bootstrap code to jobs. Build/install the wheel so `olist_data_platform` is a real installed package.

## Promotion rule

The target promotion path is:

```text
dev -> stg -> prd
```

The intended production model is **build once, promote the same approved commit/artifact**. Do not change source code between staging acceptance and production deployment.

The first vertical slice has proven `dev`. Shared `stg` and protected `prd` promotion remain gated by CI/CD authentication and deployment identities defined in the Technical Design.

## CI/CD authentication

The preferred production architecture is GitHub OIDC / Workload Identity Federation with Databricks service principals, avoiding static long-lived credentials.

Databricks Free Edition does not expose the account-level federation policy administration required for that setup. For this portfolio workspace, CI therefore uses a documented laboratory fallback: OAuth machine-to-machine authentication with the dedicated `olist-ci` service principal.

GitHub Environment `ci` stores:

```text
Environment variables:
  DATABRICKS_HOST
  DATABRICKS_CLIENT_ID

Environment secret:
  DATABRICKS_CLIENT_SECRET
```

The workflow sets:

```text
DATABRICKS_AUTH_TYPE=oauth-m2m
```

The client secret must never be committed to the repository or written into bundle configuration.

This fallback is a workspace limitation, not the target enterprise architecture. In a full Databricks account, replace it with OIDC federation and short-lived GitHub-issued credentials.

## CI/CD boundary

Repository CI proves code quality, tests, wheel build, wheel installation, the packaged GDP entry point, Databricks service-principal authentication and authenticated Bundle validation for `dev`, `stg` and `prd`.

The validation workflow is intentionally non-deploying: pull-request CI may inspect workspace-backed bundle configuration but must not create or modify Databricks resources. Deployment remains a separate promotion operation.
