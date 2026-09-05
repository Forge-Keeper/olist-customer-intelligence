import argparse
from datetime import date

import pytest

from olist_data_platform.jobs.anp_combustiveis_bronze_ingestion import (
    _build_replace_where_predicate,
    _parse_date,
    build_parser,
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


def test_parser_accepts_databricks_runtime_jdbc_configuration() -> None:
    args = build_parser().parse_args(
        [
            "--start-date",
            "2016-01-04",
            "--end-date",
            "2016-06-30",
            "--target-table",
            "dev.bronze.anp_combustiveis_precos",
            "--jdbc-host",
            "pg-olist-ci-dev.postgres.database.azure.com",
            "--jdbc-database",
            "olist",
        ]
    )

    assert args.jdbc_host == "pg-olist-ci-dev.postgres.database.azure.com"
    assert args.jdbc_database == "olist"
    assert args.jdbc_port == 5432
    assert args.jdbc_sslmode == "require"
    assert args.jdbc_secret_scope == "olist-jdbc"
    assert args.jdbc_user_secret_key == "username"
    assert args.jdbc_password_secret_key == "password"
