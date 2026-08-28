from olist_data_platform.domains.bronze.olist import (
    marketing_qualified_leads_bronze_config as mql_config,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_mql_contract_should_match_discovered_source_shape():
    config = mql_config.OLIST_MARKETING_QUALIFIED_LEADS_BRONZE_CONFIG
    columns = {column.name: column for column in config.columns}

    assert set(columns) == {
        "mql_id",
        "first_contact_date",
        "landing_page_id",
        "origin",
        "source_file",
    }
    assert columns["mql_id"].nullable is False
    assert columns["first_contact_date"].nullable is False
    assert columns["landing_page_id"].nullable is False
    assert columns["origin"].nullable is True
    assert config.key_columns == ("mql_id",)
    assert config.write_strategy is WriteStrategy.FULL_REPLACE
    assert config.layout.partition_columns == ()
    assert config.layout.clustering_columns == ()
