# Execução integrada e registro de evidências

## Responsabilidades por função

| Frente | Responsabilidade |
|---|---|
| Engenharia de Dados | Disponibilizar fixtures, QSA e responsabilidade, validar contratos, preparar snapshots, executar motor e comparar tabelas |
| Backend | Criar solicitações compatíveis com as chaves e campos do motor, correlacionar decisões e eventos |
| Frontend | Enviar casos e verificar retorno, mensagens e atualizações |
| QA | Reproduzir cenário, registrar resultado e anexar evidências de estado antes/depois |
| Negócio | Homologar o oráculo, aprovar transições, recusas e casos condicionais |

Não atribuir responsabilidades a pessoas específicas sem confirmação.

## Preparação

1. Selecionar a branch e capturar o commit/versão do catálogo, com o ambiente de teste.
2. Executar os testes offline a partir da raiz:
   `python -m unittest discover -s scripts/future/fixtures/tests -v`
3. Conferir 100 PF e 100 PJ, QSA de MEIs, estado dos 18 GEs e os dez documentos PF reservados para cenário.
4. Conferir tabelas de responsabilidade e contratos efetivamente abertos; preservar 70 operações únicas.
5. Validar ambiente, YAML das regras e schemas. **Nunca rotear mocks para produção.**
6. Restaurar snapshot e aplicar apenas as alterações de `preparo` do caso selecionado; verificar IDs e percentuais.

## Executar um caso

1. Ler no [catálogo JSON](catalogo_total.json) o `id`, grupo, componentes e overrides da solicitação.
2. Registrar pré-estado: membros/GE/tipo/QSA/responsabilidade e suas flags derivadas.
3. Abrir a solicitação com ação 1/2/3/4 e chaves `_id` e `cSoltcAtdmt` próprias.
4. Executar o Motor e capturar o retorno por componente e por solicitação.
5. Comparar eventos de grupo, eventos de componente e tabelas materializadas; observar mudança de tipo e deltas.
6. Registrar evidências e divergência com a [tabela-verdade](TABELAS_VERDADE.md).
7. Restaurar snapshot de teste antes do próximo caso. Nunca usar como pré-estado alterações de uma execução anterior, salvo sequências explicitamente definidas.

## Critérios de avaliação

- `PASS`: regra, mensagens, componentes, grupo, eventos e retorno conferem com oráculo homologado.
- `FAIL`: diferença demonstrada entre esperado e observado.
- `BLOCKED`: sem documento cadastral, sem regra oficial, sem esquema, sem liberação de ambiente.
- `NOT_RUN`: caso preparado, mas execução não realizada.

Casos marcados `CONDICIONAL` ou `PENDENTE` devem permanecer bloqueados para aceite até regra confirmada. Não converter o resultado em aprovação automática por término bem-sucedido do notebook.

## Gate de conclusão

Para cada ID, arquivar versão da massa, ID da solicitação, versões de schemas e motor, oráculo aprovado, mensagens, saídas e hashes/evidências do estado inicial e final. O aceite integrado só ocorre quando comportamento da interface, decisões e persistência estão consistentes.
