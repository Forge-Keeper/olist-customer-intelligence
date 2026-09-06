import pytest

from olist_data_platform.platform.jdbc.config import JdbcConfig


def test_jdbc_config_builds_postgres_url_and_options() -> None:
    config = JdbcConfig(
        host="db.example.com",
        port=5432,
        database="olist",
        user="reader",
        password="secret",
    )

    assert config.url == "jdbc:postgresql://db.example.com:5432/olist?sslmode=require"
    assert config.options == {
        "url": config.url,
        "user": "reader",
        "password": "secret",
        "driver": "org.postgresql.Driver",
    }


def test_jdbc_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JDBC_HOST", "db.example.com")
    monkeypatch.setenv("JDBC_DATABASE", "olist")
    monkeypatch.setenv("JDBC_USER", "reader")
    monkeypatch.setenv("JDBC_PASSWORD", "secret")
    monkeypatch.delenv("JDBC_PORT", raising=False)
    monkeypatch.delenv("JDBC_DRIVER", raising=False)
    monkeypatch.delenv("JDBC_SSLMODE", raising=False)

    config = JdbcConfig.from_env()

    assert config.port == 5432
    assert config.sslmode == "require"
    assert config.driver == "org.postgresql.Driver"


def test_jdbc_config_requires_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JDBC_HOST", raising=False)
    monkeypatch.setenv("JDBC_DATABASE", "olist")
    monkeypatch.setenv("JDBC_USER", "reader")
    monkeypatch.setenv("JDBC_PASSWORD", "secret")

    with pytest.raises(ValueError, match="JDBC_HOST"):
        JdbcConfig.from_env()
