import pytest

from olist_data_platform.platform.delta import ColumnContract, DatasetContract
from olist_data_platform.platform.delta.bronze import WriteStrategy

_COLUMN = ColumnContract(
    name="payload",
    data_type="string",
    nullable=False,
    description="Test payload.",
)


def test_full_replace_contract_can_be_keyless() -> None:
    contract = DatasetContract(
        columns=(_COLUMN,),
        key_columns=(),
        write_strategy=WriteStrategy.FULL_REPLACE,
    )

    assert contract.key_columns == ()


@pytest.mark.parametrize(
    "strategy",
    (WriteStrategy.MERGE, WriteStrategy.REPLACE_WHERE),
)
def test_non_full_replace_contract_still_requires_key(strategy: WriteStrategy) -> None:
    with pytest.raises(
        ValueError,
        match="key_columns can be empty only for FULL_REPLACE datasets",
    ):
        DatasetContract(
            columns=(_COLUMN,),
            key_columns=(),
            write_strategy=strategy,
        )
