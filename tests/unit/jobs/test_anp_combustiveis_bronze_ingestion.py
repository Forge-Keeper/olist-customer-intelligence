import argparse
from datetime import date

import pytest

from olist_data_platform.jobs.anp_combustiveis_bronze_ingestion import (
    _build_replace_where_predicate,
    _parse_date,
)


def test_parse_date_accepts_iso_date() -> None:
    assert _parse_date("2016-01-04") == date(2016, 1, 4)


def test_parse_date_rejects_invalid_value() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="Expected YYYY-MM-DD"):
        _parse_date("04/01/2016")


def test_replace_where_predicate_matches_requested_interval() -> None:
    predicate = _build_replace_where_predicate(
        start_date=date(2016, 1, 4),
        end_date=date(2016, 6, 30),
    )

    assert predicate == (
        "dt_base >= DATE '2016-01-04' "
        "AND dt_base <= DATE '2016-06-30'"
    )
