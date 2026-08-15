from unittest.mock import Mock

import pytest
import requests

from olist_data_platform.platform.http.api_client import APIClient

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_should_create_api_client_with_default_configuration():
    client = APIClient(
        base_url="https://example.com",
    )

    assert client.base_url == "https://example.com"
    assert client.timeout == 30
    assert client.max_retries == 3
    assert client.backoff_factor == 1.0
    assert client.headers == {}


def test_should_remove_trailing_slash_from_base_url():
    client = APIClient(
        base_url="https://example.com/",
    )

    assert client.base_url == "https://example.com"


def test_should_create_api_client_with_custom_configuration():
    headers = {
        "Authorization": "Bearer token",
        "Accept": "application/json",
    }

    client = APIClient(
        base_url="https://example.com",
        timeout=60,
        max_retries=5,
        backoff_factor=2.0,
        headers=headers,
    )

    assert client.timeout == 60
    assert client.max_retries == 5
    assert client.backoff_factor == 2.0
    assert client.headers == headers


def test_should_apply_headers_to_http_session():
    headers = {
        "Authorization": "Bearer token",
    }

    client = APIClient(
        base_url="https://example.com",
        headers=headers,
    )

    assert client.session.headers["Authorization"] == "Bearer token"


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("endpoint", "expected_url"),
    [
        ("v1/data", "https://example.com/v1/data"),
        ("/v1/data", "https://example.com/v1/data"),
    ],
)
def test_should_build_url_without_duplicate_slashes(
    endpoint,
    expected_url,
):
    client = APIClient(
        base_url="https://example.com/",
    )

    assert client._build_url(endpoint) == expected_url


# ---------------------------------------------------------------------------
# GET request
# ---------------------------------------------------------------------------


def test_should_execute_get_and_return_json_payload():
    client = APIClient(
        base_url="https://example.com",
        timeout=15,
    )

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "result": "ok",
    }

    client.session.get = Mock(
        return_value=response,
    )

    result = client.get(
        endpoint="/v1/data",
        params={
            "page": 1,
        },
    )

    client.session.get.assert_called_once_with(
        url="https://example.com/v1/data",
        params={
            "page": 1,
        },
        timeout=15,
    )

    response.raise_for_status.assert_called_once_with()

    assert result == {
        "result": "ok",
    }


def test_should_execute_get_without_params():
    client = APIClient(
        base_url="https://example.com",
    )

    response = Mock()
    response.status_code = 200
    response.json.return_value = []

    client.session.get = Mock(
        return_value=response,
    )

    result = client.get(
        endpoint="/v1/data",
    )

    client.session.get.assert_called_once_with(
        url="https://example.com/v1/data",
        params=None,
        timeout=30,
    )

    assert result == []


# ---------------------------------------------------------------------------
# GET error propagation
# ---------------------------------------------------------------------------


def test_should_propagate_timeout_error():
    client = APIClient(
        base_url="https://example.com",
    )

    client.session.get = Mock(
        side_effect=requests.Timeout,
    )

    with pytest.raises(requests.Timeout):
        client.get(
            endpoint="/v1/data",
        )


def test_should_propagate_connection_error():
    client = APIClient(
        base_url="https://example.com",
    )

    client.session.get = Mock(
        side_effect=requests.ConnectionError,
    )

    with pytest.raises(requests.ConnectionError):
        client.get(
            endpoint="/v1/data",
        )


def test_should_propagate_http_error():
    client = APIClient(
        base_url="https://example.com",
    )

    response = Mock()
    response.status_code = 500

    http_error = requests.HTTPError(
        response=response,
    )

    response.raise_for_status.side_effect = (
        http_error
    )

    client.session.get = Mock(
        return_value=response,
    )

    with pytest.raises(requests.HTTPError):
        client.get(
            endpoint="/v1/data",
        )


def test_should_propagate_json_decode_error():
    client = APIClient(
        base_url="https://example.com",
    )

    response = Mock()
    response.status_code = 200
    response.json.side_effect = (
        requests.JSONDecodeError(
            "Invalid JSON",
            "",
            0,
        )
    )

    client.session.get = Mock(
        return_value=response,
    )

    with pytest.raises(requests.JSONDecodeError):
        client.get(
            endpoint="/v1/data",
        )


# ---------------------------------------------------------------------------
# base_url validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        " ",
    ],
)
def test_should_reject_empty_base_url(
    base_url,
):
    with pytest.raises(
        ValueError,
        match="base_url cannot be empty",
    ):
        APIClient(
            base_url=base_url,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "example.com",
        "ftp://example.com",
    ],
)
def test_should_reject_base_url_without_http_protocol(
    base_url,
):
    with pytest.raises(
        ValueError,
        match="base_url must start with",
    ):
        APIClient(
            base_url=base_url,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://",
        "https://",
    ],
)
def test_should_reject_base_url_without_host(
    base_url,
):
    with pytest.raises(
        ValueError,
        match="base_url must contain a valid host",
    ):
        APIClient(
            base_url=base_url,
        )


def test_should_reject_non_string_base_url():
    with pytest.raises(
        TypeError,
        match="base_url must be a string",
    ):
        APIClient(
            base_url=None,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# timeout validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
    ],
)
def test_should_reject_non_positive_timeout(
    timeout,
):
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero",
    ):
        APIClient(
            base_url="https://example.com",
            timeout=timeout,
        )


@pytest.mark.parametrize(
    "timeout",
    [
        1.5,
        "30",
        None,
    ],
)
def test_should_reject_non_integer_timeout(
    timeout,
):
    with pytest.raises(
        TypeError,
        match="timeout must be an integer",
    ):
        APIClient(
            base_url="https://example.com",
            timeout=timeout,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# max_retries validation
# ---------------------------------------------------------------------------


def test_should_accept_zero_retries():
    client = APIClient(
        base_url="https://example.com",
        max_retries=0,
    )

    assert client.max_retries == 0


def test_should_reject_negative_max_retries():
    with pytest.raises(
        ValueError,
        match="max_retries cannot be negative",
    ):
        APIClient(
            base_url="https://example.com",
            max_retries=-1,
        )


@pytest.mark.parametrize(
    "max_retries",
    [
        1.5,
        "3",
        None,
    ],
)
def test_should_reject_non_integer_max_retries(
    max_retries,
):
    with pytest.raises(
        TypeError,
        match="max_retries must be an integer",
    ):
        APIClient(
            base_url="https://example.com",
            max_retries=max_retries,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# backoff_factor validation
# ---------------------------------------------------------------------------


def test_should_accept_zero_backoff_factor():
    client = APIClient(
        base_url="https://example.com",
        backoff_factor=0.0,
    )

    assert client.backoff_factor == 0.0


def test_should_reject_negative_backoff_factor():
    with pytest.raises(
        ValueError,
        match="backoff_factor cannot be negative",
    ):
        APIClient(
            base_url="https://example.com",
            backoff_factor=-0.1,
        )


@pytest.mark.parametrize(
    "backoff_factor",
    [
        1,
        "1.0",
        None,
    ],
)
def test_should_reject_non_float_backoff_factor(
    backoff_factor,
):
    with pytest.raises(
        TypeError,
        match="backoff_factor must be a float",
    ):
        APIClient(
            base_url="https://example.com",
            backoff_factor=backoff_factor,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# headers validation
# ---------------------------------------------------------------------------


def test_should_accept_none_headers():
    client = APIClient(
        base_url="https://example.com",
        headers=None,
    )

    assert client.headers == {}


def test_should_reject_non_dictionary_headers():
    with pytest.raises(
        TypeError,
        match="headers must be a dictionary",
    ):
        APIClient(
            base_url="https://example.com",
            headers=["Accept", "application/json"],  # type: ignore[arg-type]
        )


def test_should_reject_non_string_header_key():
    with pytest.raises(
        TypeError,
        match="header keys must be strings",
    ):
        APIClient(
            base_url="https://example.com",
            headers={
                123: "value",
            },  # type: ignore[dict-item]
        )


def test_should_reject_non_string_header_value():
    with pytest.raises(
        TypeError,
        match="header values must be strings",
    ):
        APIClient(
            base_url="https://example.com",
            headers={
                "X-Retry": 3,
            },  # type: ignore[dict-item]
        )


# ---------------------------------------------------------------------------
# endpoint validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        " ",
    ],
)
def test_should_reject_empty_endpoint(
    endpoint,
):
    client = APIClient(
        base_url="https://example.com",
    )

    with pytest.raises(
        ValueError,
        match="endpoint cannot be empty",
    ):
        client.get(
            endpoint=endpoint,
        )


def test_should_reject_non_string_endpoint():
    client = APIClient(
        base_url="https://example.com",
    )

    with pytest.raises(
        TypeError,
        match="endpoint must be a string",
    ):
        client.get(
            endpoint=None,  # type: ignore[arg-type]
        )
