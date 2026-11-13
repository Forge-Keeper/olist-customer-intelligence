"""Infraestrutura genérica de tabelas Delta sintéticas para testes E2E.

Referências arquiteturais: SAFRA (TableTask/DataTask) e OLIST
(DatasetContract/DeltaTableLifecycle). Não importa nenhum deles.

Requer Databricks + PySpark + Delta Lake, e privilégios de leitura de
metadados da origem e CREATE/MODIFY no schema ``*_wks`` de destino.

Invariantes:
- Origem: leitura EXCLUSIVA de metadados; não lê registros da origem.
- Destino: somente schema explicitamente informado e terminado em ``_wks``.
- Criar tabela não insere dados; nenhuma escrita ocorre na atribuição do DataFrame.
- Evolução de schema: somente adição explícita de colunas nullable.
- Nunca executa DROP TABLE, TRUNCATE, overwrite nem operações na origem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import reduce
from operator import or_
from typing import Any, Iterable, Mapping
import re

from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import DataType, StructField, StructType


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")


def _parts(name: str, *, count: int) -> tuple[str, ...]:
    """Aceita apenas identificadores UC simples; recusa SQL arbitrário."""
    if not isinstance(name, str):
        raise TypeError("O nome do objeto deve ser uma string.")
    parts = tuple(name.split("."))
    if len(parts) != count or not all(_IDENTIFIER.fullmatch(p) for p in parts):
        raise ValueError(f"Identificador UC inválido (esperados {count} níveis): {name!r}")
    return parts


def _ident(name: str) -> str:
    if not _IDENTIFIER.fullmatch(name):
        raise ValueError(f"Identificador inválido: {name!r}")
    return f"`{name}`"


def _qualified(name: str, *, count: int = 3) -> str:
    return ".".join(_ident(p) for p in _parts(name, count=count))


def _literal(value: str) -> str:
    """Escapa aspas em strings SQL de comentário, sem executar SQL do usuário."""
    return "'" + value.replace("'", "''") + "'"


def _type_str(dtype: DataType) -> str:
    return dtype.simpleString()


@dataclass(frozen=True)
class ColumnSpec:
    """Coluna selecionada; campos não preenchidos são herdados da origem.

    ``expected_type`` é uma asserção, não uma conversão: drift dispara erro.
    ``nullable`` e ``comment`` permitem ajustar o contrato do mock.
    """

    name: str
    expected_type: DataType | None = None
    nullable: bool | None = None
    comment: str | None = None


ColumnDeclaration = str | ColumnSpec | StructField


@dataclass(frozen=True)
class ResolvedContract:
    """Contrato materializado; contém SOMENTE colunas selecionadas."""

    source_table: str
    target_table: str
    schema: StructType
    primary_keys: tuple[str, ...]
    table_comment: str

    @property
    def columns(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.schema.fields)

    def as_dict(self) -> dict[str, Any]:
        """Resumo serializável, útil para revisão e documentação."""
        return {
            "source": self.source_table,
            "target": self.target_table,
            "primary_keys": list(self.primary_keys),
            "table_comment": self.table_comment,
            "columns": [
                {
                    "name": f.name,
                    "type": f.dataType.simpleString(),
                    "nullable": f.nullable,
                    "comment": f.metadata.get("comment", ""),
                }
                for f in self.schema.fields
            ],
        }


class AbstractMockContract(ABC):
    """Definição de UMA tabela: origem, colunas, chaves e destino autorizado.

    A subclasse declara ``source_table`` e ``selected_columns`` (atributos
    de classe sobrescrevem as propriedades abstratas). As colunas podem ser
    nomes, ColumnSpec ou StructField (inclusive uma tupla de um StructType).

    Somente a estrutura/metadados da origem são consultados. O destino é
    explícito; nunca é inferido do catálogo de produção.
    """

    @property
    @abstractmethod
    def source_table(self) -> str:
        """Nome de origem ``catalog.schema.table``."""

    @property
    @abstractmethod
    def selected_columns(self) -> tuple[ColumnDeclaration, ...]:
        """Tupla ordenada de colunas a manter no mock."""

    primary_keys: tuple[str, ...] = ()
    target_table_name: str | None = None
    table_comment: str | None = None

    def __init__(
        self,
        spark: SparkSession,
        *,
        target_namespace: str,
        allowed_target_namespaces: tuple[str, ...],
    ) -> None:
        self.spark = spark
        self.target_namespace = target_namespace
        self.allowed_target_namespaces = tuple(allowed_target_namespaces)
        self._resolved: ResolvedContract | None = None
        self._validate_paths()

    @property
    def target_table(self) -> str:
        name = self.target_table_name or _parts(self.source_table, count=3)[-1]
        _ident(name)
        return f"{self.target_namespace}.{name}"

    def _validate_paths(self) -> None:
        _parts(self.source_table, count=3)
        catalog, schema = _parts(self.target_namespace, count=2)
        if not schema.endswith("_wks"):
            raise ValueError("Escrita recusada: schema de destino deve terminar em '_wks'.")
        if not self.allowed_target_namespaces:
            raise ValueError("Defina uma allowlist de namespaces de escrita.")
        for namespace in self.allowed_target_namespaces:
            _parts(namespace, count=2)
        if self.target_namespace not in self.allowed_target_namespaces:
            raise PermissionError("Destino ausente da allowlist de escrita.")
        if self.target_table == self.source_table:
            raise ValueError("Fonte e destino não podem ser a mesma tabela.")
        del catalog  # Validado acima; não é necessário armazenar.

    @staticmethod
    def _normalize(declaration: ColumnDeclaration) -> ColumnSpec:
        if isinstance(declaration, str):
            return ColumnSpec(name=declaration)
        if isinstance(declaration, ColumnSpec):
            return declaration
        if isinstance(declaration, StructField):
            return ColumnSpec(
                name=declaration.name,
                expected_type=declaration.dataType,
                nullable=declaration.nullable,
                comment=declaration.metadata.get("comment"),
            )
        raise TypeError(f"Declaração de coluna não suportada: {type(declaration).__name__}")

    def resolve(self, *, refresh: bool = False) -> ResolvedContract:
        """Lê SOMENTE o schema e comentários da tabela de origem.

        Não executa ``collect()``, ``count()`` ou scans de dados da origem.
        O contrato fica em cache até ``refresh=True``.
        """
        if self._resolved is not None and not refresh:
            return self._resolved
        self._validate_paths()
        declarations = tuple(self._normalize(v) for v in self.selected_columns)
        if not declarations:
            raise ValueError("O contrato precisa selecionar pelo menos uma coluna.")
        names = tuple(spec.name for spec in declarations)
        for name in names:
            _ident(name)
        if len(set(names)) != len(names):
            raise ValueError("Há colunas duplicadas no contrato.")
        keys = tuple(self.primary_keys)
        if len(set(keys)) != len(keys) or not set(keys).issubset(set(names)):
            raise ValueError("As chaves devem ser únicas e estar nas colunas selecionadas.")

        # Resolve apenas o schema via catálogo. NÃO executa ações sobre linhas.
        original = self.spark.table(self.source_table).schema
        available = {field.name: field for field in original.fields}
        selected: list[StructField] = []
        for declaration in declarations:
            if declaration.name not in available:
                raise ValueError(f"Coluna {declaration.name!r} inexistente na origem.")
            source_field = available[declaration.name]
            if (
                declaration.expected_type is not None
                and declaration.expected_type != source_field.dataType
            ):
                raise TypeError(
                    f"Drift na coluna {declaration.name}: contrato "
                    f"{_type_str(declaration.expected_type)}, origem "
                    f"{_type_str(source_field.dataType)}."
                )
            nullable = (
                source_field.nullable if declaration.nullable is None else declaration.nullable
            )
            if not isinstance(nullable, bool):
                raise TypeError(f"nullable deve ser bool: {declaration.name}")
            comment = (
                source_field.metadata.get("comment", "")
                if declaration.comment is None
                else declaration.comment
            )
            # Não copiar tags, máscaras, políticas ou propriedades de governança.
            selected.append(
                StructField(
                    declaration.name,
                    source_field.dataType,
                    nullable,
                    {"comment": str(comment)} if comment else {},
                )
            )

        description = self.table_comment
        if description is None:
            try:
                table_info = self.spark.catalog.getTable(self.source_table)
                description = getattr(table_info, "description", None)
            except Exception:  # Comentário é opcional; schema já validou a fonte.
                description = None
        description = (description or "Tabela sintética para testes E2E.").strip()
        if not description.lower().startswith("[mock]"):
            description = "[MOCK] " + description

        self._resolved = ResolvedContract(
            source_table=self.source_table,
            target_table=self.target_table,
            schema=StructType(selected),
            primary_keys=keys,
            table_comment=description,
        )
        return self._resolved


class AbstractMockTable(ABC):
    """Gerencia o DataFrame de trabalho e o ciclo de vida da tabela Delta mock.

    Subclasses implementam ``build_contract()``. A tabela vazia pode ser criada
    com ``create_table()``; nenhum dado é persistido por atribuir ``dataframe``.
    """

    @abstractmethod
    def build_contract(self) -> AbstractMockContract:
        """Forneça um objeto de contrato já configurado e autorizado."""

    def __init__(self) -> None:
        contract = self.build_contract()
        if not isinstance(contract, AbstractMockContract):
            raise TypeError("build_contract() deve retornar AbstractMockContract.")
        self.contract = contract
        resolved = contract.resolve()
        self.spark = contract.spark
        self._dataframe: DataFrame = self.spark.createDataFrame([], resolved.schema)

    @property
    def target_table(self) -> str:
        return self.contract.target_table

    @property
    def dataframe(self) -> DataFrame:
        return self._dataframe

    @dataframe.setter
    def dataframe(self, df: DataFrame) -> None:
        self._validate_structure(df)
        self._dataframe = df

    def set_dataframe(self, df: DataFrame) -> "AbstractMockTable":
        """Atribui DataFrame sem gravar dados no Delta."""
        self.dataframe = df
        return self

    def clear_dataframe(self) -> None:
        """Limpa somente o workspace em memória; NÃO apaga a tabela Delta."""
        self._dataframe = self.spark.createDataFrame([], self.contract.resolve().schema)

    def add_rows(self, rows: Iterable[Mapping[str, Any]]) -> "AbstractMockTable":
        """Acrescenta registros ao workspace (sem persistir)."""
        items = list(rows)
        if not items:
            return self
        expected = set(self.contract.resolve().columns)
        for idx, row in enumerate(items):
            if not isinstance(row, Mapping) or set(row) != expected:
                raise ValueError(
                    f"Linha {idx} deve conter exatamente as colunas do contrato; "
                    f"recebidas: {sorted(row) if isinstance(row, Mapping) else type(row)}"
                )
        new_df = self.spark.createDataFrame(items, schema=self.contract.resolve().schema)
        self._dataframe = self._dataframe.unionByName(new_df)
        return self

    def _validate_structure(self, df: DataFrame) -> None:
        if not isinstance(df, DataFrame):
            raise TypeError("É necessário fornecer um pyspark.sql.DataFrame.")
        schema = self.contract.resolve().schema
        expected_names = {f.name for f in schema.fields}
        actual_names = set(df.columns)
        if expected_names != actual_names or len(df.columns) != len(expected_names):
            raise ValueError(
                f"Colunas do dataframe não correspondem ao contrato: "
                f"faltantes={sorted(expected_names - actual_names)}, "
                f"extras={sorted(actual_names - expected_names)}"
            )
        expected = {f.name: f.dataType for f in schema.fields}
        for field in df.schema.fields:
            if field.dataType != expected[field.name]:
                raise TypeError(
                    f"Tipo inválido em {field.name}: recebido "
                    f"{_type_str(field.dataType)}; esperado {_type_str(expected[field.name])}."
                )

    def validate(self, *, check_rows: bool = True) -> None:
        """Valida colunas, tipos, não-nulos e unicidade das chaves de negócio.

        O DataFrame vazio é válido. Check de null/duplicidade executa ações
        SOMENTE no DataFrame do usuário, nunca na tabela de origem.
        """
        self._validate_structure(self._dataframe)
        contract = self.contract.resolve()
        if not check_rows:
            return
        required = set(contract.primary_keys) | {
            f.name for f in contract.schema.fields if not f.nullable
        }
        if required:
            predicate = reduce(or_, (F.col(_ident(c)).isNull() for c in sorted(required)))
            if self._dataframe.filter(predicate).limit(1).count() > 0:
                raise ValueError(f"Há valores nulos em colunas obrigatórias: {sorted(required)}")
        if contract.primary_keys:
            duplicates = (
                self._dataframe.groupBy(*contract.primary_keys)
                .count()
                .filter(F.col("count") > 1)
                .limit(1)
                .count()
            )
            if duplicates:
                raise ValueError("Chaves de negócio duplicadas no DataFrame de trabalho.")

    def is_dataframe_empty(self) -> bool:
        """Retorna True quando nenhum registro está carregado no workspace."""
        return self._dataframe.limit(1).count() == 0

    def table_exists(self) -> bool:
        return self.spark.catalog.tableExists(self.target_table)

    @staticmethod
    def _field_ddl(field: StructField) -> str:
        dtype = _type_str(field.dataType)
        nullable = "" if field.nullable else " NOT NULL"
        comment = field.metadata.get("comment", "")
        comment_ddl = f" COMMENT {_literal(str(comment))}" if comment else ""
        return f"{_ident(field.name)} {dtype}{nullable}{comment_ddl}"

    def create_table(self) -> bool:
        """Cria Delta VAZIA caso não exista; se existir, valida o contrato.

        Retorno True: tabela criada. False: já existia e foi validada.
        Não escreve o DataFrame de trabalho, mesmo que ele contenha linhas.
        """
        self.contract._validate_paths()
        resolved = self.contract.resolve()
        if self.table_exists():
            self.validate_destination()
            return False
        columns_sql = ",\n    ".join(self._field_ddl(f) for f in resolved.schema.fields)
        statement = (
            f"CREATE TABLE IF NOT EXISTS {_qualified(self.target_table)} (\n"
            f"    {columns_sql}\n"
            f") USING DELTA\n"
            f"COMMENT {_literal(resolved.table_comment)}\n"
            f"TBLPROPERTIES ("
            f"'mock.synthetic'='true', "
            f"'mock.source_table'={_literal(resolved.source_table)}"
            f")"
        )
        self.spark.sql(statement)
        self.validate_destination()
        return True

    def validate_destination(self) -> None:
        """Bloqueia leitura/escrita se destino tiver esquema ou formato inesperado."""
        self.contract._validate_paths()
        if not self.table_exists():
            raise RuntimeError(f"Tabela mock ainda não existe: {self.target_table}")
        detail = self.spark.sql(f"DESCRIBE DETAIL {_qualified(self.target_table)}").first()
        if detail is None or str(detail["format"]).lower() != "delta":
            raise TypeError("O destino existe, mas não é uma tabela Delta.")
        # Propriedade marca origem sintética; recusa gravar em tabelas legadas.
        properties = detail["properties"] or {}
        if str(properties.get("mock.synthetic", "")).lower() != "true":
            raise PermissionError("Destino não está marcado como tabela mock sintética.")
        if properties.get("mock.source_table") != self.contract.resolve().source_table:
            raise PermissionError("A tabela já existe, mas pertence a outra origem.")

        expected = self.contract.resolve().schema.fields
        actual = self.spark.table(self.target_table).schema.fields
        if [f.name for f in actual] != [f.name for f in expected]:
            raise ValueError("Schema da tabela divergiu (colunas e/ou ordem). Use evolve_schema().")
        for a, e in zip(actual, expected):
            if a.dataType != e.dataType:
                raise TypeError(f"Tipo incompatível em {a.name}: {a.dataType} != {e.dataType}")
            if not e.nullable and a.nullable:
                raise ValueError(f"Campo obrigatório {a.name} está nullable no destino.")

    def evolve_schema(self) -> tuple[str, ...]:
        """Adiciona SOMENTE colunas novas nullable do contrato ao destino Delta.

        Alterações de tipo, remoções, novas colunas NOT NULL e reorder são
        bloqueados. Comentários de colunas existentes não são sobrescritos.
        """
        self.contract._validate_paths()
        contract = self.contract.resolve()
        if not self.table_exists():
            raise RuntimeError("Crie primeiro a tabela com create_table().")
        self._assert_mock_properties()
        expected = {f.name: f for f in contract.schema.fields}
        actual = self.spark.table(self.target_table).schema.fields
        original_names = [f.name for f in actual]
        for field in actual:
            wanted = expected.get(field.name)
            if wanted is None or wanted.dataType != field.dataType:
                raise ValueError(f"Mudança destrutiva/incompatível no campo {field.name}.")
            if not wanted.nullable and field.nullable:
                raise ValueError(f"Não é possível reforçar nullability automaticamente: {field.name}.")
        wanted_order = [f.name for f in contract.schema.fields]
        if wanted_order[: len(original_names)] != original_names:
            raise ValueError("Só é permitido acrescentar colunas ao final do contrato.")
        missing = [f for f in contract.schema.fields if f.name not in original_names]
        if any(not f.nullable for f in missing):
            raise ValueError("A evolução automática só aceita novas colunas nullable.")
        if missing:
            ddl = ", ".join(self._field_ddl(f) for f in missing)
            self.spark.sql(f"ALTER TABLE {_qualified(self.target_table)} ADD COLUMNS ({ddl})")
        self.validate_destination()
        return tuple(f.name for f in missing)

    def sync_comments(self) -> None:
        """Aplica explicitamente comentário de tabela/colunas do contrato.

        Não copia tags, grants, máscaras, filtros ou propriedades da origem.
        Exige schema compatível; não executa migration de tipos.
        """
        self.validate_destination()
        resolved = self.contract.resolve()
        target = _qualified(self.target_table)
        self.spark.sql(f"COMMENT ON TABLE {target} IS {_literal(resolved.table_comment)}")
        for field in resolved.schema.fields:
            comment = field.metadata.get("comment")
            if comment:
                self.spark.sql(
                    f"ALTER TABLE {target} ALTER COLUMN {_ident(field.name)} "
                    f"COMMENT {_literal(str(comment))}"
                )

    def _assert_mock_properties(self) -> None:
        """Verifica identidade/segurança da tabela sem exigir schema atualizado."""
        detail = self.spark.sql(f"DESCRIBE DETAIL {_qualified(self.target_table)}").first()
        if detail is None or str(detail["format"]).lower() != "delta":
            raise TypeError("Destino não é Delta.")
        props = detail["properties"] or {}
        if (
            str(props.get("mock.synthetic", "")).lower() != "true"
            or props.get("mock.source_table") != self.contract.resolve().source_table
        ):
            raise PermissionError("Destino não validado como mock desta origem.")

    def read(self) -> DataFrame:
        self.validate_destination()
        return self.spark.table(self.target_table)

    def _ready_to_write(self) -> bool:
        self.contract._validate_paths()
        self.validate_destination()
        self.validate()
        return not self.is_dataframe_empty()

    def _ordered_dataframe(self) -> DataFrame:
        return self._dataframe.select(*self.contract.resolve().columns)

    def insert(self) -> bool:
        """Append explícito; rejeita colisões das chaves no destino.

        Para semeadura repetível, prefira merge() com primary_keys.
        """
        if not self._ready_to_write():
            return False
        keys = list(self.contract.resolve().primary_keys)
        if keys:
            source_keys = self._ordered_dataframe().select(*keys)
            duplicated = (
                source_keys.join(self.read().select(*keys), on=keys, how="left_semi")
                .limit(1)
                .count()
            )
            if duplicated:
                raise ValueError("Chave já existente no destino; use merge() para upsert.")
        self._ordered_dataframe().write.format("delta").mode("append").saveAsTable(self.target_table)
        return True

    def _require_keys(self) -> tuple[str, ...]:
        keys = self.contract.resolve().primary_keys
        if not keys:
            raise ValueError("Esta operação exige primary_keys no contrato.")
        return keys

    def _delta_merge(self, mode: str) -> bool:
        keys = self._require_keys()
        if not self._ready_to_write():
            return False
        try:
            from delta.tables import DeltaTable
        except ImportError as exc:
            raise RuntimeError("delta.tables precisa estar disponível no runtime Databricks.") from exc
        predicate = " AND ".join(
            f"target.{_ident(k)} = source.{_ident(k)}" for k in keys
        )
        operation = (
            DeltaTable.forName(self.spark, self.target_table)
            .alias("target")
            .merge(self._ordered_dataframe().alias("source"), predicate)
        )
        if mode == "merge":
            operation = operation.whenMatchedUpdateAll().whenNotMatchedInsertAll()
        elif mode == "update":
            operation = operation.whenMatchedUpdateAll()
        elif mode == "delete":
            operation = operation.whenMatchedDelete()
        else:
            raise ValueError(f"Operação Delta desconhecida: {mode}")
        operation.execute()
        return True

    def merge(self) -> bool:
        """Upsert por chave; útil para povoar/reexecutar massa sintética."""
        return self._delta_merge("merge")

    def update(self) -> bool:
        """Atualiza somente chaves já presentes, com todas as colunas informadas."""
        return self._delta_merge("update")

    def delete(self) -> bool:
        """Remove SOMENTE linhas cujas chaves estão no DataFrame carregado."""
        return self._delta_merge("delete")

    def materialize(self, *, mode: str = "merge") -> bool:
        """Cria a tabela, se necessário, e persiste o workspace explicitamente.

        Com workspace vazio: cria e retorna False (nenhuma linha gravada).
        Modos: ``merge`` (com chave) ou ``insert``.
        """
        if mode not in ("merge", "insert"):
            raise ValueError("materialize() aceita apenas 'merge' ou 'insert'.")
        self.create_table()
        if self.is_dataframe_empty():
            return False
        return self.merge() if mode == "merge" else self.insert()

    def describe_contract(self) -> dict[str, Any]:
        """Obtém um resumo do contrato sem ler registros de produção."""
        return self.contract.resolve().as_dict()