from pathlib import Path
from unittest.mock import MagicMock

import pytest
from psycopg.sql import Composable

from olist_data_platform.domains.anp.ingestion.combustiveis_loader import (
    AnpCombustiveisLoader,
    LoadResult,
)
from olist_data_platform.platform.postgres.file_hash import sha256_file


def _sql_text(value: object) -> str:
    assert isinstance(value, Composable)
    return " ".join(value.as_string().split())


def _configure_db(client: MagicMock) -> tuple[MagicMock, MagicMock, MagicMock]:
    connection = MagicMock()
    cursor = MagicMock()
    copy = MagicMock()

    client.connection.return_value.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.copy.return_value.__enter__.return_value = copy

    return connection, cursor, copy


def _write_source(tmp_path: Path) -> tuple[Path, bytes]:
    payload = (
        b"Regiao - Sigla;Estado - Sigla;Municipio;Revenda;CNPJ da Revenda;"
        b"Nome da Rua;Numero Rua;Complemento;Bairro;Cep;Produto;Data da Coleta;"
        b"Valor de Venda;Valor de Compra;Unidade de Medida;Bandeira\n"
        b"S;SC;Florianopolis;Posto Teste;00.000.000/0001-00;Rua Teste;1;;Centro;"
        b"88000-000;GASOLINA;17/09/2026;6,19;;R$ / litro;BRANCA\n"
    )
    source = tmp_path / "anp.csv"
    source.write_bytes(payload)
    return source, payload


def test_anp_loader_rejects_missing_source_file(tmp_path: Path) -> None:
    loader = AnpCombustiveisLoader(MagicMock())

    with pytest.raises(FileNotFoundError):
        loader.load(tmp_path / "missing.csv")


def test_anp_loader_skips_hash_already_loaded_successfully(tmp_path: Path) -> None:
    source, _ = _write_source(tmp_path)
    expected_hash = sha256_file(source)
    client = MagicMock()
    _, cursor, _ = _configure_db(client)
    cursor.fetchone.return_value = (True,)

    result = AnpCombustiveisLoader(client).load(source)

    assert result == LoadResult(
        source_file=source.name,
        file_hash=expected_hash,
        row_count=0,
        skipped=True,
    )
    assert cursor.execute.call_count == 1
    query, params = cursor.execute.call_args.args
    query_text = _sql_text(query)
    assert "SELECT EXISTS" in query_text
    assert "FROM platform.ingestion_control" in query_text
    assert "status = 'SUCCESS'" in query_text
    assert params == (expected_hash,)
    cursor.copy.assert_not_called()


def test_anp_loader_loads_new_hash_and_records_success(tmp_path: Path) -> None:
    source, payload = _write_source(tmp_path)
    expected_hash = sha256_file(source)
    client = MagicMock()
    _, cursor, copy = _configure_db(client)
    cursor.fetchone.side_effect = [(False,), (1,)]

    result = AnpCombustiveisLoader(client).load(source)

    assert result == LoadResult(
        source_file=source.name,
        file_hash=expected_hash,
        row_count=1,
        skipped=False,
    )

    execute_calls = cursor.execute.call_args_list
    assert len(execute_calls) == 5
    query_texts = [_sql_text(call.args[0]) for call in execute_calls]
    assert "SELECT EXISTS" in query_texts[0]
    assert "CREATE TEMP TABLE anp_combustiveis_raw" in query_texts[1]
    assert query_texts[2] == "SELECT COUNT(*) FROM anp_combustiveis_raw"
    assert "INSERT INTO anp.combustiveis_precos" in query_texts[3]
    assert "INSERT INTO platform.ingestion_control" in query_texts[4]
    assert "'SUCCESS'" in query_texts[4]

    assert execute_calls[0].args[1] == (expected_hash,)
    assert execute_calls[3].args[1] == (source.name,)
    assert execute_calls[4].args[1] == (source.name, expected_hash, 1)

    cursor.copy.assert_called_once()
    copy_query = cursor.copy.call_args.args[0]
    assert "COPY anp_combustiveis_raw" in _sql_text(copy_query)
    copy.write.assert_called_once_with(payload)


def test_anp_loader_row_count_failure_does_not_record_success(tmp_path: Path) -> None:
    source, _ = _write_source(tmp_path)
    client = MagicMock()
    _, cursor, _ = _configure_db(client)
    cursor.fetchone.side_effect = [(False,), None]

    with pytest.raises(RuntimeError, match="Could not count staged ANP rows"):
        AnpCombustiveisLoader(client).load(source)

    execute_calls = cursor.execute.call_args_list
    assert len(execute_calls) == 3
    query_texts = [_sql_text(call.args[0]) for call in execute_calls]
    assert "CREATE TEMP TABLE anp_combustiveis_raw" in query_texts[1]
    assert query_texts[2] == "SELECT COUNT(*) FROM anp_combustiveis_raw"
    assert not any(
        "INSERT INTO anp.combustiveis_precos" in query for query in query_texts
    )
    assert not any(
        "INSERT INTO platform.ingestion_control" in query for query in query_texts
    )


def test_anp_loader_business_insert_failure_does_not_record_success(
    tmp_path: Path,
) -> None:
    source, _ = _write_source(tmp_path)
    client = MagicMock()
    _, cursor, _ = _configure_db(client)
    cursor.fetchone.side_effect = [(False,), (1,)]
    cursor.execute.side_effect = [None, None, None, RuntimeError("insert failed")]

    with pytest.raises(RuntimeError, match="insert failed"):
        AnpCombustiveisLoader(client).load(source)

    execute_calls = cursor.execute.call_args_list
    assert len(execute_calls) == 4
    query_texts = [_sql_text(call.args[0]) for call in execute_calls]
    assert "INSERT INTO anp.combustiveis_precos" in query_texts[3]
    assert not any(
        "INSERT INTO platform.ingestion_control" in query for query in query_texts
    )
