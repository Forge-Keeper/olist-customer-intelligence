"""ACRESCENTAR ao tabelas.py existente; manter as seis tabelas de massa.
As tabelas operacionais são criadas vazias e nunca recebem merge no setup.
"""
import json
from pathlib import Path
from pyspark.sql.types import StructType
from contratos import ContratoOperacional, schema_com_alcada, validar_sem_nulltype
from mock_table import AbstractMockTable


class TabelaOperacional(AbstractMockTable):
    def __init__(self, spark, *, target_namespace, allowed_target_namespaces,
                 target_table_name, source_table, schema):
        contrato = ContratoOperacional(
            spark,
            target_namespace=target_namespace,
            allowed_target_namespaces=allowed_target_namespaces,
            target_table_name=target_table_name,
            source_table=source_table,
            schema=schema,
        )
        super().__init__(contract=contrato)


def criar_tabelas_operacionais(spark, *, namespace, allowlist, arquivo_schemas):
    """Cria somente destinos explicitamente registrados no manifesto.
    Se já existirem, valida; não trunca, não restaura e não migra schemas.
    """
    manifesto = json.loads(Path(arquivo_schemas).read_text(encoding="utf-8"))
    tabelas = []
    for nome, spec in manifesto.items():
        schema = StructType.fromJson(spec["schema"])
        layout = spec["layout"]
        if layout in ("raw", "flat"):
            schema = schema_com_alcada(schema, layout=layout)
        elif layout != "plain":
            raise ValueError(f"Layout inválido para {nome}: {layout}")
        validar_sem_nulltype(schema)
        tabelas.append(TabelaOperacional(
            spark, target_namespace=namespace,
            allowed_target_namespaces=allowlist,
            target_table_name=nome, source_table=spec["referencia"], schema=schema,
        ))
    # Validar as tabelas existentes antes de executar qualquer CREATE.
    for tabela in tabelas:
        if tabela.table_exists():
            tabela.validate_destination()
    for tabela in tabelas:
        tabela.create_table()
    return tabelas
