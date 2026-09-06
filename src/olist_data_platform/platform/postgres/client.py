from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.sql import SQL

from .config import PostgresConfig


class PostgresClient:
    def __init__(self, config: PostgresConfig) -> None:
        self._config = config

    @contextmanager
    def connection(self) -> Iterator[Connection[tuple[Any, ...]]]:
        with psycopg.connect(self._config.conninfo) as connection:
            yield connection

    def execute_scalar(self, query: SQL) -> object:
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()

        if row is None:
            raise RuntimeError("Query returned no rows")

        return row[0]

    def ping(self) -> bool:
        return self.execute_scalar(SQL("SELECT 1")) == 1
