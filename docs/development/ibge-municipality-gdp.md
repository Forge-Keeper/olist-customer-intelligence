# IBGE Municipality GDP Bronze Feature

## Status

Implementation complete on `feature/ibge-municipality-gdp`; local and Databricks validation pending execution.

Development gates:

- Discovery — complete
- Requirements — complete
- Technical Design — complete
- Impact Analysis — complete
- Approved Plan — complete (`/autopilot`)
- Implementation — complete
- Validation — pending
- Done — pending PR/merge

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

- `MUNICIPALITY_GDP` in `datasets.py` now carries the approved six-variable production contract instead of `variables=("all",)`.

Validation assets:

- GDP extractor unit tests
- ingestion-service request-partitioning unit test
- Spark Bronze writer integration coverage
- Databricks `ibge_gdp_bronze_validation.py`

No changes are required to the generic SIDRA transport/parser or shared Bronze writer.

## Validation plan

Local gate:

```bash
uv run pytest tests/unit/test_ibge_municipality_gdp_extractor.py -q
uv run pytest tests/unit/test_ibge_municipality_gdp_ingestion_service.py -q
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run ruff check .
uv run ty check
```

Databricks gate:

Run `notebooks/exploration/ibge_gdp_bronze_validation.py` with `RESET_GDP_TABLE = False` for a normal run. Use the reset flag only for an explicit development contract migration.

The notebook intentionally does not hard-code GDP municipality cardinality before observing the real 2016-2018 source output. It validates selected years/variables, key uniqueness, `dt_base`, payload preservation, municipality-code compatibility, clustering and same-scope idempotency, while printing year/variable row counts for inspection.

## Out of scope

- SIDRA participation/share variables
- Silver numeric typing
- special-marker interpretation/quarantine rules
- inflation adjustment / real GDP calculations
- GDP per capita
- Gold KPI/data-product design
- periods outside 2016-2018
