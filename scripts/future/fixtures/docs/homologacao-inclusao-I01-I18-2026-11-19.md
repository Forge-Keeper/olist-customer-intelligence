# Homologação funcional — ação Inclusão (I01–I18)

**Status:** casos propostos, sujeitos à conferência com a massa existente e aceite de negócio. Ação `cAcaoGrpEconm = 2`. Os identificadores GE01–GE14 são aliases de planejamento, não códigos reais confirmados.

## 1. Objetivo

Definir a configuração inicial, os componentes das solicitações e a tabela-verdade para cada Inclusão antes de executar testes E2E.

## 2. Grupos-base propostos

| Grupo | Tipo | Uso |
|---|---:|---|
| GE01 | 1 | Positivos e lote misto |
| GE02 | 1 | Vínculos preexistentes |
| GE03 | 5 | Conversão de Isolado |
| GE04 | 5 | PF majoritária |
| GE05 | 6 | PJ/PF em Gerencial |
| GE06 | 1 | Conflito de CPF |
| GE07 | 1 | Documentos inválidos |
| GE08 | 1 | Situação de CNPJ e filial |
| GE09 | 1 | Natureza jurídica e QSA |
| GE10 | 5 | Sócio minoritário |
| GE11 | 1 | Componente repetido |
| GE12 | 5 | Reserva outras ações |
| GE13 | 6 | Reserva outras ações |
| GE14 | 1 | Reserva outras ações |

## 3. Matriz de Inclusão — grupos, componentes e expectativas

| Caso | Grupo-alvo | Componente solicitado (`cclub_cli`) | Pré-condições do cenário | Resultado preliminar | Regra avaliada |
|---|---|---|---|---|---|
| I01 | GE01 | PJ 0080 | Matriz, ativa, QSA 100%, sem vínculo ativo | APROVA | Inclusão PJ em Normal |
| I02 | GE01 | PF 0115 | CPF válido, majoritária >=50% na PJ pertinente, sem GE | APROVA | Inclusão PF em Normal |
| I03 | GE03 | PJ 0082 | Matriz, ativa, QSA 100%, sem GE | CONDICIONAL | Confirmar conversão 5→1 |
| I04 | GE04 | PF 0117 | CPF válido, participação >=50%, sem GE | CONDICIONAL | Aprova; confirmar manutenção tipo 5 |
| I05 | GE05 | PJ 0084 | PJ matriz ativa, QSA 100%, sem GE | CONDICIONAL | Confirmar inclusão PJ no tipo 6 |
| I06 | GE05 | PF 0119 | CPF válido, não vinculada, demais regras favoráveis | RECUSA | PF em tipo 6 |
| I07 | GE02 | PJ 0068 | Já ativa em GE02 | RECUSA | Componente já no mesmo GE |
| I08 | GE01 | PJ 0070 | Já ativa em GE02 | RECUSA | PJ em outro GE |
| I09 | GE01 | PF 0109 | Já ativa em GE06 | RECUSA | PF em outro GE |
| I10 | GE07 | PF 0121 | cindcd_cpf_valid != 1 | RECUSA | CPF inválido |
| I11 | GE07 | PJ 0086 | cindcd_cnpj_valid != 1 | RECUSA | CNPJ inválido |
| I12 | GE08 | PJ 0088 | rsit_docto_recta != ATIVA | RECUSA | CNPJ inativo |
| I13 | GE08 | PJ 0090 | rmtriz_flial_cnpj != '1' | RECUSA | Filial |
| I14 | GE09 | PJ 0092 | Natureza jurídica incompatível | PENDENTE | Confirmar regra e retorno |
| I15 | GE09 | PJ 0094 | QSA total 90%; demais flags favoráveis | RECUSA | QSA inconsistente |
| I16 | GE10 | PF 0123 | Participação 40% na PJ pertinente | RECUSA | PF não majoritária |
| I17 | GE01 | PJ 0096 + PF 0125 | Ambas válidas, QSA coerente, sem vínculos GE | APROVA | Inclusão conjunta sem duplicidade |
| I18 | GE11 | PJ 0098 repetida | Componente duplicado na solicitação | PENDENTE | Confirmar deduplicação ou recusa |

## 4. Construção das pré-condições

- Estado inicial: PJ 0068 ativa em GE02, PJ 0070 ativa em GE02 e PF 0109 ativa em GE06. Para os demais componentes novos, não gerar vínculo GE ativo incompatível.
- I02/I04: PF majoritária com no mínimo 50% da PJ pertinente ao GE; QSA total igual a 100%.
- I16: PF 0123 participa com 40% da PJ pertinente; outros sócios completam os 60% restantes.
- I15: reservar PJ 0094 com QSA inválido totalizando 90%, sem afetar outras PJs positivas.
- Nas recusas de causa única, manter todas as outras regras favoráveis para isolar a justificativa.
- Usar snapshot inicial restaurado por caso: I01, I02 e I17 não devem contaminar uns aos outros.
- Conciliar responsabilidade creditícia e QSA, sem equiparar contrato aberto a participação societária.

## 5. Tabela-verdade: foco da homologação de Inclusão

Uma linha por cenário deve registrar: `id_cenario`, `id_solicitacao`, `ge_alvo`, `tipo_ge_antes`, `componentes_antes`, `componentes_solicitados`, `qsa_aplicavel`, `responsabilidade_aplicavel`, `resultado_esperado`, `mensagens_esperadas`, `tipo_ge_depois`, `componentes_depois`, `eventos_esperados`, `parecer_negocio`.

**Validações identificadas no módulo de Inclusão:** CPF já em grupo ativo; CPF em tipo incompatível (fora de 1/5); CPF não majoritário; CPF inválido; CNPJ em grupo ativo; CNPJ filial; CNPJ inválido/inativo; QSA que não soma 100%.

**Aprovação:** somente inserir novos vínculos elegíveis, conservar os existentes, aplicar alteração do tipo de GE somente quando confirmada e gerar eventos sem duplicações.

**Recusa:** nenhuma alteração indevida do grupo; mensagens precisas de recusa; nenhum evento de inclusão aprovado.

**Pendências obrigatórias para aceite de negócio:** I03 (conversão tipo 5→1), I05 (PJ no tipo 6), I14 (regra de natureza jurídica), I18 (componente repetido). Confirmar também manutenção do tipo 5 em I04.

### Exemplo de tabela-verdade preenchida: I01

| Campo | Valor proposto |
|---|---|
| Estado inicial GE | GE01 tipo 1; componentes PJ 0062 e PF 0101 (sujeito à conferência) |
| Componente solicitado | PJ 0080 |
| Pré-condições | Matriz, ativa, QSA 100%, sem GE ativo |
| Resultado da solicitação | Aprovada |
| Componentes finais | PJ 0062, PF 0101, PJ 0080 |
| Persistência | Um novo vínculo PJ 0080; anteriores preservados |
| Evento esperado | Atualização de grupo aprovada, sem duplicidade, conforme contrato real |

## 6. Gates antes do E2E

1. Mapear todos os aliases GE aos IDs reais das tabelas já geradas.
2. Verificar existência, tipo e situação cadastral dos componentes; rever QSA de PJs controladas por PF e por PJ.
3. Validar datas, operações e o esquema real da responsabilidade creditícia.
4. Homologar com o negócio os resultados pendentes/condicionais e as mensagens.
5. Executar cada solicitação sobre snapshot conhecido e comparar todos os efeitos persistidos com a tabela-verdade.