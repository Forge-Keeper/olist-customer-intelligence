from olist_data_platform.domains.bronze.olist.geolocation_bronze_config import (
    OLIST_GEOLOCATION_BRONZE_CONFIG,
)
from olist_data_platform.domains.bronze.olist.geolocation_quality import (
    OLIST_GEOLOCATION_QUALITY_CONTRACT,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy
from olist_data_platform.platform.quality import QualitySeverity


def test_geolocation_contract_preserves_keyless_full_snapshot() -> None:
    config = OLIST_GEOLOCATION_BRONZE_CONFIG

    assert config.key_columns == ()
    assert config.write_strategy is WriteStrategy.FULL_REPLACE
    assert tuple(column.name for column in config.columns) == (
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
        "source_file",
    )


def test_geolocation_quality_has_no_blocking_uniqueness_rule() -> None:
    rules = OLIST_GEOLOCATION_QUALITY_CONTRACT.rules

    assert {rule.rule_id for rule in rules} == {
        "GEOLOCATION-DQ01",
        "GEOLOCATION-DQ02",
        "GEOLOCATION-DQ03",
        "GEOLOCATION-DQ04",
        "GEOLOCATION-DQ05",
    }
    assert all(
        rule.severity is QualitySeverity.ERROR
        for rule in rules[:4]
    )
    assert rules[4].severity is QualitySeverity.INFO
