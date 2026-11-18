# Fixtures estáticas de Grupo Econômico (uso em ambientes de teste)

**Não há geração de dados em execução.** Os três arquivos Python contêm exclusivamente valores literais, iguais em qualquer ambiente.

| Arquivo | Conteúdo |
|---|---|
| `dados_nomes_pj.py` | 100 nomes comerciais de segmentos variados, indexados por `cclub_cli` de PJ (62 a 260, pares) |
| `dados_grupos_ativos.py` | 18 GEs: seis normais (1), seis isolados (5), seis gerenciais (6) |
| `dados_componentes_ativos.py` | 48 componentes: 30 PJs e 18 PFs, sem documento ativo em dois GEs |

## Como utilizar

Use os valores em `NOMES_PJ_POR_CCLUB` para substituir apenas `irz_scial` dos cadastros PJ já existentes, mantendo documentos e demais indicadores. Os nomes de sócio PJ em QSA previamente montado também devem ser conciliados por CNPJ, para que não permaneçam as razões sociais anteriores.

As tuplas de grupos seguem as **sete colunas do StructType da tabela de grupos ativos**. As tuplas de componentes seguem as quatro colunas do schema reduzido da tabela de componentes ativos. Em cada um, utilize os nomes de colunas na mesma ordem das tuplas para preparar registros para `add_rows()`; confira o schema antes da escrita.

## Observações funcionais

- Os nomes são fictícios e não se pretende que representem marcas reais.
- Os documentos das fixtures foram transcritos das fotografias de cadastros declarados sintéticos pelo usuário; confira os dígitos com a tabela cadastrada antes de persistir.
- As datas são fixas (5 maio 2026); não há `current_date` nem sorteio.
- Cada grupo normal contém 2 PJs e 1 PF; cada isolado, 1 PJ e 1 PF; cada gerencial, 2 PJs e 1 PF. Os 48 documentos são distintos.
- Nem todas as PJs nos grupos estão necessariamente elegíveis para os mesmos testes de negócio: verifique situação cadastral, flag de validade, matriz, natureza jurídica, QSA e responsabilidades para cenários positivos.
- O código do processador de exclusão fotografado referencia uma coluna adicional de componente `cpssoa_fis_jurid_isent`; o contrato reduzido atual tem quatro colunas e pode precisar ser ampliado antes do E2E integral.
- **Não foram executadas escritas no Databricks nem modificadas tabelas produtivas.**
