# Preferências pessoais — Bruno (vale para todo projeto, não só este)

## Quem eu sou
Engenheiro de dados buscando posição sênior com foco em streaming.
Background em PySpark, Databricks, ETL/ELT batch (Ailos, Unicred).
Aprendendo/consolidando Kafka, Spark Structured Streaming e dbt.

## Como quero ser corrigido
- Seja direto sobre erros. Não amenize para soar gentil.
- Quando corrigir algo, explique por que era um problema e dê um
  exemplo concreto de quando isso quebraria em produção — não só o
  fix. Meu objetivo é aprender o padrão, não só resolver o caso.
- Se eu estiver reinventando algo que Databricks/Lakeflow já resolve
  nativamente, me avise antes de eu terminar de escrever.

## Nomenclatura atualizada que sempre devo usar
- "Lakeflow Declarative Pipelines" (não "Delta Live Tables")
- "Liquid Clustering" como padrão (não Z-Order, salvo justificativa)
- "Real-Time Mode" (não "Continuous Processing", deprecado)
- "Databricks Free Edition" quando aplicável

## Convenções gerais de código que eu gosto
- Tipagem explícita, `from __future__ import annotations`
- Validação de entrada em métodos `_validate_*` com exceções
  explícitas, não falha silenciosa
- Logging estruturado em `chave=valor`, evento nomeado em snake_case
- Sempre schema explícito em DataFrames Spark, nunca inferSchema em
  caminho de escrita para camadas Bronze/Silver