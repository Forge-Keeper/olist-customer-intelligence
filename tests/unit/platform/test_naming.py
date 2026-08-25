from __future__ import annotations

import re
from pathlib import Path

import pytest

from olist_data_platform.platform.naming import qualified_table_name


@pytest.mark.parametrize("catalog", ["dev", "stg", "prd", "feature_123"])
def test_qualified_table_name_uses_explicit_catalog(catalog: str) -> None:
    assert (
        qualified_table_name(
            catalog=catalog,
            schema="bronze",
            table="ibge_municipality_gdp",
        )
        == f"{catalog}.bronze.ibge_municipality_gdp"
    )


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("catalog", ""),
        ("catalog", "prd; DROP CATALOG prd"),
        ("schema", "bronze.data"),
        ("table", "ibge-gdp"),
    ],
)
def test_qualified_table_name_rejects_unsafe_identifiers(
    argument: str,
    value: str,
) -> None:
    kwargs = {
        "catalog": "dev",
        "schema": "bronze",
        "table": "ibge_municipality_gdp",
    }
    kwargs[argument] = value

    with pytest.raises(ValueError):
        qualified_table_name(**kwargs)


def test_runtime_python_does_not_hardcode_environment_qualified_objects() -> None:
    """Prevent reintroducing dev/stg/prd table literals into runtime Python."""
    repository_root = Path(__file__).resolve().parents[3]
    runtime_roots = (repository_root / "src", repository_root / "notebooks")
    environment_literal = re.compile(r"[\"'](?:dev|stg|prd)\.[A-Za-z_]")

    offenders: list[str] = []
    for runtime_root in runtime_roots:
        for path in runtime_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if environment_literal.search(text):
                offenders.append(str(path.relative_to(repository_root)))

    assert offenders == [], (
        "Environment-qualified object names must be injected by runtime/deployment "
        f"configuration, not hardcoded: {offenders}"
    )
