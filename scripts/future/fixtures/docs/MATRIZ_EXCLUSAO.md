# Matriz de Exclusão — E01 a E30

**Ação:** `cAcaoGrpEconm=3`. **Critério:** status `BAIXADA` ou `INAPTA` para PJ, ausência de responsabilidade ativa, salvo troca com Inclusão da mesma solicitação (`tem_acao_2=1`). Para PF, as duas regras de CNPJ não se aplicam.

O código do validador compartilhado está indicado como `valida_cnpj_baixado` e `valida_cnpj_responsabilidade`; as regras de transição de tipo/cancelamento são nomes funcionais propostos quando o código CRT completo não foi comprovado.

| Caso | GE real | Componentes antes (`cclub_cli`) | Excluir | Cadastro / responsabilidade preparados | Regra foco | Esperado | Pós-estado em análise |
|---|---:|---|---|---|---|---|---|
| E01 | 910101 | 62, 64, 101, 112 | 112 | 112:BAIXADA | exclusao_pj_parcial | CONDICIONAL | Normal com 3 PJ, remove 1 PJ |
| E02 | 910101 | 62, 64, 101, 112 | 62, 112 | 62:BAIXADA,112:BAIXADA | conversao_normal_isolado | CONDICIONAL | Normal com 3 PJ, remove 2; resta 1 PJ |
| E03 | 910101 | 62, 64, 101, 112 | 62, 64, 112 | 62:BAIXADA,64:BAIXADA,112:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Normal com 3 PJ, remove todas |
| E04 | 910101 | 62, 64, 101 | 62 | 62:BAIXADA | conversao_normal_isolado | CONDICIONAL | Normal com 2 PJ, remove uma |
| E05 | 910101 | 62, 64, 101 | 62, 64 | 62:BAIXADA,64:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Normal com 2 PJ, remove as duas |
| E06 | 910101 | 62, 101 | 62 | 62:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Normal anômalo com 1 PJ, remove última |
| E07 | 910502 | 92, 115 | 92 | 92:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Isolado com 1 PJ, remove última |
| E08 | 910502 | 92, 115, 112 | 112 | 112:BAIXADA | exclusao_isolado_anomalo | CONDICIONAL | Isolado anômalo com 2 PJs, remove uma |
| E09 | 910502 | 92, 115, 112 | 92, 112 | 92:BAIXADA,112:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Isolado anômalo com 2 PJ, remove ambas |
| E10 | 910601 | 104, 106, 125, 112 | 112 | 112:BAIXADA | exclusao_gerencial | CONDICIONAL | Gerencial com 3 PJ, remove uma |
| E11 | 910601 | 104, 106, 125, 112 | 104, 112 | 104:BAIXADA,112:BAIXADA | exclusao_gerencial | CONDICIONAL | Gerencial com 3 PJ, remove duas |
| E12 | 910601 | 104, 106, 125, 112 | 104, 106, 112 | 104:BAIXADA,106:BAIXADA,112:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Gerencial com 3 PJ, remove todas |
| E13 | 910602 | 108, 110, 127 | 108 | 108:BAIXADA | exclusao_gerencial | CONDICIONAL | Gerencial com 2 PJ, remove uma |
| E14 | 910602 | 108, 110, 127 | 108, 110 | 108:BAIXADA,110:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Gerencial com 2 PJ, remove ambas |
| E15 | 910101 | 62, 64, 101 | 101 | PF sem gate cadastral | exclusao_pf | CONDICIONAL | Excluir PF de grupo Normal |
| E16 | 910102 | 66, 68, 103 | 103 | PF sem gate cadastral | composicao_ge_sem_pf | CONDICIONAL | Excluir última PF de Normal |
| E17 | 910502 | 92, 115 | 115 | PF sem gate cadastral | exclusao_pf_isolado | CONDICIONAL | Excluir PF de Isolado |
| E18 | 910601 | 104, 106, 125 | 125 | PF sem gate cadastral | exclusao_pf_gerencial | CONDICIONAL | Excluir PF de Gerencial |
| E19 | 910102 | 66, 68, 103 | 66, 103 | 66:BAIXADA | exclusao_mista | CONDICIONAL | Excluir PJ + PF simultaneamente |
| E20 | 910502 | 92, 115 | 92, 115 | 92:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Excluir grupo todo PJ+PF |
| E21 | 910101 | 62, 64, 101 | 112 | 112:BAIXADA | componente_inexistente_no_ge | PENDENTE | Componente livre não pertence ao GE |
| E22 | 910101 | 62, 64, 101 | 68 | 68:BAIXADA | componente_de_outro_ge | PENDENTE | PJ pertence ao GE910102 |
| E23 | 910103 | 70, 72, 105 | 70, 72 | 70:BAIXADA,72:BAIXADA | cancelamento_ge_sem_pj | CONDICIONAL | Excluir ambas as PJs do Normal |
| E24 | 910101 | 62, 64, 101, 281 | 101, 281 | PF sem gate cadastral | exclusao_multiplas_pf | CONDICIONAL | Excluir duas PFs em snapshot com 2 PFs |
| E25 | 910101 | 62, 64, 101 | 62 | 62:ATIVA | valida_cnpj_baixado | RECUSA | CNPJ ATIVA sem ação 2 e sem responsabilidade |
| E26 | 910101 | 62, 64, 101 | 62 | 62:BAIXADA | valida_cnpj_baixado | APROVA | CNPJ BAIXADA sem responsabilidade |
| E27 | 910104 | 74, 76, 107 | 74 | 74:BAIXADA+RESP | valida_cnpj_responsabilidade | RECUSA | CNPJ BAIXADA mas com contrato aberto |
| E28 | 910101 | 62, 64, 101 | 64 | 64:INAPTA | valida_cnpj_responsabilidade | APROVA | CNPJ INAPTA e sem responsabilidade |
| E29 | 910104 | 74, 76, 107 | 74 | 74:ATIVA+RESP | flag_troca_componente | CONDICIONAL | CNPJ ATIVA+contrato, porém troca via inclusão na mesma solicitação |
| E30 | 910104 | 74, 76, 107 | 74, 76 | 74:BAIXADA+RESP,76:BAIXADA | valida_cnpj_responsabilidade | PARCIAL | PJ74 recusada por contrato; PJ76 elegível |

## Regras e contratos

- **Recusa:** `valida_cnpj_baixado` reprova PJ ativa sem `tem_acao_2`; `valida_cnpj_responsabilidade` reprova PJ com `flag_resp_empr=true` sem a exceção. Não associar responsabilidade ativa a participação societária.
- **Troca:** E29 precisa estar associada a Inclusão do mesmo documento; a simples existência da flag não dispensa checagem de escopo, conforme comportamento de `flag_troca_componente`.
- **Eventos:** manter duas verificações separadas: retorno do motor e efeitos `UPDATE/DELETE` de GE/componente. Os casos condicionais não são homologados até confirmar o CRT.
- **Estado de partida:** alterações `componentes_preparo_add/rem` são apenas do snapshot, não da solicitação. Validar integridade/reversibilidade dos overlays e restaurar massa-base depois.
- **Parcialidade:** no E30, a PJ74 permanece ativa e a PJ76 poderá ser removida se o processador permitir aprovação por componente.
- **Casos E21/E22:** componente inexistente ou de outro GE pode não alcançar a regra por ausência do join; resultado e mensagem dependem do fluxo real e exigem tratamento controlado.

## Aceite

Registrar código GE, tipo anterior/posterior, quantidade PJ/PF antes e depois, flags cadastrais e de responsabilidade, solicitação, decisão de cada componente, eventos e estado persistido.
