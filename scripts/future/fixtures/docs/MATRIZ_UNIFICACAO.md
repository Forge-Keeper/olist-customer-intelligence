# Matriz de Unificação — decisões binárias

**Casos:** 21. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| U01 | 910106 (tipo 1) + 910102 (tipo 1) | 84, 88, 111 / sec. 66, 103, 112 | PJ 66 (35650844000162); PF 103 (96641610047); PJ 112 (20010176000131) | QSA: 84,88,66,112; Secundário remove: 68; Secundário inclui: 112 | valida_composicao_grupo_economico | 66:APROVADO; 103:APROVADO; 112:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U02 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_grupo_economico | 92:APROVADO; 115:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U03 | 910106 (tipo 1) + 910601 (tipo 6) | 84, 88, 111 / sec. 104, 106, 125 | PJ 104 (99944451000144); PJ 106 (19271940000143); PF 125 (86038028404) | QSA: 84,88,104,106 | valida_composicao_grupo_economico | 104:APROVADO; 106:APROVADO; 125:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U04 | 910502 (tipo 5) + 910106 (tipo 1) | 92, 115 / sec. 84, 88, 111 | PJ 84 (31929392000100); PJ 88 (49043284000192); PF 111 (77449952602) | QSA: 92,84,88 | valida_composicao_grupo_economico | 84:REPROVADO; 88:REPROVADO; 111:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U05 | 910502 (tipo 5) + 910503 (tipo 5) | 92, 115 / sec. 94, 117 | PJ 94 (23211382000106); PF 117 (01860259391) | QSA: 92,94 | valida_composicao_grupo_economico | 94:REPROVADO; 117:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U06 | 910502 (tipo 5) + 910601 (tipo 6) | 92, 115 / sec. 104, 106, 125 | PJ 104 (99944451000144); PJ 106 (19271940000143); PF 125 (86038028404) | QSA: 92,104,106 | valida_composicao_grupo_economico | 104:REPROVADO; 106:REPROVADO; 125:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U07 | 910601 (tipo 6) + 910106 (tipo 1) | 104, 106, 125 / sec. 84, 88, 111 | PJ 84 (31929392000100); PJ 88 (49043284000192); PF 111 (77449952602) | QSA: 104,106,84,88 | valida_composicao_grupo_economico | 84:APROVADO; 88:APROVADO; 111:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U08 | 910601 (tipo 6) + 910502 (tipo 5) | 104, 106, 125 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 104,106,92 | valida_composicao_grupo_economico | 92:APROVADO; 115:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U09 | 910601 (tipo 6) + 910602 (tipo 6) | 104, 106, 125 / sec. 108, 110, 127 | PJ 108 (74254453000180); PJ 110 (05772590000194); PF 127 (24841583947) | QSA: 104,106,108,110 | valida_composicao_grupo_economico | 108:APROVADO; 110:APROVADO; 127:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U10 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:APROVADO; 115:REPROVADO | — | REPROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U11 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:APROVADO; 115:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U12 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U13 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U14 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:APROVADO; 115:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U15 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_qsa | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U16 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_qsa | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U17 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_qsa | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | SEM_EVENTO_APROVADO |
| U18 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:APROVADO; 115:REPROVADO | — | REPROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U19 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92; Secundário inclui: 84 | left_anti_componentes_unificacao | 92:APROVADO; 115:APROVADO | — | APROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U20 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 / sec. 92, 115 | PJ 92 (16412297000132); PF 115 (66609568910); PJ 104 (99944451000144); PJ 106 (19271940000143); PF 125 (86038028404) | QSA: 84,88,92,104,106 | valida_composicao_unificacao | 92:APROVADO; 115:APROVADO; 104:APROVADO; 106:APROVADO; 125:REPROVADO | — | REPROVADO | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U21 | 9999999 (tipo ?) + 910502 (tipo 5) | — | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 92 | flag_ge_primario | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Confirmar falha controlada; não há ramo explícito para GE primário inexistente |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
