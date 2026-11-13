# Diagrama de classes — MockTable

## Herança e composição

```mermaid
classDiagram
direction TB
class AbstractMockContract {
  <<abstract>>
  +source_table: str
  +selected_columns: tuple
  +primary_keys: tuple
  +target_namespace: str
  +target_table: str
  +resolve(refresh): ResolvedContract
}
class ColumnSpec {
  +name: str
  +expected_type: DataType
  +nullable: bool
  +comment: str
}
class ResolvedContract {
  +source_table: str
  +target_table: str
  +schema: StructType
  +primary_keys: tuple
  +table_comment: str
  +as_dict(): dict
}
class AbstractMockTable {
  <<abstract>>
  -_dataframe: DataFrame
  +build_contract(): AbstractMockContract
  +create_table(): bool
  +set_dataframe(df)
  +add_rows(rows)
  +clear_dataframe()
  +validate()
  +insert(): bool
  +merge(): bool
  +update(): bool
  +delete(): bool
  +evolve_schema()
  +sync_comments()
  +read(): DataFrame
}
class PeopleContract
class MockPeople
AbstractMockContract <|-- PeopleContract
AbstractMockTable <|-- MockPeople
AbstractMockContract o-- ColumnSpec : seleciona
AbstractMockContract --> ResolvedContract : resolve
AbstractMockTable o-- AbstractMockContract : contém
MockPeople ..> PeopleContract : constrói
```

## Papéis

- **AbstractMockContract** é a definição estável da tabela: fonte de metadados, colunas selecionadas, chaves, namespace _wks e allowlist.
- **ColumnSpec** permite declarar colunas pelo nome e validar tipos, nullability e comentários herdados da fonte.
- **ResolvedContract** é a forma materializada do contrato, imutável e com somente as colunas selecionadas.
- **AbstractMockTable** administra exclusivamente um workspace DataFrame e o ciclo de vida do destino Delta.
- **PeopleContract e MockPeople** demonstram a separação entre configuração específica e operações herdadas.

Não há dependência de importação do SAFRA ou OLIST; eles são referências arquiteturais.