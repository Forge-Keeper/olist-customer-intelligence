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

## Environment parameterization rule

Environment-specific runtime values must be supplied at a deployment or execution boundary rather than embedded in application code.

Current examples:

- DAB resolves `${var.catalog}` from `dev`, `stg` or `prd` target configuration;
- staging/production `run_as` uses the required `run_as_service_principal` bundle variable;
- GitHub Actions maps its environment-scoped `DATABRICKS_CLIENT_ID` to `BUNDLE_VAR_run_as_service_principal`;
- manual IBGE validation notebooks require an explicit `catalog` widget;
- Olist CSV ingestion jobs require explicit `--source-path` and `--target-table` arguments.

The source-of-truth audit and guardrails are documented in `environment-hardcode-audit.md`.

## Prerequisites

- Databricks CLI installed.
- A valid CLI authentication profile for the target workspace.
- Serverless Jobs enabled for the workspace used by the pilot.
- Unity Catalog catalogs/schemas and permissions required by the target job.
- `uv` installed for wheel builds.
- A service-principal application ID available when validating/deploying `stg` or `prd` configuration.

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

The staging/production run identity is intentionally not committed to `databricks.yml`. For a local shell, inject it before bundle commands:

```powershell
$env:BUNDLE_VAR_run_as_service_principal = "<service-principal-application-id>"
```

Then validate:

```powershell
databricks bundle validate -t dev --profile olist-ci-main
databricks bundle validate -t stg --profile olist-ci-main
databricks bundle validate -t prd --profile olist-ci-main
```

Expected result:

```text
Validation OK!
```

Production-mode targets must declare a deterministic `workspace.root_path`. In the Free Edition laboratory, `stg` and `prd` use the authenticated deployment identity's workspace user root because shared workspace-folder ACL administration is limited. In a full account, prefer protected shared deployment roots with explicit ACLs and separate deployment identities.

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

The wheel version is derived from Git through `setuptools-scm`, so a development artifact is traceable to source history rather than every commit producing the same filename.

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

## Manual validation notebooks

The exploratory validation notebooks no longer point at production implicitly. Before running either notebook, set its `catalog` widget to the catalog you intend to validate.

Affected notebooks:

```text
notebooks/exploration/ibge_bronze_validation.py
notebooks/exploration/ibge_gdp_bronze_validation.py
```

The widget is required and has no environment default. The notebook composes fully qualified Bronze tables from the explicit catalog plus stable schema/table names.

## Olist CSV job arguments

Olist snapshot jobs no longer default to a production Volume path. Callers must provide source and target explicitly:

```text
--source-path <resolved source file path>
--target-table <catalog.schema.table>
```

This keeps source-location ownership at the deployment/execution boundary and avoids silently reading production when a job is invoked from another environment.

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

### Missing bundle run identity

Symptom: bundle validation reports that `run_as_service_principal` has no value.

Action: supply `BUNDLE_VAR_run_as_service_principal` in the shell or pass the variable explicitly with `--var`. CI/CD injects this value from the GitHub Environment rather than committing an application ID.

### Production target root path error

Symptom:

```text
target with 'mode: production' must set 'workspace.root_path'
```

Action: declare a stable production-mode root path in the target configuration.

### Shared bundle root permission failure

Symptom: deployment authentication and validation succeed, but deployment fails while acquiring the bundle lock below a shared workspace path.

Action in Free Edition: use the authenticated deployment identity's workspace user root for bundle state. In a full account, provision the intended shared root and grant only the required deployment ACLs.

### Serverless libraries field error

Symptom:

```text
Libraries field is not supported for serverless task
```

Action: remove task-level `libraries:` and put the wheel in `environments[].spec.dependencies`.

### Unity Catalog permission failure

Symptom:

```text
[INSUFFICIENT_PERMISSIONS] ... does not have USE CATALOG
```

Grant the workload service principal only the required privileges. For the GDP Bronze pilot the intended shape is:

```text
catalog <env>: USE CATALOG
schema <env>.bronze: USE SCHEMA, CREATE TABLE, MODIFY, SELECT
```

Avoid `ALL PRIVILEGES` when narrower grants are sufficient.

### Source file imports work locally but fail in Databricks

Do not solve production packaging by adding repository-specific `sys.path` bootstrap code to jobs. Build/install the wheel so `olist_data_platform` is a real installed package.

## Promotion rule

The proven promotion path is:

```text
feature / PR
    -> CI quality + authenticated bundle validation
    -> merge to main
    -> automatic Deploy STG
    -> staging GDP smoke
    -> retained staging wheel + manifest + SHA-256
    -> manual Deploy PRD request
    -> protected GitHub Environment approval
    -> verify staging commit + wheel digest
    -> deploy the exact approved staging wheel
    -> production GDP smoke
    -> retained production evidence
```

The invariant is **build once, promote the same approved artifact**. Production must not silently rebuild a different wheel after staging acceptance.

A production dispatch takes the successful `Deploy STG` GitHub Actions run ID. The workflow downloads the retained staging artifact from that exact run and fails closed if:

- the artifact is missing;
- its manifest commit differs from current `main`;
- its wheel is missing;
- its SHA-256 does not match the staging manifest.

This also means that any new commit merged to `main` requires a new successful staging promotion before production can be deployed.

## CI/CD authentication

The preferred production architecture is GitHub OIDC / Workload Identity Federation with Databricks service principals, avoiding static long-lived credentials.

Databricks Free Edition does not expose the account-level federation policy administration required for that setup. For this portfolio workspace, CI/CD therefore uses a documented laboratory fallback: OAuth machine-to-machine authentication with the dedicated `olist-ci` service principal.

GitHub Environments `ci`, `olist-stg` and `olist-prd` provide environment-scoped configuration. They store:

```text
Environment variables:
  DATABRICKS_HOST
  DATABRICKS_CLIENT_ID

Environment secret:
  DATABRICKS_CLIENT_SECRET
```

The workflows also expose the environment-scoped client ID to DAB as:

```text
BUNDLE_VAR_run_as_service_principal = DATABRICKS_CLIENT_ID
```

This keeps the concrete application ID outside repository configuration while preserving the Free Edition single-service-principal fallback.

The client secret must never be committed to the repository or written into bundle configuration.

`olist-prd` is the protected human approval boundary for production. In a full Databricks account, replace the Free Edition authentication fallback with OIDC federation and use separate least-privilege service principals for staging and production.

## CI/CD boundary

Repository CI proves code quality, tests, wheel build, wheel installation, the packaged GDP entry point, Databricks service-principal authentication and authenticated Bundle validation for `dev`, `stg` and `prd`.

Pull-request CI is intentionally non-deploying. Deployment is separate:

- `main -> stg` is automatic and must pass its workload smoke before producing a promotion artifact;
- `stg -> prd` is manually dispatched and protected by the `olist-prd` GitHub Environment;
- production consumes the retained staging wheel rather than rebuilding it.

## First end-to-end proof

The first complete promotion cycle was proven on 2026-08-24 for the IBGE municipality GDP pilot.

Evidence:

```text
main commit:        ad0f76729d8f61472df743ba0a16a71e128104ec
Deploy STG run:     32790895866
Deploy STG result:  success
Deploy PRD run:     32791428715 (successful retry)
Deploy PRD result:  success
```

The successful production run proved, in one controlled chain, staging artifact validation, OAuth M2M service-principal authentication, `bundle validate -t prd`, deployment of the approved staging wheel, the production GDP smoke and retention of deployment evidence.
