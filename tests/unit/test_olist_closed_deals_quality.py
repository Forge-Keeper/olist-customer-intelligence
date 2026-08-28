from olist_data_platform.domains.bronze.olist.closed_deals_quality import (
    OLIST_CLOSED_DEALS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    NonEmptyRule,
    NotNullRule,
    QualitySeverity,
    UniqueRule,
)


def test_closed_deals_quality_contract_should_protect_technical_invariants():
    contract = OLIST_CLOSED_DEALS_QUALITY_CONTRACT

    assert contract.dataset == "olist_closed_deals"
    assert contract.layer == "bronze"
    assert [rule.rule_id for rule in contract.rules] == [
        "CLOSED-DEALS-DQ01",
        "CLOSED-DEALS-DQ02",
        "CLOSED-DEALS-DQ03",
    ]
    assert all(rule.severity is QualitySeverity.ERROR for rule in contract.rules)
    assert isinstance(contract.rules[0], NonEmptyRule)
    assert isinstance(contract.rules[1], NotNullRule)
    assert contract.rules[1].columns == ("mql_id",)
    assert isinstance(contract.rules[2], UniqueRule)
    assert contract.rules[2].columns == ("mql_id",)
