# Matriz de Limites e exceções — decisões binárias

**Casos:** 36. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| B01 | 910104 (tipo 1) | — | PF 299 (73002900354) | QSA: 74=107:50+299:50 | valida_socio_major | 299:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B02 | 910104 (tipo 1) | — | PF 299 (73002900354) | QSA: 74=107:50.01+299:49.99 | valida_socio_major | 299:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B03 | 910104 (tipo 1) | — | PF 299 (73002900354) | QSA: 74=107:49.99+299:50.01 | valida_socio_major | 299:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B04 | 910104 (tipo 1) | — | PF 299 (73002900354) | QSA: 74=107:100 | valida_socio_major | 299:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B05 | 910104 (tipo 1) | — | PF 299 (73002900354) | QSA: 74=107:50+299:50; Cadastro: 299.cindcd_cpf_valid=null | valida_cpf_ativo_receita | 299:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B06 | 910104 (tipo 1) | — | PF 293 (73002842133) | Cadastro: 293.remover_cadastro=true | ORACULO_CPF_AUSENTE | 293:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B07 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.rscit=ATIVA | valida_cnpj_ativo_receita | 112:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B08 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.cindcd_cnpj_valid=0 | valida_cnpj_ativo_receita | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B09 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.rsit_docto_recta=INAPTA | valida_cnpj_ativo_receita | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B10 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.rsit_docto_recta=BAIXADA | valida_cnpj_ativo_receita | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B11 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.rmtriz_flial_cnpj=2 | valida_cnpj_matriz | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B12 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.rnatur_jurid=Organização Religiosa | valida_cnpj_natureza_jurid | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B13 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | Cadastro: 112.rnatur_jurid=null | valida_cnpj_natureza_jurid | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B14 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | QSA: 112=SEM_SOCIOS | valida_qsa | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B15 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | QSA: 112=64:99.99 | valida_qsa | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B16 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | QSA: 112=64:100 | valida_qsa | 112:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B17 | 910101 (tipo 1) | — | PJ 112 (20010176000131) | QSA: 112=64:100.01 | valida_qsa | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B18 | 910101 (tipo 1) | — | PJ 118 (52592529000145) | QSA: 118=64:100 | valida_qsa | 118:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B19 | 910104 (tipo 1) | — | PF 299 (73002900354) | QSA: 74=299:50+299:50 | valida_socio_major | 299:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B20 | 910106 (tipo 1) | — | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84=64:100 | valida_composicao_unificacao | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B21 | 910102 (tipo 1) | — | PJ 62 (39070293000119) | Massa-base | valida_cnpj_em_outro_grupo | 62:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B22 | 910101 (tipo 1) | — | PF 101 (53762447683) | Massa-base | valida_cpf_em_outro_grupo | 101:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B23 | 910604 (tipo 6) | — | PF 299 (73002900354) | QSA: 124=117:50+299:50 | valida_socios_sao_pf | 299:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B24 | NOVO (tipo a definir) | — | PF 281 (73002725765) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B25 | NOVO (tipo a definir) | — | PJ 112 (20010176000131) | Massa-base | valida_composicao_formalizacao | 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B26 | NOVO (tipo a definir) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112=281:50+283:25+285:25 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B27 | 910104 (tipo 1) | — | PJ 74 (75538340000108) | Cadastro: 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=true | valida_cnpj_responsabilidade | 74:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B28 | 910101 (tipo 1) | — | PJ 62 (39070293000119) | Cadastro: 62.rsit_docto_recta=BAIXADA;62.flag_resp_empr=false | valida_cnpj_responsabilidade | 62:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B29 | 910104 (tipo 1) | — | PJ 74 (75538340000108) | Cadastro: 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=false | valida_cnpj_responsabilidade | 74:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B30 | 910104 (tipo 1) | — | PJ 74 (75538340000108) | Cadastro: 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=null | valida_cnpj_responsabilidade | 74:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B31 | 910101 (tipo 1) | — | PJ 62 (39070293000119) | Cadastro: 62.rsit_docto_recta=ATIVA;62.flag_resp_empr=false;62.tem_acao_2=0 | valida_cnpj_baixado | 62:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B32 | 910104 (tipo 1) | — | PJ 74 (75538340000108) | Cadastro: 74.rsit_docto_recta=ATIVA;74.flag_resp_empr=true;74.tem_acao_2=1; Ação 2 de Inclusão do MESMO documento na MESMA solicitação, com tem_acao_2 derivada das ações; sem ela, REPROVAR. | flag_troca_componente | 74:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| B33 | 910502 (tipo 5) | — | PJ 84 (31929392000100); PJ 88 (49043284000192); PF 111 (77449952602) | Massa-base | valida_composicao_grupo_economico | 84:REPROVADO; 88:REPROVADO; 111:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B34 | 910106 (tipo 1) | — | PJ 92 (16412297000132); PF 115 (66609568910); PJ 104 (99944451000144); PJ 106 (19271940000143); PF 125 (86038028404) | Massa-base | valida_composicao_unificacao | 92:REPROVADO; 115:REPROVADO; 104:REPROVADO; 106:REPROVADO; 125:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B35 | 910101 (tipo 1) | — | PJ 112 (20010176000131); PJ 112 (20010176000131) | Massa-base | ORACULO_DEDUPLICACAO_SOLICITACAO | 112:REPROVADO; 112:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| B36 | 910104 (tipo 1) | — | PJ 74 (75538340000108) | Cadastro: 74.rsit_docto_recta=BAIXADA;74.dt_fim_contrato=2026-11-19 | valida_cnpj_responsabilidade | 74:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
