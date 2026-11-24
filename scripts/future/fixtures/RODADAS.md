# GRUP — preparação por rodada e lote (v1.3)

**Versão operacional vigente. Não executar v1.2.** O Frontend, Backend e Motor usam os mesmos 100 PF e 100 PJ. O módulo v1.3 não cria clientes, não muda `cclub_cli`, CPF, CNPJ ou nome, e não remove cadastros. Os 18 GEs originais são usados; os códigos novos de Formalização continuam sendo gerados pelo Motor. A versão 1.2, que criava identidades por slot, está desativada no código. Caso já tenha sido carregada, reconciliar os três sistemas e recuperar a massa original antes de capturar/utilizar R00; a v1.3 recusa cadastros fora da faixa.

## Arquivos e limites da distribuição

- `atualizar_massa.py`: mesmo notebook em todas as nove tasks; o parâmetro fixo `rodada` escolhe `rodadas/RXX.json`.
- `dados_rodadas.py`: regras offline de compatibilidade; `massa_rodada.py`: chama o módulo existente de preparação Delta, com uma restauração por lote independente.
- `rodadas/R01.json` a `R09.json`: nove planos autossuficientes de alterações e casos, agrupados em lotes. `mapa_solicitacoes.csv`: índice operacional com os documentos originais. `resumo_lotes.json`: contagens. `gerar_lotes.py`: reprodutor offline dos lotes a partir da ordem de execução original, sem alterar o catálogo de negócio.
- `docs/GRUP_Solicitacoes_Testes_E2E_DV_HO.xlsx`: planilha v1.3, 12 abas, chaves Rodada + ID lógico, ordem no lote e marcação das recusas a conferir.
- `job_rodadas.example.json`: configuração Jobs API 2.2 com nove tasks; `config_rodadas.example.json`: contratos a preencher.

O catálogo versionado documenta o CPF/CNPJ de 61 dos 200 clientes. Não existe fonte completa com documentos e perfis dos 139 restantes neste pacote. Optou-se por preservar todas as identidades dos 217 casos originais e redistribuir **os casos em lotes**, em vez de substituir pessoas por outras sem comprovar seus documentos, vínculos e atributos. O R00 lê/valida a lista física completa de 100 PF (IDs ímpares 101–299) e 100 PJ (IDs pares 62–260), compara com os 61 registros documentados e verifica a imutabilidade dos 200 documentos em cada execução. O roteiro não inventa documentos nem assume que os outros 139 são intercambiáveis. A otimização integral do uso dos 200 clientes exige a relação cadastral sintética completa, inclusive situação, matriz/filial, natureza jurídica, nomes, QSA MEI e vínculos em todos os sistemas.

O particionamento DSATUR determinístico utiliza os clientes, GEs, membros, condições cadastrais, raízes de responsabilidade e dependências QSA diretas conhecidas. Não promete mínimo global. Casos que podem modificar o mesmo escopo ficam separados. Recusas simples podem compartilhar o lote quando as pré-condições se equivalem; são executadas primeiro e cada uma exige conferência de que as seis tabelas não mudaram. A expectativa de reprovação não garante ausência de efeitos: uma divergência interrompe o lote. Ensaios Pxx de integração são isolados. Sequências preservam estado entre passos. Na execução física, o QSA do R00, inclusive MEI, é acrescentado à análise de conflito; se aparecer incompatibilidade adicional, o lote não escreve e pode ser dividido pelo parâmetro `caso`.

| Rodada | Ambiente | Casos | Etapas | Lotes | Updates intermediários | Recusas a conferir | Bloqueadas |
|---|---|---:|---:|---:|---:|---:|---:|
| R01 | DV | 8 | 8 | 5 | 0 | 3 | 0 |
| R02 | DV | 63 | 64 | 26 | 1 | 37 | 3 |
| R03 | DV | 41 | 41 | 18 | 0 | 24 | 1 |
| R04 | DV | 40 | 40 | 19 | 0 | 7 | 5 |
| R05 | DV | 31 | 31 | 24 | 0 | 7 | 3 |
| R06 | DV | 16 | 32 | 16 | 8 | 0 | 2 |
| R07 | DV | 18 | 21 | 12 | 0 | 0 | 8 |
| R08 | HO | 40 | 41 | 24 | 1 | 6 | 1 |
| R09 | HO | 12 | 17 | 12 | 1 | 0 | 0 |
| Total | | 269 | 295 | 156 | 11 | 84 | 23 |

250 primeiras etapas não bloqueadas, agrupadas em 156 lotes; 11 updates intermediários; 9 passos seguintes sem novo update; 2 passos concorrentes P14 sem novo preparo; 23 etapas bloqueadas (22 anteriores e B06). Portanto, são previstos 167 runs com escrita, e até 84 conferências sem escrita nas tabelas. As conferências atualizam apenas o arquivo de estado. O número pode aumentar se o QSA físico ou uma falha exigir dividir um lote. A decisão do Motor permanece APROVADO/REPROVADO; o status de teste é PASS/FAIL/BLOCKED/NOT_RUN. As expectativas não estão homologadas pelo pacote.

## Configuração inicial

1. Importar os arquivos mantendo o layout `fixtures/`. `atualizar_massa.py` é notebook Databricks; os outros `.py` e JSONs são arquivos de workspace/Git folder importáveis. Não usar `preparar_task.py` legado em paralelo com a v1.3.
2. Copiar `config_rodadas.example.json` para `config_DV.json` e `config_HO.json`. Preencher nomes das seis tabelas Delta sintéticas exclusivas, namespace `_wks`, mapeamentos e valores físicos, `defaults_qsa` e `defaults_componentes` conforme contratos. O selo `mock.synthetic=true` é obrigatório. Confirmar o roteamento real do Frontend, Backend e Motor e que todas as tabelas são de teste. Usar caminhos absolutos persistentes e distintos por ambiente/campanha para `baseline_arquivo` e `estado_arquivo` (por exemplo, Volume autorizado). Nunca mapear um campo cadastral para a coluna de identidade/documento. Não editar CPFs/CNPJs para encaixar no catálogo.
3. Concluir R00 com exatamente os 200 clientes originais, 18 GEs, 48 vínculos, QSA MEI/não MEI e responsabilidade conferidos. Capturar o baseline com `preparo_massas/main.py` ou `MassaGRUP.capturar_baseline`. Não sobrescrever baseline. O R00 deve refletir o estado original, não o estado da v1.2.
4. Criar o Job pelo modelo `job_rodadas.example.json`, preenchendo IDs de compute e caminho do notebook. Sem schedule, sem dependências automáticas, `max_concurrent_runs=1`, `max_retries=0`, fila desabilitada. DV e HO separados em workspaces distintos: 7 tasks DV e 2 HO. Não executar outros jobs ou operações de massa simultaneamente.

## Execução manual

Selecione apenas a task da rodada. O parâmetro `rodada_autorizada` evita escrita nas demais tasks se o Job inteiro for acionado. O `lote` vem do Excel/CSV; siga `Ordem no lote`, não a ordem das abas. `diretorio_config` é o caminho persistente da configuração. O primeiro preparo da campanha não exige evidência de lote anterior. `aplicar=false` é preview; ainda lê o baseline e verifica identidades/conflitos, mas não escreve. Antes de qualquer run, aguarde processamento e consumidores. A preparação restaura R00 uma vez e consolida os overlays iniciais; nenhum pedido é criado pelo Job.

Exemplo: R01, lote 1, F06 e F22 compartilham PJ112/PF281 com o mesmo QSA. Primeiro prepare:

```json
{"rodada_autorizada":"R01","lote":"1","modo":"preparar","aplicar":"true","sem_processamento_pendente":"true"}
```

Com estado PREPARADA e sistemas reconciliados, executar F06 pelo Frontend (tipo 1). Se o resultado esperado for confirmado, conferir que não houve mudança nas seis tabelas antes de F22 (tipo 5). A mesma task verifica, sem escrever nas tabelas:

```json
{"rodada_autorizada":"R01","lote":"1","modo":"conferir","etapa":"E2E-F06-01","aplicar":"true","sem_processamento_pendente":"true","anterior_concluido":"true","evidencia_anterior":"referencia da evidencia F06"}
```

Enviar F22 apenas após `RECUSA_SEM_ALTERACAO` e validação do retorno/eventos no Backend e Frontend. O hash cobre as seis tabelas sintéticas, não os sistemas externos. Se uma recusa modificar a massa ou falhar por motivo inesperado, não continuar; registrar defeito, reconciliar e reexecutar separadamente.

Para avançar a um novo lote, manter `modo=preparar`, `etapa` vazia, novo número de lote, e informar `anterior_concluido=true` com evidência de conclusão/reconciliação do anterior. Confirmar que não há atualizações pendentes de sequência. É possível executar um único caso de um lote com `caso=ID` (por exemplo, `F22`) quando o lote inteiro estiver incompatível no ambiente, registrando o desdobramento. Não modificar manualmente o estado JSON. O Job não seleciona ou cria solicitações automaticamente.

Para `UPDATE_INTERMEDIARIO`, mesma rodada/lote/caso preparado, usar `modo=intermediario`, `etapa=E2E-C03-02` (exemplo), confirmação de conclusão do passo anterior e evidência. Não restaurar baseline; aplicar apenas o overlay do segundo passo. `SEM_UPDATE`: conferir a condição original e executar diretamente no Frontend após conclusão do passo anterior. P14: dois pedidos concorrentes, uma preparação; não predeterminar vencedor. P13: reprocessar o mesmo pedido. A planilha e o JSON preservam esses casos especiais.

## Segurança, recuperação e bloqueios

- RESTORE somente nas seis tabelas **sintéticas exclusivas** e após verificar o histórico legível, a identidade dos objetos e a correspondência de todos os documentos. Não apaga nenhum cliente original; restaura atributos e relações, não a identidade cadastral. Exige autorização operacional para sincronizar/reconciliar Backend, Frontend, caches, filas, eventos, CDF e consumidores. A restauração Delta **não** restaura esses outros estados. Se não houver exclusividade/reconciliação, não utilizar a preparação em lote.
- O controle persistente registra `EM_PREPARO`, `PREPARADA` ou `FALHA`, baseline/configuração/catálogo, lote e verificações/updates pendentes. Não é lock distribuído. Se houver interrupção, não criar solicitação. Reconciliar os sistemas, informar `anterior_concluido=true`, `evidencia_anterior` e `recuperar=true` no modo preparar, para restaurar e reiniciar explicitamente um lote ou caso. Não apagar estado para contornar o gate. Não executar VACUUM que invalide o baseline durante a sprint.
- B06 exige cadastro ausente. Isso não é permitido na massa compartilhada de 200 clientes; permanece no catálogo, bloqueado para E2E. Testar separadamente via integração autorizada da ausência de lookup, sem excluir PF/PJ. Demais bloqueios mantidos. Para resolver um bloqueio, revisar catálogo/contrato e regenerar o plano; não adulterar o arquivo do Job para ignorar bloqueios.
- Nenhum valor de `flag_resp_empr` ou `tem_acao_2` é forçado; a origem e a solicitação real derivam a condição. Não inventar contrato de responsabilidade para suprir condição ausente. Os códigos de GE gerados pelo Motor devem ser obtidos do retorno real; `9999999` permanece inexistente propositalmente.
- O ambiente corporativo não foi acessado. O baseline cadastral completo, QSA MEI, contratos físicos, permissões, RESTORE, sincronização de todos os sistemas e oráculos funcionais precisam ser validados em DV antes de HO. Os testes offline simulam a camada de execução; não demonstram comportamento real do Motor.

## Validação offline

Na pasta `fixtures/`:

```bash
python -m unittest discover -s preparo_massas/tests -p test_preparo.py -v
python -m unittest discover -s tests -p test_rodadas_v13.py -v
```

23 testes anteriores + 15 novos = 38 aprovados. O gerador pode ser executado em diretório de saída de revisão: `python gerar_lotes.py --destino /caminho/revisao` (origem padrão: `preparo_massas/rodadas`). A geração não escreve em tabelas. Não usar o Excel v1.2 ou mapas com IDs de sete dígitos.
