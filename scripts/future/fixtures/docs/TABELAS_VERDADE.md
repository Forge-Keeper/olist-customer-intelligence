# Tabelas-verdade — decisão binária do Motor

**Versão 4.0.0 | 19/11/2026 | 217 casos | Expectativas ainda não homologadas.**

A decisão funcional do Motor tem **exatamente dois resultados**:

| Esperado de negócio | Valor técnico recuperado | Interpretação |
|---|---|---|
| **APROVADO** | `retorno_solt = OK` | O componente/solicitação atende aos requisitos |
| **REPROVADO** | `retorno_solt = Solicitacao Recusada` | O componente/solicitação viola um requisito |

Não usar `PENDENTE`, `CONDICIONAL` ou `PARCIAL` como resultado do Motor. A confirmação do oráculo e a execução dos testes pertencem a **campos diferentes**.

## Contrato da tabela-verdade

| Campo | Valor/uso |
|---|---|
| `id_cenario` | F01–F48, I01–I18, E01–E30, U01–U21, C/P/B/FX/UX/EX/IX |
| `_id`, `cSoltcAtdmt` | Chaves reais de solicitação a preparar |
| `cAcaoGrpEconm` | 1 Formalização, 2 Inclusão, 3 Exclusão, 4 Unificação |
| `cGrpEconm`, tipo e demais grupos | Grupos da massa real; NOVO em Formalização |
| Componentes do pedido | `cclub_cli`, CPF/CNPJ e sua origem |
| Componentes ativos antes | Grupo inicial, composição e histórico |
| QSA | CNPJ titular, documento do sócio, participação e total |
| Responsabilidade | `noper_cli`, vigência e flag derivada |
| `decisoes_por_componente` | Apenas APROVADO ou REPROVADO para cada componente |
| `resultado_esperado` | Resultado binário consolidado da solicitação |
| `resultados_por_passo` | Resultado binário de cada pedido em casos sequenciais |
| `componentes_finais_esperados` | Estado após materialização, quando determinável |
| Mensagens esperadas | Exatamente os motivos das regras testadas |
| Eventos e transições | Efeito independente da decisão, a confirmar contra CRT |
| `fundamento_oraculo` | Regra identificada ou hipótese para homologação |
| `homologacao_funcional` | Estado de validação da expectativa, não resposta do Motor |
| Status de execução | PASS/FAIL/BLOCKED/NOT_RUN, nunca resposta do Motor |

**Regra agregadora do catálogo:** se pelo menos um componente está REPROVADO, a expectativa da solicitação é REPROVADO. Cada componente aprovado ainda deve aparecer na tabela de decisões. A aplicação parcial de eventos, quando existir, deve ter aceite explícito do negócio.

## Exemplos concretos

### I03 — Inclusão de PJ em GE Isolado

GE **910502**, tipo **5**, solicitar **PJ 118**, sem vínculo ativo, com QSA de 100% e demais dados válidos. Regra principal `valida_qsa` e elegibilidade cadastral. **Decisão: APROVADO.** Novo componente aceito. A conversão do tipo do grupo e a quantidade de eventos devem ser verificadas separadamente, sem afetar a decisão do Motor.

### I06 — Inclusão de PF em Gerencial

GE **910604**, tipo **6**, solicitar **PF 295**, CPF válido, QSA >=50%, sem outro GE. A regra `valida_socios_sao_pf` limita a participação a tipos 1 e 5. **Decisão: REPROVADO.** Não inserir vínculo de PF.

### E30 — Decisões diferentes na mesma solicitação

GE **910104**, ação Exclusão de **PJ 74 e PJ 76**. PJ74 tem contrato aberto; PJ76 não tem. Ambas estão BAIXADAS no snapshot. `valida_cnpj_responsabilidade`:

| Componente | Resultado do Motor | Efeito proposto |
|---|---|---|
| PJ 74 | REPROVADO | Preservar vínculo |
| PJ 76 | APROVADO | Remover vínculo aprovado, conforme CRT |

**Resultado consolidado da solicitação: REPROVADO.** Não existe resultado PARCIAL; a materialização parcial permanece verificação independente.

### U10 — Componente sem controle comum

GE primário **910106**, secundário **910502**. QSA preparado com controladora PF do primário a 100% em todas as PJs, sem participação majoritária da PF do secundário.

| Componente | Resultado do Motor |
|---|---|
| PJ 92 | APROVADO |
| PF 115 | REPROVADO |

**Consolidado: REPROVADO.** A seleção de eventos para os componentes aprovados precisa de validação do processador.

### C06 — Duas inclusões sequenciais da mesma PJ

Primeiro pedido: incluir PJ118 no GE910106, **APROVADO**. Segundo pedido, após atualizar o estado: tentar incluir PJ118 novamente, **REPROVADO** pela regra `valida_cnpj_em_outro_grupo`. Não existe um terceiro status para representar a sequência.

### P07 — Motor aprovado e falha de integração

A solicitação de referência I01 tem decisão esperada **APROVADO**. Se o MERGE não encontrar a solicitação de destino, o **teste de integração** deve identificar a falha ou executar a recuperação prevista. O estado técnico do teste (PASS/FAIL) não substitui a decisão do Motor.

## Critérios de homologação

Cada linha deve ser aprovada com dados de origem, decisão por componente, grupo antes/depois, mensagens e eventos. Hipóteses (por exemplo, entrada ausente, nula, duplicada ou inexistência de GE) possuem decisão binária **proposta**, mas não são apresentadas como comportamento comprovado. Divergências devem ser registradas, não mascaradas por alteração de massa.

[Plano](PLANO_TESTES.md) | [217 casos](MATRIZ_DETALHADA.md) | [Catálogo completo](catalogo_total.json).
