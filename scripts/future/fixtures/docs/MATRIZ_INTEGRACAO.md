# Matriz de Integração e sequências — decisões binárias

**Casos:** 34. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| C01 | 910106 (tipo 1) | — | P1 ação 1: 112, 281 → P2 ação 1: 112, 281 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 112:REPROVADO; 281:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C02 | 910106 (tipo 1) | — | P1 ação 1: 112, 281 → P2 ação 2: 118 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 118:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C03 | 910106 (tipo 1) | — | P1 ação 1: 112, 281 → P2 ação 3: 112 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 112:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C04 | 910106 (tipo 1) | — | P1 ação 1: 112, 281 → P2 ação 4: 92, 115 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 92:REPROVADO; 115:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C05 | 910106 (tipo 1) | — | P1 ação 2: 118 → P2 ação 1: 118, 283 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 118:REPROVADO; 283:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C06 | 910106 (tipo 1) | — | P1 ação 2: 118 → P2 ação 2: 118 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 118:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C07 | 910106 (tipo 1) | — | P1 ação 2: 118 → P2 ação 3: 118 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 118:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C08 | 910106 (tipo 1) | — | P1 ação 2: 118 → P2 ação 4: 92, 115 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 92:REPROVADO; 115:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C09 | 910106 (tipo 1) | — | P1 ação 3: 84 → P2 ação 1: 112, 281 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 112:APROVADO; 281:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C10 | 910106 (tipo 1) | — | P1 ação 3: 84 → P2 ação 2: 84 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 84:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C11 | 910106 (tipo 1) | — | P1 ação 3: 84 → P2 ação 3: 84 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 84:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C12 | 910106 (tipo 1) | — | P1 ação 3: 84 → P2 ação 4: 92, 115 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 92:REPROVADO; 115:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C13 | 910106 (tipo 1) | — | P1 ação 4: 92, 115 → P2 ação 1: 92, 283 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 92:REPROVADO; 283:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C14 | 910106 (tipo 1) | — | P1 ação 4: 92, 115 → P2 ação 2: 118 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 118:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C15 | 910106 (tipo 1) | — | P1 ação 4: 92, 115 → P2 ação 3: 92 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 92:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C16 | 910106 (tipo 1) | — | P1 ação 4: 92, 115 → P2 ação 4: 92, 115 | Massa-base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | 92:REPROVADO; 115:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| P01 | 910106 (tipo 1) | — | P1 ação 2: 112 | Massa-base | init_validacao | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P02 | 910101 (tipo 1) | — | P1 ação 2: 112 | Massa-base | finish_validacao | 112:REPROVADO | P1=REPROVADO | REPROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P03 | 910106 (tipo 1) | — | P1 ação 1: 112, 118, 281 | Massa-base | valida_status_componente_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO | P1=REPROVADO | REPROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P04 | 910101 (tipo 1) | — | P1 ação 2: 118 → P2 ação 2: 118 | Massa-base | ORACULO_CHAVE_ACAO_DOCUMENTO | 118:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P05 | 910106 (tipo 1) | — | P1 ação 2: 118 → P2 ação 2: 118 | Massa-base | ORACULO_ISOLAMENTO_SOLICITACAO | 118:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P06 | 910101 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_MERGE_SOLICITACAO | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P07 | 910106 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_MERGE_SEM_MATCH | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P08 | 910101 (tipo 1) | — | P1 ação 4: 66, 103, 112 | Massa-base | flag_ge_primario | 66:APROVADO; 103:APROVADO; 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P09 | 910106 (tipo 1) | — | P1 ação 3: 92, 115 | Massa-base | ORACULO_CRT_DELETE_GRUPO | 92:APROVADO; 115:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P10 | 910101 (tipo 1) | — | P1 ação 3: 112 | Massa-base | ORACULO_CRT_DELETE_COMPONENTE | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P11 | 910106 (tipo 1) | — | P1 ação 2: 112, 287 | Massa-base | ORACULO_CRT_INCLUSAO_SEM_DUPLICIDADE | 112:APROVADO; 287:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P12 | 910101 (tipo 1) | — | P1 ação 4: 92, 115 | Massa-base | ORACULO_CRT_UNIFICACAO_LEFT_ANTI | 92:APROVADO; 115:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P13 | 910106 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_IDEMPOTENCIA_CRT | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P14 | 910101 (tipo 1) | — | P1 ação 2: 118 → P2 ação 2: 118 | Massa-base | ORACULO_CONCORRENCIA | 118:REPROVADO | P1=APROVADO; P2=REPROVADO | REPROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P15 | 910106 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_RECUPERACAO_PARCIAL | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P16 | 910101 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_EVENTOS_INTEGRIDADE | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P17 | 910106 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_ISOLAMENTO_AMBIENTE | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P18 | 910101 (tipo 1) | — | P1 ação 2: 112 | Massa-base | ORACULO_RETORNO_PONTA_A_PONTA | 112:APROVADO | P1=APROVADO | APROVADO | Coerência entre decisão, atualização da solicitação, eventos e materialização |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
