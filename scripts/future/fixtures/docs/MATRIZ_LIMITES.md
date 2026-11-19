# Matriz de testes de limite e exceções — B01 a B36

**36 casos adicionais**: complementam as quatro ações com fronteiras numéricas, tipos nulos, cadastro ausente, responsabilidade e operações repetidas. Não substituem os casos-base.

| ID | Ação (`cAcaoGrpEconm`) | GE alvo | Componentes (`cclub_cli`) | Preparação QSA | Preparação cadastral/contratual | Regra alvo | Esperado |
|---|---|---|---|---|---|---|---|
| B01 | 2 — INCLUSAO | 910104 | 299 | 74=107:50+299:50 | cadastro normal | `valida_socio_major` | APROVA |
| B02 | 2 — INCLUSAO | 910104 | 299 | 74=107:50.01+299:49.99 | cadastro normal | `valida_socio_major` | RECUSA |
| B03 | 2 — INCLUSAO | 910104 | 299 | 74=107:49.99+299:50.01 | cadastro normal | `valida_socio_major` | APROVA |
| B04 | 2 — INCLUSAO | 910104 | 299 | 74=107:100 | cadastro normal | `valida_socio_major` | PENDENTE |
| B05 | 2 — INCLUSAO | 910104 | 299 | 74=107:50+299:50 | 299.cindcd_cpf_valid=null | `valida_cpf_ativo_receita` | PENDENTE |
| B06 | 2 — INCLUSAO | 910104 | 293 | QSA íntegro | 293.remover_cadastro=true | `ORACULO_CPF_AUSENTE` | PENDENTE |
| B07 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.rscit=ATIVA | `valida_cnpj_ativo_receita` | APROVA |
| B08 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.cindcd_cnpj_valid=0 | `valida_cnpj_ativo_receita` | RECUSA |
| B09 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.rsit_docto_recta=INAPTA | `valida_cnpj_ativo_receita` | RECUSA |
| B10 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.rsit_docto_recta=BAIXADA | `valida_cnpj_ativo_receita` | RECUSA |
| B11 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.rmtriz_flial_cnpj=2 | `valida_cnpj_matriz` | RECUSA |
| B12 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.rnatur_jurid=Organização Religiosa | `valida_cnpj_natureza_jurid` | RECUSA |
| B13 | 2 — INCLUSAO | 910101 | 112 | QSA íntegro | 112.rnatur_jurid=null | `valida_cnpj_natureza_jurid` | PENDENTE |
| B14 | 2 — INCLUSAO | 910101 | 112 | 112=SEM_SOCIOS | cadastro normal | `valida_qsa` | PENDENTE |
| B15 | 2 — INCLUSAO | 910101 | 112 | 112=64:99.99 | cadastro normal | `valida_qsa` | RECUSA |
| B16 | 2 — INCLUSAO | 910101 | 112 | 112=64:100 | cadastro normal | `valida_qsa` | APROVA |
| B17 | 2 — INCLUSAO | 910101 | 112 | 112=64:100.01 | cadastro normal | `valida_qsa` | RECUSA |
| B18 | 2 — INCLUSAO | 910101 | 118 | 118=64:100 | cadastro normal | `valida_qsa` | APROVA |
| B19 | 2 — INCLUSAO | 910104 | 299 | 74=299:50+299:50 | cadastro normal | `valida_socio_major` | PENDENTE |
| B20 | 4 — UNIFICACAO | 910106 | 92,115 | 84=64:100 | cadastro normal | `valida_composicao_unificacao` | PENDENTE |
| B21 | 2 — INCLUSAO | 910102 | 62 | QSA íntegro | cadastro normal | `valida_cnpj_em_outro_grupo` | RECUSA |
| B22 | 2 — INCLUSAO | 910101 | 101 | QSA íntegro | cadastro normal | `valida_cpf_em_outro_grupo` | RECUSA |
| B23 | 2 — INCLUSAO | 910604 | 299 | 124=117:50+299:50 | cadastro normal | `valida_socios_sao_pf` | RECUSA |
| B24 | 1 — FORMALIZACAO | NOVO | 281 | QSA íntegro | cadastro normal | `valida_composicao_formalizacao` | RECUSA |
| B25 | 1 — FORMALIZACAO | NOVO | 112 | QSA íntegro | cadastro normal | `valida_composicao_formalizacao` | RECUSA |
| B26 | 1 — FORMALIZACAO | NOVO | 112,281,283,285 | 112=281:50+283:25+285:25 | cadastro normal | `valida_composicao_formalizacao` | RECUSA |
| B27 | 3 — EXCLUSAO | 910104 | 74 | QSA íntegro | 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=true | `valida_cnpj_responsabilidade` | RECUSA |
| B28 | 3 — EXCLUSAO | 910101 | 62 | QSA íntegro | 62.rsit_docto_recta=BAIXADA;62.flag_resp_empr=false | `valida_cnpj_responsabilidade` | APROVA |
| B29 | 3 — EXCLUSAO | 910104 | 74 | QSA íntegro | 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=false | `valida_cnpj_responsabilidade` | APROVA |
| B30 | 3 — EXCLUSAO | 910104 | 74 | QSA íntegro | 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=null | `valida_cnpj_responsabilidade` | PENDENTE |
| B31 | 3 — EXCLUSAO | 910101 | 62 | QSA íntegro | 62.rsit_docto_recta=ATIVA;62.flag_resp_empr=false;62.tem_acao_2=0 | `valida_cnpj_baixado` | RECUSA |
| B32 | 3 — EXCLUSAO | 910104 | 74 | QSA íntegro | 74.rsit_docto_recta=ATIVA;74.flag_resp_empr=true;74.tem_acao_2=1 | `flag_troca_componente` | CONDICIONAL |
| B33 | 4 — UNIFICACAO | 910502 | 84,88,111 | QSA íntegro | cadastro normal | `valida_composicao_grupo_economico` | RECUSA |
| B34 | 4 — UNIFICACAO | 910106 | 92,115,104,106,125 | QSA íntegro | cadastro normal | `valida_composicao_unificacao` | CONDICIONAL |
| B35 | 2 — INCLUSAO | 910101 | 112,112 | QSA íntegro | cadastro normal | `ORACULO_DEDUPLICACAO_SOLICITACAO` | PENDENTE |
| B36 | 3 — EXCLUSAO | 910104 | 74 | QSA íntegro | 74.rsit_docto_recta=BAIXADA;74.dt_fim_contrato=2026-11-19 | `valida_cnpj_responsabilidade` | PENDENTE |

## Controles de execução

- Nas regras PySpark com comparação a `null`, a condição pode não se tornar verdadeira. Casos nulos permanecem `PENDENTE` até teste real, sem inferir recusa automática.
- `flag_socio_major` deriva do QSA: 49,99% abaixo do limite; 50% exatos elegíveis se a derivação não apresentar defeito.
- Vencimento e status de responsabilidade só devem ser avaliados depois de aplicar os filtros e ordenação de versões do enriquecimento.
- `preparo_cadastro` e `preparo_qsa` são instruções da fixture por cenário, jamais mudanças cumulativas.
- Nomes `ORACULO_*` identificam comportamentos do contrato/processador sem função de regra comprovada.

## Evidências

Em cada borda, registrar resposta, mensagens, fontes lidas, flags derivadas, eventos e estado materializado. Um `OK` de pipeline sem comparação do estado final não satisfaz o teste.
