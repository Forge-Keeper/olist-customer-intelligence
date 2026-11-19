# Homologação funcional — Inclusão I01–I18 (revisão R2)

**Data:** 19/11/2026. **Status:** documentação corrigida, ainda **NÃO LIBERADA PARA E2E**. Ação `cAcaoGrpEconm = 2`.

> Substitui a alocação anterior em aliases GE01–GE14. Os grupos e vínculos agora se baseiam nas fixtures existentes. Nenhuma alteração foi realizada nas tabelas ou nos dados-base.

## 1. Base auditada

- `../dados_grupos_ativos.py`: 18 GEs físicos de teste — seis Normais (`910101` a `910106`), seis Isolados (`910501` a `910506`), seis Gerenciais (`910601` a `910606`).
- `../dados_componentes_ativos.py`: 48 componentes (30 PJs e 18 PFs). Cada Normal e Gerencial parte de 2 PJ + 1 PF; cada Isolado, 1 PJ + 1 PF.
- `../dados_quadro_societario.py`: 54 participações de 27 PJs não MEI. MEIs têm QSA preparado fora desta fixture: conciliar antes do E2E.
- `./CENARIOS.md`: objetivos I01–I18 preservados; os identificadores não são testes já homologados.
- `./massa-responsabilidade-70-clientes-2026-11-19.md`: proposta independente de responsabilidade. Contrato aberto não comprova maioria societária.

## 2. Auditoria dos oito primeiros erros

| Caso | Por que a distribuição original falhava | Correção documentada |
|---|---|---|
| I01 | PJ80 já estava no grupo 910105 | Usar PJ112, sem GE ativo, em 910101 |
| I02 | PF115 não tinha maioria no QSA do grupo-alvo | PF299 nova, com QSA específico para a PJ74 de 910104 |
| I03 | PJ82 já estava no grupo 910105 | Usar PJ118, sem GE ativo, em 910502 |
| I04 | PF117 já estava no grupo 910503 | Usar PF297 nova em 910505, com QSA 50/50 |
| I05 | PJ84 já estava no grupo 910106 | Usar PJ112 em 910605; confirmar tipo Gerencial |
| I06 | PF119 já estava em 910504, contaminando a regra isolada de Gerencial | Usar PF295 sem GE, com maioria comprovável no QSA de cenário |
| I07 | Alias GE02 não identificava a base real | GE910101 e sua própria PJ62: duplicidade comprovada |
| I08 | PJ70 pertence a 910103, e não ao grupo informado como origem | GE910102 e PJ64 do GE910101: conflito real |

## 3. Matriz corrigida: componente que deve ser solicitado a cada grupo

**Importante:** os `cclub_cli` das PFs 299, 297, 295, 291, 289 e 287 pertencem à sequência prevista no cadastro, mas o CPF de cada uma ainda deve ser resolvido na tabela PF e verificado contra a lista de componentes ativos. **Não preencher CPFs fictícios adicionais sem consultar o cadastro.** Cada cenário precisa de snapshot restaurado; overlays societários não são mudanças na massa-base.

| Caso | Grupo real | Componente solicitado | Pré-condição e alteração de QSA por caso | Composição final prevista | Oráculo / condição |
|---|---|---|---|---|---|
| I01 | 910101 / Normal | PJ 112 (`20010176000131`) | PJ livre; QSA original: PJ 64=100%; confirmar ATIVA e matriz | 3 PJ + 1 PF | APROVA proposta; depende do cadastro |
| I02 | 910104 / Normal | PF 299 (CPF a resolver) | QSA PJ 74: PF 107=50% + PF 299=50%; CPF válido e sem GE | 2 PJ + 2 PF | APROVA proposta; exige overlay QSA |
| I03 | 910502 / Isolado | PJ 118 (`52592529000145`) | PJ livre; QSA PJ 118: PF 115=60%, PF 113=40%; QSA PJ 92: PF 115=60%, PJ 68=40% no cenário | 2 PJ + 1 PF | Conversão 5→1 PENDENTE de regra oficial |
| I04 | 910505 / Isolado | PF 297 (CPF a resolver) | QSA PJ 98: PF 121=50%, PF 297=50% no cenário; nova PF sem GE | 1 PJ + 2 PF | APROVA proposta; manter 5 a confirmar |
| I05 | 910605 / Gerencial | PJ 112 (`20010176000131`) | PJ livre e QSA100%, sócia PJ 64; demais flags válidas | 3 PJ + 1 PF | PENDENTE: regra de inclusão tipo 6 |
| I06 | 910604 / Gerencial | PF 295 (CPF a resolver) | QSA PJ 124: PF 295=50%, PF 117=25%, PF 119=25% no cenário; sem outra restrição | 2 PJ + 1 PF | RECUSA por PF em tipo 6 |
| I07 | 910101 / Normal | PJ 62 (`39070293000119`) | PJ 62 já integra o grupo 910101 | 2 PJ + 1 PF | RECUSA: componente no próprio GE |
| I08 | 910102 / Normal | PJ 64 (`47911744000121`) | PJ 64 integra 910101, não 910102 | 2 PJ + 1 PF | RECUSA: componente em outro GE |
| I09 | 910103 / Normal | PF 113 (`63124847504`) | Ativa em 910501; 60% da PJ 72 no GE alvo | 2 PJ + 1 PF | RECUSA: PF em outro GE |
| I10 | 910104 / Normal | PF 291 (CPF a resolver) | QSA PJ74: PF107=50%, PF291=50%; `cindcd_cpf_valid != 1` | 2 PJ + 1 PF | RECUSA: CPF inválido |
| I11 | 910103 / Normal | PJ 112 (`20010176000131`) | QSA100, matriz; `cindcd_cnpj_valid != 1` | 2 PJ + 1 PF | RECUSA: CNPJ inválido |
| I12 | 910105 / Normal | PJ 112 (`20010176000131`) | QSA100; `rsit_docto_recta != ATIVA` | 2 PJ + 1 PF | RECUSA: CNPJ não ativo |
| I13 | 910106 / Normal | PJ 112 (`20010176000131`) | QSA100; `rmtriz_flial_cnpj != '1'` | 2 PJ + 1 PF | RECUSA: estabelecimento filial |
| I14 | 910102 / Normal | PJ 112 (`20010176000131`) | Natureza jurídica incompatível; regra ausente no código recuperado | 2 PJ + 1 PF | PENDENTE: regra e recusa a provar |
| I15 | 910103 / Normal | PJ 112 (`20010176000131`) | QSA original 100%; reduzir para 90% exclusivamente neste cenário | 2 PJ + 1 PF | RECUSA: soma do QSA != 100 |
| I16 | 910505 / Isolado | PF 289 (CPF a resolver) | QSA PJ98: PF121=60%, PF289=40%; sem outra restrição | 1 PJ + 1 PF | RECUSA: PF não majoritária |
| I17 | 910101 / Normal | PJ112 + PF287 (CPF a resolver) | QSA PJ112: PJ64=50%, PF287=50%; sem vínculos prévios | 3 PJ + 2 PF | APROVA proposta; validar enriquecimento em lote |
| I18 | 910106 / Normal | PJ112 duas vezes (`20010176000131`) | Mesmo documento duplicado na solicitação; QSA100 | Depende da política | PENDENTE: deduplicação versus recusa |

**Nota sobre composição:** nos casos recusados o número de componentes é o do estado **inicial e final**, sem inserções. Nos condicionais, a composição indicada é apenas a projetada caso a solicitação venha a ser aprovada.

## 4. Revisão obrigatória dos quadros societários

A massa atual contém inconsistência societária em todos os seis grupos Isolados, mesmo quando o QSA da PJ soma exatamente 100%. Não se deve impor a aprovação dos positivos antes de tratar essas inconsistências:

| Grupo Isolado | Componentes atuais | Participação atual da PJ | Desvio |
|---|---|---|---|
| 910501 | PJ90 / PF113 | PJ62=50% + PJ64=50% | PF113 ausente do QSA |
| 910502 | PJ92 / PF115 | PJ68=60% + PF111=40% | PF115 ausente do QSA |
| 910503 | PJ94 / PF117 | PF113=60% + PF115=40% | PF117 ausente do QSA |
| 910504 | PJ96 / PF119 | PJ62=60% + PJ64=25% + PF105=15% | PF119 ausente do QSA |
| 910505 | PJ98 / PF121 | PJ62=60% + PF121=40% | PF121 é minoritária |
| 910506 | PJ102 / PF123 | PJ64=51% + PF107=49% | PF123 ausente do QSA |

### Alterações de QSA que devem existir somente no snapshot do teste

- **I02:** para a PJ74, PF107=50% e PF299=50%. A PF107 já pertence ao grupo 910104.
- **I03:** para a PJ92, PF115=60% e PJ68=40%. A PJ118 mantém seu QSA atual: PF115=60% e PF113=40%. A PF115 já pertence ao grupo 910502.
- **I04:** para a PJ98, PF121=50% e PF297=50%. A PF121 já pertence ao grupo 910505.
- **I06:** para a PJ124, PF295=50%, PF117=25% e PF119=25%, isolando somente a incompatibilidade do tipo 6.
- **I10:** para a PJ74, PF107=50% e PF291=50%; apenas o indicador de CPF291 deve falhar.
- **I15:** para a PJ112, reduzir de 100% para 90% em uma execução isolada; não contaminar outros cenários.
- **I16:** para a PJ98, PF121=60% e PF289=40%, isolando ausência de maioria.
- **I17:** para a PJ112, PJ64=50% e PF287=50%, para avaliar inclusão conjunta PJ/PF.

Todas as porcentagens são propostas de **preparo de cenário** e não correções retroativas de quadros societários reais. Não substituir os 19 padrões de QSA existentes por uma única estrutura artificial. Antes de implantar qualquer mudança compartilhada, revisar a finalidade de cada QSA e sua relação com os grupos.

## 5. Tabela-verdade focal para homologação

Para cada execução registrar: `id_cenario`, `_id`, `cSoltcAtdmt`, grupo real `cGrpEconm`, tipo inicial `cTpoGrpEconm`, `cAcaoGrpEconm=2`, documento resolvido, `cclub_cli` correspondente, componentes ativos antes, QSA por CNPJ e sócio, responsabilidade aberta, componentes da solicitação, `retorno_solt`, `iMsgemRetor`, componentes ativos depois, tipo depois, eventos gerados, decisão funcional homologada e evidência.

| Classe do caso | Resultado da solicitação | Componente/grupo após processamento | Eventos esperados |
|---|---|---|---|
| Positivo validado | Aprovação conforme contrato oficial | Preservar os anteriores e inserir cada novo componente uma vez; mudar tipo somente se homologado | Atualização do GE e componentes, sem duplicação entre linhas ou replay |
| Negativo de causa única | `Solicitacao Recusada` com motivo específico | Nenhum vínculo ou tipo deve ser alterado | Nenhum evento de inclusão aprovado do componente recusado |
| Tipo/deduplicação pendente | Resultado ainda não estabelecido | Não fixar pós-estado sem regra oficial | Quantidade e decisão de eventos pendentes |

**Código recuperado de Inclusão:** verifica PF/PJ em grupo ativo, PF com tipo diferente de 1/5, PF não majoritária, CPF inválido, PJ filial, CNPJ inválido ou não ATIVA, QSA total diferente de 100%. O trecho não comprova natureza jurídica (I14), conversão de tipo (I03) nem deduplicação oficial (I18). A regra de grupo ativo não diferencia próprio GE de outro GE na condição, embora o texto da mensagem exponha o grupo encontrado.

**Risco técnico em QSA:** a preparação antiga aparenta agregar percentuais por `cclub_cli` do sócio, não somente pelo CNPJ da empresa titular. Pode produzir `sum_quad_soc_empr` incorreto quando há mais de um sócio. Isso é hipótese de defeito do enriquecimento e não justifica manipular a massa válida para forçar aprovação.

**Responsabilidade:** na proposta de 70 contratos, PF299 e PF289 possuem uma linha de operação aberta; PF297, PF295, PF291, PF287, PJ112 e PJ118 não foram selecionadas. Essa condição não determina participação societária e não é, por si, uma rejeição de Inclusão no módulo consultado.

## 6. Critérios antes de preparar as solicitações E2E

1. Resolver e validar os CPFs dos candidatos PF a partir do notebook real, incluindo ausência de vínculo ativo, CPF válido/inválido esperado e flags consistentes.
2. Confirmar a situação cadastral e a condição de matriz das candidatas PJ112 e PJ118; a fixture de QSA não comprova cadastro ativo.
3. Reconciliar o QSA dos MEIs e a coerência dos seis grupos Isolados. Gerar os overlays de QSA por cenário, restaurando a massa-base entre execuções.
4. Validar a derivação de `flag_socio_major` e `sum_quad_soc_empr` na preparação; registrar falhas de lógica como defeitos, não erros da fixture.
5. Homologar I03, I04, I05, I14 e I18 com negócio antes de fixar decisão final; confirmar se há regra adicional de controladores comuns para os casos positivos.
6. Validar o resultado por componente e a persistência por grupo, além dos eventos, sem depender apenas do retorno da solicitação.

**Escopo desta revisão:** somente a documentação do catálogo I01–I18 foi atualizada. Nenhum dado de cliente, QSA, grupo, contrato ou solicitação foi gravado/alterado.
