from datetime import date

from olist_data_platform.domains.bronze.ibge.bronze_municipality_gdp_writer import (
    BronzeMunicipalityGdpWriter,
)
from olist_data_platform.domains.bronze.ibge.municipality_gdp_bronze_config import (
    IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.ibge.municipality_gdp_quality import (
    build_municipality_gdp_quality_contract,
)
from olist_data_platform.domains.ingestion.ibge.datasets import MUNICIPALITY_GDP
from olist_data_platform.platform.quality import DataQualityRunner, QualityStatus


def _record(variable: str, *, municipality: str = "3550308", value: str = "1000"):
    return {
        "municipality_code": municipality,
        "reference_year": "2018",
        "variable_code": variable,
        "dt_base": date(2018, 1, 1),
        "payload": {"Valor": value},
    }


def test_gdp_quality_contract_passes_complete_scope_and_observes_special_values(spark):
    writer = BronzeMunicipalityGdpWriter(spark, "bronze.test_gdp")
    records = [
        _record(variable, value="..." if variable == "6575" else "1000")
        for variable in MUNICIPALITY_GDP.variables
    ]
    dataframe = writer._build_dataframe(records=records, request_id="run-pass")

    checked = DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=build_municipality_gdp_quality_contract(("2018",)),
        run_id="run-pass",
        evaluation_scope='{"periods":["2018"]}',
        validated_key_columns=IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG.key_columns,
    )

    assert checked.report.row_count == len(MUNICIPALITY_GDP.variables)
    assert checked.report.has_blocking_failures is False
    assert all(result.status is QualityStatus.PASS for result in checked.report.results)
    special = next(result for result in checked.report.results if result.rule_id == "GDP-DQ08")
    assert '"observed_row_count":1' in special.observed_value


def test_gdp_quality_contract_rejects_duplicate_and_missing_combination(spark):
    writer = BronzeMunicipalityGdpWriter(spark, "bronze.test_gdp")
    variables = MUNICIPALITY_GDP.variables[:-1]
    records = [_record(variable) for variable in variables]
    records.append(_record(variables[0]))
    dataframe = writer._build_dataframe(records=records, request_id="run-fail")

    checked = DataQualityRunner().evaluate(
        dataframe=dataframe,
        contract=build_municipality_gdp_quality_contract(("2018",)),
        run_id="run-fail",
        evaluation_scope='{"periods":["2018"]}',
        validated_key_columns=IBGE_MUNICIPALITY_GDP_BRONZE_CONFIG.key_columns,
    )

    failed = {
        result.rule_id
        for result in checked.report.results
        if result.status is QualityStatus.FAIL
    }
    assert {"GDP-DQ03", "GDP-DQ07"}.issubset(failed)
    assert checked.report.has_blocking_failures is True
