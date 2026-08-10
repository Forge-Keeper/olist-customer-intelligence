from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import requests
from requests import Response
from requests.exceptions import RequestException


class APIClient:
    """
    Generic HTTP client for REST APIs.

    Responsibilities:
        - Validate client configuration
        - Build HTTP requests
        - Handle timeouts
        - Handle retries
        - Validate HTTP responses
        - Return parsed JSON

    API-specific behavior should be implemented by subclasses.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        headers: dict[str, str] | None = None,
    ) -> None:

        self._validate_base_url(base_url)
        self._validate_timeout(timeout)
        self._validate_max_retries(max_retries)
        self._validate_backoff_factor(backoff_factor)
        self._validate_headers(headers)

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.headers = headers or {}

    @staticmethod
    def _validate_base_url(base_url: str) -> None:
        if not isinstance(base_url, str):
            raise TypeError("base_url must be a string.")

        if not base_url.strip():
            raise ValueError("base_url cannot be empty.")

        parsed_url = urlparse(base_url)

        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError(
                "base_url must use HTTP or HTTPS."
            )

        if not parsed_url.netloc:
            raise ValueError(
                "base_url must contain a valid hostname."
            )

    @staticmethod
    def _validate_timeout(timeout: int) -> None:
        if not isinstance(timeout, int):
            raise TypeError("timeout must be an integer.")

        if timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

    @staticmethod
    def _validate_max_retries(max_retries: int) -> None:
        if not isinstance(max_retries, int):
            raise TypeError(
                "max_retries must be an integer."
            )

        if max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )

    @staticmethod
    def _validate_backoff_factor(
        backoff_factor: float,
    ) -> None:
        if not isinstance(backoff_factor, (int, float)):
            raise TypeError(
                "backoff_factor must be numeric."
            )

        if backoff_factor < 0:
            raise ValueError(
                "backoff_factor cannot be negative."
            )

    @staticmethod
    def _validate_headers(
        headers: dict[str, str] | None,
    ) -> None:
        if headers is None:
            return

        if not isinstance(headers, dict):
            raise TypeError(
                "headers must be a dictionary."
            )

        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in headers.items()
        ):
            raise TypeError(
                "header keys and values must be strings."
            )

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:

        if not isinstance(endpoint, str):
            raise TypeError("endpoint must be a string.")

        if not endpoint.strip():
            raise ValueError("endpoint cannot be empty.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url=url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout,
                )

                self._validate_response(response)

                return response.json()

            except RequestException as exc:

                if attempt >= self.max_retries:
                    raise RuntimeError(
                        f"API request failed after "
                        f"{self.max_retries + 1} attempts: "
                        f"{url}"
                    ) from exc

                sleep_time = (
                    self.backoff_factor * (2 ** attempt)
                )

                time.sleep(sleep_time)

        raise RuntimeError("Unexpected API client state.")

    @staticmethod
    def _validate_response(response: Response) -> None:
        response.raise_for_status()