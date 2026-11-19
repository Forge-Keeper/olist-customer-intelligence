# Matriz detalhada consolidada — quatro ações e testes complementares

**217 cenários:** 48 Formalização, 18 Inclusão, 30 Exclusão, 21 Unificação, 16 pares de ações, 18 de integração, 36 de limites e 30 variantes específicas por regra.

**Estado:** expectativas documentadas; nenhuma execução ou homologação de negócio realizada nesta entrega.

A fonte canônica de cada linha é `catalogo_total.json`, com documentos, atributos, grupos, quadros societários e condições por snapshot.

| Caso | GE primário/segundário | Componentes solicitados (`cclub_cli`) | Preparo de QSA, cadastro e membros | Regra foco | Resultado | Efeito esperado / status |
|---|---|---|---|---|---|---|
| F01 | NOVO | — | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F02 | NOVO | 281 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F03 | NOVO | 281,283 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F04 | NOVO | 281,283,285 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F05 | NOVO | 112 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F06 | NOVO | 112,281 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F07 | NOVO | 112,281,283 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F08 | NOVO | 112,281,283,285 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F09 | NOVO | 112,118 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F10 | NOVO | 112,118,281 | QSA 112,118 | valida_composicao_formalizacao | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F11 | NOVO | 112,118,281,283 | QSA 112,118 | valida_composicao_formalizacao | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F12 | NOVO | 112,118,281,283,285 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F13 | NOVO | 112,118,120 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F14 | NOVO | 112,118,120,281 | QSA 112,118,120 | valida_composicao_formalizacao | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F15 | NOVO | 112,118,120,281,283 | QSA 112,118,120 | valida_composicao_formalizacao | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F16 | NOVO | 112,118,120,281,283,285 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F17 | NOVO | — | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F18 | NOVO | 281 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F19 | NOVO | 281,283 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F20 | NOVO | 281,283,285 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F21 | NOVO | 112 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F22 | NOVO | 112,281 | QSA 112 | valida_composicao_formalizacao | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F23 | NOVO | 112,281,283 | QSA 112 | valida_composicao_formalizacao | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F24 | NOVO | 112,281,283,285 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F25 | NOVO | 112,118 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F26 | NOVO | 112,118,281 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F27 | NOVO | 112,118,281,283 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F28 | NOVO | 112,118,281,283,285 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F29 | NOVO | 112,118,120 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F30 | NOVO | 112,118,120,281 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F31 | NOVO | 112,118,120,281,283 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F32 | NOVO | 112,118,120,281,283,285 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F33 | NOVO | — | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F34 | NOVO | 281 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F35 | NOVO | 281,283 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F36 | NOVO | 281,283,285 | estado base | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F37 | NOVO | 112 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F38 | NOVO | 112,281 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F39 | NOVO | 112,281,283 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F40 | NOVO | 112,281,283,285 | QSA 112 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F41 | NOVO | 112,118 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F42 | NOVO | 112,118,281 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F43 | NOVO | 112,118,281,283 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F44 | NOVO | 112,118,281,283,285 | QSA 112,118 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F45 | NOVO | 112,118,120 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F46 | NOVO | 112,118,120,281 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F47 | NOVO | 112,118,120,281,283 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| F48 | NOVO | 112,118,120,281,283,285 | QSA 112,118,120 | valida_composicao_formalizacao | RECUSA | SEM_EVENTO_APROVADO |
| I01 | 910101 | 112 | estado base | valida_qsa | APROVA | UPDATE (confirmar CRT) |
| I02 | 910104 | 299 | QSA 74 | valida_socio_major | APROVA | UPDATE (confirmar CRT) |
| I03 | 910502 | 118 | estado base | valida_qsa | CONDICIONAL | UPDATE (confirmar CRT) |
| I04 | 910505 | 297 | QSA 98 | valida_socio_major | CONDICIONAL | UPDATE (confirmar CRT) |
| I05 | 910605 | 112 | estado base | valida_cnpj_natureza_jurid | CONDICIONAL | UPDATE (confirmar CRT) |
| I06 | 910604 | 295 | QSA 124 | valida_socios_sao_pf | RECUSA | NENHUM |
| I07 | 910101 | 62 | estado base | valida_cnpj_em_outro_grupo | RECUSA | NENHUM |
| I08 | 910102 | 64 | estado base | valida_cnpj_em_outro_grupo | RECUSA | NENHUM |
| I09 | 910103 | 113 | estado base | valida_cpf_em_outro_grupo | RECUSA | NENHUM |
| I10 | 910104 | 291 | QSA 74; CAD 291 | valida_cpf_ativo_receita | RECUSA | NENHUM |
| I11 | 910103 | 112 | CAD 112 | valida_cnpj_ativo_receita | RECUSA | NENHUM |
| I12 | 910105 | 112 | CAD 112 | valida_cnpj_ativo_receita | RECUSA | NENHUM |
| I13 | 910106 | 112 | CAD 112 | valida_cnpj_matriz | RECUSA | NENHUM |
| I14 | 910102 | 112 | CAD 112 | valida_cnpj_natureza_jurid | RECUSA | NENHUM |
| I15 | 910103 | 112 | QSA 112 | valida_qsa | RECUSA | NENHUM |
| I16 | 910505 | 289 | QSA 98 | valida_socio_major | RECUSA | NENHUM |
| I17 | 910101 | 112,287 | QSA 112 | valida_socio_major | CONDICIONAL | UPDATE (confirmar CRT) |
| I18 | 910106 | 112,112 | estado base | deduplicacao_solicitacao_inclusao | PENDENTE | UPDATE (confirmar CRT) |
| E01 | 910101 | 112 | CAD 112; MEMBROS+112 | exclusao_pj_parcial | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E02 | 910101 | 62,112 | CAD 62,112; MEMBROS+112 | conversao_normal_isolado | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E03 | 910101 | 62,64,112 | CAD 62,64,112; MEMBROS+112 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E04 | 910101 | 62 | CAD 62 | conversao_normal_isolado | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E05 | 910101 | 62,64 | CAD 62,64 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E06 | 910101 | 62 | CAD 62; MEMBROS-64 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E07 | 910502 | 92 | CAD 92 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E08 | 910502 | 112 | CAD 112; MEMBROS+112 | exclusao_isolado_anomalo | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E09 | 910502 | 92,112 | CAD 92,112; MEMBROS+112 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E10 | 910601 | 112 | CAD 112; MEMBROS+112 | exclusao_gerencial | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E11 | 910601 | 104,112 | CAD 104,112; MEMBROS+112 | exclusao_gerencial | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E12 | 910601 | 104,106,112 | CAD 104,106,112; MEMBROS+112 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E13 | 910602 | 108 | CAD 108 | exclusao_gerencial | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E14 | 910602 | 108,110 | CAD 108,110 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E15 | 910101 | 101 | estado base | exclusao_pf | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E16 | 910102 | 103 | estado base | composicao_ge_sem_pf | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E17 | 910502 | 115 | estado base | exclusao_pf_isolado | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E18 | 910601 | 125 | estado base | exclusao_pf_gerencial | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E19 | 910102 | 66,103 | CAD 66 | exclusao_mista | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E20 | 910502 | 92,115 | CAD 92 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E21 | 910101 | 112 | CAD 112 | componente_inexistente_no_ge | PENDENTE | CONFIRMAR_CRT_COMPOSICAO |
| E22 | 910101 | 68 | CAD 68 | componente_de_outro_ge | PENDENTE | CONFIRMAR_CRT_COMPOSICAO |
| E23 | 910103 | 70,72 | CAD 70,72 | cancelamento_ge_sem_pj | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E24 | 910101 | 101,281 | MEMBROS+281 | exclusao_multiplas_pf | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E25 | 910101 | 62 | CAD 62 | valida_cnpj_baixado | RECUSA | NENHUM |
| E26 | 910101 | 62 | CAD 62 | valida_cnpj_baixado | APROVA | DELETE_COMPONENTE + UPDATE_GE |
| E27 | 910104 | 74 | CAD 74 | valida_cnpj_responsabilidade | RECUSA | NENHUM |
| E28 | 910101 | 64 | CAD 64 | valida_cnpj_responsabilidade | APROVA | DELETE_COMPONENTE + UPDATE_GE |
| E29 | 910104 | 74 | CAD 74 | flag_troca_componente | CONDICIONAL | CONFIRMAR_CRT_COMPOSICAO |
| E30 | 910104 | 74,76 | CAD 74,76 | valida_cnpj_responsabilidade | PARCIAL | CONFIRMAR_CRT_COMPOSICAO |
| U01 | 910106 → 910102 | 66,103,112 | QSA 84,88,66,112; SEC+112; SEC-68 | valida_composicao_grupo_economico | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U02 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_grupo_economico | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U03 | 910106 → 910601 | 104,106,125 | QSA 84,88,104,106 | valida_composicao_grupo_economico | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U04 | 910502 → 910106 | 84,88,111 | QSA 92,84,88 | valida_composicao_grupo_economico | RECUSA | SEM_EVENTO_APROVADO |
| U05 | 910502 → 910503 | 94,117 | QSA 92,94 | valida_composicao_grupo_economico | RECUSA | SEM_EVENTO_APROVADO |
| U06 | 910502 → 910601 | 104,106,125 | QSA 92,104,106 | valida_composicao_grupo_economico | RECUSA | SEM_EVENTO_APROVADO |
| U07 | 910601 → 910106 | 84,88,111 | QSA 104,106,84,88 | valida_composicao_grupo_economico | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U08 | 910601 → 910502 | 92,115 | QSA 104,106,92 | valida_composicao_grupo_economico | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U09 | 910601 → 910602 | 108,110,127 | QSA 104,106,108,110 | valida_composicao_grupo_economico | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U10 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | PARCIAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U11 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U12 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | RECUSA | SEM_EVENTO_APROVADO |
| U13 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | RECUSA | SEM_EVENTO_APROVADO |
| U14 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U15 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_qsa | RECUSA | SEM_EVENTO_APROVADO |
| U16 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_qsa | RECUSA | SEM_EVENTO_APROVADO |
| U17 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_qsa | RECUSA | SEM_EVENTO_APROVADO |
| U18 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | PARCIAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U19 | 910106 → 910502 | 92,115 | QSA 84,88,92; SEC+84 | left_anti_componentes_unificacao | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U20 | 910106 → 910502 | 92,115,104,106,125 | QSA 84,88,92,104,106 | valida_composicao_unificacao | CONDICIONAL | UPDATE_GE_PRIMARIO + DELETE_GE_SECUNDARIO + MIGRACAO_SE_ELEGIVEL |
| U21 | 9999999 → 910502 | 92,115 | QSA 92 | flag_ge_primario | PENDENTE | SEM_EVENTO_APROVADO |
| C01 | 910106 | 112,281 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C02 | 910106 | 112,281,118 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C03 | 910106 | 112,281,84 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C04 | 910106 | 112,281,92,115 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C05 | 910106 | 118,283 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C06 | 910106 | 118 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C07 | 910106 | 118 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C08 | 910106 | 118,92,115 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C09 | 910106 | 84,112,281 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C10 | 910106 | 84 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C11 | 910106 | 84 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C12 | 910106 | 84,92,115 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C13 | 910106 | 92,115,283 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C14 | 910106 | 92,115,118 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C15 | 910106 | 92,115 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| C16 | 910106 | 92,115 | estado base | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO | PENDENTE_CONTRATO_DE_SEQUENCIA | Compor efeitos sem duplicação, respeitar recusas e estado intermediário |
| P01 | 910106 | 112,281 | estado base | init_validacao | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P02 | 910101 | 62,64 | estado base | finish_validacao | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P03 | 910106 | 112,281 | estado base | valida_status_componente_formalizacao | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P04 | 910101 | 62,64 | estado base | ORACULO_CHAVE_ACAO_DOCUMENTO | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P05 | 910106 | 112,281 | estado base | ORACULO_ISOLAMENTO_SOLICITACAO | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P06 | 910101 | 62,64 | estado base | ORACULO_MERGE_SOLICITACAO | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P07 | 910106 | 112,281 | estado base | ORACULO_MERGE_SEM_MATCH | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P08 | 910101 | 62,64 | estado base | flag_ge_primario | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P09 | 910106 | 112,281 | estado base | ORACULO_CRT_DELETE_GRUPO | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P10 | 910101 | 62,64 | estado base | ORACULO_CRT_DELETE_COMPONENTE | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P11 | 910106 | 112,281 | estado base | ORACULO_CRT_INCLUSAO_SEM_DUPLICIDADE | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P12 | 910101 | 62,64 | estado base | ORACULO_CRT_UNIFICACAO_LEFT_ANTI | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P13 | 910106 | 112,281 | estado base | ORACULO_IDEMPOTENCIA_CRT | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P14 | 910101 | 62,64 | estado base | ORACULO_CONCORRENCIA | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P15 | 910106 | 112,281 | estado base | ORACULO_RECUPERACAO_PARCIAL | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P16 | 910101 | 62,64 | estado base | ORACULO_EVENTOS_INTEGRIDADE | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P17 | 910106 | 112,281 | estado base | ORACULO_ISOLAMENTO_AMBIENTE | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| P18 | 910101 | 62,64 | estado base | ORACULO_RETORNO_PONTA_A_PONTA | A_DEFINIR_ORACULO_DE_INTEGRACAO | Coerência entre decisão, atualização da solicitação, eventos e materialização |
| B01 | 910104 | 299 | QSA 74=107:50+299:50 | valida_socio_major | APROVA | Conferir contrato de eventos |
| B02 | 910104 | 299 | QSA 74=107:50.01+299:49.99 | valida_socio_major | RECUSA | Conferir contrato de eventos |
| B03 | 910104 | 299 | QSA 74=107:49.99+299:50.01 | valida_socio_major | APROVA | Conferir contrato de eventos |
| B04 | 910104 | 299 | QSA 74=107:100 | valida_socio_major | PENDENTE | Conferir contrato de eventos |
| B05 | 910104 | 299 | QSA 74=107:50+299:50; CAD 299.cindcd_cpf_valid=null | valida_cpf_ativo_receita | PENDENTE | Conferir contrato de eventos |
| B06 | 910104 | 293 | CAD 293.remover_cadastro=true | ORACULO_CPF_AUSENTE | PENDENTE | Conferir contrato de eventos |
| B07 | 910101 | 112 | CAD 112.rscit=ATIVA | valida_cnpj_ativo_receita | APROVA | Conferir contrato de eventos |
| B08 | 910101 | 112 | CAD 112.cindcd_cnpj_valid=0 | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| B09 | 910101 | 112 | CAD 112.rsit_docto_recta=INAPTA | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| B10 | 910101 | 112 | CAD 112.rsit_docto_recta=BAIXADA | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| B11 | 910101 | 112 | CAD 112.rmtriz_flial_cnpj=2 | valida_cnpj_matriz | RECUSA | Conferir contrato de eventos |
| B12 | 910101 | 112 | CAD 112.rnatur_jurid=Organização Religiosa | valida_cnpj_natureza_jurid | RECUSA | Conferir contrato de eventos |
| B13 | 910101 | 112 | CAD 112.rnatur_jurid=null | valida_cnpj_natureza_jurid | PENDENTE | Conferir contrato de eventos |
| B14 | 910101 | 112 | QSA 112=SEM_SOCIOS | valida_qsa | PENDENTE | Conferir contrato de eventos |
| B15 | 910101 | 112 | QSA 112=64:99.99 | valida_qsa | RECUSA | Conferir contrato de eventos |
| B16 | 910101 | 112 | QSA 112=64:100 | valida_qsa | APROVA | Conferir contrato de eventos |
| B17 | 910101 | 112 | QSA 112=64:100.01 | valida_qsa | RECUSA | Conferir contrato de eventos |
| B18 | 910101 | 118 | QSA 118=64:100 | valida_qsa | APROVA | Conferir contrato de eventos |
| B19 | 910104 | 299 | QSA 74=299:50+299:50 | valida_socio_major | PENDENTE | Conferir contrato de eventos |
| B20 | 910106 | 92,115 | QSA 84=64:100 | valida_composicao_unificacao | PENDENTE | Conferir contrato de eventos |
| B21 | 910102 | 62 | estado base | valida_cnpj_em_outro_grupo | RECUSA | Conferir contrato de eventos |
| B22 | 910101 | 101 | estado base | valida_cpf_em_outro_grupo | RECUSA | Conferir contrato de eventos |
| B23 | 910604 | 299 | QSA 124=117:50+299:50 | valida_socios_sao_pf | RECUSA | Conferir contrato de eventos |
| B24 | NOVO | 281 | estado base | valida_composicao_formalizacao | RECUSA | Conferir contrato de eventos |
| B25 | NOVO | 112 | estado base | valida_composicao_formalizacao | RECUSA | Conferir contrato de eventos |
| B26 | NOVO | 112,281,283,285 | QSA 112=281:50+283:25+285:25 | valida_composicao_formalizacao | RECUSA | Conferir contrato de eventos |
| B27 | 910104 | 74 | CAD 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=true | valida_cnpj_responsabilidade | RECUSA | Conferir contrato de eventos |
| B28 | 910101 | 62 | CAD 62.rsit_docto_recta=BAIXADA;62.flag_resp_empr=false | valida_cnpj_responsabilidade | APROVA | Conferir contrato de eventos |
| B29 | 910104 | 74 | CAD 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=false | valida_cnpj_responsabilidade | APROVA | Conferir contrato de eventos |
| B30 | 910104 | 74 | CAD 74.rsit_docto_recta=BAIXADA;74.flag_resp_empr=null | valida_cnpj_responsabilidade | PENDENTE | Conferir contrato de eventos |
| B31 | 910101 | 62 | CAD 62.rsit_docto_recta=ATIVA;62.flag_resp_empr=false;62.tem_acao_2=0 | valida_cnpj_baixado | RECUSA | Conferir contrato de eventos |
| B32 | 910104 | 74 | CAD 74.rsit_docto_recta=ATIVA;74.flag_resp_empr=true;74.tem_acao_2=1 | flag_troca_componente | CONDICIONAL | Conferir contrato de eventos |
| B33 | 910502 | 84,88,111 | estado base | valida_composicao_grupo_economico | RECUSA | Conferir contrato de eventos |
| B34 | 910106 | 92,115,104,106,125 | estado base | valida_composicao_unificacao | CONDICIONAL | Conferir contrato de eventos |
| B35 | 910101 | 112,112 | estado base | ORACULO_DEDUPLICACAO_SOLICITACAO | PENDENTE | Conferir contrato de eventos |
| B36 | 910104 | 74 | CAD 74.rsit_docto_recta=BAIXADA;74.dt_fim_contrato=2026-11-19 | valida_cnpj_responsabilidade | PENDENTE | Conferir contrato de eventos |
| FX01 | NOVO | 84,281 | QSA 84 | valida_cnpj_em_outro_grupo | RECUSA | Conferir contrato de eventos |
| FX02 | NOVO | 112,281 | QSA 112; CAD 112 | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| FX03 | NOVO | 112,281 | QSA 112; CAD 112 | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| FX04 | NOVO | 112,281 | QSA 112; CAD 112 | valida_cnpj_matriz | RECUSA | Conferir contrato de eventos |
| FX05 | NOVO | 112,281 | QSA 112; CAD 112 | valida_cnpj_natureza_jurid | RECUSA | Conferir contrato de eventos |
| FX06 | NOVO | 112,281 | QSA 112 | valida_qsa | RECUSA | Conferir contrato de eventos |
| FX07 | NOVO | 112,113 | QSA 112 | valida_cpf_em_outro_grupo | RECUSA | Conferir contrato de eventos |
| FX08 | NOVO | 112,281 | QSA 112; CAD 281 | valida_cpf_ativo_receita | RECUSA | Conferir contrato de eventos |
| FX09 | NOVO | 112,281 | QSA 112 | valida_socio_major_formalizacao | RECUSA | Conferir contrato de eventos |
| FX10 | NOVO | 112,118,281 | QSA 112,118; CAD 118 | valida_status_componente_formalizacao | RECUSA | Conferir contrato de eventos |
| FX11 | NOVO | passo 1: 112,118,281; passo 2: 120,283 | QSA 112,118 | gera_codigo_grupo_formalizacao | CONDICIONAL | Conferir contrato de eventos |
| FX12 | NOVO | 112,281 | QSA 112; CAD 281 | valida_cpf_ativo_receita | PENDENTE | Conferir contrato de eventos |
| FX13 | NOVO | 112,281 | QSA 112; CAD 112 | valida_cnpj_natureza_jurid | PENDENTE | Conferir contrato de eventos |
| FX14 | NOVO | 112,281 | QSA 112 | valida_qsa | PENDENTE | Conferir contrato de eventos |
| UX01 | 910106 → 910502 | 92,115 | QSA 84,88,92; CAD 92 | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| UX02 | 910106 → 910502 | 92,115 | QSA 84,88,92; CAD 92 | valida_cnpj_ativo_receita | RECUSA | Conferir contrato de eventos |
| UX03 | 910106 → 910502 | 92,115 | QSA 84,88,92; CAD 92 | valida_cnpj_matriz | RECUSA | Conferir contrato de eventos |
| UX04 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_qsa | RECUSA | Conferir contrato de eventos |
| UX05 | 910106 → 910502 | 92,115 | QSA 84,88,92; CAD 111 | valida_cpf_ativo_receita | RECUSA | Conferir contrato de eventos |
| UX06 | 910502 → 910106 | 84,88,111 | QSA 84,88,92 | flag_ge_primario | RECUSA | Conferir contrato de eventos |
| UX07 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | CONDICIONAL | Conferir contrato de eventos |
| UX08 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | RECUSA | Conferir contrato de eventos |
| UX09 | 910106 → 910502 | 92,115 | QSA 84,88,92 | valida_composicao_unificacao | PENDENTE | Conferir contrato de eventos |
| EX01 | 910101 | 62 | CAD 62 | valida_cnpj_baixado | APROVA | Conferir contrato de eventos |
| EX02 | 910101 | 64 | CAD 64 | valida_cnpj_baixado | APROVA | Conferir contrato de eventos |
| EX03 | 910101 | 62 | CAD 62 | valida_cnpj_baixado | RECUSA | Conferir contrato de eventos |
| EX04 | 910104 | 74 | CAD 74 | valida_cnpj_responsabilidade | RECUSA | Conferir contrato de eventos |
| EX05 | 910104 | 74 | CAD 74 | flag_troca_componente | CONDICIONAL | Conferir contrato de eventos |
| IX01 | 910101 | 112 | CAD 112 | valida_cnpj_natureza_jurid | APROVA | Conferir contrato de eventos |
| IX02 | 910104 | 281 | QSA 74 | valida_socio_major | APROVA | Conferir contrato de eventos |

## Índice operacional por ação

| Escopo | Casos | Matriz de detalhe | Dados estruturados |
|---|---:|---|---|
| Formalização | 48 | [MATRIZ_FORMALIZACAO.md](MATRIZ_FORMALIZACAO.md) | [catalogo_formalizacao.json](catalogo_formalizacao.json) |
| Inclusão | 18 | [MATRIZ_INCLUSAO.md](MATRIZ_INCLUSAO.md) | [catalogo_inclusao.json](catalogo_inclusao.json) |
| Exclusão | 30 | [MATRIZ_EXCLUSAO.md](MATRIZ_EXCLUSAO.md) | [catalogo_exclusao.json](catalogo_exclusao.json) |
| Unificação | 21 | [MATRIZ_UNIFICACAO.md](MATRIZ_UNIFICACAO.md) | [catalogo_unificacao.json](catalogo_unificacao.json) |
| Pares e integração | 34 | [MATRIZ_INTEGRACAO.md](MATRIZ_INTEGRACAO.md) | [catalogo_integracao.json](catalogo_integracao.json) |
| Limites | 36 | [MATRIZ_LIMITES.md](MATRIZ_LIMITES.md) | [catalogo_limites.json](catalogo_limites.json) |
| Variantes de regras | 30 | [MATRIZ_REGRAS_VARIANTES.md](MATRIZ_REGRAS_VARIANTES.md) | [catalogo_variantes_regras.json](catalogo_variantes_regras.json) |

## Liberação para homologação

- Reconciliar 100 PF e 100 PJ existentes com as fixtures e sincronizar as PFs 281–299 de cenário, sem duplicar `cclub_cli`.
- Confirmar QSA dos MEIs na fonte atual; os seis Isolados não MEI foram ajustados no arquivo de QSA.
- Aplicar overlays exclusivos por cenário, restaurando snapshots antes de cada teste.
- Validar as regras em execução, não apenas o nome do método; resultados condicionais e pendentes exigem aprovação funcional.
- Comparar eventos e tabelas materializadas por componente e por grupo, inclusive idempotência e efeito em concorrência.
