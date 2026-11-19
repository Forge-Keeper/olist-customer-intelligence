# Matriz de Formalização — decisões binárias

**Casos:** 48. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| F01 | NOVO (tipo 1) | — | — | Massa-base | valida_composicao_formalizacao | — | — | REPROVADO | SEM_EVENTO_APROVADO |
| F02 | NOVO (tipo 1) | — | PF 281 (73002725765) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F03 | NOVO (tipo 1) | — | PF 281 (73002725765); PF 283 (73002745103) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F04 | NOVO (tipo 1) | — | PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F05 | NOVO (tipo 1) | — | PJ 112 (20010176000131) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F06 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F07 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F08 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F09 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F10 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765) | QSA: 112,118 | valida_composicao_formalizacao | 112:APROVADO; 118:APROVADO; 281:APROVADO | — | APROVADO | CREATE_GE + INSERT_COMPONENTES |
| F11 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112,118 | valida_composicao_formalizacao | 112:APROVADO; 118:APROVADO; 281:APROVADO; 283:APROVADO | — | APROVADO | CREATE_GE + INSERT_COMPONENTES |
| F12 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F13 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F14 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:APROVADO; 118:APROVADO; 120:APROVADO; 281:APROVADO | — | APROVADO | CREATE_GE + INSERT_COMPONENTES |
| F15 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:APROVADO; 118:APROVADO; 120:APROVADO; 281:APROVADO; 283:APROVADO | — | APROVADO | CREATE_GE + INSERT_COMPONENTES |
| F16 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F17 | NOVO (tipo 5) | — | — | Massa-base | valida_composicao_formalizacao | — | — | REPROVADO | SEM_EVENTO_APROVADO |
| F18 | NOVO (tipo 5) | — | PF 281 (73002725765) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F19 | NOVO (tipo 5) | — | PF 281 (73002725765); PF 283 (73002745103) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F20 | NOVO (tipo 5) | — | PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F21 | NOVO (tipo 5) | — | PJ 112 (20010176000131) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F22 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112 | valida_composicao_formalizacao | 112:APROVADO; 281:APROVADO | — | APROVADO | CREATE_GE + INSERT_COMPONENTES |
| F23 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112 | valida_composicao_formalizacao | 112:APROVADO; 281:APROVADO; 283:APROVADO | — | APROVADO | CREATE_GE + INSERT_COMPONENTES |
| F24 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F25 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F26 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F27 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F28 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F29 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F30 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F31 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F32 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F33 | NOVO (tipo 6) | — | — | Massa-base | valida_composicao_formalizacao | — | — | REPROVADO | SEM_EVENTO_APROVADO |
| F34 | NOVO (tipo 6) | — | PF 281 (73002725765) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F35 | NOVO (tipo 6) | — | PF 281 (73002725765); PF 283 (73002745103) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F36 | NOVO (tipo 6) | — | PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | Massa-base | valida_composicao_formalizacao | 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F37 | NOVO (tipo 6) | — | PJ 112 (20010176000131) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F38 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F39 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F40 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112 | valida_composicao_formalizacao | 112:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F41 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F42 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F43 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F44 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112,118 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F45 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F46 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F47 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765); PF 283 (73002745103) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO; 283:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| F48 | NOVO (tipo 6) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PJ 120 (45639543000191); PF 281 (73002725765); PF 283 (73002745103); PF 285 (73002764582) | QSA: 112,118,120 | valida_composicao_formalizacao | 112:REPROVADO; 118:REPROVADO; 120:REPROVADO; 281:REPROVADO; 283:REPROVADO; 285:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
