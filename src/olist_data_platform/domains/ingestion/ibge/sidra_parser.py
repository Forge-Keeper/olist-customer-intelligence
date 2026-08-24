from __future__ import annotations

from typing import Any


class SidraParser:
    """Parse SIDRA responses without hardcoding dimension semantics."""

    @staticmethod
    def split(
        payload: list[Any],
    ) -> tuple[dict[str, str], list[dict[str, Any]]]:
        if not isinstance(payload, list):
            raise TypeError("SIDRA payload must be a list.")
        if not payload:
            raise ValueError("SIDRA payload cannot be empty.")

        header = payload[0]
        if not isinstance(header, dict):
            raise TypeError("SIDRA header must be a dictionary.")
        if not header:
            raise ValueError("SIDRA header cannot be empty.")
        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in header.items()
        ):
            raise TypeError(
                "SIDRA header keys and labels must be strings."
            )

        rows = payload[1:]
        if not all(isinstance(row, dict) for row in rows):
            raise TypeError("SIDRA data rows must be dictionaries.")

        return dict(header), [dict(row) for row in rows]

    @classmethod
    def decode(cls, payload: list[Any]) -> list[dict[str, Any]]:
        header, rows = cls.split(payload)
        decoded: list[dict[str, Any]] = []

        for row in rows:
            decoded.append(
                {
                    header.get(key, key): value
                    for key, value in row.items()
                }
            )

        return decoded
