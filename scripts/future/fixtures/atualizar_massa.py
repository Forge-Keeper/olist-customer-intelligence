# Databricks notebook source
# As nove tasks apontam para este notebook e diferem somente no parametro rodada.
# COMMAND ----------
import json
from pathlib import Path
from dados_rodadas import ler_rodada
from massa_rodada import MassaRodada

for nome, padrao in {'rodada':'', 'rodada_autorizada':'', 'diretorio_config':'',
                     'aplicar':'false', 'sem_processamento_pendente':'false',
                     'etapa':'', 'evidencia_anterior':''}.items():
    dbutils.widgets.text(nome,padrao)


def flag(nome):
    v=dbutils.widgets.get(nome).strip().lower()
    if v not in ('true','false'): raise ValueError(f'{nome}: true ou false.')
    return v=='true'

rodada=dbutils.widgets.get('rodada').strip().upper()
dados=ler_rodada(rodada)
if rodada!=dbutils.widgets.get('rodada_autorizada').strip().upper():
    dbutils.notebook.exit('IGNORADA: rodada nao autorizada.')
pasta=Path(dbutils.widgets.get('diretorio_config').strip())
if not pasta.is_absolute(): raise ValueError('Informe diretorio_config absoluto.')
massa=MassaRodada(spark,pasta/f"config_{dados['ambiente']}.json")
resultado=massa.preparar(rodada,aplicar=flag('aplicar'),
    sem_processamento_pendente=flag('sem_processamento_pendente'),
    etapa=dbutils.widgets.get('etapa').strip().upper(),
    evidencia_anterior=dbutils.widgets.get('evidencia_anterior').strip())
print(json.dumps({'rodada':rodada,'status':resultado.get('status','UPDATE'),
                  'linhas':resultado.get('linhas'),'id':resultado.get('id')},ensure_ascii=False,default=str))
