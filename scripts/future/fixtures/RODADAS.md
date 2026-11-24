# GRUP — preparação de massas por rodada (v1.2)

## Uso operacional

A versão 1.2 substitui o fluxo de preparo por caso da versão 1.1 para esta sprint. A carga inicial das seis tabelas sintéticas e o R00 continuam iguais. Capture o baseline Delta uma única vez antes da campanha, usando `preparo_massas/main.py` (ou `MassaGRUP.capturar_baseline`). A versão do catálogo original é preservada; o novo mapa de solicitações deve ser utilizado no Frontend em lugar da planilha com os documentos antigos.

Os nove arquivos `rodadas/R01.json` a `R09.json` contêm os planos completos de cada caso, seus passos e um slot exclusivo por rodada/caso. O código lê apenas o JSON da rodada selecionada para determinar o que preparar. `dados_rodadas.py` remapeia os clientes, CPFs/CNPJs, grupos e referências. `massa_rodada.py` lê as versões históricas das tabelas sintéticas do R00, clona somente o fechamento de dependências (componentes de grupos e QSA nos dois sentidos), conserva características cadastrais e operações, aplica os overlays iniciais em memória e acrescenta as linhas preparadas às seis tabelas. Não sobrescreve os registros originais, nem restaura o baseline entre casos/rodadas. `atualizar_massa.py` é o notebook compartilhado.

| Rodada | Ambiente | Casos | Etapas |
|---|---|---:|---:|
| R01 — Smoke | DV | 8 | 8 |
| R02 — Formalização | DV | 63 | 64 |
| R03 — Inclusão | DV | 41 | 41 |
| R04 — Exclusão | DV | 40 | 40 |
| R05 — Unificação | DV | 31 | 31 |
| R06 — Sequências | DV | 16 | 32 |
| R07 — Integração | DV | 18 | 21 |
| R08 — Regressão funcional | HO | 40 | 41 |
| R09 — Regressão integrada | HO | 12 | 17 |

269 ocorrências de caso, 295 etapas (217 casos distintos e 237 etapas em DV, mais 52 casos e 58 etapas em HO). 251 primeiras etapas sem bloqueio catalogado; 15 updates intermediários sem bloqueio; 5 passos seguintes sem alteração física; 2 passos P14 que não requerem nova preparação; 22 etapas com bloqueios do catálogo (18 primeiros passos e 4 passos seguintes). As expectativas binárias não foram homologadas nesta entrega.

## Configuração

1. Importar o diretório `fixtures/` no workspace autorizado, mantendo os módulos Python e JSON no mesmo layout, incluindo `preparo_massas/preparar_massa.py` e `preparo_massas/cenarios.json` (dependência legada para o catálogo/base). O notebook `atualizar_massa.py` precisa poder importar os módulos do diretório. Não usar o `preparar_task.py` antigo em conjunto com este fluxo.
2. Copiar `config_rodadas.example.json` para `config_DV.json` e `config_HO.json`, em diretório persistente. Preencher os mapeamentos originais, nomes reais das seis tabelas Delta sintéticas exclusivas, namespaces `_wks` e valores físicos. O baseline e `clonagem.diretorio_saida` são caminhos absolutos persistentes, separados por ambiente/campanha. As tabelas precisam ter `mock.synthetic=true`. O baseline original precisa conter os 100 PF, 100 PJ, 18 GEs, 48 vínculos, QSA e responsabilidade reconciliados. O código confere vínculos, cadastros de referência e relacionamentos; não presume dados MEI desconhecidos.
3. Em `clonagem.nomes`, mapear as colunas de nome PF, PJ e GE. Confirmar `tipo_responsabilidade_pf` e `raiz_pf_digitos` conforme schema real. As colunas extras não identitárias podem ser listadas por papel em `clonagem.preservar`; para colunas derivadas de documento em PF/PJ/componentes, mapear coluna física para `raiz`, `filial` ou `controle` em `clonagem.derivadas`. Não declarar chaves ou referências extras como não identitárias; se o schema incluir outras chaves não suportadas, ajustar o mapeamento/código antes de escrever. Verificar capacidade dos tipos, nomes, raiz e código de grupo, além de disponibilidade das faixas sintéticas. Marcar `clonagem.confirmada`, `massa_exclusiva_confirmada` e `contratos_confirmados` apenas após a conferência. Nenhum acesso a dados produtivos.
4. Importar `job_rodadas.example.json` como modelo de configurações do Jobs API 2.2 ou criar as nove tasks na UI. Substituir IDs de compute e caminho do notebook. Sem agendamento, sem dependências, sem retry automático. Em workspaces separados, distribuir R01–R07 em DV e R08–R09 em HO.

## Execução do Job

Todas as tasks apontam para `atualizar_massa.py`; apenas `rodada` (R01…R09) muda por task. No Job, `rodada_autorizada` deve corresponder à task selecionada; outras tasks retornam sem escrever, mesmo se iniciadas por engano. `diretorio_config` é constante no ambiente. `aplicar=false` (default) compila o preview sem escrever. Para aplicar a rodada, após confirmar ausência de processamento, preencher:

```json
{"rodada_autorizada":"R03","aplicar":"true","sem_processamento_pendente":"true","diretorio_config":"/Volumes/.../config","etapa":""}
```

A task prepara todos os casos independentes não bloqueados da rodada em um único run. O relatório `<ambiente>_<rodada>.json` lista identidades, planos remapeados, linhas e status. Somente envie pedidos pelo Frontend após `PREPARADA`. Consulte `rodadas/mapa_solicitacoes.csv` para os novos documentos e GEs (importe como texto para preservar dígitos). Este CSV é o substituto operacional da planilha anterior, que usa IDs antigos. Nomes sintéticos contêm rodada, caso e ID-base. `9999999` continua ausente propositalmente; códigos gerados pelo Motor devem ser capturados na execução. O status PREPARADO não é aprovação do Motor.

## Sequências

Casos independentes têm slots diferentes; todos os passos da mesma sequência compartilham o mesmo slot. Quando o segundo passo não exige mudança física, execute-o diretamente no Frontend após concluir o anterior. Para os 15 passos com atualização intermediária, executar novamente **a mesma task**, preenchendo `etapa` com o ID do segundo passo e `evidencia_anterior` com a referência de evidência do primeiro pedido concluído, além das confirmações acima. Essa execução atualiza apenas os registros isolados do caso, sem restaurar baseline nem tocar outros casos. P14 é uma preparação, dois pedidos concorrentes, sem passo 2 de preparação. P13 reprocessa o mesmo pedido. Nenhum vencedor é predeterminado em P14. Bloqueios do catálogo não são removidos; confirmar e revisar os dados da rodada antes de uma nova campanha para resolvê-los. Não inserir overlays incompatíveis do segundo passo antecipadamente.

## Segurança e limitações

As faixas propostas são determinísticas, não consultadas em bases oficiais: IDs = 1.000.000 + slot×1.000 + ID-base; CPF base 720.000.000 + slot×1.000 + ID-base; CNPJ raiz 83.000.000 + slot×1.000 + ID-base, preservando filial; dígitos verificadores recalculados; GE = 920.000 + slot×50 + índice do GE-base; operação = 9.800.000.000 + slot×1.000 + índice da operação-base. São para uso exclusivo em ambiente de teste, não garantem inexistência de documentos reais nem compatibilidade com faixas corporativas. Confirmar reservas, tipos e geração de GEs antes de escrever; colisões detectadas interrompem a carga. O remapeamento rejeita raiz compartilhada no baseline em vez de inventar uma relação de matriz/filial.

O Job tem `max_concurrent_runs=1`; não iniciar outros Jobs, cargas ou testes enquanto prepara. Não há transação distribuída entre as seis tabelas. O relatório persistente impede reexecução automática da mesma rodada e registra EM_PREPARO/FALHA/PREPARADA; em falha, não enviar solicitações, reconciliar apenas as identidades do lote antes de uma nova campanha. Não apagar relatório para contornar a proteção. Não restaurar o baseline global automaticamente: isso poderia apagar cenários já executados. Preservar versões históricas Delta durante a sprint (sem VACUUM que as invalide). As tabelas precisam ser efetivamente consumidas pelo Frontend/Backend/Motor; sincronização, cache, filas e eventual carga adicional de cadastro do Frontend não são automatizados. Verificar essa integração e fazer um smoke em DV antes de HO.

O catálogo original, regras, resultados binários e antigos scripts são mantidos como referência. Os arquivos novos são validados offline; nenhum teste Spark/Delta ou execução corporativa foi realizado.
