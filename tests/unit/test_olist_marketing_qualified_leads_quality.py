from olist_data_platform.domains.bronze.olist.marketing_qualified_leads_quality import (
    OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    NonEmptyRule,
    NotNullRule,
    PredicateRule,
    QualitySeverity,
    UniqueRule,
)


def test_mql_quality_contract_should_protect_discovered_technical_invariants():
    contract = OLIST_MARKETING_QUALIFIED_LEADS_QUALITY_CONTRACT

    assert contract.dataset == "olist_marketing_qualified_leads"
    assert contract.layer == "bronze"
    assert [rule.rule_id for rule in contract.rules] == [
        "MQL-DQ01",
        "MQL-DQ02",
        "MQL-DQ03",
        "MQL-DQ04",
        "MQL-DQ05",
    ]
    assert all(rule.severity is QualitySeverity.ERROR for rule in contract.rules)
    assert isinstance(contract.rules[0], NonEmptyRule)
    assert isinstance(contract.rules[1], NotNullRule)
    assert contract.rules[1].columns == ("mql_id",)
    assert isinstance(contract.rules[2], UniqueRule)
    assert contract.rules[2].columns == ("mql_id",)
    assert isinstance(contract.rules[3], NotNullRule)
    assert contract.rules[3].columns == ("first_contact_date", "landing_page_id")
    assert isinstance(contract.rules[4], PredicateRule)
    assert "try_to_timestamp(first_contact_date" in contract.rules[4].expression
