import pytest

from src.ingestion.api.api_client import APIClient

# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------


def test_should_create_client_with_default_configuration():
    # Arrange
    base_url = "https://api.example.com"

    # Act
    client = APIClient(base_url=base_url)

    # Assert
    assert client.base_url == base_url
    assert client.timeout == 30
    assert client.max_retries == 3
    assert client.backoff_factor == 1.0
    assert client.headers == {}


def test_should_create_client_with_custom_configuration():
    # Arrange
    base_url = "https://api.example.com"
    headers = {
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }

    # Act
    client = APIClient(
        base_url=base_url,
        timeout=60,
        max_retries=5,
        backoff_factor=2.0,
        headers=headers,
    )

    # Assert
    assert client.base_url == base_url
    assert client.timeout == 60
    assert client.max_retries == 5
    assert client.backoff_factor == 2.0
    assert client.headers == headers


# ---------------------------------------------------------------------------
# Base URL validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        " ",
        "api.example.com",
        "ftp://api.example.com",
        "http://",
        "https://",
    ],
)
def test_should_reject_invalid_base_url(base_url):
    # Act / Assert
    with pytest.raises((TypeError, ValueError)):
        APIClient(base_url=base_url)


def test_should_reject_non_string_base_url():
    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(base_url=None)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]


def test_should_remove_trailing_slash_from_base_url():
    # Arrange
    base_url = "https://api.example.com/"

    # Act
    client = APIClient(base_url=base_url)

    # Assert
    assert client.base_url == "https://api.example.com"


# ---------------------------------------------------------------------------
# Timeout validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
    ],
)
def test_should_reject_invalid_timeout(timeout):
    # Act / Assert
    with pytest.raises(ValueError):
        APIClient(
            base_url="https://api.example.com",
            timeout=timeout,
        )


@pytest.mark.parametrize(
    "timeout",
    [
        "30",
        30.5,
        None,
    ],
)
def test_should_reject_invalid_timeout_type(timeout):
    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(
            base_url="https://api.example.com",
            timeout=timeout,
        )


# ---------------------------------------------------------------------------
# Retry configuration validation
# ---------------------------------------------------------------------------


def test_should_accept_zero_retries():
    # Act
    client = APIClient(
        base_url="https://api.example.com",
        max_retries=0,
    )

    # Assert
    assert client.max_retries == 0


def test_should_reject_negative_retries():
    # Act / Assert
    with pytest.raises(ValueError):
        APIClient(
            base_url="https://api.example.com",
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
def test_should_reject_invalid_retry_type(max_retries):
    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(
            base_url="https://api.example.com",
            max_retries=max_retries,
        )


# ---------------------------------------------------------------------------
# Backoff configuration validation
# ---------------------------------------------------------------------------


def test_should_accept_zero_backoff():
    # Act
    client = APIClient(
        base_url="https://api.example.com",
        backoff_factor=0,
    )

    # Assert
    assert client.backoff_factor == 0


def test_should_reject_negative_backoff():
    # Act / Assert
    with pytest.raises(ValueError):
        APIClient(
            base_url="https://api.example.com",
            backoff_factor=-1,
        )


@pytest.mark.parametrize(
    "backoff_factor",
    [
        "1",
        None,
    ],
)
def test_should_reject_invalid_backoff_type(backoff_factor):
    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(
            base_url="https://api.example.com",
            backoff_factor=backoff_factor,
        )


# ---------------------------------------------------------------------------
# Headers validation
# ---------------------------------------------------------------------------


def test_should_accept_none_headers():
    # Act
    client = APIClient(
        base_url="https://api.example.com",
        headers=None,
    )

    # Assert
    assert client.headers == {}


def test_should_accept_valid_headers():
    # Arrange
    headers = {
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }

    # Act
    client = APIClient(
        base_url="https://api.example.com",
        headers=headers,
    )

    # Assert
    assert client.headers == headers


@pytest.mark.parametrize(
    "headers",
    [
        [],
        "Authorization",
        123,
    ],
)
def test_should_reject_invalid_headers_type(headers):
    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(
            base_url="https://api.example.com",
            headers=headers,
        )


def test_should_reject_non_string_header_key():
    # Arrange
    headers = {
        "123": "value",
    }

    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(
            base_url="https://api.example.com",
            headers=headers,
        )


def test_should_reject_non_string_header_value():
    # Arrange
    headers = {
        "Authorization": 123, # type: ignore[dict-item]
    }

    # Act / Assert
    with pytest.raises(TypeError):
        APIClient(
            base_url="https://api.example.com",
            headers=headers, # ty: ignore[invalid-argument-type]
        )


# ---------------------------------------------------------------------------
# Endpoint validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        " ",
    ],
)
def test_should_reject_empty_endpoint(endpoint):
    # Arrange
    client = APIClient(
        base_url="https://api.example.com",
    )

    # Act / Assert
    with pytest.raises(ValueError):
        client.get(endpoint)


def test_should_reject_non_string_endpoint():
    # Arrange
    client = APIClient(
        base_url="https://api.example.com",
    )

    # Act / Assert
    with pytest.raises(TypeError):
        client.get(None) # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
