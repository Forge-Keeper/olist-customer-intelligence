# IBGE CEMPRE — Municipal Business Activity

## Scope

This feature ingests municipal indicators from the IBGE Cadastro Central de Empresas (CEMPRE) through SIDRA table 1685 for the Olist historical enrichment window: 2016, 2017 and 2018.

The Bronze layer preserves the source payload and does not harmonize, derive or reinterpret business indicators. Analytical integration with population, GDP/VAB and Olist belongs to Silver or later layers.

## Source contract

- Source system: IBGE SIDRA
- Table: 1685
- Territorial level: N6 — Município
- Periods: 2016, 2017, 2018
- Variables: 367, 706, 707, 708, 5944, 662, 1606, 10143
- Logical grain: municipality code + reference year + variable code

The selected variables represent active companies/organizations, local units, total occupied personnel, salaried personnel, average salaried personnel, salaries and other remuneration, average monthly salary and average monthly salary in reais.

## Ingestion flow

`SidraDataset -> SidraQuery -> SidraClient -> SidraParser -> MunicipalityBusinessActivityExtractor -> MunicipalityBusinessActivityIngestionService -> BronzeMunicipalityBusinessActivityWriter -> BronzeWriter -> DeltaTableLifecycle`

The service queries one year/variable slice at a time. Empty requested slices fail explicitly. Source special values such as suppression or unavailable markers remain inside the preserved payload and are not converted to zero.

## Bronze contract

Target table: `${catalog}.bronze.ibge_municipality_business_activity`

Persisted source columns:

- `municipality_code`
- `reference_year`
- `variable_code`
- `dt_base`
- `payload` as Delta `VARIANT`
- `request_id`
- managed `ingestion_timestamp`

The logical key is `(municipality_code, reference_year, variable_code)`. The write strategy is `MERGE`, and the table uses liquid clustering by `dt_base`.

## Execution boundary

The job receives the target table and comma-separated periods from DAB. Environment resolution is performed at deployment/execution time through `${var.catalog}` and never inside the domain implementation.

Default periods are controlled by `cempre_periods=2016,2017,2018`.

## Out of scope

- CEMPRE data after 2018
- SIDRA table 9509
- CNAE breakdowns
- Silver harmonization
- derived business-density or employment indicators
- generic SIDRA service/writer abstractions

These concerns should only be introduced when a later feature demonstrates concrete need.
