# Matriz de integração e pares de ações — C01–C16, P01–P18

**Total:** 34 testes complementares. Contam cenários de sequência e integridade, sem se confundirem com o total isolado das quatro ações.

## Pares ordenados de ações (16)

| ID | Ação 1 | GE 1 | Componentes 1 | Ação 2 | GE 2 | Componentes 2 | Regra / esperado |
|---|---|---|---|---|---|---|---|
| C01 | Formalização | NOVO | 112,281 | Formalização | NOVO | 112,281 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Executar sobre snapshot restaurado; após passo 1 consultar o estado e resolver IDs antes do passo 2. |
| C02 | Formalização | NOVO | 112,281 | Inclusão | codigo_criado_em_passo_1 | 118 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Resolver GE gerado pelo primeiro passo; conferir composição antes de 2ª ação. |
| C03 | Formalização | NOVO | 112,281 | Exclusão | codigo_criado_em_passo_1 | 84 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Resolver GE gerado pelo primeiro passo; conferir composição antes de 2ª ação. |
| C04 | Formalização | NOVO | 112,281 | Unificação | codigo_criado_em_passo_1 | 92,115 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Resolver GE gerado pelo primeiro passo; conferir composição antes de 2ª ação. |
| C05 | Inclusão | 910106 | 118 | Formalização | NOVO | 118,283 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; PJ118 incluída anteriormente deve bloquear nova formalização. |
| C06 | Inclusão | 910106 | 118 | Inclusão | 910106 | 118 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Segundo pedido do mesmo PJ deve recusar já ativo. |
| C07 | Inclusão | 910106 | 118 | Exclusão | 910106 | 118 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Remover componente recém-incluído; transição e eventos sem duplicidade. |
| C08 | Inclusão | 910106 | 118 | Unificação | 910106 | 92,115 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Executar sobre snapshot restaurado; após passo 1 consultar o estado e resolver IDs antes do passo 2. |
| C09 | Exclusão | 910106 | 84 | Formalização | NOVO | 112,281 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Executar sobre snapshot restaurado; após passo 1 consultar o estado e resolver IDs antes do passo 2. |
| C10 | Exclusão | 910106 | 84 | Inclusão | 910502 | 84 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Troca de GE do mesmo documento: conferir `tem_acao_2` e compatibilidade de status. |
| C11 | Exclusão | 910106 | 84 | Exclusão | 910106 | 84 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Segunda exclusão do mesmo documento deve ser tratada como inexistente ou idempotente. |
| C12 | Exclusão | 910106 | 84 | Unificação | 910106 | 92,115 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Executar sobre snapshot restaurado; após passo 1 consultar o estado e resolver IDs antes do passo 2. |
| C13 | Unificação | 910106 | 92,115 | Formalização | NOVO | 92,283 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; PJ já migrada após unificação não pode formalizar GE novo. |
| C14 | Unificação | 910106 | 92,115 | Inclusão | 910106 | 118 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Adicionar PJ ao grupo primário após unificação. |
| C15 | Unificação | 910106 | 92,115 | Exclusão | 910106 | 92 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Excluir componente migrado do GE primário após unificação. |
| C16 | Unificação | 910106 | 92,115 | Unificação | 910106 | 92,115 | ORACULO_CORRELACAO_ACOES_E_ISOLAMENTO: estado intermediário / duplicidades; Repetição de unificação com secundário já cancelado não pode duplicar eventos. |

## Persistência, eventos e retorno (18)

| Caso | GE base | Componentes envolvidos | Regra identificada / nome de teste | O que comparar |
|---|---|---|---|---|
| P01 | 910106 | 112,281 | `init_validacao` | Campos de processamento começam em OK / mensagem vazia |
| P02 | 910101 | 62,64 | `finish_validacao` | Recusa preserva motivo e data do retorno |
| P03 | 910106 | 112,281 | `valida_status_componente_formalizacao` | Reprovar uma PF e propagar rejeição da Formalização |
| P04 | 910101 | 62,64 | `ORACULO_CHAVE_ACAO_DOCUMENTO` | Múltiplas ações no mesmo documento sem colisão |
| P05 | 910106 | 112,281 | `ORACULO_ISOLAMENTO_SOLICITACAO` | Mesmo documento em solicitações diferentes |
| P06 | 910101 | 62,64 | `ORACULO_MERGE_SOLICITACAO` | MERGE por _id e cSoltcAtdmt |
| P07 | 910106 | 112,281 | `ORACULO_MERGE_SEM_MATCH` | Solicitação sem destino no MERGE |
| P08 | 910101 | 62,64 | `flag_ge_primario` | Seleção do primário em Unificação |
| P09 | 910106 | 112,281 | `ORACULO_CRT_DELETE_GRUPO` | Cancelar grupo e componentes no consumidor |
| P10 | 910101 | 62,64 | `ORACULO_CRT_DELETE_COMPONENTE` | Excluir componente e preservar GE |
| P11 | 910106 | 112,281 | `ORACULO_CRT_INCLUSAO_SEM_DUPLICIDADE` | Adicionar PF+PJ, apenas um UPDATE de GE |
| P12 | 910101 | 62,64 | `ORACULO_CRT_UNIFICACAO_LEFT_ANTI` | Componente já presente no primário |
| P13 | 910106 | 112,281 | `ORACULO_IDEMPOTENCIA_CRT` | Reexecutar a mesma solicitação sem evento duplicado |
| P14 | 910101 | 62,64 | `ORACULO_CONCORRENCIA` | Executar duas solicitações concorrentes |
| P15 | 910106 | 112,281 | `ORACULO_RECUPERACAO_PARCIAL` | Falha após MERGE e antes dos eventos |
| P16 | 910101 | 62,64 | `ORACULO_EVENTOS_INTEGRIDADE` | Evento sem correspondente ativo |
| P17 | 910106 | 112,281 | `ORACULO_ISOLAMENTO_AMBIENTE` | Roteamento DV/HO sem acesso ao produtivo |
| P18 | 910101 | 62,64 | `ORACULO_RETORNO_PONTA_A_PONTA` | Decisão correta na interface e bases persistidas |

## Critérios gerais

1. Executar sequências sobre snapshot com restauração entre casos; não pressupor que o segundo passo mantém o mesmo grupo após cancelamento/unificação.
2. Sempre registrar a origem da solicitação, o `_id`, `cSoltcAtdmt`, `cAcaoGrpEconm`, documentos, eventos e estado final.
3. Pares que reutilizam documento devem exercitar isolamento entre solicitações; para `tem_acao_2`, testar explicitamente mesmo lote e solicitações distintas.
4. Confirmar nos processadores CRT como são gerados IDs, `INSERT/UPDATE/DELETE`, replays e seleção de eventos de componentes aceitos.
5. Os nomes `ORACULO_*` são **identificadores de teste**, não funções do motor comprovadas; os demais são nomes reais encontrados nas regras.

**Status:** planejamento. Nenhum caso cruzado ou E2E possui aceite nesta documentação.
