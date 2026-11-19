# Regras do motor e rastreabilidade de cobertura

**Fonte:** quatro configurações de execução da camada de regras, consultadas em 19/11/2026. Os nomes na coluna `Regra no motor` são os nomes das funções chamadas no pipeline, não nomes arbitrários de testes.

**Importante:** os resultados esperados derivam da versão das regras disponível. **Cobertura planejada ≠ testes executados ≠ homologação concluída.** As regras de processadores CRT, sem implementação integral confirmada, têm identificadores `ORACULO_*` ou nomes funcionais marcados como inferidos.


## Formalização (ação 1)

| Regra no motor | Testes que exercitam | Confiança da regra |
|---|---|---|
| `init_validacao` | P01 | Configurada / comportamento a conferir em execução |
| `filtro_solicitacao_formalizacao` | F01–F48 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_em_outro_grupo` | FX01 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_ativo_receita` | FX02, FX03 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_matriz` | FX04 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_natureza_jurid` | FX05, FX13 | Configurada / comportamento a conferir em execução |
| `valida_qsa` | FX06, FX14 | Configurada / comportamento a conferir em execução |
| `valida_socios_sao_pf` | F34–F48 (tipo 6 com PF) | Configurada / comportamento a conferir em execução |
| `valida_cpf_em_outro_grupo` | FX07 | Configurada / comportamento a conferir em execução |
| `valida_cpf_ativo_receita` | FX08, FX12 | Configurada / comportamento a conferir em execução |
| `valida_socio_major_formalizacao` | FX09, F com 3 PF | Configurada / comportamento a conferir em execução |
| `valida_composicao_formalizacao` | F01–F48, B24–B26 | Configurada / comportamento a conferir em execução |
| `valida_status_componente_formalizacao` | FX10 | Configurada / comportamento a conferir em execução |
| `gera_codigo_grupo_formalizacao` | FX11 | Configurada / comportamento a conferir em execução |
| `finish_validacao` | P02 | Configurada / comportamento a conferir em execução |

## Inclusão (ação 2)

| Regra no motor | Testes que exercitam | Confiança da regra |
|---|---|---|
| `filtro_solicitacao_inclusao` | I01–I18 | Configurada / comportamento a conferir em execução |
| `init_validacao` | P01 | Configurada / comportamento a conferir em execução |
| `valida_cpf_em_outro_grupo` | I09, B22 | Configurada / comportamento a conferir em execução |
| `valida_socios_sao_pf` | I06, B23 | Configurada / comportamento a conferir em execução |
| `valida_socio_major` | I02, I16, B01–B04 | Configurada / comportamento a conferir em execução |
| `valida_cpf_ativo_receita` | I10, B05 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_em_outro_grupo` | I07, I08, B21 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_natureza_jurid` | I14, IX01, B12 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_matriz` | I13, B11 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_ativo_receita` | I11, I12, B07–B10 | Configurada / comportamento a conferir em execução |
| `valida_qsa` | I15, B14–B18 | Configurada / comportamento a conferir em execução |
| `finish_validacao` | P02 | Configurada / comportamento a conferir em execução |

## Exclusão (ação 3)

| Regra no motor | Testes que exercitam | Confiança da regra |
|---|---|---|
| `init_validacao` | P01 | Configurada / comportamento a conferir em execução |
| `flag_troca_componente` | E29, EX05, B32 | Configurada / comportamento a conferir em execução |
| `filtro_solicitacao_exclusao` | E01–E30 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_baixado` | E25, E26, EX01–EX03 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_responsabilidade` | E27, E28, EX04, B27–B30 | Configurada / comportamento a conferir em execução |
| `finish_validacao` | P02 | Configurada / comportamento a conferir em execução |

## Unificação (ação 4)

| Regra no motor | Testes que exercitam | Confiança da regra |
|---|---|---|
| `init_validacao` | P01 | Configurada / comportamento a conferir em execução |
| `filtro_solicitacao_unificacao` | U01–U21 | Configurada / comportamento a conferir em execução |
| `flag_ge_primario` | U21, UX06 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_ativo_receita` | UX01, UX02 | Configurada / comportamento a conferir em execução |
| `valida_cnpj_matriz` | UX03 | Configurada / comportamento a conferir em execução |
| `valida_qsa` | U15–U17, UX04 | Configurada / comportamento a conferir em execução |
| `valida_cpf_ativo_receita` | UX05 | Configurada / comportamento a conferir em execução |
| `valida_composicao_unificacao` | U10–U14, UX07, UX08 | Configurada / comportamento a conferir em execução |
| `valida_composicao_grupo_economico` | U04–U06, UX06 | Configurada / comportamento a conferir em execução |
| `finish_validacao` | P02 | Configurada / comportamento a conferir em execução |

## Regras de evento e processo (nomes de oráculos)

| Regra funcional a verificar | Casos principais | Limite de evidência |
|---|---|---|
| Conversão Normal → Isolado | E02, E04, E26 | Resultado depende do CRT de Exclusão e do consumidor de eventos |
| Cancelamento de GE sem PJ | E03, E05, E07, E09, E12, E14, E20, E23 | Confirmar DELETE de grupo e de componentes remanescentes |
| Exclusão parcial de PF e Gerencial | E15–E19, E24, E30 | Confirmar seleção apenas de componentes aprovados |
| Inclusão que modifica tipo de GE | I03, I04, I05 | Confirmar tipo final, não presumir conversão |
| Deduplicação de solicitação | I18, B35 | A função de deduplicação ainda não foi comprovada |
| Unificação com migração e `left_anti` | U01–U21, P12 | Confirmar secundários selecionados e ausência de INSERT repetido |
| Persistência, concorrência, reprocessamento e retorno | P01–P18 | Não considerar PASS sem evidência E2E |

## Achados que merecem teste de defeito, não alteração da massa para esconder

1. `valida_socio_major_formalizacao` monta uma saída com recusa, mas a versão recuperada retorna um DataFrame intermediário em vez do validado.
2. Preparação de QSA com agregação por `cclub_cli` do sócio pode fragmentar a soma por CNPJ titular, quando há vários sócios.
3. `flag_troca_componente` em versão recuperada utiliza janela pelo documento sem particionar por solicitação; testar vazamento entre pedidos simultâneos.
4. `valida_composicao_grupo_economico` examina a composição do GE primário antes da migração: primário Isolado de uma PJ pode ser recusado mesmo quando a unificação final teria mais PJs.
5. Regras que usam `!=` sobre `null` podem não retornar `True`; os testes nulos estão PENDENTES de comportamento observado.
6. As regras de grupo, responsável e QSA devem ser confrontadas com as etapas de enriquecimento atuais, pois flags derivadas incorretas podem invalidar o oráculo.
7. O gerador de código da Formalização não deve acessar namespace produtivo durante testes; validar resolução de ambiente e bloqueio da escrita não autorizada.

## Critério de encerramento

Cada regra acima deve ter pelo menos um caso positivo e um negativo quando o predicado o permitir, evidência do estado anterior, decisão por componente e efeito materializado. Ausência de fonte/contrato vira `BLOCKED`, não `PASS`. Casos `CONDICIONAL`/`PENDENTE` exigem homologação explícita.
