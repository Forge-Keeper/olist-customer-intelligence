import json
from pathlib import Path

import pytest

from scripts.run_deployment_smokes import (
    build_environment,
    discover_dab_jobs,
    load_manifest,
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
    _write_manifest(manifest_path, {"first_job": {"variables": {"periods": "2018"}}})

    manifest = load_manifest(manifest_path)
    validate_manifest_coverage(manifest, resources)


def test_manifest_coverage_rejects_missing_smoke_contract(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    resources.mkdir()
    _write_job(resources / "first.job.yml", "first_job")
    _write_job(resources / "second.job.yml", "second_job")
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(manifest_path, {"first_job": {"variables": {}}})

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
            "first_job": {"variables": {}},
            "removed_job": {"variables": {}},
        },
    )

    with pytest.raises(ValueError, match="unknown smoke contracts: removed_job"):
        validate_manifest_coverage(load_manifest(manifest_path), resources)


def test_build_environment_scopes_bundle_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXISTING_VALUE", "kept")

    env = build_environment({"cempre_periods": "2018"})

    assert env["EXISTING_VALUE"] == "kept"
    assert env["BUNDLE_VAR_cempre_periods"] == "2018"
