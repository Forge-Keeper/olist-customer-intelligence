import json
from pathlib import Path

import pytest

from scripts.run_deployment_smokes import (
    build_command,
    discover_dab_jobs,
    load_manifest,
    resolve_arguments,
    validate_manifest_coverage,
)


def _write_job(path: Path, job_name: str) -> None:
    path.write_text(
        f"resources:\n  jobs:\n    {job_name}:\n      name: test\n",
        encoding="utf-8",
    )


def _write_manifest(path: Path, jobs: dict[str, dict[str, object]]) -> None:
    path.write_text(json.dumps({"jobs": jobs}), encoding="utf-8")


def test_discover_dab_jobs_reads_job_resource_keys(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    resources.mkdir()
    _write_job(resources / "first.job.yml", "first_job")
    _write_job(resources / "second.job.yml", "second_job")

    assert discover_dab_jobs(resources) == {"first_job", "second_job"}


def test_manifest_coverage_accepts_exact_job_set(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    resources.mkdir()
    _write_job(resources / "first.job.yml", "first_job")
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(
        manifest_path,
        {"first_job": {"arguments": ["--periods", "2018"]}},
    )

    manifest = load_manifest(manifest_path)
    validate_manifest_coverage(manifest, resources)


def test_manifest_coverage_rejects_missing_smoke_contract(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    resources.mkdir()
    _write_job(resources / "first.job.yml", "first_job")
    _write_job(resources / "second.job.yml", "second_job")
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(manifest_path, {"first_job": {"arguments": []}})

    with pytest.raises(ValueError, match="missing smoke contracts: second_job"):
        validate_manifest_coverage(load_manifest(manifest_path), resources)


def test_manifest_coverage_rejects_unknown_smoke_contract(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    resources.mkdir()
    _write_job(resources / "first.job.yml", "first_job")
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(
        manifest_path,
        {
            "first_job": {"arguments": []},
            "removed_job": {"arguments": []},
        },
    )

    with pytest.raises(ValueError, match="unknown smoke contracts: removed_job"):
        validate_manifest_coverage(load_manifest(manifest_path), resources)


def test_load_manifest_rejects_non_string_arguments(tmp_path: Path) -> None:
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(manifest_path, {"first_job": {"arguments": ["--periods", 2018]}})

    with pytest.raises(ValueError, match="must be a string list"):
        load_manifest(manifest_path)


def test_resolve_arguments_replaces_target_placeholder() -> None:
    arguments = ["--target-table", "${target}.bronze.example", "--periods", "2018"]

    assert resolve_arguments("stg", arguments) == [
        "--target-table",
        "stg.bronze.example",
        "--periods",
        "2018",
    ]
    assert resolve_arguments("prd", arguments) == [
        "--target-table",
        "prd.bronze.example",
        "--periods",
        "2018",
    ]


def test_build_command_passes_complete_runtime_arguments_after_separator() -> None:
    command = build_command(
        "stg",
        "ibge_municipality_gdp",
        [
            "--target-table",
            "${target}.bronze.ibge_municipality_gdp",
            "--periods",
            "2018",
        ],
    )

    assert command == [
        "databricks",
        "bundle",
        "run",
        "-t",
        "stg",
        "ibge_municipality_gdp",
        "--",
        "--target-table",
        "stg.bronze.ibge_municipality_gdp",
        "--periods",
        "2018",
    ]


def test_runtime_smoke_contracts_are_complete_and_bounded_to_2018() -> None:
    manifest = load_manifest()

    assert resolve_arguments("stg", manifest["ibge_municipality_gdp"]["arguments"]) == [
        "--target-table",
        "stg.bronze.ibge_municipality_gdp",
        "--periods",
        "2018",
    ]
    assert resolve_arguments(
        "prd", manifest["ibge_municipality_business_activity"]["arguments"]
    ) == [
        "--target-table",
        "prd.bronze.ibge_municipality_business_activity",
        "--periods",
        "2018",
    ]
