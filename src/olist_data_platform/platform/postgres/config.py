from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PostgresConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    sslmode: str = "prefer"
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> PostgresConfig:
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=cls._required_env("POSTGRES_DB"),
            user=cls._required_env("POSTGRES_USER"),
            password=cls._required_env("POSTGRES_PASSWORD"),
            sslmode=os.getenv("POSTGRES_SSLMODE", "prefer"),
            connect_timeout=int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "10")),
        )

    @staticmethod
    def _required_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Required environment variable is not set: {name}")
        return value

    @property
    def conninfo(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"sslmode={self.sslmode} "
            f"connect_timeout={self.connect_timeout}"
        )
