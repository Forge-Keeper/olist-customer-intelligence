# Fluxogramas de funcionamento — MockTable

## Inicialização e criação de tabela vazia

```mermaid
flowchart TD
  A[Instanciar MockPeople] --> B[build_contract]
  B --> C[AbstractMockContract.resolve]
  C --> D[Consultar SOMENTE schema da origem]
  D --> E[Selecionar colunas e comentários]
  E --> F[ResolvedContract em memória]
  F --> G[Inicializar DataFrame vazio]
  G --> H[create_table]
  H --> I{Destino existe?}
  I -- Não --> J[CREATE TABLE DELTA vazia em _wks]
  I -- Sim --> K[Verificar formato, selo mock e schema]
  J --> K
  K --> L[Tabela pronta para dados sintéticos]
```

## Preparação, validação e persistência

```mermaid
flowchart TD
  A[Receber DataFrame ou add_rows] --> B[self._dataframe]
  B --> C[validate]
  C --> D{Tipos, nulos e chaves válidos?}
  D -- Não --> E[Erro sem escrita]
  D -- Sim --> F{Operação explícita}
  F -- insert --> G[Checar colisão de chave e append]
  F -- merge --> H[Delta MERGE upsert]
  F -- update --> I[Delta MERGE update-only]
  F -- delete --> J[Delta MERGE delete-only]
  G --> K[Tabela sintética _wks]
  H --> K
  I --> K
  J --> K
  K --> L[read e inspeção dos resultados]
```

## Evolução controlada

```mermaid
flowchart TD
  A[Atualizar selected_columns] --> B[contract.resolve refresh=True]
  B --> C[evolve_schema]
  C --> D{Somente colunas nullable no final?}
  D -- Não --> E[Rejeitar alteração incompatível]
  D -- Sim --> F[ALTER TABLE ADD COLUMNS]
  F --> G[Recarregar DataFrame com novo contrato]
  G --> H[validate e escrita explícita]
```

**Observação:** os fluxos usam os mesmos métodos do código Python. Nenhum método de atribuição do DataFrame escreve em Delta.