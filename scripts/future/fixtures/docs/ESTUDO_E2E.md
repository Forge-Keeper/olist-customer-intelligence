# Testes integrados de Grupo Econômico — visão de trabalho

**Situação em 18/11/2026:** preparação de massa e roteiro de cenários. As fixtures estão publicadas, mas a execução E2E nos ambientes de teste ainda precisa ser comprovada.

## Por que estamos fazendo isso

Hoje é possível testar pedaços do fluxo separadamente, mas isso não garante que uma solicitação aberta na interface chegue ao motor com os dados certos nem que a decisão volte corretamente. Há outra limitação: os ambientes de desenvolvimento e homologação não podem depender de dados pessoais reais de produção.

Nosso caminho é manter cadastros sintéticos consistentes entre as fronteiras da aplicação e executar o mesmo fluxo de negócio: **Frontend → Backend → preparação/enriquecimento → regras do Motor GRUP → atualização da solicitação → eventos de grupo e componente → retorno ao usuário**.

O teste só está completo quando a decisão do motor e os efeitos persistidos conferem com o resultado apresentado na interface. Gerar uma linha em `resul_soltc` é necessário, mas não suficiente.

## Escopo desta primeira campanha

- Grupos econômicos tipo **1 = Normal**, **5 = Isolado** e **6 = Gerencial**.
- Ações: **formalização (1), inclusão (2), exclusão (3), unificação (4)**, isoladas e combinadas.
- Cadastros de PF e PJ, quadro societário, responsabilidades, grupos e componentes ativos; cenários positivos, rejeições e falhas controladas.
- Regras de composição, participação societária, vínculos ativos, transição de tipo, transferência de componentes e decisões por componente.
- Processadores CRT, atualização da solicitação original, staging de eventos, reexecução e integridade entre sistemas.

**Fora da contagem principal:** Rural, Alçada Comercial e tipos 8/9/10/12. São extensões importantes, mas precisam de critérios funcionais e massa específicos. Não misturar a cobertura deles com o aceite dos tipos 1/5/6.

## O que já temos

- 100 registros PF e 100 PJ sintéticos preparados no notebook, com indicadores cadastrais distintos. O usuário informou 20 PJs não ativas.
- Convenção de `cclub_cli`: PF ímpares, de 101 a 299; PJ pares, de 62 a 260.
- QSA dos MEIs já preparado no notebook: **cada MEI tem um único sócio PF**. Os vínculos dessa parte não devem ser reinseridos por engano.
- Nomes fixos para as 100 PJs em `../dados_nomes_pj.py`.
- 18 grupos ativos fixos: seis de cada tipo, em `../dados_grupos_ativos.py`.
- 48 componentes ativos fixos (30 PJs, 18 PFs) em `../dados_componentes_ativos.py`.
- 54 vínculos de QSA para 27 PJs não MEI em `../dados_quadro_societario.py`. Contemplam 5 PFs titulares de MEI que participam de outras empresas, pelo menos 3 PJs MEI sócias e três PFs sem majoritário.
- Infraestrutura de classes para contratos e operações Delta em `../../mock_table.py`. O material publicado nessa pasta é genérico; a versão refatorada do contrato recebida posteriormente ainda não foi substituída aqui.

Esses números são um **inventário do material preparado**, não prova de que todos os registros já estejam inseridos no Databricks ou de que a massa cubra todas as regras. A massa do notebook, o QSA dos MEIs e os arquivos de fixtures precisam ser conciliados antes da primeira execução.

## Como vamos medir a cobertura

A proposta levantada foi um **catálogo inicial de 151 casos lógicos**: 48 combinações estruturais de formalização, 18 casos de inclusão, 30 de exclusão, 21 de unificação, 16 pares ordenados de ações e 18 testes de persistência/integração. É uma meta de planejamento, com possíveis sobreposições; não são 151 testes já implementados nem uma prova matemática de cobertura total.

A cobertura será medida por **regra e condição exercitada**, e não somente pelo número de cenários executados. Para cada caso, registrar:
1. estado inicial do grupo e de cada componente;
2. solicitação e ações enviadas;
3. decisão esperada por componente e consolidada;
4. eventos esperados (INSERT/UPDATE/DELETE);
5. estado final esperado e retorno ao Frontend;
6. evidências de execução, diferença encontrada, ambiente e versão de código.

As combinações sem fim prático — volumes arbitrários, ordens de ação, concorrência — serão tratadas com limites e testes parametrizados, não com a promessa de testar literalmente todas as sequências possíveis.

## Critério para dizer que o E2E passou

Uma solicitação sintética percorre a interface, o backend e o Motor GRUP; as leituras usam somente fontes de teste autorizadas; a decisão individual e consolidada está certa; a solicitação original é atualizada; os eventos representam exatamente as alterações aprovadas; o consumidor não executa alterações indevidas; o usuário vê o resultado correto. O cenário deve poder ser repetido depois de restaurar o estado inicial.

## Leitura complementar

- [Catálogo de cenários](CENARIOS.md)
- [Massas, chaves e dependências](MASSAS.md)
- [Execução, integração e responsabilidades](EXECUCAO.md)

**Origem do levantamento:** código e YAMLs reconstruídos no ledger privado do Motor GE, discutidos em 18/11/2026. As rotinas CRT documentadas a partir de fotografias não foram validadas linha a linha contra a versão atual. A equipe deve confirmar os pontos divergentes no Databricks antes de tratá-los como contrato definitivo.
