"""Testes unitários isolados; não acessam catálogo de produção.

Executar no runtime PySpark: pytest -q tests/test_mock_table.py
Os testes usam uma SparkSession simulada (MagicMock) e não gravam tabelas.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytest.importorskip("pyspark")
from pyspark.sql.types import IntegerType, StringType, StructField, StructType  # noqa: E402

from mock_table import (  # noqa: E402
    AbstractMockContract,
    AbstractMockTable,
    ColumnSpec,
)


SRC = "sandbox_src.reference_data.people"
DEST = "sandbox_dev.synthetic_wks.people"
NAMESPACE = "sandbox_dev.synthetic_wks"
SRC_SCHEMA = StructType(
    [
        StructField("id", IntegerType(), False, {"comment": "Chave"}),
        StructField("name", StringType(), True, {"comment": "Nome de teste"}),
        StructField("other", StringType(), True),
    ]
)


class Contract(AbstractMockContract):
    source_table = SRC
    selected_columns = (ColumnSpec("id"), ColumnSpec("name"))
    primary_keys = ("id",)


class Table(AbstractMockTable):
    def __init__(self, spark):
        self._spark = spark
        super().__init__()

    def build_contract(self):
        return Contract(
            self._spark,
            target_namespace=NAMESPACE,
            allowed_target_namespaces=(NAMESPACE,),
        )


def fake_spark(*, target_exists=False):
    spark = MagicMock()
    source_df = MagicMock()
    source_df.schema = SRC_SCHEMA
    target_df = MagicMock()
    target_df.schema = StructType(SRC_SCHEMA.fields[:2])

    def get_table(name):
        return source_df if name == SRC else target_df

    spark.table.side_effect = get_table
    spark.catalog.getTable.return_value = SimpleNamespace(description="Origem")
    spark.catalog.tableExists.return_value = target_exists
    spark.sql.return_value.first.return_value = {
        "format": "delta",
        "properties": {"mock.synthetic": "true", "mock.source_table": SRC},
    }
    return spark


def test_contract_seleciona_apenas_duas_colunas_e_herda_comentarios():
    spark = fake_spark()
    c = Contract(spark, target_namespace=NAMESPACE, allowed_target_namespaces=(NAMESPACE,))
    meta = c.resolve()
    assert meta.columns == ("id", "name")
    assert meta.schema[0].nullable is False
    assert meta.schema[1].metadata["comment"] == "Nome de teste"
    assert meta.table_comment.startswith("[MOCK]")
    spark.table.assert_called_once_with(SRC)


def test_create_table_vazia_nao_escreve_origem_nem_dados():
    spark = fake_spark(target_exists=False)
    t = Table(spark)
    # Simula tabela criada, após primeira checagem de existência.
    spark.catalog.tableExists.side_effect = [False, True]
    assert t.create_table() is True
    ddl = spark.sql.call_args_list[0].args[0]
    assert "CREATE TABLE IF NOT EXISTS" in ddl
    assert "USING DELTA" in ddl
    assert "mock.synthetic" in ddl
    assert "`id` int NOT NULL" in ddl
    assert "`name` string COMMENT 'Nome de teste'" in ddl
    assert "`other`" not in ddl
    spark.table.assert_any_call(SRC)
    spark.table.assert_any_call(DEST)
    assert not spark.table(SRC).collect.called


def test_create_table_existente_nao_executa_ddl():
    spark = fake_spark(target_exists=True)
    Table(spark).create_table()
    assert all("CREATE TABLE" not in call.args[0] for call in spark.sql.call_args_list)


def test_bloqueia_schema_fora_de_wks():
    spark = fake_spark()
    with pytest.raises(ValueError, match="_wks"):
        Contract(
            spark,
            target_namespace="sandbox_src.reference_data",
            allowed_target_namespaces=("sandbox_src.reference_data",),
        )
    spark.table.assert_not_called()


def test_bloqueia_namespace_nao_autorizado():
    spark = fake_spark()
    with pytest.raises(PermissionError, match="allowlist"):
        Contract(
            spark,
            target_namespace="sandbox_dev.synthetic_wks",
            allowed_target_namespaces=("sandbox_qa.synthetic_wks",),
        )


def test_drift_de_tipo_detectado_antes_da_criacao():
    class Drift(Contract):
        selected_columns = (ColumnSpec("id", expected_type=StringType()),)
        primary_keys = ("id",)

    spark = fake_spark()
    c = Drift(spark, target_namespace=NAMESPACE, allowed_target_namespaces=(NAMESPACE,))
    with pytest.raises(TypeError, match="Drift"):
        c.resolve()


def test_coluna_ausente_e_chave_ausente_falham():
    class Missing(Contract):
        selected_columns = ("not_here",)
        primary_keys = ()

    class BadKey(Contract):
        primary_keys = ("not_here",)

    spark = fake_spark()
    with pytest.raises(ValueError, match="inexistente"):
        Missing(spark, target_namespace=NAMESPACE, allowed_target_namespaces=(NAMESPACE,)).resolve()
    with pytest.raises(ValueError, match="chaves"):
        BadKey(spark, target_namespace=NAMESPACE, allowed_target_namespaces=(NAMESPACE,)).resolve()


def test_dataframe_invalido_nao_e_aceito():
    spark = fake_spark()
    t = Table(spark)
    from pyspark.sql import DataFrame
    wrong = MagicMock(spec=DataFrame)
    wrong.columns = ["id", "other"]
    with pytest.raises(ValueError, match="faltantes"):
        t.dataframe = wrong