# IBGE Municipality GDP Bronze Feature

## Status

**DONE.** Implementation, validation, PR review and merge are complete.

Merged into `dev` via PR #6 on 2026-08-24.

Merge commit: `cff34e52179ff532e1c9bd2567ee85325b334e1b`.

Development gates:

- Discovery — complete
- Requirements — complete
- Technical Design — complete
- Impact Analysis — complete
- Approved Plan — complete (`/autopilot`)
- Implementation — complete
- Validation — complete
- Done — complete

## Objective

Add municipality-level GDP and gross value added enrichment from IBGE SIDRA while reusing the SIDRA infrastructure delivered by the municipality population feature.

Initial processing scope is intentionally limited to 2016, 2017 and 2018 to align with the primary Olist analytical period.

## Source contract

SIDRA table: `5938`

Territorial level: `6` (municipality)

Approved variables:

| Code | Meaning |
| --- | --- |
| `37` | GDP at current prices |
| `498` | Total gross value added at current prices |
| `513` | Agriculture gross value added |
| `517` | Industry gross value added |
| `525` | Public administration, defense, education, health and social security gross value added |
| `6575` | Services gross value added excluding public administration |

Participation/share variables are outside this feature.

The SIDRA source represents `Valor` as a string and may return special markers such as `...`. Bronze therefore preserves the decoded source row in `payload VARIANT`; numeric interpretation belongs downstream.

## Bronze contract

Target logical dataset: `ibge_municipality_gdp`.

Columns:

- `municipality_code STRING`
- `reference_year STRING`
- `variable_code STRING`
- `dt_base DATE`
- `payload VARIANT`
- `request_id STRING`
- `ingestion_timestamp TIMESTAMP` added by the shared Bronze writer

Natural key:

`(municipality_code, reference_year, variable_code)`

`dt_base` is the annual technical competence date: January 1 of `reference_year`.

Write strategy: idempotent `MERGE`.

Layout: Liquid Clustering by `dt_base`.

## Request sizing and reliability

The previous population feature proved that large multi-period SIDRA requests can exceed the default read timeout. GDP has a larger variable set, so the ingestion deliberately bounds each API request to:

`1 period × 1 variable × all municipalities`

For the approved scope this produces 18 independent SIDRA calls (3 years × 6 variables), all sharing one ingestion `request_id`. Decoded rows are accumulated and written once for the logical ingestion scope.

This choice reduces retry blast radius without increasing the global HTTP timeout or creating a second transport stack.

## Reuse

Reused components:

- `SidraClient`
- `SidraQuery`
- `SidraDataset`
- `SidraParser`
- shared `BronzeWriter`
- logging and HTTP retry/backoff platform capabilities

GDP-specific responsibilities remain in GDP-specific extractor/service/writer/configuration code.

## Impact analysis

New runtime components:

- `municipality_gdp_extractor.py`
- `municipality_gdp_ingestion_service.py`
- `municipality_gdp_bronze_config.py`
- `bronze_municipality_gdp_writer.py`
- `ibge_municipality_gdp_ingestion.py`

Changed reusable configuration:

- `MUNICIPALITY_GDP` in `datasets.py` carries the approved six-variable production contract instead of `variables=("all",)`.

Validation assets:

- GDP extractor unit tests
- ingestion-service request-partitioning unit test
- Spark Bronze writer integration coverage
- Databricks `ibge_gdp_bronze_validation.py`

No changes were required to the generic SIDRA transport/parser or shared Bronze writer.

## Validation evidence

### Local

Final local gate:

- unit tests: `166 passed`
- integration tests: `6 passed`
- Ruff: passed
- `ty`: passed

### Databricks / real SIDRA + Delta

`notebooks/exploration/ibge_gdp_bronze_validation.py` completed successfully against the real SIDRA source and Delta Bronze table.

Observed total row count:

- `100260` rows

Observed matrix for every approved `reference_year × variable_code` pair:

| Year | Variable | Rows | Unique municipalities |
| --- | --- | ---: | ---: |
| 2016 | 37 | 5570 | 5570 |
| 2016 | 498 | 5570 | 5570 |
| 2016 | 513 | 5570 | 5570 |
| 2016 | 517 | 5570 | 5570 |
| 2016 | 525 | 5570 | 5570 |
| 2016 | 6575 | 5570 | 5570 |
| 2017 | 37 | 5570 | 5570 |
| 2017 | 498 | 5570 | 5570 |
| 2017 | 513 | 5570 | 5570 |
| 2017 | 517 | 5570 | 5570 |
| 2017 | 525 | 5570 | 5570 |
| 2017 | 6575 | 5570 | 5570 |
| 2018 | 37 | 5570 | 5570 |
| 2018 | 498 | 5570 | 5570 |
| 2018 | 513 | 5570 | 5570 |
| 2018 | 517 | 5570 | 5570 |
| 2018 | 525 | 5570 | 5570 |
| 2018 | 6575 | 5570 | 5570 |

Additional observed evidence:

- `special_value_rows = 0` for the approved 2016-2018 / six-variable scope;
- `clusteringColumns = ['dt_base']`;
- selected years/variables validation passed;
- natural-key uniqueness validation passed;
- `dt_base` annual-competence validation passed;
- payload preservation validation passed;
- municipality-code compatibility validation passed;
- same-scope re-execution/idempotency validation passed.

The `5570` cardinality is observed validation evidence for this SIDRA table/scope, not a permanent external-source contract. It intentionally differs from the `5571` municipality cardinality observed in the population dataset.

## Out of scope

- SIDRA participation/share variables
- Silver numeric typing
- special-marker interpretation/quarantine rules
- inflation adjustment / real GDP calculations
- GDP per capita
- Gold KPI/data-product design
- periods outside 2016-2018

## Follow-up boundary

Any extension into Silver, additional SIDRA variables, periods outside 2016–2018, inflation-adjusted measures or Gold metrics is a **new feature** and must restart the project development gates.
