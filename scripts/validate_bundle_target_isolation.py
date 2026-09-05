from __future__ import annotations

import json
import subprocess
from typing import Any

ANP_JOB_KEY = "anp_combustiveis"
TARGETS = ("dev", "stg", "prd")


def _resolved_bundle(target: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["databricks", "bundle", "validate", "-t", target, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _job_keys(bundle: dict[str, Any]) -> set[str]:
    resources = bundle.get("resources", {})
    jobs = resources.get("jobs", {})
    return set(jobs)


def main() -> None:
    jobs_by_target = {target: _job_keys(_resolved_bundle(target)) for target in TARGETS}

    if ANP_JOB_KEY not in jobs_by_target["dev"]:
        raise ValueError(f"{ANP_JOB_KEY} must resolve in DEV bundle resources")

    leaking_targets = [
        target
        for target in ("stg", "prd")
        if ANP_JOB_KEY in jobs_by_target[target]
    ]
    if leaking_targets:
        joined = ", ".join(leaking_targets)
        raise ValueError(f"{ANP_JOB_KEY} must remain DEV-only; found in: {joined}")

    print(
        "ANP bundle target isolation OK: "
        "present in dev and absent from stg/prd resolved resources."
    )


if __name__ == "__main__":
    main()
