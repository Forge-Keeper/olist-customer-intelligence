# Matriz de Unificação — U01 a U21

**Ação:** `cAcaoGrpEconm=4`. Verificar grupo primário, grupo(s) secundário(s), componentes comuns, participação societária e eventos de migração.

A regra `valida_composicao_unificacao` busca sócios com **>=50% em TODAS as PJs** da solicitação. A regra `valida_composicao_grupo_economico` exige composição no **GE primário**; com primário Isolado de uma PJ, o ramo recuperado tende a recusar (U04–U06).

Para não violar a restrição de sócio único do MEI, no U01 o cenário substitui a PJ68 (MEI) pela PJ112 (não MEI) **somente no snapshot do GE secundário 910102**. Os demais pares usam PJs não MEI.

| ID | GE primário (tipo) | Secundário (tipo) | PJs envolvidas (`cclub_cli`) | PFs controladoras (QSA) | Regra | Esperado | Efeito e observação |
|---|---|---|---|---|---|---|---|
| U01 | 910106 (1) | 910102 (1) | 84,88,66,112 | 111:50%+103:50% | `valida_composicao_grupo_economico` | CONDICIONAL | Controle comum 50/50 em todas as PJs; conferir eventos e tipo final |
| U02 | 910106 (1) | 910502 (5) | 84,88,92 | 111:50%+115:50% | `valida_composicao_grupo_economico` | CONDICIONAL | Controle comum 50/50 em todas as PJs; conferir eventos e tipo final |
| U03 | 910106 (1) | 910601 (6) | 84,88,104,106 | 111:50%+125:50% | `valida_composicao_grupo_economico` | CONDICIONAL | Controle comum 50/50 em todas as PJs; conferir eventos e tipo final |
| U04 | 910502 (5) | 910106 (1) | 92,84,88 | 115:50%+111:50% | `valida_composicao_grupo_economico` | RECUSA | Primário Isolado não atende o requisito atual de >=2 PJ no próprio GE |
| U05 | 910502 (5) | 910503 (5) | 92,94 | 115:50%+117:50% | `valida_composicao_grupo_economico` | RECUSA | Primário Isolado não atende o requisito atual de >=2 PJ no próprio GE |
| U06 | 910502 (5) | 910601 (6) | 92,104,106 | 115:50%+125:50% | `valida_composicao_grupo_economico` | RECUSA | Primário Isolado não atende o requisito atual de >=2 PJ no próprio GE |
| U07 | 910601 (6) | 910106 (1) | 104,106,84,88 | 125:50%+111:50% | `valida_composicao_grupo_economico` | CONDICIONAL | Controle comum 50/50 em todas as PJs; conferir eventos e tipo final |
| U08 | 910601 (6) | 910502 (5) | 104,106,92 | 125:50%+115:50% | `valida_composicao_grupo_economico` | CONDICIONAL | Controle comum 50/50 em todas as PJs; conferir eventos e tipo final |
| U09 | 910601 (6) | 910602 (6) | 104,106,108,110 | 125:50%+127:50% | `valida_composicao_grupo_economico` | CONDICIONAL | Controle comum 50/50 em todas as PJs; conferir eventos e tipo final |
| U10 | 910106 (1) | 910502 (5) | 84,88,92 | 111:100% | `valida_composicao_unificacao` | PARCIAL | Apenas a PF primária controla todas as PJs |
| U11 | 910106 (1) | 910502 (5) | 84,88,92 | 111:50%+115:50% | `valida_composicao_unificacao` | CONDICIONAL | Duas PFs com 50% em todas as PJs |
| U12 | 910106 (1) | 910502 (5) | 84,88,92 | 111:49.99%+115:50.01% | `valida_composicao_unificacao` | RECUSA | PF primária 49,99% em uma PJ; não controla todas |
| U13 | 910106 (1) | 910502 (5) | 84,88,92 | 115:100% | `valida_composicao_unificacao` | RECUSA | Sem controlador comum para todas as PJs |
| U14 | 910106 (1) | 910502 (5) | 84,88,92 | 111:50%+115:50% | `valida_composicao_unificacao` | CONDICIONAL | Dois controladores 50/50 |
| U15 | 910106 (1) | 910502 (5) | 84,88,92 |  | `valida_qsa` | RECUSA | QSA ausente de uma PJ |
| U16 | 910106 (1) | 910502 (5) | 84,88,92 | 111:49%+115:50% | `valida_qsa` | RECUSA | QSA 99% de uma PJ |
| U17 | 910106 (1) | 910502 (5) | 84,88,92 | 111:50%+111:50%+115:50% | `valida_qsa` | RECUSA | QSA com repetição e total 150% |
| U18 | 910106 (1) | 910502 (5) | 84,88,92 | 111:100% | `valida_composicao_unificacao` | PARCIAL | Parcial: PF secundária não elegível |
| U19 | 910106 (1) | 910502 (5) | 84,88,92 | 111:50%+115:50% | `left_anti_componentes_unificacao` | CONDICIONAL | Sobreposição PJ84 entre primário e secundário no snapshot |
| U20 | 910106 (1) | 910502 (5) | 84,88,92,104,106 | 111:50%+115:50% | `valida_composicao_unificacao` | CONDICIONAL | Unificação de três grupos com terceira PF potencialmente não elegível |
| U21 | 9999999 (inválido) | 910502 (5) | 92 | 111:50%+115:50% | `flag_ge_primario` | RECUSA | Primário ausente; falha controlada |

## Tabela-verdade e eventos

1. Garantir `flag_ge_primario` calculado segundo a primeira referência de grupo na solicitação, sem confundir com ordem física dos joins.
2. Garantir soma QSA 100% em cada PJ nos casos positivos. Sócios PF com 50% exatos são majoritários pela comparação inclusiva; 49,99% não são.
3. Conferir `flag_comp_unificacao` individualmente para PFs/PJs, incluindo aprovação parcial.
4. Grupo primário: decisão e tipo final homologados; secundários: `DELETE` apenas após aprovação; PJs/PFs migrados sem duplicidade (`left_anti`).
5. Não aceitar como sucesso a execução que deixa componentes em dois grupos ativos, com órfãos ou com duplicação de eventos.
6. U19 é um cenário negativo intencional de sobreposição no estado inicial; não transportar essa inconsistência ao cadastro canônico.

## Gate funcional

A lógica recuperada utiliza `info_qsa`, `info_componentes_ge`, `flag_socio_major_pj` e valida a composição do primário antes da materialização. Os casos `CONDICIONAL` só terão resultado final aprovado com evidência do processo CRT; não inventar a decisão de transição/eliminação.
