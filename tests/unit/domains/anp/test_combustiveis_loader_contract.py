from pathlib import Path
from unittest.mock import MagicMock

import pytest

from olist_data_platform.domains.anp.ingestion.combustiveis_loader import (
    AnpCombustiveisLoader,
)


def test_anp_loader_rejects_missing_source_file(tmp_path: Path) -> None:
    loader = AnpCombustiveisLoader(MagicMock())

    with pytest.raises(FileNotFoundError):
        loader.load(tmp_path / "missing.csv")
