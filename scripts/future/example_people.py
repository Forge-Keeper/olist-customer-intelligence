"""Exemplo para Databricks; NÃO executa gravação quando importado.

Ajuste nomes, colunas e chaves conforme o schema efetivo no Unity Catalog.
Uso sugerido: importar após instalar/colar mock_table.py no workspace.
"""

from pyspark.sql import SparkSession
from mock_table import AbstractMockContract, AbstractMockTable, ColumnSpec


class PeopleContract(AbstractMockContract):
    # Fonte de exemplo: consulta apenas schema/metadados, NUNCA registros.
    source_table = "sandbox_src.reference_data.people"

    # Os campos abaixo são ilustrativos; os tipos serão herdados
    # diretamente da origem. A chave precisa ser confirmada no projeto.
    selected_columns = (
        ColumnSpec("id"),
        ColumnSpec("is_valid"),
        ColumnSpec("category"),
        ColumnSpec("status"),
    )

    # ATENÇÃO: confirme a existência/semântica das colunas e a chave no UC.
    primary_keys = ("id",)  # EXEMPLO; validar a chave efetiva!
    table_comment = "Massa sintética para testes de pessoas."


class MockPeople(AbstractMockTable):
    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark
        super().__init__()

    def build_contract(self) -> AbstractMockContract:
        return PeopleContract(
            self._spark,
            target_namespace="sandbox_dev.synthetic_wks",
            allowed_target_namespaces=("sandbox_dev.synthetic_wks",),
        )


# No notebook Databricks, depois de confirmar colunas, tipos, chaves e destino:
# pj = MockPeople(spark)
# pj.create_table()                 # cria vazia (idempotente)
# pj.add_rows([{...}])              # prepara dados em memória
# pj.validate()                     # tipos, nulos, duplicidade
# pj.merge()                        # persiste (upsert por chave)
# display(pj.read())                # consulta SOMENTE a tabela _wks