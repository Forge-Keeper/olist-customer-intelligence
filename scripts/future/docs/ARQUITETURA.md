# Arquitetura e contratos técnicos

## 1. Objetivo

Framework pequeno e independente para criar e administrar tabelas Delta de teste com dados sintéticos. Adota a herança de tarefas do SAFRA e a separação contrato/ciclo de vida do OLIST, sem importar seus pacotes.

## 2. Componentes

| Componente | Entrada | Saída | Responsabilidade |
|---|---|---|---|
| AbstractMockContract | source_table, selected_columns, primary_keys, target_namespace, allowlist | ResolvedContract | Validar configuração, ler metadados de schema, selecionar campos e derivar nome do destino |
| ResolvedContract | Campos resolvidos | StructType e metadados | Snapshot da estrutura utilizada pela instância |
| AbstractMockTable | Contrato e DataFrame | Tabela Delta em _wks | Criar, validar, evoluir e escrever somente sob invocação explícita |
| Classe concreta | Configuração de um dataset | Objeto utilizável | Declarar contrato e fornecer seu objeto à classe-base |

## 3. Contrato de leitura e metadados

O contrato acessa spark.table(source_table).schema e, opcionalmente, spark.catalog.getTable para descrição. Esses acessos são de estrutura, não executam collect/count nos registros da origem. As colunas podem ser strings, ColumnSpec ou StructField. O tipo de uma coluna declarada é uma asserção de compatibilidade; não há cast silencioso. Copiam-se apenas tipo, nullability e comentário da coluna. A descrição da tabela é prefixada com [MOCK].

Tags, máscaras, filtros de linha, privilégios, propriedades e ownership da origem NÃO são copiados. A tabela alvo deve ser autorizada de forma explícita e o schema deve terminar em _wks.

## 4. Contrato de escrita

- Instanciar a tabela inicia um DataFrame vazio com StructType resolvido; não cria objetos no catálogo.
- create_table(): DDL da tabela Delta vazia e idempotência com validação do objeto preexistente.
- dataframe/set_dataframe(): substitui somente o workspace local; verifica nomes e tipos.
- add_rows(): acrescenta registros ao workspace, sem IO no destino.
- validate(): verifica estrutura, nulos e chaves duplicadas no DataFrame local.
- insert(): append, com pré-checagem de colisão se houver chaves declaradas.
- merge(): upsert por primary_keys; update(): atualização de matches; delete(): exclusão de matches.
- materialize(mode): cria o alvo se necessário e aplica a operação explícita quando houver linhas.
- read(): acessa somente o destino sintético, nunca a origem.

Todas as operações de escrita e leitura do destino conferem o formato Delta, o schema e os atributos mock.synthetic=true e mock.source_table. Qualquer destino fora da allowlist falha antes de emitir DDL/DML.

## 5. Evolução de schema

Após modificar a declaração, chamar contract.resolve(refresh=True), recriar o DataFrame de trabalho com o novo schema e executar evolve_schema(). A implementação suporta somente acrescentar colunas nullable ao fim. Renomear, remover, trocar tipos, reordenar colunas ou reforçar NOT NULL exige migração manual.

## 6. Segurança, limitações e fronteiras

- Esta versão NÃO valida que valores recebidos são sintéticos. É responsabilidade da origem do DataFrame.
- A criação não configura o roteamento do sistema consumidor para o mock; essa integração deve ser tratada separadamente.
- insert() não oferece atomicidade transacional para a pré-verificação de chaves em escritores concorrentes.
- Chaves erradas podem causar matches indesejados. Confirmar chaves reais do caso de uso antes de executar MERGE.
- A implementação não copia nem grava dados produtivos por conta própria.
- Não executa DROP, TRUNCATE ou overwrite da tabela.
- Comentários, compatibilidade Delta no workspace e permissões precisam ser testados no ambiente Databricks autorizado.

## 7. Organização dos arquivos

| Arquivo | Uso |
|---|---|
| ../mock_table.py | Implementação reutilizável |
| ../example_people.py | Classe concreta genérica, sem identificadores de cliente |
| ../tests/test_mock_table.py | Testes unitários isolados com mocks |
| ../README.md | API pública, configuração e ciclo de vida |
| CLASSES.md | Diagrama de classes |
| FLUXOS.md | Fluxos de execução |
| TESTES.md | Matriz de validação e smoke no Databricks |

## 8. Referências

- SAFRA (TableTask/DataTask): https://github.com/Forge-Keeper/estudos_databricks_automated_bundle
- OLIST (DatasetContract/DeltaTableLifecycle): https://github.com/Forge-Keeper/olist-customer-intelligence

Esta pasta é experimental e não altera o runtime, os jobs ou as pipelines do OLIST.