"""Build or reuse the wheel consumed by Databricks Asset Bundles.

Normal developer and staging deployments build a fresh wheel with ``uv``. Production
promotion may set ``DATABRICKS_BUNDLE_USE_PREBUILT_WHEEL=1`` to require that the
already-approved staging wheel is present in ``dist`` and reuse it unchanged.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

PREBUILT_ENV = "DATABRICKS_BUNDLE_USE_PREBUILT_WHEEL"
DIST_DIR = Path("dist")


def _existing_wheels() -> list[Path]:
    """Return wheel artifacts currently available in ``dist``."""
    return sorted(DIST_DIR.glob("*.whl"))


def main() -> None:
    """Build a wheel normally or require one prebuilt wheel for promotion."""
    if os.getenv(PREBUILT_ENV) == "1":
        wheels = _existing_wheels()
        if len(wheels) != 1:
            raise RuntimeError(
                "Production promotion requires exactly one prebuilt wheel in dist; "
                f"found {len(wheels)}."
            )
        print(f"Reusing approved prebuilt wheel: {wheels[0]}")
        return

    subprocess.run(["uv", "build", "--wheel"], check=True)


if __name__ == "__main__":
    main()
