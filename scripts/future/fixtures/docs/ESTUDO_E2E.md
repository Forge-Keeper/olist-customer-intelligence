## Política obrigatória: somente dois resultados de Motor

A decisão funcional esperada é **APROVADO** ou **REPROVADO**. No resultado técnico recuperado, correspondem respectivamente a `retorno_solt=OK` e `retorno_solt=Solicitacao Recusada`. Não existe `CONDICIONAL`, `PARCIAL` ou `PENDENTE` como terceira resposta do Motor.

- Em solicitações com vários componentes, cada componente recebe uma decisão binária. Se algum for REPROVADO, a expectativa da solicitação consolidada é REPROVADO; os componentes APROVADOS permanecem discriminados e seus efeitos são conferidos separadamente.
- Nos pares sequenciais (C01–C16), há decisão do primeiro pedido e do segundo pedido. `resultado_esperado` representa o **segundo pedido**; não agrega pedidos distintos em uma terceira resposta.
- Nos testes de persistência/integração (P01–P18), o Motor da solicitação de referência continua binário; o teste técnico é julgado à parte como PASS ou FAIL.
- Incertezas são mantidas em `fundamento_oraculo`, `homologacao_funcional` e validação dos eventos; nenhuma incerteza é resultado do Motor.
- Resultados são **expectativas para homologação**, não comprovante de execução. Entradas nulas, ausentes ou duplicadas com comportamento não demonstrado usam o oráculo funcional proposto REPROVADO; se o Motor divergir, registrar defeito ou submeter mudança de critério ao negócio.

# Estratégia de testes integrados — Grupo Econômico

**Preparação concluída em documentação:** 217 casos distribuídos entre as quatro ações, suas combinações e os testes de persistência. **Execução E2E não comprovada.**

## Fluxo que deve ser exercitado

Solicitação recebida → preparação e enriquecimento cadastral/QSA/responsabilidade → validações por ação → `resul_soltc` → atualização da solicitação original → geração de eventos de grupo/componente → persistência por consumidor → retorno à interface.

Não basta comparar `retorno_solt`: o aceite requer conferência dos eventos e do estado final.

## Cobertura funcional

- Formalização (1): grupos novos Normal, Isolado e ramo não mapeado Gerencial; composição e majoritário.
- Inclusão (2): elegibilidade PF/PJ, vínculo ativo, matriz, natureza jurídica, QSA100%, variação de tipo e deduplicação.
- Exclusão (3): situação BAIXADA/INAPTA, responsabilidade ativa, troca com ação 2, remoção parcial, cancelamento e transições.
- Unificação (4): primário, secundário, controlador comum >=50% em todas as PJs, consistência do QSA, migração de membros e parcialidade.
- Combinações (16): as quatro ações cruzadas, com estado intermediário e solicitações distintas.
- Persistência/integração (18): MERGE, eventos, replay, concorrência, falha parcial, ambiente e interface.
- Bordas e regressão de regras (66): nulidade, 49,99/50/50,01, QSA, responsabilidade e aplicação de regras compartilhadas por ação.

## Ordem de teste

1. Validar dados e executar testes offline, conferindo a massa sintética.
2. Executar smokes de uma aprovação e uma recusa por ação em ambiente isolado.
3. Executar [matrizes de cada ação](MATRIZ_DETALHADA.md), com snapshots distintos.
4. Executar pares e persistência; validar eventos, idempotência e ambiente.
5. Submeter as tabelas-verdade ao negócio; bloquear cenários sem decisão funcional.
6. Encerrar o caso somente após confrontar retorno e dados materializados.

## Limitações de confiança

As funções disponíveis foram recuperadas de uma versão registrada; eventuais alterações no motor em execução devem provocar revalidação da matriz. Os processadores de eventos e as flags derivadas têm riscos documentados em [REGRAS_E_COBERTURA.md](REGRAS_E_COBERTURA.md).

[Plano detalhado](PLANO_TESTES.md) | [Evidências e passos](EXECUCAO.md) | [Modelo de verdade](TABELAS_VERDADE.md).
