import os

import pytest

from olist_data_platform.platform.postgres import PostgresClient, PostgresConfig


@pytest.mark.integration
def test_postgres_client_ping_against_local_container() -> None:
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing PostgreSQL environment variables: {', '.join(missing)}")

    config = PostgresConfig.from_env()
    client = PostgresClient(config)

    assert client.ping() is True
