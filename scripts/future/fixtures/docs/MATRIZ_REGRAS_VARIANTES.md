# Matriz complementar: cobertura das regras por ação (30 casos)

Esses testes isolam regras compartilhadas **dentro de Formalização e Unificação**, evitando supor que um teste de Inclusão cobre automaticamente a aplicação da mesma função em outra ação. Incluem ainda duas variáveis de Exclusão e Inclusão.

| Caso | Ação | GE | Componentes solicitados (`cclub_cli`) | Preparo por cenário | Regra implementada | Esperado |
|---|---|---|---|---|---|---|
| FX01 | 1 | NOVO | 84, 281 | PJ já em GE ativo (910106) | `valida_cnpj_em_outro_grupo` | RECUSA |
| FX02 | 1 | NOVO | 112, 281 | Indicador CNPJ inválido | `valida_cnpj_ativo_receita` | RECUSA |
| FX03 | 1 | NOVO | 112, 281 | CNPJ inativo | `valida_cnpj_ativo_receita` | RECUSA |
| FX04 | 1 | NOVO | 112, 281 | PJ filial | `valida_cnpj_matriz` | RECUSA |
| FX05 | 1 | NOVO | 112, 281 | Natureza jurídica não permitida | `valida_cnpj_natureza_jurid` | RECUSA |
| FX06 | 1 | NOVO | 112, 281 | QSA com soma 90% | `valida_qsa` | RECUSA |
| FX07 | 1 | NOVO | 112, 113 | PF já ativa em GE910501 | `valida_cpf_em_outro_grupo` | RECUSA |
| FX08 | 1 | NOVO | 112, 281 | CPF com indicador inválido | `valida_cpf_ativo_receita` | RECUSA |
| FX09 | 1 | NOVO | 112, 281 | CPF minoritário com 40% | `valida_socio_major_formalizacao` | RECUSA |
| FX10 | 1 | NOVO | 112, 118, 281 | Propagação: uma PJ irregular recusa toda solicitação | `valida_status_componente_formalizacao` | RECUSA |
| FX11 | 1 | NOVO | passo 1: 112, 118, 281; passo 2: 120, 283 | Duas solicitações aprovadas devem gerar códigos distintos | `gera_codigo_grupo_formalizacao` | CONDICIONAL |
| FX12 | 1 | NOVO | 112, 281 | Flag de CPF nula e sem resultado explícito de null | `valida_cpf_ativo_receita` | PENDENTE |
| FX13 | 1 | NOVO | 112, 281 | Natureza jurídica nula | `valida_cnpj_natureza_jurid` | PENDENTE |
| FX14 | 1 | NOVO | 112, 281 | QSA não encontrado | `valida_qsa` | PENDENTE |
| UX01 | 4 | 910106 | 92, 115 | CNPJ inválido na unificação | `valida_cnpj_ativo_receita` | RECUSA |
| UX02 | 4 | 910106 | 92, 115 | CNPJ INAPTA na unificação | `valida_cnpj_ativo_receita` | RECUSA |
| UX03 | 4 | 910106 | 92, 115 | CNPJ filial em unificação | `valida_cnpj_matriz` | RECUSA |
| UX04 | 4 | 910106 | 92, 115 | Soma de QSA 99 na unificação | `valida_qsa` | RECUSA |
| UX05 | 4 | 910106 | 92, 115 | CPF do primário inválido | `valida_cpf_ativo_receita` | RECUSA |
| UX06 | 4 | 910502 | 84, 88, 111 | Inversão de grupo primário passa a Isolado com 1 PJ | `flag_ge_primario` | RECUSA |
| UX07 | 4 | 910106 | 92, 115 | Controle comum 50/50 em todas as PJs | `valida_composicao_unificacao` | CONDICIONAL |
| UX08 | 4 | 910106 | 92, 115 | PF primária 49,99 em uma PJ | `valida_composicao_unificacao` | RECUSA |
| UX09 | 4 | 910106 | 92, 115 | QSA nulo/ausente no enriquecimento | `valida_composicao_unificacao` | PENDENTE |
| EX01 | 3 | 910101 | 62 | PJ BAIXADA e sem responsabilidade | `valida_cnpj_baixado` | APROVA |
| EX02 | 3 | 910101 | 64 | PJ INAPTA e sem responsabilidade | `valida_cnpj_baixado` | APROVA |
| EX03 | 3 | 910101 | 62 | PJ ATIVA sem ação 2 | `valida_cnpj_baixado` | RECUSA |
| EX04 | 3 | 910104 | 74 | PJ BAIXADA com operação aberta | `valida_cnpj_responsabilidade` | RECUSA |
| EX05 | 3 | 910104 | 74 | PJ ativa e responsável com Inclusão no mesmo pedido | `flag_troca_componente` | CONDICIONAL |
| IX01 | 2 | 910101 | 112 | PJ natureza permitida e QSA 100 | `valida_cnpj_natureza_jurid` | APROVA |
| IX02 | 2 | 910104 | 281 | PF 50% em PJ74; isolando participação | `valida_socio_major` | APROVA |

## Regras de homologação

- `PENDENTE`: ausência ou `null` não implica automaticamente recusa em expressões PySpark triestadas; validar flag e retorno real.
- Casos FX01–FX14 exercitam os ramos compartilhados no fluxo de Formalização com o tipo de grupo 5 (exceto FX10/FX11, tipo 1).
- Casos UX01–UX09 exercitam `valida_cnpj_ativo_receita`, `valida_cnpj_matriz`, `valida_qsa`, `valida_cpf_ativo_receita`, `flag_ge_primario`, `valida_composicao_unificacao` e composição do primário.
- Casos EX01–EX05 abordam flag de troca e responsabilidade associada ao documento; não assumir que crédito aberto é motivo de recusa de Inclusão.
- `qsa_substituir` é temporário por caso, não deve produzir persistência cumulativa.
- Testes de regra não comprovam geração de eventos: comparar também `resul_soltc`, alterações de solicitação e tabelas de staging/consumo.
