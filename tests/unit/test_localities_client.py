from typing import Any

import pytest

from olist_data_platform.domains.ingestion.ibge.localities_client import (
    LocalitiesClient,
)


def test_get_municipality_delegates_http_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = LocalitiesClient()
    captured: dict[str, Any] = {}

    def fake_get(
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        captured["endpoint"] = endpoint
        captured["params"] = params
        return {"id": 3550308, "nome": "São Paulo"}

    monkeypatch.setattr(client, "get", fake_get)

    response = client.get_municipality(3550308)

    assert response["id"] == 3550308
    assert captured["endpoint"] == (
        "/api/v1/localidades/municipios/3550308"
    )
    assert captured["params"] is None


def test_get_municipalities_uses_name_ordering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = LocalitiesClient()
    captured: dict[str, Any] = {}

    def fake_get(
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        captured["endpoint"] = endpoint
        captured["params"] = params
        return [{"id": 5200050, "nome": "Abadia de Goiás"}]

    monkeypatch.setattr(client, "get", fake_get)

    response = client.get_municipalities()

    assert response[0]["id"] == 5200050
    assert captured["endpoint"] == "/api/v1/localidades/municipios"
    assert captured["params"] == {"orderBy": "nome"}


def test_get_municipality_rejects_invalid_id() -> None:
    client = LocalitiesClient()

    with pytest.raises(ValueError, match="greater than zero"):
        client.get_municipality(0)


def test_get_municipalities_rejects_non_list_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = LocalitiesClient()
    monkeypatch.setattr(client, "get", lambda **_: {"unexpected": True})

    with pytest.raises(TypeError, match="response must be a list"):
        client.get_municipalities()
