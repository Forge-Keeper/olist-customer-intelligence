# Matriz de Variantes de regras — decisões binárias

**Casos:** 30. **Versão:** 4.0.0.

> **Oráculo do Motor:** somente `APROVADO` ou `REPROVADO`. No código recuperado, esses valores correspondem semanticamente a `OK` e `Solicitacao Recusada`. A homologação ainda não foi executada.

Um teste pode ter componentes com decisões diferentes, mas a expectativa consolidada da solicitação é **REPROVADO** se pelo menos um componente for reprovado. A validação de eventos e do estado final é independente, não uma terceira decisão.

**Status das expectativas:** todas são propostas de homologação. As classificadas como hipótese no JSON precisam de confirmação funcional; nenhuma é evidência de execução.

| ID | GE e tipo | Componentes antes (`cclub_cli`) | Ação e componentes solicitados (`cclub_cli`, documento) | Preparação exclusiva do caso | Regra-alvo | Decisão por componente | Decisão por passo | **Resultado do Motor** | Efeito a verificar |
|---|---|---|---|---|---|---|---|---|---|
| FX01 | NOVO (tipo 5) | — | PJ 84 (31929392000100); PF 281 (73002725765) | QSA: 84 | valida_cnpj_em_outro_grupo | 84:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX02 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 112 | valida_cnpj_ativo_receita | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX03 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 112 | valida_cnpj_ativo_receita | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX04 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 112 | valida_cnpj_matriz | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX05 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 112 | valida_cnpj_natureza_jurid | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX06 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112 | valida_qsa | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX07 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 113 (63124847504) | QSA: 112 | valida_cpf_em_outro_grupo | 112:REPROVADO; 113:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX08 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 281 | valida_cpf_ativo_receita | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX09 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112 | valida_socio_major_formalizacao | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX10 | NOVO (tipo 1) | — | PJ 112 (20010176000131); PJ 118 (52592529000145); PF 281 (73002725765) | QSA: 112,118; Cadastro: 118 | valida_status_componente_formalizacao | 112:REPROVADO; 118:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX11 | NOVO (tipo 1) | — | P1 ação 1: 112, 118, 281 → P2 ação 1: 120, 283 | QSA: 112,118; Duas solicitações independentes | gera_codigo_grupo_formalizacao | 112:APROVADO; 118:APROVADO; 281:APROVADO; 120:APROVADO; 283:APROVADO | P1=APROVADO; P2=APROVADO | APROVADO | Conferir decisão e estado materializado |
| FX12 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 281 | valida_cpf_ativo_receita | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX13 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112; Cadastro: 112 | valida_cnpj_natureza_jurid | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| FX14 | NOVO (tipo 5) | — | PJ 112 (20010176000131); PF 281 (73002725765) | QSA: 112 | valida_qsa | 112:REPROVADO; 281:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX01 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92; Cadastro: 92 | valida_cnpj_ativo_receita | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX02 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92; Cadastro: 92 | valida_cnpj_ativo_receita | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX03 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92; Cadastro: 92 | valida_cnpj_matriz | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX04 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_qsa | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX05 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92; Cadastro: 111 | valida_cpf_ativo_receita | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX06 | 910502 (tipo 5) + 910106 (tipo 1) | 92, 115 | PJ 84 (31929392000100); PJ 88 (49043284000192); PF 111 (77449952602) | QSA: 84,88,92 | flag_ge_primario | 84:REPROVADO; 88:REPROVADO; 111:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX07 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:APROVADO; 115:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| UX08 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| UX09 | 910106 (tipo 1) + 910502 (tipo 5) | 84, 88, 111 | PJ 92 (16412297000132); PF 115 (66609568910) | QSA: 84,88,92 | valida_composicao_unificacao | 92:REPROVADO; 115:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| EX01 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119) | Cadastro: 62 | valida_cnpj_baixado | 62:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| EX02 | 910101 (tipo 1) | 62, 64, 101 | PJ 64 (47911744000121) | Cadastro: 64 | valida_cnpj_baixado | 64:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| EX03 | 910101 (tipo 1) | 62, 64, 101 | PJ 62 (39070293000119) | Cadastro: 62 | valida_cnpj_baixado | 62:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| EX04 | 910104 (tipo 1) | 74, 76, 107 | PJ 74 (75538340000108) | Cadastro: 74 | valida_cnpj_responsabilidade | 74:REPROVADO | — | REPROVADO | Conferir decisão e estado materializado |
| EX05 | 910104 (tipo 1) | 74, 76, 107 | PJ 74 (75538340000108) | Cadastro: 74; Ação 2 de Inclusão do MESMO documento na MESMA solicitação, com tem_acao_2 derivada das ações; sem ela, REPROVAR. | flag_troca_componente | 74:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| IX01 | 910101 (tipo 1) | 62, 64, 101 | PJ 112 (20010176000131) | Cadastro: 112 | valida_cnpj_natureza_jurid | 112:APROVADO | — | APROVADO | Conferir decisão e estado materializado |
| IX02 | 910104 (tipo 1) | 74, 76, 107 | PF 281 (73002725765) | QSA: 74 | valida_socio_major | 281:APROVADO | — | APROVADO | Conferir decisão e estado materializado |

## Critérios de aceite

- `APROVADO` e `REPROVADO` são as únicas decisões permitidas para o Motor; não usar status de testes, eventos ou homologação na coluna de resultado.
- Para decisões negativas, registrar a mensagem exata da regra (ou o defeito se o Motor não produzir recusa), sem alterar os dados para disfarçar divergências.
- Para aprovação, conferir também efeito persistido e eventos de GE/componente; status do motor não substitui a verificação do processador.
- Os campos `preparo` são overlays de snapshot, não mudanças permanentes na massa.
- A matriz e os resultados são **expectativas de teste ainda não homologadas**. Ver os critérios técnicos detalhados no JSON e no [plano](PLANO_TESTES.md).
