from __future__ import annotations

from typing import Any

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from olist_data_platform.common.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class APIClient:
    """
    Generic HTTP API client.

    Responsibilities:
        - Validate HTTP client configuration
        - Configure retries and backoff
        - Execute GET requests
        - Raise errors for unsuccessful HTTP responses
        - Return decoded JSON responses
        - Provide technical logging for API communication
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: int | float = 1.0,
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

        self.session = self._create_session()

        logger.debug(
            "api_client_created | "
            "base_url=%s | "
            "timeout=%s | "
            "max_retries=%s | "
            "backoff_factor=%s",
            self.base_url,
            self.timeout,
            self.max_retries,
            self.backoff_factor,
        )

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Execute a GET request and return the decoded JSON response.
        """

        self._validate_endpoint(endpoint)

        url = self._build_url(endpoint)

        logger.debug(
            "api_get_started | "
            "url=%s | "
            "has_params=%s",
            url,
            params is not None,
        )

        try:
            response = self.session.get(
                url=url,
                params=params,
                timeout=self.timeout,
            )

            logger.debug(
                "api_response_received | "
                "url=%s | "
                "status_code=%s",
                url,
                response.status_code,
            )

            response.raise_for_status()

            payload = response.json()

            logger.debug(
                "api_get_completed | "
                "url=%s | "
                "status_code=%s",
                url,
                response.status_code,
            )

            return payload

        except requests.Timeout:
            logger.warning(
                "api_request_timeout | "
                "url=%s | "
                "timeout=%s",
                url,
                self.timeout,
            )
            raise

        except requests.ConnectionError:
            logger.warning(
                "api_connection_error | "
                "url=%s",
                url,
            )
            raise

        except requests.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )

            logger.warning(
                "api_http_error | "
                "url=%s | "
                "status_code=%s",
                url,
                status_code,
            )
            raise

        except requests.JSONDecodeError:
            logger.warning(
                "api_invalid_json_response | "
                "url=%s",
                url,
            )
            raise

    def _create_session(self) -> Session:
        """
        Create an HTTP session configured with retry behavior.
        """

        retry_strategy = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=self.max_retries,
            status=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=(
                429,
                500,
                502,
                503,
                504,
            ),
            allowed_methods=(
                "GET",
            ),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy
        )

        session = requests.Session()

        session.mount(
            "https://",
            adapter,
        )

        session.mount(
            "http://",
            adapter,
        )

        if self.headers:
            session.headers.update(
                self.headers
            )

        return session

    def _build_url(
        self,
        endpoint: str,
    ) -> str:
        return (
            f"{self.base_url}/"
            f"{endpoint.lstrip('/')}"
        )

    @staticmethod
    def _validate_base_url(
        base_url: str,
    ) -> None:
        if not isinstance(base_url, str):
            raise TypeError(
                "base_url must be a string."
            )

        if not base_url.strip():
            raise ValueError(
                "base_url cannot be empty."
            )

        if not base_url.startswith(
            ("http://", "https://")
        ):
            raise ValueError(
                "base_url must start with "
                "'http://' or 'https://'."
            )

        if base_url in (
            "http://",
            "https://",
        ):
            raise ValueError(
                "base_url must contain a valid host."
            )

    @staticmethod
    def _validate_timeout(
        timeout: int,
    ) -> None:
        if not isinstance(timeout, int):
            raise TypeError(
                "timeout must be an integer."
            )

        if timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

    @staticmethod
    def _validate_max_retries(
        max_retries: int,
    ) -> None:
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
        backoff_factor: int | float,
    ) -> None:
        if not isinstance(
            backoff_factor,
            (int, float),
        ):
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

        for key, value in headers.items():
            if not isinstance(key, str):
                raise TypeError(
                    "header keys must be strings."
                )

            if not isinstance(value, str):
                raise TypeError(
                    "header values must be strings."
                )

    @staticmethod
    def _validate_endpoint(
        endpoint: str,
    ) -> None:
        if not isinstance(endpoint, str):
            raise TypeError(
                "endpoint must be a string."
            )

        if not endpoint.strip():
            raise ValueError(
                "endpoint cannot be empty."
            )