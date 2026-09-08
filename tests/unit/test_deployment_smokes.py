import json
import subprocess
import threading
import time
from pathlib import Path

import pytest

from scripts.run_deployment_smokes import (
    build_command,
    discover_dab_jobs,
    load_manifest,
    resolve_arguments,
    run_smokes,
    validate_manifest_coverage,
    validate_manifest_dependencies,
)


def _write_job(path: Path, job_name: str) -> None:
    path.write_text(
        f"resources:\n  jobs:\n    {job_name}:\n      name: test\n",
        encoding="utf-8",
    )


def _write_manifest(path: Path, jobs: dict[str, dict[str, object]]) -> None:
    path.write_text(json.dumps({"jobs": jobs}), encoding="utf-8")


def _manifest(*jobs: tuple[str, list[str]]) -> dict[str, dict[str, list[str]]]:
    return {
        job_name: {"arguments": [], "depends_on": depends_on}
        for job_name, depends_on in jobs
    }


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
        {"first_job": {"arguments": ["--periods", "2018"], "depends_on": []}},
    )

    manifest = load_manifest(manifest_path)
    validate_manifest_coverage(manifest, resources)


def test_manifest_coverage_rejects_missing_smoke_contract(tmp_path: Path) -> None:
    resources = tmp_path / "resources"
    resources.mkdir()
    _write_job(resources / "first.job.yml", "first_job")
    _write_job(resources / "second.job.yml", "second_job")
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(
        manifest_path,
        {"first_job": {"arguments": [], "depends_on": []}},
    )

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
            "first_job": {"arguments": [], "depends_on": []},
            "removed_job": {"arguments": [], "depends_on": []},
        },
    )

    with pytest.raises(ValueError, match="unknown smoke contracts: removed_job"):
        validate_manifest_coverage(load_manifest(manifest_path), resources)


def test_load_manifest_rejects_non_string_arguments(tmp_path: Path) -> None:
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(
        manifest_path,
        {"first_job": {"arguments": ["--periods", 2018], "depends_on": []}},
    )

    with pytest.raises(ValueError, match="must be a string list"):
        load_manifest(manifest_path)


def test_load_manifest_rejects_non_string_dependencies(tmp_path: Path) -> None:
    manifest_path = tmp_path / "smokes.yml"
    _write_manifest(
        manifest_path,
        {"first_job": {"arguments": [], "depends_on": [123]}},
    )

    with pytest.raises(ValueError, match="depends_on.*string list"):
        load_manifest(manifest_path)


def test_validate_manifest_dependencies_rejects_unknown_dependency() -> None:
    manifest = _manifest(("silver_orders", ["olist_orders"]))

    with pytest.raises(ValueError, match="unknown dependencies for silver_orders"):
        validate_manifest_dependencies(manifest)


def test_validate_manifest_dependencies_rejects_cycles() -> None:
    manifest = _manifest(("first", ["second"]), ("second", ["first"]))

    with pytest.raises(ValueError, match="cyclic smoke dependencies detected"):
        validate_manifest_dependencies(manifest)


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


def test_scheduler_runs_independent_jobs_in_parallel_and_waits_for_dependencies(
    tmp_path: Path,
) -> None:
    manifest = _manifest(
        ("bronze_orders", []),
        ("bronze_items", []),
        ("silver_orders", ["bronze_orders", "bronze_items"]),
    )
    lock = threading.Lock()
    active = 0
    max_active = 0
    completed: set[str] = set()
    silver_started_after: set[str] = set()

    def runner(command: list[str]) -> None:
        nonlocal active, max_active
        job_name = command[5]
        with lock:
            active += 1
            max_active = max(max_active, active)
            if job_name == "silver_orders":
                silver_started_after.update(completed)
        time.sleep(0.03)
        with lock:
            completed.add(job_name)
            active -= 1

    run_smokes(
        "stg",
        manifest,
        tmp_path / "results.txt",
        max_workers=2,
        command_runner=runner,
    )

    assert max_active == 2
    assert silver_started_after == {"bronze_orders", "bronze_items"}


def test_scheduler_blocks_dependency_closure_but_continues_unrelated_branch(
    tmp_path: Path,
) -> None:
    manifest = _manifest(
        ("bronze_orders", []),
        ("bronze_products", []),
        ("silver_orders", ["bronze_orders"]),
    )
    executed: list[str] = []

    def runner(command: list[str]) -> None:
        job_name = command[5]
        executed.append(job_name)
        if job_name == "bronze_orders":
            raise subprocess.CalledProcessError(1, command)

    results_path = tmp_path / "results.txt"
    with pytest.raises(RuntimeError, match="bronze_orders=FAILED"):
        run_smokes(
            "stg",
            manifest,
            results_path,
            max_workers=2,
            command_runner=runner,
        )

    assert "bronze_products" in executed
    assert "silver_orders" not in executed
    results = results_path.read_text(encoding="utf-8")
    assert "job=bronze_orders status=failed" in results
    assert "job=bronze_products status=success" in results
    assert "job=silver_orders status=blocked" in results


def test_scheduler_enforces_bounded_concurrency(tmp_path: Path) -> None:
    manifest = _manifest(
        ("first", []),
        ("second", []),
        ("third", []),
        ("fourth", []),
    )
    lock = threading.Lock()
    active = 0
    max_active = 0

    def runner(command: list[str]) -> None:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.03)
        with lock:
            active -= 1

    run_smokes(
        "stg",
        manifest,
        tmp_path / "results.txt",
        max_workers=2,
        command_runner=runner,
    )

    assert max_active == 2


def test_runtime_smoke_contracts_are_complete_and_bounded_to_2018() -> None:
    manifest = load_manifest()
    validate_manifest_dependencies(manifest)

    assert all(config["depends_on"] == [] for config in manifest.values())
    assert resolve_arguments("stg", manifest["ibge_municipality_gdp"]["arguments"]) == [
        "--target-table",
        "stg.bronze.ibge_municipality_gdp",
        "--execution-runs-table",
        "stg_admin.operations.execution_runs",
        "--quality-results-table",
        "stg_admin.quality.data_quality_results",
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
