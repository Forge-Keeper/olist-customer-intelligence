from __future__ import annotations

from pathlib import Path

import pytest

from scripts import build_bundle_artifact


def _configure_dist(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    monkeypatch.setattr(build_bundle_artifact, "DIST_DIR", dist_dir)
    return dist_dir


def test_normal_build_removes_stale_wheels_before_building(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dist_dir = _configure_dist(monkeypatch, tmp_path)
    stale = dist_dir / "stale.whl"
    stale.write_text("stale", encoding="utf-8")
    monkeypatch.delenv(build_bundle_artifact.PREBUILT_ENV, raising=False)

    def fake_run(command: list[str], *, check: bool) -> None:
        assert command == ["uv", "build", "--wheel"]
        assert check is True
        assert not stale.exists()
        (dist_dir / "fresh.whl").write_text("fresh", encoding="utf-8")

    monkeypatch.setattr(build_bundle_artifact.subprocess, "run", fake_run)

    build_bundle_artifact.main()

    assert [path.name for path in dist_dir.glob("*.whl")] == ["fresh.whl"]


def test_normal_build_rejects_multiple_generated_wheels(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dist_dir = _configure_dist(monkeypatch, tmp_path)
    monkeypatch.delenv(build_bundle_artifact.PREBUILT_ENV, raising=False)

    def fake_run(command: list[str], *, check: bool) -> None:
        assert command == ["uv", "build", "--wheel"]
        assert check is True
        (dist_dir / "first.whl").write_text("first", encoding="utf-8")
        (dist_dir / "second.whl").write_text("second", encoding="utf-8")

    monkeypatch.setattr(build_bundle_artifact.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="exactly one wheel"):
        build_bundle_artifact.main()


def test_prebuilt_promotion_reuses_single_wheel_without_rebuilding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dist_dir = _configure_dist(monkeypatch, tmp_path)
    approved = dist_dir / "approved.whl"
    approved.write_text("approved", encoding="utf-8")
    monkeypatch.setenv(build_bundle_artifact.PREBUILT_ENV, "1")

    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("prebuilt promotion must not rebuild the wheel")

    monkeypatch.setattr(build_bundle_artifact.subprocess, "run", fail_if_called)

    build_bundle_artifact.main()

    assert approved.exists()


def test_prebuilt_promotion_requires_exactly_one_wheel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dist_dir = _configure_dist(monkeypatch, tmp_path)
    (dist_dir / "first.whl").write_text("first", encoding="utf-8")
    (dist_dir / "second.whl").write_text("second", encoding="utf-8")
    monkeypatch.setenv(build_bundle_artifact.PREBUILT_ENV, "1")

    with pytest.raises(RuntimeError, match="exactly one prebuilt wheel"):
        build_bundle_artifact.main()
