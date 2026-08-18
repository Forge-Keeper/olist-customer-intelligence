import argparse
from pathlib import Path

from olist_data_platform.platform.postgres import PostgresClient, PostgresConfig
from olist_data_platform.platform.postgres.bootstrap import run_sql_bootstrap

DEFAULT_SQL_DIR = Path("infra/postgres/init")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply PostgreSQL bootstrap SQL scripts in lexical order."
    )
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR)
    return parser


def run(args: argparse.Namespace) -> list[str]:
    client = PostgresClient(PostgresConfig.from_env())
    return run_sql_bootstrap(client=client, sql_dir=args.sql_dir)


def main() -> None:
    args = build_parser().parse_args()
    applied = run(args)
    print(
        "postgres_bootstrap_completed "
        f"database={PostgresConfig.from_env().database} "
        f"scripts={','.join(applied)}"
    )


if __name__ == "__main__":
    main()
