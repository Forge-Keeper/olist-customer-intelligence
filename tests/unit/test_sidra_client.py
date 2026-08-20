from typing import Any

import pytest

from olist_data_platform.domains.ingestion.ibge.sidra_client import SidraClient
from olist_data_platform.domains.ingestion.ibge.sidra_query import SidraQuery


def test_build_values_endpoint_encodes_sidra_query() -> None:
    query = SidraQuery(
        table_id=6579,
        territorial_level=6,
        territories="all",
        variables="9324",
        periods="last 1",
    )

    assert SidraClient._build_values_endpoint(query) == (
        "/values/t/6579/n6/all/v/9324/p/last%201"
    )


def test_build_values_endpoint_supports_multiple_periods() -> None:
    query = SidraQuery(
        table_id=6579,
        territorial_level=6,
        territories="3550308",
        variables="9324",
        periods=("2019", "2020", "2025"),
    )

    assert SidraClient._build_values_endpoint(query).endswith(
        "/p/2019,2020,2025"
    )


def test_get_values_delegates_http_call(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SidraClient()
    captured: dict[str, Any] = {}

    def fake_get(
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        captured["endpoint"] = endpoint
        captured["params"] = params
        return [{"V": "Valor"}, {"V": "10"}]

    monkeypatch.setattr(client, "get", fake_get)

    response = client.get_values(
        SidraQuery(
            table_id=6579,
            territorial_level=6,
            territories="all",
            variables="9324",
            periods="last 1",
        )
    )

    assert response == [{"V": "Valor"}, {"V": "10"}]
    assert captured["params"] == {"formato": "json"}
    assert captured["endpoint"] == (
        "/values/t/6579/n6/all/v/9324/p/last%201"
    )


def test_get_values_rejects_non_list_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SidraClient()
    monkeypatch.setattr(client, "get", lambda **_: {"unexpected": True})

    query = SidraQuery(
        table_id=6579,
        territorial_level=6,
        territories="all",
        variables="9324",
        periods="last 1",
    )

    with pytest.raises(TypeError, match="response must be a list"):
        client.get_values(query)
