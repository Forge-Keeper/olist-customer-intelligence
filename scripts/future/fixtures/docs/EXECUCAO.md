# Execução integrada, participantes e critérios de aceite

## Participação das áreas

A divisão abaixo descreve **o que precisa ser combinado**, não uma atribuição já aprovada. Não há, neste estudo, nomes confirmados para os responsáveis técnicos de Frontend, Backend, QA ou homologação funcional.

| Frente | Contribuição esperada | Quem confirma / situação |
|---|---|---|
| Engenharia de Dados / Motor GRUP | Contratos Delta, massa sintética, roteamento das leituras, jobs, regras e eventos; evidências técnicas | Trabalho em curso pelo responsável do Motor |
| Backend | Acordar IDs/documentos das solicitações, disponibilizar cenário de teste, encaminhamento ao motor e contrato de retorno | Responsável e data a combinar com o time |
| Frontend | Criar e acompanhar solicitações na interface, verificar mensagens e decisões por componente | Responsável e data a combinar com o time |
| QA / testes integrados | Catálogo e execução de cenários, comparação com esperado, defeitos e regressões | Confirmar participantes e ferramenta de gestão |
| Negócio / PO | Decidir os comportamentos ambíguos: tipo 6, transições, parcialidade, limites de QSA e regras especiais | Validação funcional a combinar |
| PM (Levi) | Converter o escopo em card Jira e acompanhar dependências entre as equipes | Levi é o contato informado para a criação do card; demais responsabilidades não presumidas |

## Sequência para não perder tempo

### Etapa 1 — Contratos e dados

- Confirmar schema do cadastral PJ/PF, QSA, responsabilidades, grupos e componentes ativos.
- Validar as seis tabelas de negócio e suas colunas efetivamente consumidas.
- Conciliar as fixtures estáticas com o notebook: 100 PF, 100 PJ, 18 GEs, 48 componentes, QSA MEI e não MEI.
- Revisar o QSA de empresas com sócios distintos, porque o agrupamento antigo por `cclub_cli` pode estar incorreto.

**Saída:** tabelas criadas e massa íntegra no namespace de teste, sem depender de dados de produção.

### Etapa 2 — Roteamento e entrada da solicitação

- Conferir os YAMLs de enriquecimento atuais, ainda incompletos no ledger.
- Roteamento explícito para fontes sintéticas em DV/HO.
- Conferir referências de ambiente fixas no código recuperado (`env = 'pr'`) para não atravessar fronteiras.
- Alinhar com Backend e Frontend o conjunto de solicitações e chaves de correlação.

**Saída:** uma solicitação sintética percorre preparação, enriquecimento e chega à `base_solicitacao` corretamente.

### Etapa 3 — Smoke do motor por operação

Começar por um caso positivo e um negativo por ação. Em seguida ampliar pela ordem: exclusão, inclusão, formalização, unificação. Para cada execução, verificar `resul_soltc`, atualização por `process_motor_grup`, eventos CRT e estado final no consumidor.

**Saída:** quatro operações percorrendo o motor, sem erro estrutural e com resultados verificáveis.

### Etapa 4 — Cobertura dos limites e cruzamentos

Executar os casos do catálogo de cenários, inclusive 16 pares de ações, resultados parciais, tipos anômalos, duplicidades, ausência de join e transição de tipo. Criar fixtures derivadas apenas quando necessário, com valores fixos e versionados.

**Saída:** matriz de evidências com regras exercitadas, casos aprovados, bloqueados e defeitos identificados.

### Etapa 5 — E2E com as equipes

Executar no Frontend os cenários acordados com Backend e Motor, comparar decisão e efeitos persistidos, validar retorno ao usuário e reexecução depois de restaurar a massa inicial.

**Saída:** aceite técnico e funcional por cenário e pendências conhecidas documentadas no card.

## O que cada execução precisa registrar

| Campo | Para quê |
|---|---|
| ID do caso e ID da solicitação | Localizar a execução |
| Ambiente, versão do motor e data | Reproduzir |
| IDs de GEs e documentos mascarados | Contextualizar sem expor cadastro |
| Ações e componentes enviados | Conferir o pedido |
| Resultado individual e consolidado | Conferir regra de negócio |
| Eventos de grupo e componente | Conferir efeito materializado |
| Estado final e retorno de Frontend | Conferir jornada |
| Status, evidência e defeito | Separar PASS/FAIL/BLOCKED |
| Responsável pela execução | Dar encaminhamento ao caso |

Não basta marcar PASS pelo sucesso do job. Uma solicitação recusada que escreveu DELETE indevido falhou, mesmo que o notebook termine sem exception.

## Dependências e pendências abertas

- Reconciliar processadores `process_crt_*` fotografados com o código atual.
- Confirmar a regra funcional para grupo gerencial (tipo 6) em formalização, inclusão e transições.
- Fechar correspondência de nomes e tipos de colunas entre origem, preparação e regras.
- Verificar inconsistências potenciais de `valida_socio_major_formalizacao`, `flag_formalizacao` e `flag_composicao_unificacao`.
- Validar QSA com sócios PJ majoritários: a regra recuperada de unificação procura PF controlador de todas as PJs.
- Verificar seleção de GE secundário em unificação com aprovação parcial.
- Confirmar comportamento de `append` dos eventos em reexecução; desenhar limite de idempotência.
- Planejar falha entre atualização da solicitação e geração de eventos; conferir recuperação sem efeito parcial.
- Resolver caminhos de ambiente e isolamentos de leitura em DV e HO.
- Identificar quem valida o retorno de Backend/Frontend e quem dá aceite funcional.

## Condição para encerramento da história

A entrega terá evidências de que um pedido criado no Frontend, com cadastros exclusivamente sintéticos, é recebido pelo Backend, enriquecido, validado pelo Motor GRUP, refletido na solicitação original e convertido nos eventos corretos. O resultado chega à interface e pode ser repetido após restauração da massa. Os testes de todas as regras aplicáveis estão registrados, inclusive rejeições, parcialidade, transições, reexecuções e falhas.

Qualquer lacuna funcional ou técnica que não possa ser fechada durante a execução deve permanecer explícita no Jira, com responsável por definição e cenário bloqueado — nunca ser convertida em PASS por ausência de erro de execução.
