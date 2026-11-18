# Catálogo de cenários para a campanha E2E

Os identificadores abaixo são internos deste estudo. **Ainda não são IDs do Jira ou de uma ferramenta de testes**. O cenário esperado é uma hipótese verificável derivada das regras recuperadas; se a versão atual ou o requisito funcional discordar, registrar a divergência e ajustar o oráculo antes de aprovar o teste.

## 1. Formalização — 48 combinações de composição

Executar os três tipos (1, 5, 6) com quatro quantidades de PJ (0, 1, 2 e 3) cruzadas com quatro quantidades de PF (0, 1, 2 e 3). Isso dá 16 configurações por tipo, **48 casos**.

| Tipo | Estrutura aprovada pelo ramo recuperado | Principais negativas |
|---|---|---|
| Normal (1) | 2 ou 3 PJs e 1 ou 2 PFs | 0 PJ, 0 PF, 1 PJ, 3 PFs |
| Isolado (5) | 1 PJ e 1 ou 2 PFs | 0 PJ, 0 PF, 2+ PJs, 3 PFs |
| Gerencial (6) | Sem ramo explícito de aprovação | Composição não mapeada; verificar requisito atual |

Ampliar com QSA total 100% / diferente de 100%, CPF válido/inválido, CNPJ ativo/inativo, matriz/filial, natureza permitida/não permitida, sócio majoritário presente/ausente, componente já associado a outro GE, aprovação parcial e geração de código de novo GE. Não contar essas variantes como já executadas nas 48 combinações estruturais.

Pontos de atenção: a versão recuperada de `valida_socio_major_formalizacao` monta um DataFrame de rejeição, mas retorna outro; `valida_composicao_formalizacao` referencia uma flag calculada mais adiante. Validar o comportamento real e registrar defeito se persistir.

## 2. Inclusão — 18 casos-base

| ID | Situação | O que conferir |
|---|---|---|
| I01 | PJ nova em GE normal | Novo componente; GE segue normal |
| I02 | PF nova em GE normal | Novo componente; GE atualizado uma vez |
| I03 | PJ nova em GE isolado | Possível conversão do GE 5→1 |
| I04 | PF nova em GE isolado | Manutenção do tipo, sem evento duplicado |
| I05 | PJ nova em GE gerencial | Comportamento de tipo 6 e eventos |
| I06 | PF nova em GE gerencial | Rejeição pelo ramo de tipo na versão recuperada |
| I07 | PJ já presente no próprio GE | Duplicidade / decisão correta |
| I08 | PJ em outro GE | Bloqueio de vínculo |
| I09 | PF em outro GE | Bloqueio de vínculo |
| I10 | CPF inválido | Rejeição |
| I11 | CNPJ inválido | Rejeição |
| I12 | CNPJ não ativo na Receita | Rejeição |
| I13 | CNPJ filial | Rejeição |
| I14 | Natureza jurídica não permitida | Rejeição |
| I15 | QSA diferente de 100% | Rejeição |
| I16 | PF não majoritária | Rejeição |
| I17 | Inclusão de PJ e PF no mesmo GE/lote | Sem dois eventos de grupo |
| I18 | Componente repetido no lote | Sem duplicação indevida |

Conferir ambos os caminhos de preparação de componente (PJ e PF), `unionByName`, `distinct` e `left_anti` no processador CRT.

## 3. Exclusão — 30 casos-base

| ID | Estado inicial / ação | Efeito que queremos observar |
|---|---|---|
| E01 | Normal 3 PJ, exclui 1 PJ | GE continua normal |
| E02 | Normal 3 PJ, exclui 2 | Converte para isolado |
| E03 | Normal 3 PJ, exclui 3 | Cancela GE e componentes |
| E04 | Normal 2 PJ, exclui 1 | Converte para isolado |
| E05 | Normal 2 PJ, exclui 2 | Cancela GE |
| E06 | Normal anômalo 1 PJ, exclui 1 | Tratamento do último PJ |
| E07 | Isolado 1 PJ, exclui 1 | Cancela GE |
| E08 | Isolado anômalo 2 PJ, exclui 1 | Comportamento de borda |
| E09 | Isolado anômalo 2 PJ, exclui 2 | Cancela GE |
| E10 | Gerencial 3 PJ, exclui 1 | Mantém tipo 6 se ativo |
| E11 | Gerencial 3 PJ, exclui 2 | Resta 1 PJ; observar tipo 6 |
| E12 | Gerencial 3 PJ, exclui 3 | Cancela GE |
| E13 | Gerencial 2 PJ, exclui 1 | Preserva tipo 6 |
| E14 | Gerencial 2 PJ, exclui 2 | Cancela GE |
| E15 | Exclui 1 PF de normal | DELETE componente e UPDATE GE |
| E16 | Exclui última PF de normal | Composição pós-exclusão |
| E17 | Exclui PF de isolado | Atualização sem DELETE indevido |
| E18 | Exclui PF de gerencial | Preservação do tipo |
| E19 | Exclui PJ e PF no mesmo GE | Não duplicar evento de grupo |
| E20 | Cancela GE com PJ e PF | DELETE em lote para componentes |
| E21 | Componente não existe no GE ativo | Join sem resultado; erro/decisão |
| E22 | Documento pertence a outro GE | Nunca apagar o grupo errado |
| E23 | Exclui 2 PJs na mesma solicitação | Contagens de PJ |
| E24 | Exclui várias PFs | Deduplicação |
| E25 | Excluir PJ ATIVA na Receita | Rejeição salvo exceção aplicável |
| E26 | Excluir PJ BAIXADA/INAPTA | Caminho cadastral positivo |
| E27 | Excluir PJ com responsabilidade ativa | Rejeição |
| E28 | Excluir PJ sem responsabilidade ativa | Prosseguimento |
| E29 | Exclusão e inclusão do mesmo documento | `tem_acao_2` |
| E30 | Aprovação parcial | Nenhum efeito sobre recusados |

Estressar limites adicionais de 0, 1, 2 e 3 PJs e quantidades removidas de zero até o total. Não assumir que o tipo 6 vira isolado; o ramo de conversão recuperado é explícito para o tipo 1. Confirmar também a elegibilidade funcional de PF na exclusão: existem variantes de `rules_exclusao.py` com condições diferentes.

## 4. Unificação — 21 casos-base

As primeiras nove combinações cruzam tipo do **GE primário** com tipo do **GE secundário**. Usar a sequência: N→N, N→I, N→G, I→N, I→I, I→G, G→N, G→I, G→G (N=Normal, I=Isolado, G=Gerencial). Em cada caso, comparar os eventos do primário, exclusão do secundário e migração de componentes.

| ID | Composição adicional | Teste esperado |
|---|---|---|
| U10 | Um PF com 100% em todas as PJs | Controle comum |
| U11 | Um PF com 50% em todas | Limite inclusivo |
| U12 | PF com 49,99% em uma PJ | Sem controle comum |
| U13 | PJs com controladores diferentes | Sem PF comum |
| U14 | Dois PFs com 50% em todas | Ambos elegíveis |
| U15 | PJ sem QSA | Ausência de controlador |
| U16 | QSA soma ≠100% | Rejeição de QSA |
| U17 | Sócio replicado no QSA | Deduplicação |
| U18 | Parte aprovada, parte recusada | Sem DELETE/migração indevida |
| U19 | Componente já presente no primário | `left_anti` impede novo INSERT |
| U20 | Três ou mais GEs numa unificação | Todos secundários tratados |
| U21 | GE primário ausente/inconsistente | Rejeição/falha controlada |

O código recuperado busca **PF com participação >=50% em todas as PJs**. É essencial exercitar os casos com PJ majoritária do nosso QSA para descobrir como isso afeta a validação. Há também um risco importante: o CRT de unificação seleciona um par solicitação/primário se ao menos um resultado estiver OK. A seleção de GE secundário para exclusão deve ser verificada em casos parcialmente aprovados.

## 5. Pares ordenados de ações — 16

São quatro ações cruzadas com as quatro, incluindo a mesma ação duas vezes:

| Primeira | Segunda | O que observar |
|---|---|---|
| Formalização | Formalização | Reaproveitamento de pessoas |
| Formalização | Inclusão | Novo componente após criar GE |
| Formalização | Exclusão | Exclusão após formalização |
| Formalização | Unificação | GE recém-formalizado como participante |
| Inclusão | Formalização | Documento compartilhado |
| Inclusão | Inclusão | Inclusões repetidas |
| Inclusão | Exclusão | Inclusão seguida de remoção |
| Inclusão | Unificação | Migração após inclusão |
| Exclusão | Formalização | Reutilização do componente |
| Exclusão | Inclusão | Troca de GE; `tem_acao_2` |
| Exclusão | Exclusão | Exclusão duplicada |
| Exclusão | Unificação | Estado após exclusão parcial |
| Unificação | Formalização | Reaproveitamento pós-migração |
| Unificação | Inclusão | Inclusão no GE resultante |
| Unificação | Exclusão | Exclusão após migrar |
| Unificação | Unificação | Participação em duas unificações |

Executar os pares com **mesma solicitação** onde o contrato permitir e com **solicitações distintas em sequência**. A janela de `flag_troca_componente` no ledger está particionada pelo documento, não pela solicitação; testar também interferência entre solicitações independentes.

## 6. Atualização da solicitação, eventos e integração — 18

| ID | Teste |
|---|---|
| P01 | Decisão OK marcada no componente original |
| P02 | Decisão recusada e motivo preservados |
| P03 | Aprovação parcial corretamente refletida |
| P04 | Chave `ação_documento` em múltiplas ações |
| P05 | Mesmo documento em solicitações diferentes |
| P06 | MERGE por `_id` e `cSoltcAtdmt` |
| P07 | Sem correspondência no destino da solicitação |
| P08 | Filtro exclusivo do primário em unificação |
| P09 | DELETE de grupo e componentes na exclusão total |
| P10 | Exclusão parcial sem DELETE de GE |
| P11 | Inclusão conjunta de PF/PJ sem evento duplicado |
| P12 | Unificação de componente já existente no primário |
| P13 | Reprocessamento da mesma solicitação (idempotência) |
| P14 | Duas execuções concorrentes |
| P15 | Falha entre MERGE da solicitação e escrita de eventos |
| P16 | Evento sem correspondente ativo |
| P17 | Isolamento DV/HO: nenhuma leitura/escrita produtiva |
| P18 | Resultado correto no Frontend, a partir do Backend |

Atenção especial: os CRTs recuperados escrevem eventos com `append`. Um `distinct()` não impede duplicidade entre duas execuções.

## 7. Variações transversais a acrescentar

- CPF válido, inválido, nulo e ausente no cadastro.
- CNPJ válido/inválido, matriz/filial; situações ATIVA, BAIXADA, INAPTA, outras e nula.
- Natureza jurídica permitida, não permitida e ausente.
- QSA: 0, 49,99, 50, 50,01, 99,99, 100 e >100%; sócios PF/PJ; sem sócio; vínculos duplicados e data de origem concorrente; sentinela de percentual.
- Responsabilidade: ausente, ativa, encerrada, última versão ativa, última versão excluída.
- Componente no próprio GE, em outro GE, duplicado e sem grupo.
- Dados nulos, join vazio, documentos inconsistentes, falta de fonte, replay e concorrência.

Essas são **variações necessárias para fechar ramos não cobertos**; não considerar 151 como uma contagem final exaustiva.
