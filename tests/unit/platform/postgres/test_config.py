import pytest

from olist_data_platform.platform.postgres.config import PostgresConfig


REQUIRED_ENV = {
    "POSTGRES_DB": "olist",
    "POSTGRES_USER": "olist",
    "POSTGRES_PASSWORD": "secret",
}


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)


def test_from_env_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)

    config = PostgresConfig.from_env()

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "olist"
    assert config.user == "olist"
    assert config.password == "secret"
    assert config.sslmode == "prefer"
    assert config.connect_timeout == 10


def test_from_env_allows_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("POSTGRES_SSLMODE", "require")
    monkeypatch.setenv("POSTGRES_CONNECT_TIMEOUT", "30")

    config = PostgresConfig.from_env()

    assert config.host == "db.example.com"
    assert config.port == 6543
    assert config.sslmode == "require"
    assert config.connect_timeout == 30


def test_from_env_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "olist")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    with pytest.raises(ValueError, match="POSTGRES_DB"):
        PostgresConfig.from_env()


def test_connection_kwargs_matches_psycopg_contract() -> None:
    config = PostgresConfig(
        host="localhost",
        port=5432,
        database="olist",
        user="olist",
        password="secret",
    )

    assert config.connection_kwargs == {
        "host": "localhost",
        "port": 5432,
        "dbname": "olist",
        "user": "olist",
        "password": "secret",
        "sslmode": "prefer",
        "connect_timeout": 10,
    }
