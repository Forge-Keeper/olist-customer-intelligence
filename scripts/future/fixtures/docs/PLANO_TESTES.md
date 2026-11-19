## Política obrigatória: somente dois resultados de Motor

A decisão funcional esperada é **APROVADO** ou **REPROVADO**. No resultado técnico recuperado, correspondem respectivamente a `retorno_solt=OK` e `retorno_solt=Solicitacao Recusada`. Não existe `CONDICIONAL`, `PARCIAL` ou `PENDENTE` como terceira resposta do Motor.

- Em solicitações com vários componentes, cada componente recebe uma decisão binária. Se algum for REPROVADO, a expectativa da solicitação consolidada é REPROVADO; os componentes APROVADOS permanecem discriminados e seus efeitos são conferidos separadamente.
- Nos pares sequenciais (C01–C16), há decisão do primeiro pedido e do segundo pedido. `resultado_esperado` representa o **segundo pedido**; não agrega pedidos distintos em uma terceira resposta.
- Nos testes de persistência/integração (P01–P18), o Motor da solicitação de referência continua binário; o teste técnico é julgado à parte como PASS ou FAIL.
- Incertezas são mantidas em `fundamento_oraculo`, `homologacao_funcional` e validação dos eventos; nenhuma incerteza é resultado do Motor.
- Resultados são **expectativas para homologação**, não comprovante de execução. Entradas nulas, ausentes ou duplicadas com comportamento não demonstrado usam o oráculo funcional proposto REPROVADO; se o Motor divergir, registrar defeito ou submeter mudança de critério ao negócio.

# Plano de testes e homologação — quatro ações

**Referência:** 19/11/2026. **Situação:** massa e matriz documentadas, E2E não executado. **Escopo:** Grupo Econômico Normal (1), Isolado (5) e Gerencial (6); ações Formalização (1), Inclusão (2), Exclusão (3) e Unificação (4).

## 1. Objetivo e cobertura

Validar regras aplicadas a cada componente, composição de grupo, coerência societária, responsabilidade creditícia, eventos e estado efetivamente materializado. A campanha contém **217 casos lógicos**:

| Trilha | Quantidade | Matriz |
|---|---:|---|
| Formalização | 48 | [MATRIZ_FORMALIZACAO.md](MATRIZ_FORMALIZACAO.md) |
| Inclusão | 18 | [MATRIZ_INCLUSAO.md](MATRIZ_INCLUSAO.md) |
| Exclusão | 30 | [MATRIZ_EXCLUSAO.md](MATRIZ_EXCLUSAO.md) |
| Unificação | 21 | [MATRIZ_UNIFICACAO.md](MATRIZ_UNIFICACAO.md) |
| Pares ordenados de ações | 16 | [MATRIZ_INTEGRACAO.md](MATRIZ_INTEGRACAO.md) |
| Persistência e integração | 18 | [MATRIZ_INTEGRACAO.md](MATRIZ_INTEGRACAO.md) |
| Limites e ausências | 36 | [MATRIZ_LIMITES.md](MATRIZ_LIMITES.md) |
| Variantes de regras por ação | 30 | [MATRIZ_REGRAS_VARIANTES.md](MATRIZ_REGRAS_VARIANTES.md) |
| **Total** | **217** | [MATRIZ_DETALHADA.md](MATRIZ_DETALHADA.md) |

A trilha original de 151 casos foi preservada, com 66 casos adicionais de fronteiras e variantes de regras. **217 não significa cobertura combinatória exaustiva**, e o total poderá aumentar se o motor vigente revelar novas regras.

## 2. Massa canônica e sobreposições de teste

- **18 GEs fixos**: seis por tipo 1, 5 e 6, IDs `910101–910106`, `910501–910506`, `910601–910606`.
- **48 membros ativos fixos**: 30 PJ e 18 PF, documentos distintos.
- **QSA de não MEIs**: 54 vínculos, 27 PJs, totais de 100% por CNPJ e seis Isolados com sua PF ativa majoritária após reconciliação.
- **QSA de MEIs**: disponível em fonte externa a estas fixtures; **importar uma única vez**, nunca duplicar. Os 100 cadastros PF/PJ de origem precisam de conciliação.
- **Responsabilidade**: 70 contratos, 40 PF e 30 PJ, números fictícios únicos, começo anterior a 2025 e término em 19/11/2027, abertos na data de referência.
- **PFs adicionais de cenário**: dez IDs entre 281 e 299; o cadastro sintético deve ser reconciliado/substituído especificamente para os testes. Proibida inclusão duplicada do mesmo `cclub_cli`.

Cada caso tem seu próprio `qsa_substituir`, `cadastro_override` e eventualmente membros extras/removidos **somente no snapshot de teste**. A massa-base jamais é alterada como efeito residual de um caso anterior.

## 3. Fases e gates

### Gate G0 — Integridade estática (obrigatório)

1. Executar `python -m unittest discover -s scripts/future/fixtures/tests -v` a partir da raiz do checkout.
2. Conferir 18 GEs, 48 membros, 54 QSA não MEI, 70 operações e 217 cenários, com identificadores únicos.
3. Confirmar documentos PF/PJ do catálogo contra cadastro efetivo, incluindo validade, matriz, atividade, natureza jurídica e CNPJ raiz.
4. Conferir QSA MEI e a relação `cclub_cli` = sócio, `ccnpj_empr` = empresa titular.
5. Confirmar origem dos 20 CNPJs não ativos e sua distribuição real antes dos testes negativos.

**Critério de passagem:** 0 divergência não explicada. Qualquer cadastro não localizado: BLOCKED, nunca substituição silenciosa.

### Gate G1 — Regras do motor

1. Confirmar o YAML/versão vigente de cada ação e a sequência de funções em [REGRAS_E_COBERTURA.md](REGRAS_E_COBERTURA.md).
2. Exercitar ao menos uma aprovação e uma recusa específica por função com ramo de negócio.
3. Verificar derivação real de `flag_socio_major`, `sum_quad_soc_empr`, `flag_resp_empr` e `tem_acao_2`.
4. Confirmar efeitos das falhas em itens irmãos (Formalização) e no primário/secundário (Unificação).

**Critério de passagem:** tabela-verdade de cada regra aceita pelo negócio, com discrepâncias como defeito.

### Gate G2 — Componentes, grupos e processadores

- Executar as quatro ações com snapshot restaurado por caso e comparação do estado inicial/final.
- Validar `UPDATE/INSERT/DELETE` de GE e componente, transição de tipo, cancelamento, migração e deduplicação.
- Confirmar decisões APROVADO/REPROVADO por componente e por solicitação; não usar PARCIAL como saída do Motor.
- Tratar resultados não homologados com aceite funcional antes de executar como homologação positiva.

### Gate G3 — Fluxo integrado

- Abrir solicitações pelo caminho autorizado e conferir o mapeamento do Backend.
- Verificar decisões no motor, persistência da solicitação original, geração/consumo de eventos e retorno.
- Executar 16 sequências de ações, os 18 casos de integração, replay e concorrência.
- Registrar ambiente, versão, snapshot, chaves `_id` e `cSoltcAtdmt`, evento produzido e estado materializado.

### Gate G4 — Aceite

Somente marcar PASS se decisão por componente, mensagens, estado persistido, efeito sobre tipo/GE e retorno aos sistemas estiverem coerentes. Caso sem execução, evidência ou contrato definido: BLOCKED ou NOT_RUN. Nunca converter planejamento em homologação concluída.

## 4. Riscos e prioridades

1. Preparação antiga do QSA agrupava percentuais por sócio, e pode subavaliar o somatório da empresa com múltiplos sócios.
2. A validação de majoritário em Formalização, na versão recuperada, pode descartar o DataFrame de rejeição.
3. O primário Isolado na Unificação pode falhar por composição antes da consolidação do grupo.
4. `flag_troca_componente` pode transbordar entre solicitações do mesmo documento se a janela não for isolada.
5. Eventos em modo `append` exigem teste explícito de replay e idempotência.
6. O ambiente de geração de código/roteamento não pode apontar para produção durante DV/HO.
7. Os arquivos de fixtures são dados de preparação, não prova de carga ou E2E.

## 5. Artefatos de saída

- [Catálogo completo JSON](catalogo_total.json): consumo automatizado e chaves de rastreio.
- [Matriz detalhada](MATRIZ_DETALHADA.md): leitura funcional.
- [Regras e cobertura](REGRAS_E_COBERTURA.md): rastreio das 43 chamadas/25 nomes.
- [Tabelas-verdade](TABELAS_VERDADE.md): modelo de aceite e exemplos.
- [Execução](EXECUCAO.md): procedimento e papéis.

## 6. Materialização offline reproduzível

Após o gate estático, executar `python scripts/future/fixtures/materializar_cenario.py <ID>` para obter um JSON com snapshot lógico, QSA aplicado, responsabilidade e oráculo do cenário. O comando **não** chama o motor, não envia solicitação e não escreve tabelas. Consulte os avisos emitidos; overlays de borda descritos textualmente e sequências com dependência do passo anterior exigem preparo adicional antes do E2E.
