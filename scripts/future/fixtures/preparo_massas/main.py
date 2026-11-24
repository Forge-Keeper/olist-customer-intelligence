# Databricks notebook source
# Execute as células separadamente. Nenhuma escrita é habilitada por padrão.
from preparar_massa import MassaGRUP, plano, rodada

# COMMAND ----------
# 1. Consultar o plano offline, antes de configurar o ambiente.
CENARIO = 'B01'
PASSO = 1
print(plano(CENARIO, PASSO))
# print(rodada('R03'))

# COMMAND ----------
# 2. Configuração: copie config.example.json para config_DV.json/config_HO.json.
# Preencha os nomes reais das tabelas mock, mapeamentos e caminho do baseline.
# Spark já está disponível no cluster Databricks.
# massa = MassaGRUP(spark, 'config_DV.json')

# COMMAND ----------
# 3. R00: somente após carregar/conferir a massa-base e parar processamentos.
# Executar uma vez por ambiente, não antes de cada caso.
# massa.capturar_baseline(r00_conferido=True, sem_processamento_pendente=True)

# COMMAND ----------
# 4. Visualizar as alterações, incluindo as condições cadastrais padrão de F01–F48.
# display(massa.preparar(CENARIO, PASSO, aplicar=False))

# COMMAND ----------
# 5. Aplicar somente após conferir a exclusividade das tabelas e o estado externo.
# Para um cenário independente (passo 1), restaura baseline e aplica overlay.
# massa.preparar(CENARIO, PASSO, aplicar=True, sem_processamento_pendente=True)

# COMMAND ----------
# 6. Enviar a solicitação no Frontend, acompanhar até o fim, registrar evidências.
# Para sequência, somente depois de concluir o passo 1 na mesma sessão:
# massa.preparar('C03', 2, aplicar=True, sem_processamento_pendente=True,
#                passo_anterior_concluido=True)
# P14: preparar apenas passo 1; enviar os dois pedidos concorrentemente.
# P13: reprocessar a mesma solicitação; não criar outro pedido.

# COMMAND ----------
# 7. Encerramento da campanha ou recuperação após falha, com sistemas ociosos.
# massa.restaurar(confirmar=True, sem_processamento_pendente=True)
