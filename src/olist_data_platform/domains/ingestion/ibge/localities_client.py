from __future__ import annotations

from typing import Any, ClassVar

from olist_data_platform.platform.http.api_client import APIClient


class LocalitiesClient(APIClient):
    """Client for the IBGE Localities API."""

    DEFAULT_BASE_URL: ClassVar[str] = "https://servicodados.ibge.gov.br"
    MUNICIPALITIES_ENDPOINT: ClassVar[str] = "/api/v1/localidades/municipios"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        super().__init__(
            base_url=self.DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )

    def get_municipality(self, municipality_id: int) -> dict[str, Any]:
        if not isinstance(municipality_id, int):
            raise TypeError("municipality_id must be an integer.")
        if municipality_id <= 0:
            raise ValueError("municipality_id must be greater than zero.")

        response = self.get(
            endpoint=f"{self.MUNICIPALITIES_ENDPOINT}/{municipality_id}"
        )
        if not isinstance(response, dict):
            raise TypeError("IBGE municipality response must be a dictionary.")
        return response

    def get_municipalities(
        self,
        *,
        order_by: str = "nome",
    ) -> list[dict[str, Any]]:
        if not isinstance(order_by, str):
            raise TypeError("order_by must be a string.")
        if not order_by.strip():
            raise ValueError("order_by cannot be empty.")

        response = self.get(
            endpoint=self.MUNICIPALITIES_ENDPOINT,
            params={"orderBy": order_by},
        )
        if not isinstance(response, list):
            raise TypeError("IBGE municipalities response must be a list.")
        if not all(isinstance(item, dict) for item in response):
            raise TypeError(
                "IBGE municipalities response must contain dictionaries."
            )
        return response
