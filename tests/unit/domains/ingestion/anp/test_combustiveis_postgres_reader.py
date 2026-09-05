from datetime import date

import pytest

from olist_data_platform.domains.ingestion.anp import AnpCombustiveisReadRequest


def test_anp_read_request_accepts_bounded_interval() -> None:
    request = AnpCombustiveisReadRequest(
        start_date=date(2016, 1, 4),
        end_date=date(2016, 6, 30),
    )

    assert request.start_date == date(2016, 1, 4)
    assert request.end_date == date(2016, 6, 30)


def test_anp_read_request_rejects_inverted_interval() -> None:
    with pytest.raises(ValueError, match="start_date cannot be after end_date"):
        AnpCombustiveisReadRequest(
            start_date=date(2016, 6, 30),
            end_date=date(2016, 1, 4),
        )
