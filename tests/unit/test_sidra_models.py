import pytest

from olist_data_platform.domains.ingestion.ibge.datasets import (
    MUNICIPALITY_GDP,
    MUNICIPALITY_POPULATION,
)
from olist_data_platform.domains.ingestion.ibge.sidra_dataset import SidraDataset
from olist_data_platform.domains.ingestion.ibge.sidra_query import SidraQuery


def test_sidra_query_normalizes_selectors() -> None:
    query = SidraQuery(
        table_id=6579,
        territorial_level=6,
        territories="all",
        variables=["9324"],
        periods=("2019", "2020"),
    )

    assert query.territories == ("all",)
    assert query.variables == ("9324",)
    assert query.periods == ("2019", "2020")


def test_sidra_query_rejects_empty_selector() -> None:
    with pytest.raises(ValueError, match="periods cannot be empty"):
        SidraQuery(
            table_id=6579,
            territorial_level=6,
            territories="all",
            variables="9324",
            periods=[],
        )


def test_sidra_query_rejects_invalid_table_id() -> None:
    with pytest.raises(ValueError, match="table_id must be greater than zero"):
        SidraQuery(
            table_id=0,
            territorial_level=6,
            territories="all",
            variables="9324",
            periods="last 1",
        )


def test_sidra_dataset_builds_query_from_defaults() -> None:
    dataset = SidraDataset(
        name="population",
        table_id=6579,
        territorial_level=6,
        variables=("9324",),
    )

    query = dataset.build_query()

    assert query.table_id == 6579
    assert query.territorial_level == 6
    assert query.territories == ("all",)
    assert query.variables == ("9324",)
    assert query.periods == ("last 1",)


def test_sidra_dataset_allows_explicit_periods() -> None:
    query = MUNICIPALITY_POPULATION.build_query(
        periods=("2019", "2020", "2025"),
    )

    assert query.periods == ("2019", "2020", "2025")


def test_initial_dataset_catalog_matches_discovery() -> None:
    assert MUNICIPALITY_POPULATION.table_id == 6579
    assert MUNICIPALITY_POPULATION.variables == ("9324",)
    assert MUNICIPALITY_GDP.table_id == 5938
    assert MUNICIPALITY_GDP.variables == ("all",)
