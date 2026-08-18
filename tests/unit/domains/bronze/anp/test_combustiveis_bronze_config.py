from olist_data_platform.domains.bronze.anp import ANP_COMBUSTIVEIS_BRONZE_CONFIG
from olist_data_platform.platform.delta.bronze.config import WriteStrategy


def test_anp_bronze_config_uses_source_id_as_primary_key() -> None:
    assert ANP_COMBUSTIVEIS_BRONZE_CONFIG.primary_key_columns == ("id",)


def test_anp_bronze_config_requires_expected_columns() -> None:
    required_columns = set(ANP_COMBUSTIVEIS_BRONZE_CONFIG.required_columns)

    assert {
        "id",
        "cnpj_revenda",
        "produto",
        "data_coleta",
        "valor_venda",
        "dt_base",
        "source_system",
    } <= required_columns


def test_anp_bronze_config_clusters_by_dt_base() -> None:
    assert ANP_COMBUSTIVEIS_BRONZE_CONFIG.clustering_columns == ("dt_base",)
    assert ANP_COMBUSTIVEIS_BRONZE_CONFIG.partition_columns == ()


def test_anp_bronze_config_uses_replace_where() -> None:
    assert (
        ANP_COMBUSTIVEIS_BRONZE_CONFIG.write_strategy
        is WriteStrategy.REPLACE_WHERE
    )
