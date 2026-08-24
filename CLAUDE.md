# olist-customer-intelligence

## Contexto do projeto

Plataforma de engenharia de dados ponta a ponta construída sobre o
dataset público da Olist (e-commerce brasileiro). Stack: Databricks,
PySpark, Delta Lake, Unity Catalog, ingestão via REST API (Open-Meteo),
qualidade de dados, orquestração, feature engineering e MLflow.

Estrutura de código-fonte (`src/olist_data_platform/`):

- `ingestion/api` — clientes de API externas (ex.: `open_meteo_client.py`)
- `ingestion/parsers` — parsing de payloads de resposta em registros
- `ingestion/services` — orquestração do fluxo de ingestão
- `ingestion/writers` — persistência em Delta (camada Bronze)
- `common/logging` — factory de logger compartilhado
- `transformations`, `features`, `ml`, `quality` — camadas seguintes do
  pipeline (Silver/Gold, features, modelos, validações)

Testes em `tests/unit` (lógica isolada, sem Spark real quando possível)
e `tests/integration` (Spark local via fixture `spark` em
`tests/conftest.py`, sessão `local[2]`).

Decisões arquiteturais relevantes são registradas em `docs/adr/` no
formato Status/Context/Decision/Rationale/Consequences/Alternatives
Considered/Revisit Criteria (ver `ADR-001-liquid-clustering-bronze-weather.md`
como modelo de referência).

## Convenções obrigatórias

- **Liquid Clustering em vez de Hive-style `PARTITION BY`** para tabelas
  Delta gerenciadas — decisão registrada no ADR-001. Nunca sugerir
  `PARTITION BY` ou Z-Order como alternativa padrão sem justificar
  explicitamente por que o caso é diferente do que motivou o ADR-001.
- Clustering é propriedade de layout da tabela: definir apenas na
  criação (`writer.clusterBy(...)` quando `not table_exists`);
  escritas subsequentes preservam a configuração existente. Nunca
  combinar `clusterBy` com `partitionBy` na mesma tabela.
- Reprocessamento usa `replaceWhere` seletivo por predicado de data +
  chave de negócio (ex.: `dt_base` + coordenadas), nunca overwrite
  completo da tabela.
- Camada Bronze não faz transformação de negócio — só valida,
  enriquece com metadados técnicos (`ingestion_timestamp`, `request_id`)
  e persiste com schema explícito (`StructType`, sem inferência).
- Logging estruturado via `LoggerFactory.get_logger(__name__)`, padrão
  `chave=valor` separado por `" | "`, sempre com um evento nomeado em
  `snake_case` no início da mensagem (ex.: `bronze_weather_write_started`).
- Validação de entrada em métodos `_validate_*` estáticos, levantando
  `TypeError`/`ValueError` com mensagem explícita — não falhar
  silenciosamente nem depender apenas de exceções do Spark.
- Toda mudança de comportamento de escrita/idempotência em um writer
  precisa de teste correspondente em `tests/unit` e, quando envolver
  Spark de fato, em `tests/integration`.
- Python 3.11+, tipagem explícita (`from __future__ import annotations`,
  `ClassVar`, tipos em assinaturas). `ruff` é o linter do projeto
  (ver `pyproject.toml`).

## Como revisar meu código

- Aponte falhas de idempotência antes de qualquer outra coisa: um job
  de ingestão rodado duas vezes para o mesmo período/chave deve ser
  seguro. Se não for, isso é bloqueante.
- Verifique schema explícito e nullability — nunca aceitar
  `inferSchema` implícito em caminhos de escrita para Bronze/Silver.
- Questione qualquer PySpark que funcione numa amostra pequena mas não
  escale: `collect()`/`toPandas()` desnecessário, `Row(**dict)` em
  volume alto, joins sem estratégia de broadcast quando um dos lados é
  pequeno, UDFs Python quando existe função nativa equivalente.
- Se eu estiver reimplementando algo que o Lakeflow Declarative
  Pipelines, o Auto Loader ou o próprio Delta/Unity Catalog já resolvem
  de forma nativa, me avise antes de eu terminar de escrever.
- Verifique se decisões de layout de tabela (partição/clustering) têm
  justificativa registrada — se não tiver ADR e for uma decisão não
  trivial, sugira criar um.
- Não aprove código sem teste correspondente. Não elogie antes de
  listar os problemas. Seja direto — meu objetivo é aprender onde
  estou errando, não me sentir bem com o código.

## O que NÃO fazer

- Não sugerir Hive-style `PARTITION BY` como padrão para tabelas Delta
  gerenciadas sem justificar por que o caso foge do ADR-001.
- Não misturar transformação de negócio na camada Bronze.
- Não aceitar overwrite completo de tabela como solução de
  reprocessamento quando `replaceWhere` seletivo é viável.
- Não silenciar ou reduzir o nível de um warning de qualidade de dados
  sem explicar a justificativa no código ou no PR.
- Não usar nomenclatura antiga da Databricks nas sugestões: usar
  "Lakeflow Declarative Pipelines" (não "Delta Live Tables"), "Liquid
  Clustering" (não "Z-Order" como recomendação padrão), "Real-Time
  Mode" (não "Continuous Processing").

## Comandos úteis do projeto

\```bash
pip install -e ".[dev]"   # instala projeto + deps de dev (pytest, ruff)
pytest                     # roda toda a suíte (unit + integration)
pytest tests/unit          # só unit, mais rápido, sem Spark pesado
ruff check .                # lint
\```