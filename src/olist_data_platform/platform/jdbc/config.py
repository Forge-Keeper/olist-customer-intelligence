from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JdbcConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    driver: str = "org.postgresql.Driver"
    sslmode: str = "require"

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("host cannot be empty")
        if self.port <= 0:
            raise ValueError("port must be positive")
        if not self.database.strip():
            raise ValueError("database cannot be empty")
        if not self.user.strip():
            raise ValueError("user cannot be empty")
        if not self.password:
            raise ValueError("password cannot be empty")
        if not self.driver.strip():
            raise ValueError("driver cannot be empty")
        if not self.sslmode.strip():
            raise ValueError("sslmode cannot be empty")

    @classmethod
    def from_env(cls) -> JdbcConfig:
        return cls(
            host=cls._required_env("JDBC_HOST"),
            port=int(os.getenv("JDBC_PORT", "5432")),
            database=cls._required_env("JDBC_DATABASE"),
            user=cls._required_env("JDBC_USER"),
            password=cls._required_env("JDBC_PASSWORD"),
            driver=os.getenv("JDBC_DRIVER", "org.postgresql.Driver"),
            sslmode=os.getenv("JDBC_SSLMODE", "require"),
        )

    @staticmethod
    def _required_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Required environment variable is not set: {name}")
        return value

    @property
    def url(self) -> str:
        return (
            f"jdbc:postgresql://{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )

    @property
    def options(self) -> dict[str, str]:
        return {
            "url": self.url,
            "user": self.user,
            "password": self.password,
            "driver": self.driver,
        }
