from olist_data_platform.domains.bronze.olist.closed_deals_bronze_config import (
    OLIST_CLOSED_DEALS_BRONZE_CONFIG,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy


def test_closed_deals_config_should_define_snapshot_contract():
    config = OLIST_CLOSED_DEALS_BRONZE_CONFIG

    assert config.primary_key_columns == ("mql_id",)
    assert config.write_strategy is WriteStrategy.FULL_REPLACE
    assert config.partition_columns == ()
    assert config.clustering_columns == ()
    assert "seller_id" in config.required_columns
    assert "won_date" in config.required_columns
    assert "source_file" in config.required_columns
