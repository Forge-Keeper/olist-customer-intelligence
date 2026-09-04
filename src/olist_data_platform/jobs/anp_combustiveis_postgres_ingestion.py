import argparse

from olist_data_platform.domains.anp.ingestion.combustiveis_loader import (
    AnpCombustiveisLoader,
    LoadResult,
)
from olist_data_platform.platform.postgres import PostgresClient, PostgresConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load an ANP combustiveis CSV file into PostgreSQL."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the ANP combustiveis CSV file.",
    )
    return parser


def run(args: argparse.Namespace) -> LoadResult:
    config = PostgresConfig.from_env()
    client = PostgresClient(config)
    loader = AnpCombustiveisLoader(client)
    return loader.load(args.file)


def main() -> None:
    args = build_parser().parse_args()
    result = run(args)

    status = "skipped" if result.skipped else "loaded"
    print(
        "anp_combustiveis_postgres_ingestion_completed "
        f"status={status} "
        f"file={result.source_file} "
        f"rows={result.row_count} "
        f"hash={result.file_hash}"
    )


if __name__ == "__main__":
    main()
