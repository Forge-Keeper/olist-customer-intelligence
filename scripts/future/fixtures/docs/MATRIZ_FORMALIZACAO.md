# Matriz de Formalização — F01 a F48

**Ação:** `cAcaoGrpEconm=1`. **Status:** oráculos derivados das funções recuperadas, não testes executados ou aprovados pelo negócio.

Os 48 cenários correspondem a 3 tipos × 4 quantidades de PJ (0–3) × 4 quantidades de PF (0–3). Em Formalização o grupo é **NOVO**: não atribuir código existente. Os componentes não possuem GE ativo inicial.

## Matriz executável

| Caso | Tipo | PJ solicitadas (`cclub_cli`) | PF solicitadas (`cclub_cli`) | QSA de cada PJ no snapshot | Regra | Resultado preliminar | Efeito esperado |
|---|---:|---|---|---|---|---|---|
| F01 | 1 | — | — | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F02 | 1 | — | 281 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F03 | 1 | — | 281, 283 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F04 | 1 | — | 281, 283, 285 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F05 | 1 | 112 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F06 | 1 | 112 | 281 | 281=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F07 | 1 | 112 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F08 | 1 | 112 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F09 | 1 | 112, 118 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F10 | 1 | 112, 118 | 281 | 281=100% | `valida_composicao_formalizacao` | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F11 | 1 | 112, 118 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F12 | 1 | 112, 118 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F13 | 1 | 112, 118, 120 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F14 | 1 | 112, 118, 120 | 281 | 281=100% | `valida_composicao_formalizacao` | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F15 | 1 | 112, 118, 120 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F16 | 1 | 112, 118, 120 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F17 | 5 | — | — | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F18 | 5 | — | 281 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F19 | 5 | — | 281, 283 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F20 | 5 | — | 281, 283, 285 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F21 | 5 | 112 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F22 | 5 | 112 | 281 | 281=100% | `valida_composicao_formalizacao` | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F23 | 5 | 112 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | APROVA | CREATE_GE + INSERT_COMPONENTES |
| F24 | 5 | 112 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F25 | 5 | 112, 118 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F26 | 5 | 112, 118 | 281 | 281=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F27 | 5 | 112, 118 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F28 | 5 | 112, 118 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F29 | 5 | 112, 118, 120 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F30 | 5 | 112, 118, 120 | 281 | 281=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F31 | 5 | 112, 118, 120 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F32 | 5 | 112, 118, 120 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F33 | 6 | — | — | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F34 | 6 | — | 281 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F35 | 6 | — | 281, 283 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F36 | 6 | — | 281, 283, 285 | não aplicável | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F37 | 6 | 112 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F38 | 6 | 112 | 281 | 281=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F39 | 6 | 112 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F40 | 6 | 112 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F41 | 6 | 112, 118 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F42 | 6 | 112, 118 | 281 | 281=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F43 | 6 | 112, 118 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F44 | 6 | 112, 118 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F45 | 6 | 112, 118, 120 | — | 64=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F46 | 6 | 112, 118, 120 | 281 | 281=100% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F47 | 6 | 112, 118, 120 | 281, 283 | 281=50% + 283=50% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |
| F48 | 6 | 112, 118, 120 | 281, 283, 285 | 281=50% + 283=25% + 285=25% | `valida_composicao_formalizacao` | RECUSA | SEM_EVENTO_APROVADO |

## Restrições e contrato de teste

- `valida_composicao_formalizacao`: tipo 5 exige exatamente 1 PJ e 1–2 PF; tipo 1 exige 2 ou mais PJ e 1–2 PF; tipo 6 retorna `TIPO_NAO_MAPEADO` no ramo recuperado.
- `valida_socio_major_formalizacao`: PF precisa ter >=50% em alguma PJ pertinente; com três PF a composição 50/25/25 provoca também rejeição de minoritárias. O código recuperado monta retorno recusado, mas retorna dataframe intermediário — registrar eventual defeito em vez de alterar a expectativa estrutural.
- `valida_status_componente_formalizacao`: recusa de um componente deve contaminar a solicitação inteira conforme janela por `cSoltcAtdmt`.
- `gera_codigo_grupo_formalizacao`: nunca fixar novo código na solicitação; validar unicidade, ambiente correto e ausência de colisão.
- Validar em separado CPF/CNPJ, matriz, natureza jurídica, QSA100%, vínculo em outro GE e CPF maior/menor que 50%; usar a matriz de bordas para as variações.
- `qsa_substituir` é uma sobreposição exclusiva da execução, não modificação da massa canônica.

## Resultado de homologação

Cada linha requer ID de solicitação, execução em snapshot limpo, resposta por componente, número do grupo novo (quando aprovado), eventos, estado final e assinatura de negócio.
