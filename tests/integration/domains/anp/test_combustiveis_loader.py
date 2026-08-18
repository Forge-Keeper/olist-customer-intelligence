import os
from decimal import Decimal

import pytest
from psycopg import DataError
from psycopg.sql import SQL

from olist_data_platform.domains.anp.ingestion.combustiveis_loader import (
    AnpCombustiveisLoader,
)
from olist_data_platform.platform.postgres import PostgresClient, PostgresConfig

CSV_HEADER = (
    "Regiao - Sigla;Estado - Sigla;Municipio;Revenda;CNPJ da Revenda;"
    "Nome da Rua;Numero Rua;Complemento;Bairro;Cep;Produto;Data da Coleta;"
    "Valor de Venda;Valor de Compra;Unidade de Medida;Bandeira"
)
CSV_ROW_1 = (
    "SE;SP;SAO PAULO;POSTO A; 00.000.000/0001-00;RUA A;10;;CENTRO;01000-000;"
    "GASOLINA;04/01/2016;3,499;;R$ / litro;BRANCA"
)
CSV_ROW_2 = (
    "SE;RJ;RIO DE JANEIRO;POSTO B; 11.111.111/0001-11;RUA B;20;LOJA 1;CENTRO;"
    "20000-000;ETANOL;05/01/2016;2,799;2,100;R$ / litro;BANDEIRA B"
)
CSV_CONTENT = "\n".join((CSV_HEADER, CSV_ROW_1, CSV_ROW_2, ""))


def _postgres_client() -> PostgresClient:
    required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing PostgreSQL environment variables: {', '.join(missing)}")
    return PostgresClient(PostgresConfig.from_env())


def _cleanup(client: PostgresClient, source_file: str) -> None:
    with client.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                SQL("DELETE FROM platform.ingestion_control WHERE source_file = %s"),
                (source_file,),
            )
            cursor.execute(
                SQL(
                    """
                    DELETE FROM anp.combustiveis_precos
                    WHERE cnpj_revenda IN (
                        ' 00.000.000/0001-00',
                        ' 11.111.111/0001-11'
                    )
                    """
                )
            )


@pytest.mark.integration
def test_loader_copies_converts_and_skips_same_file(tmp_path) -> None:
    client = _postgres_client()
    loader = AnpCombustiveisLoader(client)
    csv_path = tmp_path / "anp-integration.csv"
    csv_path.write_text(CSV_CONTENT, encoding="utf-8")

    _cleanup(client, csv_path.name)
    try:
        result = loader.load(csv_path)

        assert result.skipped is False
        assert result.row_count == 2

        with client.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    SQL(
                        """
                        SELECT
                            cnpj_revenda,
                            data_coleta,
                            valor_venda,
                            valor_compra,
                            complemento
                        FROM anp.combustiveis_precos
                        WHERE cnpj_revenda IN (
                            ' 00.000.000/0001-00',
                            ' 11.111.111/0001-11'
                        )
                        ORDER BY cnpj_revenda
                        """
                    )
                )
                rows = cursor.fetchall()

                cursor.execute(
                    SQL(
                        """
                        SELECT row_count, status
                        FROM platform.ingestion_control
                        WHERE source_file = %s
                        """
                    ),
                    (csv_path.name,),
                )
                control = cursor.fetchone()

        assert len(rows) == 2
        assert rows[0][1].isoformat() == "2016-01-04"
        assert rows[0][2] == Decimal("3.499")
        assert rows[0][3] is None
        assert rows[0][4] is None
        assert rows[1][1].isoformat() == "2016-01-05"
        assert rows[1][2] == Decimal("2.799")
        assert rows[1][3] == Decimal("2.100")
        assert rows[1][4] == "LOJA 1"
        assert control == (2, "SUCCESS")

        skipped = loader.load(csv_path)
        assert skipped.skipped is True
        assert skipped.row_count == 0

        with client.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    SQL(
                        """
                        SELECT COUNT(*)
                        FROM anp.combustiveis_precos
                        WHERE cnpj_revenda IN (
                            ' 00.000.000/0001-00',
                            ' 11.111.111/0001-11'
                        )
                        """
                    )
                )
                count = cursor.fetchone()

        assert count == (2,)
    finally:
        _cleanup(client, csv_path.name)


@pytest.mark.integration
def test_loader_rolls_back_when_conversion_fails(tmp_path) -> None:
    client = _postgres_client()
    loader = AnpCombustiveisLoader(client)
    csv_path = tmp_path / "anp-invalid-integration.csv"
    csv_path.write_text(
        CSV_CONTENT.replace("3,499", "not-a-number"),
        encoding="utf-8",
    )

    _cleanup(client, csv_path.name)
    try:
        with pytest.raises(DataError):
            loader.load(csv_path)

        with client.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    SQL(
                        """
                        SELECT COUNT(*)
                        FROM anp.combustiveis_precos
                        WHERE cnpj_revenda IN (
                            ' 00.000.000/0001-00',
                            ' 11.111.111/0001-11'
                        )
                        """
                    )
                )
                target_count = cursor.fetchone()

                cursor.execute(
                    SQL(
                        """
                        SELECT COUNT(*)
                        FROM platform.ingestion_control
                        WHERE source_file = %s
                        """
                    ),
                    (csv_path.name,),
                )
                control_count = cursor.fetchone()

        assert target_count == (0,)
        assert control_count == (0,)
    finally:
        _cleanup(client, csv_path.name)
