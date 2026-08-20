# IBGE API ingestion

## Scope

This feature integrates IBGE as a reusable external source for Olist Customer Intelligence, beginning with municipality population and a current municipality reference snapshot. The reusable SIDRA client/query/dataset infrastructure is intended to support future justified datasets such as municipal GDP without duplicating HTTP or query composition logic.

## Architecture

```text
IBGE Localidades API
        |
        v
LocalitiesClient
        |
        v
MunicipalitiesIngestionService
        |
        v
MunicipalitiesExtractor
        |
        v
BronzeMunicipalitiesWriter
        |
        v
prd.bronze.ibge_municipalities

IBGE SIDRA API
        |
        v
SidraClient + SidraQuery + SidraDataset
        |
        v
SidraParser
        |
        v
MunicipalityPopulationExtractor
        |
        v
MunicipalityPopulationIngestionService
        |
        v
BronzeMunicipalityPopulationWriter
        |
        v
prd.bronze.ibge_municipality_population
```

Reusable HTTP transport remains in `platform/http`. IBGE-specific clients and query semantics remain in `domains/ingestion/ibge`. Generic Bronze persistence remains in `platform/delta/bronze`.

## Bronze principle

IBGE Bronze follows ADR-003: preserve the source as-is as far as practical and extract only the technical envelope required for identity, time semantics, layout, and operations.

Business typing, flattened geographic attributes, historical reconstruction, and analytical interpretation belong downstream.

## Municipality population contract

Source: SIDRA table `6579`, territorial level `6`, variable `9324`.

Default analytical periods for the initial feature are 2016, 2017, and 2018.

Bronze columns:

```text
municipality_code STRING
reference_year STRING
variable_code STRING
dt_base DATE
payload VARIANT
request_id STRING
ingestion_timestamp TIMESTAMP
```

Natural/idempotency key:

```text
(municipality_code, reference_year, variable_code)
```

`dt_base` is the annual technical competence date and is defined as January 1 of `reference_year`.

`payload` preserves the decoded SIDRA source row, including values such as `Valor`, names, unit labels, territorial labels, and future unexpected attributes. `Valor` is intentionally not converted to a numeric Bronze column.

Normal write strategy: `MERGE`.

Liquid Clustering: `dt_base`.

## Localidades contract

The Localidades endpoint is a current snapshot source. Bronze must not manufacture 2016/2017/2018 copies from the current response.

Bronze columns:

```text
municipality_code STRING
dt_base DATE
payload VARIANT
request_id STRING
ingestion_timestamp TIMESTAMP
```

Natural/idempotency key:

```text
(municipality_code, dt_base)
```

`dt_base` is the source snapshot capture date. Re-running ingestion on the same date updates the same logical snapshot through `MERGE`; ingestion on a later date intentionally creates a new snapshot.

`payload` preserves the nested Localidades municipality object. Flattening state, region, immediate/intermediate region, microregion, or mesoregion attributes belongs downstream.

Normal write strategy: `MERGE`.

Liquid Clustering: `dt_base`.

## Idempotency and reprocessing

Population is idempotent by municipality/year/variable. A repeated request for the same periods updates matching rows rather than duplicating them.

Localidades is idempotent for a municipality on the same snapshot date. Different snapshot dates represent different source snapshots.

No dedicated IBGE reprocessing API is introduced in this feature. A replay/backfill operation should be added only when a concrete operational requirement defines its scope and authoritative-empty behavior.

## Validation

Local gates:

```powershell
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run ruff check .
uv run ty check
```

IBGE integration coverage verifies that both source payloads become Spark `VARIANT` values and that unexpected fields are preserved.

Databricks validation notebook:

```text
notebooks/exploration/ibge_bronze_validation.py
```

It validates:

- current Localidades snapshot ingestion;
- population coverage for 2016-2018;
- natural-key uniqueness;
- source payload preservation in `VARIANT`;
- compatibility of historical population municipality codes with the current municipality reference;
- Liquid Clustering metadata;
- idempotent same-scope `MERGE` behavior.

Because Localidades is a current snapshot, the notebook intentionally does not assert a fabricated historical `dt_base` join between Localidades and population.

## Databricks execution note

When running the repository notebook directly in Databricks Repos, the validation notebook bootstraps the repository `src/` path before importing `olist_data_platform`. This is a notebook execution concern, not a package-level `sys.path` workaround.

## Future reuse: municipal GDP

`MUNICIPALITY_GDP` is already represented as a `SidraDataset` configuration, but GDP ingestion is not implemented by this feature.

Future GDP work should reuse:

- `ApiClient` HTTP behavior;
- `SidraClient`;
- `SidraQuery`;
- `SidraDataset`;
- `SidraParser`;
- generic Bronze persistence.

GDP-specific variables, natural grain, `dt_base` semantics, validation, and downstream interpretation must be discovered and approved in that feature rather than inferred from the population contract.
