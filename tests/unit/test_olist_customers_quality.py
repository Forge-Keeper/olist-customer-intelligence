from olist_data_platform.domains.bronze.olist.customers_quality import (
    OLIST_CUSTOMERS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    NonEmptyRule,
    NotNullRule,
    PredicateRule,
    QualitySeverity,
    UniqueRule,
)


def test_customers_quality_contract_should_protect_discovered_technical_invariants():
    contract = OLIST_CUSTOMERS_QUALITY_CONTRACT

    assert contract.dataset == "olist_customers"
    assert contract.layer == "bronze"
    assert [rule.rule_id for rule in contract.rules] == [
        "CUSTOMERS-DQ01",
        "CUSTOMERS-DQ02",
        "CUSTOMERS-DQ03",
        "CUSTOMERS-DQ04",
        "CUSTOMERS-DQ05",
    ]
    assert all(rule.severity is QualitySeverity.ERROR for rule in contract.rules)
    assert isinstance(contract.rules[0], NonEmptyRule)
    assert isinstance(contract.rules[1], NotNullRule)
    assert contract.rules[1].columns == ("customer_id",)
    assert isinstance(contract.rules[2], UniqueRule)
    assert contract.rules[2].columns == ("customer_id",)
    assert isinstance(contract.rules[3], NotNullRule)
    assert contract.rules[3].columns == (
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    )
    assert isinstance(contract.rules[4], PredicateRule)
    assert "^[0-9]{5}$" in contract.rules[4].expression
