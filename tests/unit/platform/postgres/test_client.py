from unittest.mock import MagicMock, patch

import pytest
from psycopg.sql import Composable, SQL

from olist_data_platform.platform.postgres.client import PostgresClient
from olist_data_platform.platform.postgres.config import PostgresConfig


def _config() -> PostgresConfig:
    return PostgresConfig(
        host="db.example.com",
        port=5432,
        database="olist",
        user="app",
        password="secret",
        sslmode="require",
        connect_timeout=5,
    )


def _sql_text(value: object) -> str:
    assert isinstance(value, Composable)
    return " ".join(value.as_string().split())


def _configure_connection_method(client: PostgresClient) -> tuple[MagicMock, MagicMock]:
    connection = MagicMock()
    cursor = MagicMock()
    connection_method = MagicMock()
    connection_method.return_value.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    client.connection = connection_method  # type: ignore[method-assign]
    return connection_method, cursor


def test_connection_uses_configured_conninfo_and_context_manager() -> None:
    config = _config()
    client = PostgresClient(config)
    connection = MagicMock()

    with patch(
        "olist_data_platform.platform.postgres.client.psycopg.connect"
    ) as connect:
        connect.return_value.__enter__.return_value = connection

        with client.connection() as yielded:
            assert yielded is connection

    connect.assert_called_once_with(config.conninfo)
    connect.return_value.__enter__.assert_called_once_with()
    connect.return_value.__exit__.assert_called_once_with(None, None, None)


def test_connection_propagates_connect_error() -> None:
    client = PostgresClient(_config())

    with patch(
        "olist_data_platform.platform.postgres.client.psycopg.connect",
        side_effect=RuntimeError("database unavailable"),
    ):
        with pytest.raises(RuntimeError, match="database unavailable"):
            with client.connection():
                pass


def test_execute_scalar_returns_first_column() -> None:
    client = PostgresClient(_config())
    connection_method, cursor = _configure_connection_method(client)
    cursor.fetchone.return_value = (42, "ignored")
    query = SQL("SELECT 42")

    result = client.execute_scalar(query)

    assert result == 42
    connection_method.assert_called_once_with()
    cursor.execute.assert_called_once_with(query)


def test_execute_scalar_rejects_query_without_rows() -> None:
    client = PostgresClient(_config())
    _, cursor = _configure_connection_method(client)
    cursor.fetchone.return_value = None

    with pytest.raises(RuntimeError, match="Query returned no rows"):
        client.execute_scalar(SQL("SELECT NULL WHERE FALSE"))


def test_execute_scalar_propagates_query_error() -> None:
    client = PostgresClient(_config())
    _, cursor = _configure_connection_method(client)
    cursor.execute.side_effect = RuntimeError("query failed")

    with pytest.raises(RuntimeError, match="query failed"):
        client.execute_scalar(SQL("SELECT broken"))


@pytest.mark.parametrize(("scalar", "expected"), [(1, True), (0, False)])
def test_ping_reflects_select_one_result(scalar: int, expected: bool) -> None:
    client = PostgresClient(_config())

    with patch.object(client, "execute_scalar", return_value=scalar) as execute_scalar:
        assert client.ping() is expected

    execute_scalar.assert_called_once()
    query = execute_scalar.call_args.args[0]
    assert _sql_text(query) == "SELECT 1"
