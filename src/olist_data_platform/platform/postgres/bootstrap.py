from pathlib import Path

from .client import PostgresClient


def discover_sql_scripts(sql_dir: str | Path) -> list[Path]:
    directory = Path(sql_dir)
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    scripts = sorted(directory.glob("*.sql"))
    if not scripts:
        raise FileNotFoundError(f"No SQL scripts found in: {directory}")
    return scripts


def run_sql_bootstrap(client: PostgresClient, sql_dir: str | Path) -> list[str]:
    scripts = discover_sql_scripts(sql_dir)
    applied: list[str] = []

    with client.connection() as connection:
        with connection.cursor() as cursor:
            for script in scripts:
                cursor.execute(script.read_text(encoding="utf-8"))
                applied.append(script.name)

    return applied
