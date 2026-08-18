import pytest

from olist_data_platform.platform.jdbc import JdbcConfig


def test_url_and_options() -> None:
    config = JdbcConfig(
        host="pg.example.com",
        port=5432,
        database="olist",
        user="reader",
        password="secret",
    )

    assert config.url == (
        "jdbc:postgresql://pg.example.com:5432/olist?sslmode=require"
    )
    assert config.options == {
        "url": config.url,
        "user": "reader",
        "password": "secret",
        "driver": "org.postgresql.Driver",
    }


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("host", {"host": ""}),
        ("port", {"port": 0}),
        ("database", {"database": ""}),
        ("user", {"user": ""}),
        ("password", {"password": ""}),
        ("driver", {"driver": ""}),
        ("sslmode", {"sslmode": ""}),
    ],
)
def test_invalid_config_fails(field_name: str, kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "host": "localhost",
        "port": 5432,
        "database": "olist",
        "user": "reader",
        "password": "secret",
        "driver": "org.postgresql.Driver",
        "sslmode": "require",
    }
    values.update(kwargs)

    with pytest.raises((TypeError, ValueError), match=field_name):
        JdbcConfig(**values)  # type: ignore[arg-type]
