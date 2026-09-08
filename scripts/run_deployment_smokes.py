from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path

DEFAULT_MANIFEST = Path("deployment/smoke-jobs.yml")
DEFAULT_RESOURCES_DIR = Path("resources")
DEFAULT_RESULTS = Path("dist/deployment-smoke-results.txt")
DEFAULT_MAX_WORKERS = 4
JOB_KEY_PATTERN = re.compile(r"^    ([A-Za-z0-9_-]+):\s*$")
TARGET_PLACEHOLDER = "${target}"
TERMINAL_FAILURE_STATES = {"FAILED", "BLOCKED"}

SmokeConfig = dict[str, list[str]]
SmokeManifest = dict[str, SmokeConfig]
CommandRunner = Callable[[list[str]], object]


def load_manifest(
    path: Path = DEFAULT_MANIFEST,
) -> SmokeManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise ValueError("Smoke manifest must contain a non-empty 'jobs' mapping.")

    normalized: SmokeManifest = {}
    for job_name, config in jobs.items():
        if not isinstance(job_name, str) or not job_name:
            raise ValueError("Smoke job names must be non-empty strings.")
        if not isinstance(config, dict):
            raise ValueError(f"Smoke config for {job_name} must be a mapping.")

        arguments = config.get("arguments", [])
        depends_on = config.get("depends_on", [])
        for field_name, value in (
            ("arguments", arguments),
            ("depends_on", depends_on),
        ):
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ValueError(
                    f"Smoke {field_name} for {job_name} must be a string list."
                )

        if len(depends_on) != len(set(depends_on)):
            raise ValueError(f"Smoke dependencies for {job_name} must be unique.")

        normalized[job_name] = {
            "arguments": arguments,
            "depends_on": depends_on,
        }
    return normalized


def discover_dab_jobs(resources_dir: Path = DEFAULT_RESOURCES_DIR) -> set[str]:
    jobs: set[str] = set()
    for path in sorted(resources_dir.glob("*.job.yml")):
        in_jobs = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line == "  jobs:":
                in_jobs = True
                continue
            if in_jobs:
                match = JOB_KEY_PATTERN.match(line)
                if match:
                    jobs.add(match.group(1))
                    break
    return jobs


def validate_manifest_coverage(
    manifest: SmokeManifest,
    resources_dir: Path = DEFAULT_RESOURCES_DIR,
) -> None:
    declared_jobs = discover_dab_jobs(resources_dir)
    smoke_jobs = set(manifest)

    missing = sorted(declared_jobs - smoke_jobs)
    extra = sorted(smoke_jobs - declared_jobs)
    problems: list[str] = []
    if missing:
        problems.append(f"missing smoke contracts: {', '.join(missing)}")
    if extra:
        problems.append(f"unknown smoke contracts: {', '.join(extra)}")
    if problems:
        raise ValueError("; ".join(problems))


def validate_manifest_dependencies(manifest: SmokeManifest) -> None:
    job_names = set(manifest)
    for job_name, config in manifest.items():
        unknown = sorted(set(config["depends_on"]) - job_names)
        if unknown:
            raise ValueError(
                f"unknown dependencies for {job_name}: {', '.join(unknown)}"
            )

    indegree = {
        job_name: len(config["depends_on"])
        for job_name, config in manifest.items()
    }
    downstream: dict[str, list[str]] = {job_name: [] for job_name in manifest}
    for job_name, config in manifest.items():
        for dependency in config["depends_on"]:
            downstream[dependency].append(job_name)

    ready = [job_name for job_name, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        job_name = ready.pop()
        visited += 1
        for child in downstream[job_name]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if visited != len(manifest):
        cyclic = sorted(job_name for job_name, degree in indegree.items() if degree > 0)
        raise ValueError(f"cyclic smoke dependencies detected: {', '.join(cyclic)}")


def resolve_arguments(target: str, arguments: list[str]) -> list[str]:
    return [argument.replace(TARGET_PLACEHOLDER, target) for argument in arguments]


def build_command(target: str, job_name: str, arguments: list[str]) -> list[str]:
    resolved_arguments = resolve_arguments(target, arguments)
    command = ["databricks", "bundle", "run", "-t", target, job_name]
    if resolved_arguments:
        command.extend(["--", *resolved_arguments])
    return command


def _default_command_runner(command: list[str]) -> object:
    return subprocess.run(command, check=True)


def _propagate_blocked(
    manifest: SmokeManifest,
    statuses: dict[str, str],
) -> None:
    changed = True
    while changed:
        changed = False
        for job_name, config in manifest.items():
            if statuses[job_name] != "PENDING":
                continue
            dependency_states = [statuses[name] for name in config["depends_on"]]
            if any(state in TERMINAL_FAILURE_STATES for state in dependency_states):
                statuses[job_name] = "BLOCKED"
                changed = True


def _write_results(
    results_path: Path,
    target: str,
    manifest: SmokeManifest,
    statuses: dict[str, str],
) -> None:
    lines = []
    for job_name, config in manifest.items():
        arguments = resolve_arguments(target, config["arguments"])
        serialized_arguments = json.dumps(arguments)
        lines.append(
            f"target={target} job={job_name} status={statuses[job_name].lower()} "
            f"arguments={serialized_arguments}\n"
        )
    results_path.write_text("".join(lines), encoding="utf-8")


def run_smokes(
    target: str,
    manifest: SmokeManifest,
    results_path: Path = DEFAULT_RESULTS,
    *,
    max_workers: int = DEFAULT_MAX_WORKERS,
    command_runner: CommandRunner = _default_command_runner,
) -> None:
    if target not in {"stg", "prd"}:
        raise ValueError("Deployment smoke target must be 'stg' or 'prd'.")
    if max_workers < 1:
        raise ValueError("max_workers must be at least 1.")

    validate_manifest_dependencies(manifest)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    statuses = {job_name: "PENDING" for job_name in manifest}
    running: dict[Future[object], str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while any(status == "PENDING" for status in statuses.values()) or running:
            _propagate_blocked(manifest, statuses)

            available_slots = max_workers - len(running)
            if available_slots > 0:
                ready_jobs = [
                    job_name
                    for job_name, config in manifest.items()
                    if statuses[job_name] == "PENDING"
                    and all(
                        statuses[name] == "SUCCESS"
                        for name in config["depends_on"]
                    )
                ]
                for job_name in ready_jobs[:available_slots]:
                    config = manifest[job_name]
                    arguments = resolve_arguments(target, config["arguments"])
                    command = build_command(target, job_name, config["arguments"])
                    print(
                        "Running deployment smoke: "
                        f"target={target} job={job_name} arguments={arguments}"
                    )
                    statuses[job_name] = "RUNNING"
                    future = executor.submit(command_runner, command)
                    running[future] = job_name

            if not running:
                pending = [
                    job_name
                    for job_name, status in statuses.items()
                    if status == "PENDING"
                ]
                if pending:
                    pending_jobs = ", ".join(pending)
                    raise RuntimeError(
                        f"Smoke scheduler stalled with pending jobs: {pending_jobs}"
                    )
                break

            completed, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in completed:
                job_name = running.pop(future)
                try:
                    future.result()
                except Exception as exc:
                    statuses[job_name] = "FAILED"
                    print(f"Deployment smoke failed: job={job_name} error={exc}")
                else:
                    statuses[job_name] = "SUCCESS"

    _write_results(results_path, target, manifest, statuses)

    failures = [
        f"{job_name}={status}"
        for job_name, status in statuses.items()
        if status in TERMINAL_FAILURE_STATES
    ]
    if failures:
        failure_summary = ", ".join(failures)
        raise RuntimeError(
            f"Deployment smokes did not fully succeed: {failure_summary}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and execute DAB deployment smoke contracts."
    )
    parser.add_argument("--target", choices=("stg", "prd"))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--resources-dir", type=Path, default=DEFAULT_RESOURCES_DIR)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    validate_manifest_coverage(manifest, args.resources_dir)
    validate_manifest_dependencies(manifest)
    print(f"Deployment smoke coverage valid for {len(manifest)} DAB jobs.")

    if args.validate_only:
        return
    if args.target is None:
        raise SystemExit("--target is required unless --validate-only is used.")
    run_smokes(
        args.target,
        manifest,
        args.results,
        max_workers=args.max_workers,
    )


if __name__ == "__main__":
    main()
