# Fixtures estáticas de Grupo Econômico (uso em ambientes de teste)

**Não há geração de dados em execução.** Os arquivos de massa contêm exclusivamente valores literais, iguais em qualquer ambiente.

| Arquivo | Conteúdo |
|---|---|
| `dados_nomes_pj.py` | 100 nomes comerciais de segmentos variados, indexados por `cclub_cli` de PJ (62 a 260, pares) |
| `dados_grupos_ativos.py` | 18 GEs: seis normais (1), seis isolados (5), seis gerenciais (6) |
| `dados_componentes_ativos.py` | 48 componentes: 30 PJs e 18 PFs, sem documento ativo em dois GEs |
| `dados_quadro_societario.py` | 54 vínculos fixos de QSA para 27 PJs não MEI; inclui controladoras PJ e três PF sem majoritário |

## Como utilizar

Use os valores em `NOMES_PJ_POR_CCLUB` para substituir apenas `irz_scial` dos cadastros PJ já existentes, mantendo documentos e demais indicadores. Os nomes de sócio PJ em QSA previamente montado também devem ser conciliados por CNPJ, para que não permaneçam as razões sociais anteriores.

As tuplas de grupos seguem as **sete colunas do StructType da tabela de grupos ativos**. As tuplas de componentes seguem as quatro colunas do schema reduzido da tabela de componentes ativos. Em cada um, utilize os nomes de colunas na mesma ordem das tuplas para preparar registros para `add_rows()`; confira o schema antes da escrita.

## Quadro societário

O arquivo `dados_quadro_societario.py` utiliza tuplas na ordem do seu notebook original: `ccnpj_empr`, `pprtcp_soctr`, `cindcd_quadr_soctr`, `ipartc_empr`, `dfim_prtcp_soctr`, `cclub_cli`, `ccpf_cnpj_pssoa_soctr`, `dptcao_orige`. O `cclub_cli` é **do sócio**. As participações somam 100% por CNPJ titular.

- Os vínculos MEI já preparados pelo usuário permanecem separados; **não reinsira os MEIs se já foram persistidos**.
- 39 vínculos correspondem às 19 empresas do QSA anteriormente discutido; os demais cobrem oito PJs presentes nos grupos ativos.
- As razões sociais de sócios PJ estão alinhadas aos novos nomes de `dados_nomes_pj.py`.
- Antes de persistir, verifique a existência no cadastro de três CNPJs titulares usados nas listas anteriores: cclub_cli 112, 118 e 120; os demais grupos têm seus documentos cadastrados nas fixtures de componentes.
- Os testes em `tests/test_quadro_societario.py` verificam 100% por empresa, inexistência de vínculos repetidos, cinco PFs titulares de MEI, três PJs MEI como sócias e ao menos uma empresa com três PFs sem majoritário.

## Observações funcionais

- Os nomes são fictícios e não se pretende que representem marcas reais.
- Os documentos das fixtures foram transcritos das fotografias de cadastros declarados sintéticos pelo usuário; confira os dígitos com a tabela cadastrada antes de persistir.
- As datas são fixas (5 maio 2026); não há `current_date` nem sorteio.
- Cada grupo normal contém 2 PJs e 1 PF; cada isolado, 1 PJ e 1 PF; cada gerencial, 2 PJs e 1 PF. Os 48 documentos são distintos.
- Nem todas as PJs nos grupos estão necessariamente elegíveis para os mesmos testes de negócio: verifique situação cadastral, flag de validade, matriz, natureza jurídica, QSA e responsabilidades para cenários positivos.
- O código do processador de exclusão fotografado referencia uma coluna adicional de componente `cpssoa_fis_jurid_isent`; o contrato reduzido atual tem quatro colunas e pode precisar ser ampliado antes do E2E integral.
- **Não foram executadas escritas no Databricks nem modificadas tabelas produtivas.**


## Estudo dos testes integrados

O roteiro de cenários, composição das massas e coordenação com Frontend, Backend, Motor GRUP e validação funcional está em [docs/README.md](docs/README.md). É um estudo de cobertura e execução: as massas estão preparadas, mas os testes ainda precisam ser rodados e confrontados com a versão atual do motor.
