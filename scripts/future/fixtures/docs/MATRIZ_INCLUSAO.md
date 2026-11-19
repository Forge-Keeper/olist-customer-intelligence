# Matriz de Inclusão — decisões binárias

**Casos:** 18. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| I01 | 910101 (tipo 1) | 62, 64, 101 | PJ 112 (20010176000131) | Massa-base | valida_qsa | 112:APROVADO | — | APROVADO | UPDATE (confirmar CRT) |
| I02 | 910104 (tipo 1) | 74, 76, 107 | PF 299 (73002900354) | QSA: 74 | valida_socio_major | 299:APROVADO | — | APROVADO | UPDATE (confirmar CRT) |
| I03 | 910502 (tipo 5) | 92, 115 | PJ 118 (52592529000145) | Massa-base | valida_qsa | 118:APROVADO | — | APROVADO | UPDATE (confirmar CRT) |
| I04 | 910505 (tipo 5) | 98, 121 | PF 297 (73002880906) | QSA: 98 | valida_socio_major | 297:APROVADO | — | APROVADO | UPDATE (confirmar CRT) |
| I05 | 910605 (tipo 6) | 126, 128, 133 | PJ 112 (20010176000131) | Massa-base | valida_cnpj_natureza_jurid | 112:APROVADO | — | APROVADO | UPDATE (confirmar CRT) |
| I06 | 910604 (tipo 6) | 122, 124, 131 | PF 295 (73002861510) | QSA: 124 | valida_socios_sao_pf | 295:REPROVADO | — | REPROVADO | NENHUM |
| I07 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119) | Massa-base | valida_cnpj_em_outro_grupo | 62:REPROVADO | — | REPROVADO | NENHUM |
| I08 | 910102 (tipo 1) | 66, 68, 103 | PJ 64 (47911744000121) | Massa-base | valida_cnpj_em_outro_grupo | 64:REPROVADO | — | REPROVADO | NENHUM |
| I09 | 910103 (tipo 1) | 70, 72, 105 | PF 113 (63124847504) | Massa-base | valida_cpf_em_outro_grupo | 113:REPROVADO | — | REPROVADO | NENHUM |
| I10 | 910104 (tipo 1) | 74, 76, 107 | PF 291 (73002822701) | QSA: 74; Cadastro: 291 | valida_cpf_ativo_receita | 291:REPROVADO | — | REPROVADO | NENHUM |
| I11 | 910103 (tipo 1) | 70, 72, 105 | PJ 112 (20010176000131) | Cadastro: 112 | valida_cnpj_ativo_receita | 112:REPROVADO | — | REPROVADO | NENHUM |
| I12 | 910105 (tipo 1) | 80, 82, 109 | PJ 112 (20010176000131) | Cadastro: 112 | valida_cnpj_ativo_receita | 112:REPROVADO | — | REPROVADO | NENHUM |
| I13 | 910106 (tipo 1) | 84, 88, 111 | PJ 112 (20010176000131) | Cadastro: 112 | valida_cnpj_matriz | 112:REPROVADO | — | REPROVADO | NENHUM |
| I14 | 910102 (tipo 1) | 66, 68, 103 | PJ 112 (20010176000131) | Cadastro: 112 | valida_cnpj_natureza_jurid | 112:REPROVADO | — | REPROVADO | NENHUM |
| I15 | 910103 (tipo 1) | 70, 72, 105 | PJ 112 (20010176000131) | QSA: 112 | valida_qsa | 112:REPROVADO | — | REPROVADO | NENHUM |
| I16 | 910505 (tipo 5) | 98, 121 | PF 289 (73002803316) | QSA: 98 | valida_socio_major | 289:REPROVADO | — | REPROVADO | NENHUM |
| I17 | 910101 (tipo 1) | 62, 64, 101 | PJ 112 (20010176000131); PF 287 (73002783960) | QSA: 112 | valida_socio_major | 112:APROVADO; 287:APROVADO | — | APROVADO | UPDATE (confirmar CRT) |
| I18 | 910106 (tipo 1) | 84, 88, 111 | PJ 112 (20010176000131); PJ 112 (20010176000131) | Massa-base | deduplicacao_solicitacao_inclusao | 112:REPROVADO; 112:REPROVADO | — | REPROVADO | UPDATE (confirmar CRT) |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
