# Matriz de Exclusão — decisões binárias

**Casos:** 30. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| E01 | 910101 (tipo 1) | 62, 64, 101, 112 | PJ 112 (20010176000131) | Cadastro: 112; Antes +[112] | exclusao_pj_parcial | 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E02 | 910101 (tipo 1) | 62, 64, 101, 112 | PJ 62 (39070293000119); PJ 112 (20010176000131) | Cadastro: 62,112; Antes +[112] | conversao_normal_isolado | 62:APROVADO; 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E03 | 910101 (tipo 1) | 62, 64, 101, 112 | PJ 62 (39070293000119); PJ 64 (47911744000121); PJ 112 (20010176000131) | Cadastro: 62,64,112; Antes +[112] | cancelamento_ge_sem_pj | 62:APROVADO; 64:APROVADO; 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E04 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119) | Cadastro: 62 | conversao_normal_isolado | 62:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E05 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119); PJ 64 (47911744000121) | Cadastro: 62,64 | cancelamento_ge_sem_pj | 62:APROVADO; 64:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E06 | 910101 (tipo 1) | 62, 101 | PJ 62 (39070293000119) | Cadastro: 62; Antes -[64] | cancelamento_ge_sem_pj | 62:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E07 | 910502 (tipo 5) | 92, 115 | PJ 92 (16412297000132) | Cadastro: 92 | cancelamento_ge_sem_pj | 92:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E08 | 910502 (tipo 5) | 92, 115, 112 | PJ 112 (20010176000131) | Cadastro: 112; Antes +[112] | exclusao_isolado_anomalo | 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E09 | 910502 (tipo 5) | 92, 115, 112 | PJ 92 (16412297000132); PJ 112 (20010176000131) | Cadastro: 92,112; Antes +[112] | cancelamento_ge_sem_pj | 92:APROVADO; 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E10 | 910601 (tipo 6) | 104, 106, 125, 112 | PJ 112 (20010176000131) | Cadastro: 112; Antes +[112] | exclusao_gerencial | 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E11 | 910601 (tipo 6) | 104, 106, 125, 112 | PJ 104 (99944451000144); PJ 112 (20010176000131) | Cadastro: 104,112; Antes +[112] | exclusao_gerencial | 104:APROVADO; 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E12 | 910601 (tipo 6) | 104, 106, 125, 112 | PJ 104 (99944451000144); PJ 106 (19271940000143); PJ 112 (20010176000131) | Cadastro: 104,106,112; Antes +[112] | cancelamento_ge_sem_pj | 104:APROVADO; 106:APROVADO; 112:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E13 | 910602 (tipo 6) | 108, 110, 127 | PJ 108 (74254453000180) | Cadastro: 108 | exclusao_gerencial | 108:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E14 | 910602 (tipo 6) | 108, 110, 127 | PJ 108 (74254453000180); PJ 110 (05772590000194) | Cadastro: 108,110 | cancelamento_ge_sem_pj | 108:APROVADO; 110:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E15 | 910101 (tipo 1) | 62, 64, 101 | PF 101 (53762447683) | Massa-base | exclusao_pf | 101:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E16 | 910102 (tipo 1) | 66, 68, 103 | PF 103 (96641610047) | Massa-base | composicao_ge_sem_pf | 103:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E17 | 910502 (tipo 5) | 92, 115 | PF 115 (66609568910) | Massa-base | exclusao_pf_isolado | 115:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E18 | 910601 (tipo 6) | 104, 106, 125 | PF 125 (86038028404) | Massa-base | exclusao_pf_gerencial | 125:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E19 | 910102 (tipo 1) | 66, 68, 103 | PJ 66 (35650844000162); PF 103 (96641610047) | Cadastro: 66 | exclusao_mista | 66:APROVADO; 103:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E20 | 910502 (tipo 5) | 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | Cadastro: 92 | cancelamento_ge_sem_pj | 92:APROVADO; 115:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E21 | 910101 (tipo 1) | 62, 64, 101 | PJ 112 (20010176000131) | Cadastro: 112 | componente_inexistente_no_ge | 112:REPROVADO | — | REPROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E22 | 910101 (tipo 1) | 62, 64, 101 | PJ 68 (93773779000169) | Cadastro: 68 | componente_de_outro_ge | 68:REPROVADO | — | REPROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E23 | 910103 (tipo 1) | 70, 72, 105 | PJ 70 (31297282000164); PJ 72 (08730759000131) | Cadastro: 70,72 | cancelamento_ge_sem_pj | 70:APROVADO; 72:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E24 | 910101 (tipo 1) | 62, 64, 101, 281 | PF 101 (53762447683); PF 281 (73002725765) | Antes +[281] | exclusao_multiplas_pf | 101:APROVADO; 281:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E25 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119) | Cadastro: 62 | valida_cnpj_baixado | 62:REPROVADO | — | REPROVADO | NENHUM |
| E26 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119) | Cadastro: 62 | valida_cnpj_baixado | 62:APROVADO | — | APROVADO | DELETE_COMPONENTE + UPDATE_GE |
| E27 | 910104 (tipo 1) | 74, 76, 107 | PJ 74 (75538340000108) | Cadastro: 74 | valida_cnpj_responsabilidade | 74:REPROVADO | — | REPROVADO | NENHUM |
| E28 | 910101 (tipo 1) | 62, 64, 101 | PJ 64 (47911744000121) | Cadastro: 64 | valida_cnpj_responsabilidade | 64:APROVADO | — | APROVADO | DELETE_COMPONENTE + UPDATE_GE |
| E29 | 910104 (tipo 1) | 74, 76, 107 | PJ 74 (75538340000108) | Cadastro: 74; Ação 2 de Inclusão do MESMO documento na MESMA solicitação, com tem_acao_2 derivada das ações; sem ela, REPROVAR. | flag_troca_componente | 74:APROVADO | — | APROVADO | CONFIRMAR_CRT_COMPOSICAO |
| E30 | 910104 (tipo 1) | 74, 76, 107 | PJ 74 (75538340000108); PJ 76 (82080682000154) | Cadastro: 74,76 | valida_cnpj_responsabilidade | 74:REPROVADO; 76:APROVADO | — | REPROVADO | CONFIRMAR_CRT_COMPOSICAO |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
