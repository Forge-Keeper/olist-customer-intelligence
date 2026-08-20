from __future__ import annotations

from typing import Any, ClassVar
from urllib.parse import quote

from olist_data_platform.domains.ingestion.ibge.sidra_query import SidraQuery
from olist_data_platform.platform.http.api_client import APIClient


class SidraClient(APIClient):
    """Client for the IBGE SIDRA values API."""

    DEFAULT_BASE_URL: ClassVar[str] = "https://apisidra.ibge.gov.br"

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

    def get_values(self, query: SidraQuery) -> list[Any]:
        if not isinstance(query, SidraQuery):
            raise TypeError("query must be a SidraQuery.")

        response = self.get(
            endpoint=self._build_values_endpoint(query),
            params={"formato": "json"},
        )
        if not isinstance(response, list):
            raise TypeError("SIDRA values response must be a list.")
        return response

    @classmethod
    def _build_values_endpoint(cls, query: SidraQuery) -> str:
        territories = cls._encode_selector(query.territories)
        variables = cls._encode_selector(query.variables)
        periods = cls._encode_selector(query.periods)
        return (
            f"/values/t/{query.table_id}/"
            f"n{query.territorial_level}/{territories}/"
            f"v/{variables}/p/{periods}"
        )

    @staticmethod
    def _encode_selector(values: tuple[str, ...]) -> str:
        joined = ",".join(values)
        return quote(joined, safe=",")
