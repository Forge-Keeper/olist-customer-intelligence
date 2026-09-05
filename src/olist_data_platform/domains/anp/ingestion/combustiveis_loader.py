from dataclasses import dataclass
from pathlib import Path

from psycopg.sql import SQL

from olist_data_platform.platform.postgres import PostgresClient
from olist_data_platform.platform.postgres.file_hash import sha256_file


@dataclass(frozen=True, slots=True)
class LoadResult:
    source_file: str
    file_hash: str
    row_count: int
    skipped: bool


class AnpCombustiveisLoader:
    def __init__(self, client: PostgresClient) -> None:
        self._client = client

    def load(self, path: str | Path) -> LoadResult:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        file_hash = sha256_file(file_path)

        with self._client.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    SQL(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM platform.ingestion_control
                            WHERE file_hash = %s
                              AND status = 'SUCCESS'
                        )
                        """
                    ),
                    (file_hash,),
                )
                already_loaded_row = cursor.fetchone()
                if already_loaded_row and already_loaded_row[0]:
                    return LoadResult(
                        source_file=file_path.name,
                        file_hash=file_hash,
                        row_count=0,
                        skipped=True,
                    )

                cursor.execute(
                    SQL(
                        """
                        CREATE TEMP TABLE anp_combustiveis_raw (
                            regiao_sigla TEXT,
                            estado_sigla TEXT,
                            municipio TEXT,
                            revenda TEXT,
                            cnpj_revenda TEXT,
                            nome_rua TEXT,
                            numero_rua TEXT,
                            complemento TEXT,
                            bairro TEXT,
                            cep TEXT,
                            produto TEXT,
                            data_coleta TEXT,
                            valor_venda TEXT,
                            valor_compra TEXT,
                            unidade_medida TEXT,
                            bandeira TEXT
                        ) ON COMMIT DROP
                        """
                    )
                )

                copy_sql = SQL(
                    """
                    COPY anp_combustiveis_raw (
                        regiao_sigla,
                        estado_sigla,
                        municipio,
                        revenda,
                        cnpj_revenda,
                        nome_rua,
                        numero_rua,
                        complemento,
                        bairro,
                        cep,
                        produto,
                        data_coleta,
                        valor_venda,
                        valor_compra,
                        unidade_medida,
                        bandeira
                    )
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        HEADER TRUE,
                        DELIMITER ';',
                        ENCODING 'UTF8'
                    )
                    """
                )

                with cursor.copy(copy_sql) as copy:
                    with file_path.open("rb") as source:
                        while chunk := source.read(1024 * 1024):
                            copy.write(chunk)

                cursor.execute(SQL("SELECT COUNT(*) FROM anp_combustiveis_raw"))
                row_count_row = cursor.fetchone()
                if row_count_row is None:
                    raise RuntimeError("Could not count staged ANP rows")
                row_count = int(row_count_row[0])

                cursor.execute(
                    SQL(
                        """
                        INSERT INTO anp.combustiveis_precos (
                            regiao_sigla,
                            estado_sigla,
                            municipio,
                            revenda,
                            cnpj_revenda,
                            nome_rua,
                            numero_rua,
                            complemento,
                            bairro,
                            cep,
                            produto,
                            data_coleta,
                            valor_venda,
                            valor_compra,
                            unidade_medida,
                            bandeira,
                            source_file
                        )
                        SELECT
                            regiao_sigla,
                            estado_sigla,
                            municipio,
                            revenda,
                            cnpj_revenda,
                            nome_rua,
                            numero_rua,
                            NULLIF(complemento, ''),
                            bairro,
                            cep,
                            produto,
                            TO_DATE(data_coleta, 'DD/MM/YYYY'),
                            REPLACE(valor_venda, ',', '.')::NUMERIC,
                            NULLIF(REPLACE(valor_compra, ',', '.'), '')::NUMERIC,
                            unidade_medida,
                            bandeira,
                            %s
                        FROM anp_combustiveis_raw
                        """
                    ),
                    (file_path.name,),
                )

                cursor.execute(
                    SQL(
                        """
                        INSERT INTO platform.ingestion_control (
                            source_file,
                            file_hash,
                            row_count,
                            status
                        )
                        VALUES (%s, %s, %s, 'SUCCESS')
                        """
                    ),
                    (file_path.name, file_hash, row_count),
                )

        return LoadResult(
            source_file=file_path.name,
            file_hash=file_hash,
            row_count=row_count,
            skipped=False,
        )
