# olist-customer-intelligence

## Contexto atual do projeto

Plataforma de Engenharia de Dados orientada a Databricks, construída com fontes
públicas da Olist e fontes complementares como IBGE, Open-Meteo e ANP/Azure
PostgreSQL.

Stack principal:

- Python 3.11+;
- PySpark;
- Databricks / Delta Lake / Unity Catalog;
- Databricks Asset Bundles (DAB);
- Data Quality first-class com evidência persistida;
- Control Plane operacional para runs e resultados de qualidade;
- GitHub Actions;
- MkDocs Material.

Não inferir maturidade pela existência de diretórios ou código. O estado público
atual de datasets e ambientes está em `docs/platform-status.md`. Gold / Customer
Intelligence continua roadmap enquanto o Platform Status não registrar evidência
aceita.

## Hierarquia de source of truth

Use as fontes conforme a pergunta:

1. `main` — verdade executável: código, recursos e testes implementados;
2. `docs/platform-status.md` — readiness atual de datasets/capabilities por ambiente;
3. GitHub Issues — backlog e trabalho futuro;
4. ADRs aceitos em `docs/adr/` — decisões arquiteturais duráveis;
5. README/docs home — narrativa de portfólio;
6. documentos de feature/gate — histórico detalhado, sem sobrepor o estado atual.

Um merge de código não autoriza sozinho um claim de `DONE`. Runtime evidence e
closeout devem corresponder ao escopo aceito.

## Arquitetura atual

Estrutura principal em `src/olist_data_platform/`:

- `domains/ingestion` — adapters/readers e serviços específicos de fonte;
- `domains/bronze` — contratos, DQ e adapters específicos da Bronze;
- `domains/silver` — contratos e transformações Silver tipadas;
- `domains/gold`, `domains/customer_intelligence`, `domains/ml` — namespaces
  existentes; existência do pacote não significa readiness funcional;
- `platform/delta` — `DatasetContract`, lifecycle, Bronze persistence,
  `SilverSnapshotWriter` para protected full snapshots e writers operacionais
  relacionados a Delta;
- `platform/quality` — regras, contracts, runner e modelo de Data Quality;
- `platform/operations` — tracking e estado operacional;
- `platform/http`, `jdbc`, `postgres`, `governance`, `logging` — capacidades
  compartilhadas;
- `jobs/` — composition roots/entry points executáveis.

Outros pontos importantes:

- `resources/` — recursos Databricks Asset Bundles;
- `deployment/smoke-jobs.yml` — contratos do deployment smoke;
- `docs/adr/` — decisões arquiteturais;
- `docs/development/` — especificações, runbooks e registros de entrega;
- `tests/unit` — testes isolados;
- `tests/integration` — testes com Spark local via fixture `spark`.

## Contratos e responsabilidades

### DatasetContract

`DatasetContract` é a autoridade para o schema persistido, tipos, nullability
lógica, chaves, estratégia de escrita, layout e metadata.

Não introduza schema inference em caminhos persistidos quando existe contrato
explícito.

### DeltaTableLifecycle

`DeltaTableLifecycle` é responsável por:

- criação/inspeção da tabela;
- compatibilidade de schema;
- layout físico;
- metadata/comments/tags;
- evolução explicitamente suportada.

Não mover sem necessidade essas responsabilidades para writers de domínio.

### BronzeWriter

`BronzeWriter` é responsável por:

- preparação do batch;
- `ingestion_timestamp` gerenciado pela plataforma;
- validação runtime do DataFrame contra o `DatasetContract`;
- validação de chave quando a evidência não veio do DQ;
- semântica de `MERGE`, `FULL_REPLACE` e reprocessamento explícito.

O boundary da Bronze não faz cast implícito para "consertar" um DataFrame.
O tipo Spark recebido deve ser compatível com o tipo declarado no contrato.

## Estratégias de escrita

A estratégia é definida pela semântica da fonte, não por preferência genérica.

### FULL_REPLACE — snapshots Olist

Por ADR-009, os CSVs Olist modelados como snapshots completos/autoritativos usam
`FULL_REPLACE` como escrita normal.

Invariantes:

- o batch representa o universo completo aceito do dataset;
- blocking DQ deve falhar antes da substituição;
- snapshot vazio inesperado deve ser rejeitado;
- schema/tipos são explícitos;
- rerun do mesmo business state deve preservar as mesmas linhas/chaves de negócio,
  desconsiderando timestamps operacionais esperados;
- linhas ausentes do novo snapshot não devem sobreviver no target;
- datasets naturalmente keyless, como Geolocation, não recebem chave artificial.

Não tratar full overwrite como antipattern quando o contrato é um snapshot completo.

### MERGE — batches keyed de estado parcial

Use `MERGE` quando o batch contém inserts/updates por chave mas não representa o
universo completo da tabela.

Ter uma chave não é, sozinho, justificativa para trocar um snapshot Olist para
`MERGE`.

### replaceWhere — replay/reprocessamento limitado

`replaceWhere` é reprocessamento explícito e limitado por predicado.

Exemplos atuais incluem escopos por data/coordenadas ou intervalo de datas. Não
usar `replaceWhere` como substituto cerimonial para um snapshot cujo escopo
autoritativo é a tabela inteira.

## Camadas de dados

### Bronze

Bronze preserva semântica de fonte e evita normalização de negócio.

- Olist CSV: preservar os valores source-faithful, em geral strings, mais metadata
  técnica;
- APIs semi-estruturadas governadas pelo ADR-003: preservar payload em `VARIANT`
  quando aplicável;
- JDBC/ANP: preservar tipos técnicos/source-compatible definidos pelo adapter;
- não fabricar histórico que a fonte não fornece;
- não mover tipagem/normalização analítica para Bronze por conveniência.

### Silver

Silver é responsável por:

- tipos analíticos explícitos;
- grain explícito;
- relacionamentos/referential DQ;
- harmonização determinística;
- lineage útil;
- blocking DQ antes de protected writes.

A Silver Olist atualmente entregue usa snapshots completos derivados da Bronze e
protected `FULL_REPLACE`.

`SilverSnapshotWriter` centraliza somente o protocolo já observado de DQ,
persistência de evidência, blocking gate, empty guard, lifecycle e replacement
integral. Ele não é um `SilverWriter` genérico e não possui MERGE/SCD/CDC.

Não ampliar essa abstração para framework de SCD, CDC, checkpoint, surrogate keys,
orquestração genérica ou novas estratégias sem nova evidência e novo gate.

Regra de evolução:

```text
necessidade real
  -> solução explícita
  -> repetição observada
  -> contrato
  -> abstração
  -> testes
  -> docs/ADR
  -> automação
```

## Data Quality e target protection

Data Quality é comportamento de plataforma, não comentário documental.

- `ERROR` bloqueante deve impedir protected write;
- `WARNING`/`INFO` registram evidência sem alterar o contrato silenciosamente;
- evidência deve ser persistida quando o fluxo first-class DQ está configurado;
- `BronzeWriter.write_checked()` reutiliza evidência de chave compatível com o
  `DatasetContract`;
- `SilverSnapshotWriter.write_checked()` recebe o DataFrame transformado e possui
  explicitamente a avaliação/persistência de DQ do protocolo de snapshot Silver;
- falha bloqueante não deve destruir nem substituir o target anterior;
- não rebaixar severidade apenas para fazer o job passar.

## Layout Delta

ADR-001 governa Weather: Liquid Clustering em vez de Hive-style partitioning.

Regras gerais:

- não sugerir `PARTITION BY` ou Z-Order como padrão Databricks sem evidência;
- clustering é propriedade da tabela/lifecycle, não detalhe de cada batch;
- não combinar clustering e partitioning para a mesma coluna/tabela;
- não alterar semântica lógica de uma coluna para acomodar layout físico.

## Logging

Logging compartilhado via `LoggerFactory.get_logger(__name__)`.

Eventos operacionais devem usar:

```text
snake_case_event | key=value | key=value
```

Inclua identificadores úteis para investigação sem logar secrets ou payloads
sensíveis.

## Como revisar código

Priorize, nesta ordem, quando aplicável:

1. perda/corrupção de dados e idempotência incorreta;
2. semântica de escrita incompatível com a fonte;
3. bypass de DQ ou protected-write guarantees;
4. schema/type drift e contratos inconsistentes;
5. quebra de lifecycle/layout/governance;
6. problemas de escalabilidade;
7. abstração prematura.

Questione especialmente:

- `collect()`/`toPandas()` desnecessário em volume;
- Python UDF quando existe função Spark nativa;
- joins sem estratégia proporcional ao tamanho dos lados;
- casts silenciosos que escondem source/type drift;
- lógica de negócio vazando para Bronze;
- regras de DQ inventadas sem evidência;
- frameworks genéricos criados antes de repetição real.

Não aprove mudança comportamental sem cobertura de teste proporcional.

## Git e promotion flow

Fluxo governado:

```text
topic branch
  -> PR para dev
  -> CI/docs
  -> human merge gate
  -> dev
  -> PR de promoção para main
  -> CI/docs
  -> human promotion gate
  -> main
```

PR direto de topic branch para `main` viola o branch-governance da CI.

Use merge commit regular em `dev -> main` quando a preservação de ancestry fizer
parte do fluxo de promoção. Não usar squash automaticamente em promoção sem
avaliar lineage.

## Documentação e decisões

Mudança arquitetural durável deve usar ADR.

Formato atual:

```text
Status
Context
Decision
Alternatives considered
Consequences
Implementation constraints
Validation
Supersession / related decisions
```

Mudanças relevantes devem respeitar o fluxo de engenharia quando proporcional:

```text
Discovery
  -> Requirements
  -> Technical Design
  -> Impact Analysis
  -> Implementation Plan
  -> Implementation / Validation
  -> Closeout / Platform Status
  -> Done
```

Não crie todos os artefatos mecanicamente para uma correção pequena; preserve a
proporcionalidade e o source of truth.

## O que NÃO fazer

- não proibir `FULL_REPLACE` genericamente: ADR-009 autoriza e exige essa semântica
  para snapshots Olist completos;
- não usar `FULL_REPLACE` quando a completude do batch é desconhecida;
- não converter `FULL_REPLACE` para `MERGE` só porque existe chave;
- não misturar transformação de negócio na Bronze;
- não usar schema inference para contratos persistidos;
- não introduzir cast implícito no `BronzeWriter`;
- não aceitar blocking DQ e escrever mesmo assim;
- não inferir readiness STG/PRD de código ou deployment smoke;
- não criar abstração genérica antes de repetição observada;
- não atualizar README como ledger de runtime;
- não usar nomenclatura Databricks obsoleta nas recomendações quando houver nome
  atual adotado no projeto.

## Comandos de validação

Espelhe a CI:

```bash
uv python install 3.11
uv sync --frozen --group dev
uv run ruff check .
uv run ty check
uv run pytest -q
uv run python scripts/run_deployment_smokes.py --validate-only
uv build --wheel
uv run mkdocs build --strict
```

Para testes focados, use `uv run pytest <path> -q`, mas o gate final deve considerar
a suíte/CI completa correspondente ao escopo.
