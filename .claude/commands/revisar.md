---
description: Revisão crítica de PySpark/Databricks antes de commit
allowed-tools: Read, Grep, Glob, Bash
---

Revise o diff atual (`git diff` e arquivos novos não rastreados
relevantes) como um engenheiro de dados sênior cético revisando o
código de um colega — não como um assistente tentando agradar.

Para cada arquivo alterado, nessa ordem:

1. **Idempotência.** Rodar esse job/writer duas vezes para o mesmo
   período ou chave de negócio produz o mesmo resultado ou duplica
   dados? Se não for seguro, isso é bloqueante — diga isso claramente.
2. **Escala.** Isso funciona numa amostra de 100 linhas mas quebra ou
   fica lento com volume de produção? Procure `collect()`,
   `toPandas()` desnecessário, joins sem broadcast quando um lado é
   pequeno, UDFs Python onde existe função nativa do Spark.
3. **Schema e nullability.** O schema está explícito (`StructType`) ou
   dependendo de inferência? Colunas obrigatórias estão marcadas como
   `nullable=False` de fato, ou só na intenção?
4. **Convenções do projeto.** Está alinhado com o que está em
   `CLAUDE.md` e com os ADRs em `docs/adr/` (ex.: Liquid Clustering em
   vez de `PARTITION BY`, clustering definido só na criação da tabela,
   `replaceWhere` seletivo para reprocessamento)? Se o código contradiz
   um ADR existente sem justificativa, aponte isso explicitamente.
5. **Reinvenção.** Isso já é resolvido nativamente pelo Lakeflow
   Declarative Pipelines, Auto Loader, Delta Lake ou Unity Catalog? Se
   sim, diga o que existe pronto antes de aprovar uma solução manual.
6. **Testes.** Existe teste cobrindo o caminho feliz E pelo menos um
   caminho de erro/borda? Se a mudança envolve Spark de fato, ela
   precisa de cobertura em `tests/integration`, não só `tests/unit`.
7. **Logging.** Segue o padrão estruturado do projeto (evento em
   `snake_case` + pares `chave=valor` separados por `" | "`)? Eventos
   de skip/warning/erro relevantes estão logados?

Formato da resposta:

- Liste primeiro os problemas **bloqueantes** (idempotência, perda de
  dados, quebra de schema), depois os **importantes** (escala,
  convenção violada sem justificativa), depois **sugestões** (estilo,
  pequenas melhorias).
- Para cada problema, cite o arquivo e a linha (ou trecho), explique o
  risco concreto — "isso quebra quando X" — e proponha a correção.
- Não abra com elogios genéricos. Se o código estiver de fato bom,
  diga isso ao final, brevemente, depois de cobrir os riscos.
- Não aprove silenciosamente nada sem teste correspondente.
