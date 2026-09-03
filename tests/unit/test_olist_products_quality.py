from olist_data_platform.domains.bronze.olist.products_quality import (
    OLIST_PRODUCTS_QUALITY_CONTRACT,
)
from olist_data_platform.platform.quality import (
    NonEmptyRule,
    NotNullRule,
    ObservedCountRule,
    PredicateRule,
    QualitySeverity,
    UniqueRule,
)


def test_products_quality_contract_should_match_discovery_evidence():
    contract = OLIST_PRODUCTS_QUALITY_CONTRACT

    assert contract.dataset == "olist_products"
    assert contract.layer == "bronze"
    assert [rule.rule_id for rule in contract.rules] == [
        "PRODUCTS-DQ01",
        "PRODUCTS-DQ02",
        "PRODUCTS-DQ03",
        "PRODUCTS-DQ04",
        "PRODUCTS-DQ05",
        "PRODUCTS-DQ06",
        "PRODUCTS-DQ07",
    ]
    assert isinstance(contract.rules[0], NonEmptyRule)
    assert isinstance(contract.rules[1], NotNullRule)
    assert contract.rules[1].columns == ("product_id",)
    assert isinstance(contract.rules[2], UniqueRule)
    assert contract.rules[2].columns == ("product_id",)
    assert isinstance(contract.rules[3], PredicateRule)
    assert all(
        rule.severity is QualitySeverity.ERROR for rule in contract.rules[:4]
    )
    assert all(
        isinstance(rule, ObservedCountRule)
        and rule.severity is QualitySeverity.INFO
        for rule in contract.rules[4:]
    )
    zero_weight_rule = contract.rules[6]
    assert isinstance(zero_weight_rule, ObservedCountRule)
    assert "try_cast(product_weight_g AS BIGINT)" in zero_weight_rule.expression
