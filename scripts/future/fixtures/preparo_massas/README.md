> **Histórico do preparo por cenário.** O fluxo operacional vigente da sprint está em [RODADAS.md](../RODADAS.md) (v1.3). Não utilizar o fluxo legado em paralelo com os lotes. A exclusão de cadastro e a clonagem de identidades foram desativadas. Não sobrescrever documentos nem criar clientes.

# Motor GRUP — preparo operacional das massas sintéticas

**Versão 1.0 | Sprint de testes integrados e E2E em DV e HO**

Este pacote complementa o roteiro de execução e a planilha de solicitações. Ele prepara as tabelas de teste antes de cada caso. A criação de solicitações, o processamento, a validação de eventos e o retorno ao Frontend continuam sendo realizados pelo fluxo real. Não é um executor automatizado de E2E nem substitui os contratos físicos existentes.

## 1. Arquivos

| Arquivo | Finalidade |
|---|---|
| `preparar_massa.py` | Funções de consulta offline, captura/restauração de baseline e aplicação de overlays no Databricks |
| `main.py` | Notebook Python de exemplo, com células separadas e escritas comentadas |
| `config.example.json` | Mapeamento a preencher com os contratos e nomes reais das tabelas mock de DV ou HO |
| `cenarios.json` | 237 etapas de 217 cenários, com alterações e pré-condições |
| `rodadas/R00.json` | Checklist de prontidão |
| `rodadas/R01.json` a `R09.json` | Ordem de execução de cada rodada, conforme roteiro |
| `roteiro_alteracoes.csv` | Índice operacional de 295 etapas em DV/HO |
| `alteracoes_detalhadas.csv` | Lista legível das alterações e instruções por etapa/ambiente |
| `tests/test_preparo.py` | Testes offline de integridade, planejamento e proteções de configuração |

## 2. Estratégia de restauração

A massa-base deve ser carregada uma vez em cada ambiente. O operador captura a versão Delta das seis tabelas sintéticas: PF, PJ, QSA, responsabilidade, grupos e componentes. O manifesto guarda a identidade, o schema e a versão de cada tabela. Antes de um cenário independente, o script restaura as seis tabelas para esse baseline e aplica somente os overlays do caso. Isso elimina resíduos de GEs novos, inclusões, exclusões e unificações de testes anteriores. **Não restaura tabelas compartilhadas, produtivas ou não sintéticas.** A escolha por restaurar as seis tabelas exclusivas, em vez de tentar calcular todas as alterações inversas do Motor, é deliberada para esta campanha manual.

Não há transação atômica entre as seis tabelas. A substituição do QSA também envolve DELETE por titular seguido de append dos novos vínculos. Se houver falha, não envie a solicitação; restaure a massa e repita o cenário completo. Não execute `VACUUM` que remova os arquivos das versões de baseline durante a campanha. Confirme suporte a `RESTORE TABLE` e privilégios no runtime.

**Importante:** o baseline Delta não inclui MongoDB, tabelas do Backend, filas, consumidores, caches, sequências de geração de código, tabelas de eventos ou outros estados externos. O operador deve aguardar o término de todos os efeitos assíncronos e coordenar a restauração/reconciliação dos sistemas que também mantêm estado de grupos/componentes. Se houver CDF/consumidores que interpretem RESTORE como novas alterações, pausar e reconciliar conforme procedimento autorizado. Não restaurar enquanto houver jobs ou eventos pendentes. Se não houver isolamento exclusivo, não usar este mecanismo; definir um procedimento de restauração seletiva com a equipe.

## 3. Configuração (uma vez por ambiente)

1. Copiar o pacote para o workspace autorizado. Usar Python com PySpark e Delta Lake no Databricks; o objeto `spark` já existente é passado ao operador. A consulta offline usa apenas a biblioteca padrão.
2. Copiar `config.example.json` para `config_DV.json` e `config_HO.json`, preencher `ambiente`, seis nomes completos `catalog.schema.table`, `namespace_autorizados` e um `baseline_arquivo` persistente e diferente por ambiente. Não apontar para tabelas de origem reais.
3. Confirmar os mapeamentos de colunas e tipos. A configuração usa nomes candidatos recuperados dos contratos; `rnatur_jurid` está vazio de propósito porque a coluna física precisa ser confirmada (`rnatu_jurid`/outra nomenclatura). `rscit` é alias textual do catálogo, não coluna comprovada. Confirmar a coluna de CNPJ completo, o tipo de pessoa na responsabilidade e os valores de validade/matriz/atividade. Se a tabela tiver colunas adicionais, preencher `defaults_qsa` e `defaults_componentes` com valores sintéticos explícitos, inclusive null somente quando permitido. A escala do QSA padrão é 0–100, conforme a fixture. Não inventar chaves ou datas de contrato.
4. Validar que as seis tabelas são Delta, dedicadas à campanha, em schemas `*_wks` explicitamente autorizados, com propriedade `mock.synthetic=true`. O script verifica a propriedade; não a cria nem a altera. Se os mocks concretos ainda não possuem o selo, confirmar com o responsável que são realmente sintéticos antes de adequar a criação. O nome/allowlist/selo são barreiras adicionais, não substituem controle de acesso e roteamento de todos os sistemas.
5. Concluir R00: conciliar 100 PFs, 100 PJs, 18 GEs, 48 vínculos, QSA MEI e não MEI (54 vínculos de 27 PJs não MEI) e 70 operações de responsabilidade. O código confere as quantidades cadastrais, documentos dos 61 clientes de referência e composição dos 18 GEs; a conferência completa do QSA e responsabilidade, bem como os contratos vigentes e o roteamento, permanece responsabilidade do operador. Confirmar as dez PFs 281–299 e PJs 112/118/120. O baseline deve refletir a massa correta, não um estado já alterado por testes.
6. Somente após as confirmações, marcar `massa_exclusiva_confirmada` e `contratos_confirmados` como `true`. Capturar baseline uma única vez por ambiente, com todos os processamentos ociosos.

```python
from preparar_massa import MassaGRUP, plano, rodada

massa = MassaGRUP(spark, 'config_DV.json')
massa.capturar_baseline(r00_conferido=True, sem_processamento_pendente=True)
```

O arquivo de baseline não deve ser sobrescrito automaticamente. Em caso de nova carga, capture outro manifesto após R00. Mantenha a sessão e os arquivos persistentes; não compartilhe uma mesma massa entre campanhas concorrentes.

## 4. Execução durante a sprint

Consultar offline, sem Spark ou escrita:

```bash
python preparar_massa.py rodada R03
python preparar_massa.py plano B02
python preparar_massa.py plano C03 --passo 2
```

No Databricks, antes de enviar cada solicitação:

```python
# 1. Visualizar, sem escrita (inclui condições padrão F01–F48).
massa.preparar('B01', aplicar=False)
# 2. Restaurar baseline e aplicar as alterações específicas.
massa.preparar('B01', aplicar=True, sem_processamento_pendente=True)
# 3. Conferir pré-condições, estado do Backend e UI; enviar B01 pelo Frontend.
# 4. Aguardar conclusão, eventos e consumidor; registrar evidências.
# 5. Preparar B02: restaura inclusive o vínculo criado por B01.
massa.preparar('B02', aplicar=True, sem_processamento_pendente=True)
```

A preparação B01 coloca PJ74 com PF107=50% e PF299=50%; B02 substitui pelo QSA PF107=50,01% e PF299=49,99%. Não envie B02 enquanto houver efeitos de B01 em trânsito. O retorno `preparo_aplicado=True` significa apenas que o preparo físico foi realizado e as alterações conferidas; **não** significa que o E2E passou. Conferir todos os pré-requisitos e o oráculo funcional antes de criar o pedido.

### Sequências e casos especiais

```python
massa.preparar('C03', 1, aplicar=True, sem_processamento_pendente=True)
# Enviar Formalização no Frontend, aguardar conclusão e capturar GE criado.
# Sem restaurar baseline: aplicar somente alterações do segundo passo.
massa.preparar('C03', 2, aplicar=True, sem_processamento_pendente=True,
               passo_anterior_concluido=True)
# Enviar Exclusão usando o código de GE efetivamente gerado no passo 1.
```

O segundo passo exige que o primeiro tenha sido preparado na mesma instância do operador e que sua conclusão seja confirmada. Em caso de reinício de sessão ou falha, restaure e repita a sequência desde o início. FX11 mantém o primeiro GE até a comparação de códigos. P13 reprocessa o mesmo pedido, sem criar outro. P14 prepara uma vez (passo 1) e envia os dois pedidos concorrentes; não executar `preparar` para o passo 2. O resultado do par é uma hipótese de um aprovado e um reprovado, não uma atribuição de vencedor.

Ao terminar a campanha, ou para recuperar uma falha, com sistemas ociosos:

```python
massa.restaurar(confirmar=True, sem_processamento_pendente=True)
```

## 5. O que o script altera

- **Cadastro:** atualiza apenas os campos definidos no overlay, por `cclub_cli` e documento conferidos. B06 remove o cadastro PF específico. F01–F48 também aplicam a condição explícita do catálogo: CPF válido; CNPJ válido, ativo e matriz. Demais campos permanecem na massa-base. O script não muda o documento de uma PJ para fabricar uma filial; o caso altera o indicador previsto no catálogo.
- **QSA:** substitui apenas o quadro do titular indicado, mantendo percentuais, sócios e duplicidades intencionais; QSA ausente significa remover todos os registros do titular. A escrita usa o schema físico e valores de datas/indicadores configurados. Não normaliza somatórios inválidos.
- **Responsabilidade:** `EXIGIR_ATIVA` verifica que o enriquecimento recuperado produziria flag verdadeira; se faltar contrato, interrompe em vez de inventar operação. `SEM_REGISTRO` remove os registros da PJ sintética (raiz e filial 1, tipo confirmado), e verifica a ausência de responsabilidade derivada. B29 acrescenta versão mais recente com `catulz_reg='D'`, preservando histórico, como representação técnica de operação não ativa segundo a preparação recuperada; confirmar que isso representa a situação funcional desejada. Não escreve `flag_resp_empr`. B30 (null) e B36 (vencimento) ficam bloqueados até revisão, porque o código recuperado deriva a flag com `isNotNull()` e não filtra vencimento diretamente.
- **Vínculos:** adiciona/remove somente o par GE/documento indicado. U19/P12 preservam a sobreposição proposital em dois grupos. Não altera o grupo em si para fabricar um código inexistente.
- **Ações:** `tem_acao_2` é instrução para a solicitação real, não alteração em tabela intermediária. Se falso, não incluir ação 2 para o mesmo documento; se verdadeiro, criar Inclusão e Exclusão do mesmo documento no mesmo pedido, após confirmar destino e contrato.

## 6. Pendências e desbloqueio

As pendências de definição estão em `cenarios.json` e nos índices de rodada. 21 etapas lógicas estão sinalizadas (algumas repetidas em HO). Não preencher dados desconhecidos arbitrariamente. B30 e B36 não possuem operação física definida nesta versão e não são desbloqueados por uma confirmação genérica. Para os demais, registrar confirmação por ID de etapa no config, por exemplo (valores abaixo são **estrutura**, não definições de negócio):

```json
{
  "confirmacoes_cenarios": {
    "E2E-B24-01": {"justificativa": "<definição confirmada>", "tipo_grupo": 5},
    "E2E-E29-01": {"justificativa": "<contrato e destino confirmados>", "grupo_destino_inclusao": 910105},
    "E2E-B20-01": {"justificativa": "<GE secundário confirmado>", "grupos_secundarios": [910502]}
  }
}
```

Não copiar esses valores como decisão funcional; substituir por valores efetivamente confirmados. Se a definição mudar os dados do catálogo, revisar o cenário e gerar novo overlay. P03/P04/P05 e C05/C13 exigem confirmação do caso pretendido. P07/P15/P16 exigem injeção de falha autorizada e manual; o script prepara apenas a massa de referência. Formalizações vazias podem ser bloqueadas pela UI; não contar como teste do Motor se o pedido não chegar ao Motor.

## 7. Cobertura e validação

O pacote contém 217 casos / 237 etapas lógicas em DV e 52 casos / 58 etapas de repetição em HO (295 etapas no roteiro). Os overlays foram extraídos da planilha de solicitações e comparados com o catálogo v4.0.0: ações, grupos-alvo, componentes, decisão binária, QSA, cadastro/flags e vínculos coincidem para as 237 etapas. As escolhas operacionais (restauração Delta, tradução de flags, B29 e bloqueios) estão documentadas acima e não alteram o oráculo.

```bash
python -m unittest discover -s tests -v
```

Os testes offline não executam Spark, Delta ou o Motor. A aplicação física ainda exige confirmar os contratos e fazer um dry-run/smoke controlado em DV antes de usar HO. Não foi realizada nenhuma escrita em DV/HO nesta entrega. O resultado esperado do Motor é somente APROVADO/REPROVADO; o resultado da campanha é PASS/FAIL/BLOCKED/NOT_RUN. Nenhum cenário foi homologado por este pacote.
