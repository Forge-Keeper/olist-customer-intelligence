"""ACRESCENTAR ao contratos.py existente; não substituir os seis contratos de massa.
Contratos operacionais sem inferência de tipos. Interface resolve() do Ledger.
"""
import re
from pyspark.sql.types import (
    ArrayType, IntegerType, MapType, NullType, StructField, StructType,
)
from mock_contract import AbstractMockContract, ResolvedContract


def validar_sem_nulltype(tipo, caminho="schema"):
    if isinstance(tipo, NullType):
        raise ValueError(f"NullType não permitido no contrato: {caminho}")
    if isinstance(tipo, StructType):
        for campo in tipo.fields:
            validar_sem_nulltype(campo.dataType, f"{caminho}.{campo.name}")
    elif isinstance(tipo, ArrayType):
        validar_sem_nulltype(tipo.elementType, f"{caminho}[]")
    elif isinstance(tipo, MapType):
        validar_sem_nulltype(tipo.keyType, f"{caminho}.key")
        validar_sem_nulltype(tipo.valueType, f"{caminho}.value")


def schema_com_alcada(schema, *, layout):
    """Ajusta apenas o campo de alçada em um schema de referência homologado.
    layout='raw': alçada só na ação; layout='flat': ação e coluna projetada.
    Não migra linhas antigas nem atribui a alçada raiz a todas as ações.
    """
    if layout not in ("raw", "flat"):
        raise ValueError("layout deve ser raw ou flat")
    acao = schema["aAcaoGrpEconm"]
    tipo = acao.dataType
    if not isinstance(tipo, ArrayType) or not isinstance(tipo.elementType, StructType):
        raise TypeError("Esperado array<struct> em aAcaoGrpEconm")

    def alcada(campos, manter):
        saida = []
        achou = False
        for campo in campos:
            if campo.name != "cIdAlcad":
                saida.append(campo)
                continue
            if not isinstance(campo.dataType, (IntegerType, NullType)):
                raise TypeError("cIdAlcad divergente do contrato INT")
            achou = True
            if manter:
                saida.append(StructField(campo.name, IntegerType(), True, campo.metadata))
        if manter and not achou:
            saida.append(StructField("cIdAlcad", IntegerType(), True))
        return saida

    elemento = StructType(alcada(tipo.elementType.fields, True))
    array = StructField(acao.name, ArrayType(elemento, tipo.containsNull), acao.nullable, acao.metadata)
    campos = [array if f.name == acao.name else f for f in schema.fields]
    resultado = StructType(alcada(campos, layout == "flat"))
    validar_sem_nulltype(resultado)
    return resultado


class ContratoOperacional(AbstractMockContract):
    """Schema explícito versionado, sem consulta de dados à tabela de referência."""
    primary_keys = ()  # Tabelas operacionais: setup não faz upsert.
    table_comment = "[MOCK] Tabela operacional do Motor GRUP."

    def __init__(self, spark, *, target_namespace, allowed_target_namespaces,
                 target_table_name, source_table, schema):
        if not re.fullmatch(r"(?:dv|ho)_[A-Za-z0-9_]+\.[A-Za-z0-9_]+_wks", target_namespace):
            raise PermissionError("Destino operacional deve ser DV ou HO, schema _wks")
        if not isinstance(schema, StructType) or not schema.fields:
            raise ValueError("Informe StructType explícito não vazio")
        validar_sem_nulltype(schema)
        if len(set(schema.fieldNames())) != len(schema.fields):
            raise ValueError("Colunas duplicadas")
        self._schema_operacional = schema
        self._referencia_operacional = source_table
        self.target_table_name = target_table_name
        super().__init__(spark, target_namespace=target_namespace,
                         allowed_target_namespaces=allowed_target_namespaces)

    @property
    def source_table(self):
        return self._referencia_operacional

    @property
    def selected_columns(self):
        return tuple(self._schema_operacional.fields)

    def resolve(self, *, refresh=False):
        self._validate_paths()
        validar_sem_nulltype(self._schema_operacional)
        return ResolvedContract(
            source_table=self.source_table,
            target_table=self.target_table,
            schema=self._schema_operacional,
            primary_keys=(),
            table_comment=self.table_comment,
        )
