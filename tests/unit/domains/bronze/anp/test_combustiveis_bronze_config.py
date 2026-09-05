from pyspark.sql.types import DecimalType

from olist_data_platform.domains.bronze.anp import ANP_COMBUSTIVEIS_BRONZE_CONFIG
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_anp_bronze_contract_preserves_postgres_numeric_precision() -> None:
    schema = ANP_COMBUSTIVEIS_BRONZE_CONFIG.to_struct_type()

    valor_venda = schema["valor_venda"]
    valor_compra = schema["valor_compra"]

    assert isinstance(valor_venda.dataType, DecimalType)
    assert valor_venda.dataType.precision == 38
    assert valor_venda.dataType.scale == 18
    assert valor_venda.nullable is False

    assert isinstance(valor_compra.dataType, DecimalType)
    assert valor_compra.dataType.precision == 38
    assert valor_compra.dataType.scale == 18
    assert valor_compra.nullable is True


def test_anp_bronze_contract_uses_explicit_reprocessing_scope() -> None:
    contract = ANP_COMBUSTIVEIS_BRONZE_CONFIG

    assert contract.key_columns == ("id",)
    assert contract.clustering_columns == ("dt_base",)
    assert contract.write_strategy is WriteStrategy.REPLACE_WHERE
    assert contract.metadata.tags["domain"] == "anp"
    assert contract.metadata.tags["source_system"] == "azure_postgresql"
