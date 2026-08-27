from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

DEFAULT_MANIFEST = Path("deployment/smoke-jobs.yml")
DEFAULT_RESOURCES_DIR = Path("resources")
DEFAULT_RESULTS = Path("dist/deployment-smoke-results.txt")
JOB_KEY_PATTERN = re.compile(r"^    ([A-Za-z0-9_-]+):\s*$")


def load_manifest(
    path: Path = DEFAULT_MANIFEST,
) -> dict[str, dict[str, list[str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise ValueError("Smoke manifest must contain a non-empty 'jobs' mapping.")

    normalized: dict[str, dict[str, list[str]]] = {}
    for job_name, config in jobs.items():
        if not isinstance(job_name, str) or not job_name:
            raise ValueError("Smoke job names must be non-empty strings.")
        if not isinstance(config, dict):
            raise ValueError(f"Smoke config for {job_name} must be a mapping.")
        arguments = config.get("arguments", [])
        if not isinstance(arguments, list) or not all(
            isinstance(argument, str) for argument in arguments
        ):
            raise ValueError(f"Smoke arguments for {job_name} must be a string list.")
        normalized[job_name] = {"arguments": arguments}
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
    manifest: dict[str, dict[str, list[str]]],
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


def build_command(target: str, job_name: str, arguments: list[str]) -> list[str]:
    command = ["databricks", "bundle", "run", "-t", target, job_name]
    if arguments:
        command.extend(["--", *arguments])
    return command


def run_smokes(
    target: str,
    manifest: dict[str, dict[str, list[str]]],
    results_path: Path = DEFAULT_RESULTS,
) -> None:
    if target not in {"stg", "prd"}:
        raise ValueError("Deployment smoke target must be 'stg' or 'prd'.")

    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text("", encoding="utf-8")

    for job_name, config in manifest.items():
        arguments = config["arguments"]
        command = build_command(target, job_name, arguments)
        print(
            "Running deployment smoke: "
            f"target={target} job={job_name} arguments={arguments}"
        )
        subprocess.run(command, check=True)
        serialized_arguments = json.dumps(arguments)
        with results_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"target={target} job={job_name} status=success "
                f"arguments={serialized_arguments}\n"
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    validate_manifest_coverage(manifest, args.resources_dir)
    print(f"Deployment smoke coverage valid for {len(manifest)} DAB jobs.")

    if args.validate_only:
        return
    if args.target is None:
        raise SystemExit("--target is required unless --validate-only is used.")
    run_smokes(args.target, manifest, args.results)


if __name__ == "__main__":
    main()
