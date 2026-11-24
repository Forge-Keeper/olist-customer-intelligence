# Databricks notebook source
# Nove tasks: somente o parâmetro fixo rodada muda.
# COMMAND ----------
import json
from pathlib import Path
from dados_rodadas import ler_rodada
from massa_rodada import MassaRodada

for nome, padrao in {'rodada':'','rodada_autorizada':'','diretorio_config':'',
                     'lote':'1','caso':'','modo':'preparar','etapa':'','aplicar':'false',
                     'sem_processamento_pendente':'false','anterior_concluido':'false',
                     'evidencia_anterior':'','recuperar':'false'}.items():
    dbutils.widgets.text(nome,padrao)

def param(nome):return dbutils.widgets.get(nome).strip()
def flag(nome):
    v=param(nome).lower()
    if v not in ('true','false'):raise ValueError(f'{nome}: true ou false.')
    return v=='true'

rodada=param('rodada').upper()
dados=ler_rodada(rodada)
if rodada!=param('rodada_autorizada').upper():dbutils.notebook.exit('IGNORADA: rodada não autorizada.')
pasta=Path(param('diretorio_config'))
if not pasta.is_absolute():raise ValueError('Informe diretorio_config absoluto.')
massa=MassaRodada(spark,pasta/f"config_{dados['ambiente']}.json")
resultado=massa.preparar(rodada,lote=int(param('lote')),caso=param('caso').upper(),modo=param('modo').lower(),
    etapa=param('etapa').upper(),aplicar=flag('aplicar'),sem_processamento_pendente=flag('sem_processamento_pendente'),
    anterior_concluido=flag('anterior_concluido'),evidencia_anterior=param('evidencia_anterior'),recuperar=flag('recuperar'))
print(json.dumps(resultado,ensure_ascii=False,default=str,indent=2))
