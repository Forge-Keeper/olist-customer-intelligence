# [Motor GRUP] Execução dos testes E2E nos ambientes DV e HO

## Descrição

Executar, durante a sprint de duas semanas, os testes integrados de ponta a ponta do Motor GRUP nos ambientes de Desenvolvimento (DV) e Homologação (HO), utilizando as massas sintéticas, os cenários, as matrizes e os planos de teste já preparados e versionados.

O foco desta história é **colocar o fluxo em execução, validar os resultados, identificar defeitos, corrigir os impedimentos encontrados e reexecutar os cenários afetados**. A criação das massas e a elaboração inicial dos casos de teste são entregas já realizadas e não constituem o objetivo desta sprint.

Os testes contemplarão as quatro ações de Grupo Econômico: **Formalização, Inclusão, Exclusão e Unificação**, verificando o processamento desde a entrada da solicitação e seu enriquecimento até a aplicação das regras, geração de eventos, atualização de grupos/componentes e retorno do resultado.

## Atividades previstas

- Conferir a prontidão operacional de DV e HO para iniciar as execuções, ajustando apenas configurações, acessos, contratos ou cargas que efetivamente bloqueiem os testes.
- Utilizar as massas sintéticas e os **217 cenários já documentados**, priorizando os casos representativos das regras e dos fluxos das quatro ações, sem recriar a massa ou redesenhar o catálogo.
- Executar inicialmente os cenários de fluxo válido e de recusa em DV, confirmando a passagem pelas etapas de preparação, enriquecimento, regras e processamento.
- Executar os cenários integrados das quatro ações, incluindo validações de CPF/CNPJ, QSA, participação societária, responsabilidade creditícia, composição de grupo e vínculos ativos.
- Conferir, por componente e por solicitação, o resultado **APROVADO ou REPROVADO**, as mensagens das regras e a correspondência com a tabela-verdade planejada.
- Validar os efeitos de cada execução nas tabelas de grupos e componentes e nos eventos gerados, incluindo inclusões, exclusões, formalizações, unificações e transições aplicáveis.
- Registrar evidências dos resultados, defeitos encontrados, casos bloqueados e divergências entre o comportamento observado e o esperado.
- Corrigir ou encaminhar os problemas técnicos identificados, realizar os ajustes pontuais necessários nas fixtures/contratos e **reexecutar os testes afetados**.
- Repetir em HO os fluxos e cenários priorizados validados em DV, verificando a consistência do processamento entre os ambientes.
- Alinhar com Backend e Frontend a execução das solicitações e a verificação do retorno integrado, conforme a disponibilidade dos fluxos, registrando dependências que impeçam o E2E completo.

## Planejamento das duas semanas

**Semana 1 — Execução e estabilização em DV:** realizar os primeiros testes ponta a ponta das quatro ações, ampliar a execução para as regras priorizadas, analisar os resultados e tratar os bloqueios identificados.

**Semana 2 — Execução em HO e regressão:** reproduzir os fluxos em HO, validar as correções, reexecutar cenários impactados e consolidar as evidências e pendências para continuidade da homologação.

## Critérios de aceite

1. Execuções ponta a ponta realizadas e evidenciadas em DV e HO para as quatro ações, contemplando cenários de aprovação e reprovação; eventuais impedimentos devem estar identificados e encaminhados.
2. Resultados do Motor confrontados com a matriz existente, considerando **somente APROVADO ou REPROVADO**, com decisão por componente e por solicitação.
3. Eventos gerados e alterações efetivas de grupos/componentes verificados nos cenários executados, não apenas o sucesso técnico dos jobs.
4. Defeitos, falhas de integração e divergências encontrados durante a execução registrados com cenário, evidência e encaminhamento.
5. Correções e ajustes técnicos necessários à continuidade dos testes validados por reexecução dos cenários afetados.
6. Cenários executados identificados como PASS ou FAIL; casos não executados ou bloqueados registrados separadamente, com motivo, sem serem contabilizados como homologados.
7. Resultados de DV e HO consolidados, com indicação de cobertura executada, pendências e riscos remanescentes.
8. Preservado o isolamento entre DV, HO e produção durante toda a execução.

## Resultado esperado da sprint

Ao final das duas semanas, o Motor GRUP deverá ter passado por **execuções E2E efetivas em DV e HO**, com evidências das quatro ações, validação dos resultados e dos efeitos persistidos, correções e regressões realizadas quando necessário, e um panorama claro dos cenários aprovados, reprovados, bloqueados ou ainda não executados.

A matriz existente de **217 cenários** será utilizada como referência de cobertura e priorização. **Não é escopo recriar esses testes nem assumir a execução integral dos 217 casos nesta sprint**; a meta é avançar a execução real dos fluxos, eliminar bloqueios e deixar evidências e pendências organizadas para a continuidade da homologação.
