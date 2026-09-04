from olist_data_platform.domains.bronze.olist import (
    product_category_name_translation_quality as translation_quality,
)
from olist_data_platform.platform.quality import (
    NonEmptyRule,
    NotNullRule,
    PredicateRule,
    QualitySeverity,
    UniqueRule,
)


def test_category_translation_quality_contract_should_match_discovery_evidence():
    contract = (
        translation_quality.OLIST_PRODUCT_CATEGORY_NAME_TRANSLATION_QUALITY_CONTRACT
    )

    assert contract.dataset == "olist_product_category_name_translation"
    assert contract.layer == "bronze"
    assert [rule.rule_id for rule in contract.rules] == [
        "CATEGORY-TRANSLATION-DQ01",
        "CATEGORY-TRANSLATION-DQ02",
        "CATEGORY-TRANSLATION-DQ03",
        "CATEGORY-TRANSLATION-DQ04",
        "CATEGORY-TRANSLATION-DQ05",
    ]
    assert isinstance(contract.rules[0], NonEmptyRule)
    assert isinstance(contract.rules[1], NotNullRule)
    assert contract.rules[1].columns == ("product_category_name",)
    assert isinstance(contract.rules[2], UniqueRule)
    assert contract.rules[2].columns == ("product_category_name",)
    assert isinstance(contract.rules[3], NotNullRule)
    assert contract.rules[3].columns == ("product_category_name_english",)
    assert isinstance(contract.rules[4], PredicateRule)
    assert all(rule.severity is QualitySeverity.ERROR for rule in contract.rules)
