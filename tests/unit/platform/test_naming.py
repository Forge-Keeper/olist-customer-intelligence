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
    kwargs: dict[str, str] = {
        "catalog": "dev",
        "schema": "bronze",
        "table": "ibge_municipality_gdp",
    }
    kwargs[argument] = value

    with pytest.raises(ValueError):
        qualified_table_name(**kwargs)


def test_runtime_python_does_not_hardcode_environment_resources() -> None:
    """Prevent reintroducing environment-specific tables or Volume paths."""
    repository_root = Path(__file__).resolve().parents[3]
    runtime_roots = (repository_root / "src", repository_root / "notebooks")
    forbidden_patterns = (
        re.compile(r"[\"'](?:dev|stg|prd)\.[A-Za-z_]"),
        re.compile(r"[\"']/Volumes/(?:dev|stg|prd)/"),
    )

    offenders: list[str] = []
    for runtime_root in runtime_roots:
        for path in runtime_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if any(pattern.search(text) for pattern in forbidden_patterns):
                offenders.append(str(path.relative_to(repository_root)))

    assert offenders == [], (
        "Environment-specific runtime resources must be injected by deployment or "
        f"runtime configuration, not hardcoded: {offenders}"
    )


def test_bundle_does_not_hardcode_service_principal_application_id() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    bundle_config = (repository_root / "databricks.yml").read_text(encoding="utf-8")
    hardcoded_service_principal = re.compile(
        r"service_principal_name:\s*[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F-]{27,36}\s*$",
        re.MULTILINE,
    )

    assert hardcoded_service_principal.search(bundle_config) is None
