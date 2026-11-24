"""Regera v1.3 a partir do catálogo e da ordem original (sem Databricks)."""
import csv
import copy
import json
from pathlib import Path
from collections import Counter
from dados_rodadas import ROOT, REFERENCIAS, planejar_lotes, modo_passo, validar_plano
from preparo_massas.preparar_massa import DATA


def gerar(origem, destino):
    origem, destino = Path(origem), Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    mapa=[]; res=[]
    for i in range(1,10):
        rodada=f'R{i:02d}'
        fonte=json.loads((origem/f'{rodada}.json').read_text(encoding='utf-8'))
        # Ordens originais da sprint; também aceita JSON v1.3 já compilado.
        if 'execucoes' in fonte:
            casos={}
            for e in fonte['execucoes']:
                casos.setdefault(e['cenario'], {'cenario':e['cenario'],'passos':[]})['passos'].append(copy.deepcopy(DATA['etapas'][e['id']]))
            casos=list(casos.values())
        else:
            # Reconstituir a partir do catálogo imutável, nunca usar IDs de v1.2.
            nomes=fonte.get('ordem_original') or [c['cenario'] for c in fonte['casos']]
            casos=[]
            for nome in nomes:
                ps=[copy.deepcopy(p) for p in DATA['etapas'].values() if p['cenario']==nome]
                casos.append({'cenario':nome,'passos':sorted(ps,key=lambda p:p['passo'])})
        for c in casos:
            for p in c['passos']:
                if any(x['campo']=='remover_cadastro' for x in p['cadastro']):
                    p['bloqueios'].append('B06: não excluir cadastro compartilhado; testar ausência de lookup em integração autorizada.')
                if not p['bloqueios']: validar_plano(p)
        lotes=planejar_lotes(casos)
        idx={c['cenario']:(l['lote'],j+1,c['passos'][0]['id'] in l['verificar_recusas']) for l in lotes for j,c in enumerate(l['casos'])}
        dados={'versao':'1.3','rodada':rodada,'ambiente':fonte['ambiente'],'quantidade_casos':len(casos),
               'quantidade_etapas':sum(len(c['passos']) for c in casos),'ordem_original':[c['cenario'] for c in casos],
               'lotes':[{'lote':l['lote'],'casos':[c['cenario'] for c in l['casos']],'verificar_recusas':l['verificar_recusas']} for l in lotes],
               'casos':casos}
        (destino/f'{rodada}.json').write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        cnt=Counter()
        for c in casos:
            lote,ordem,check=idx.get(c['cenario'],('','',False))
            for p in c['passos']:
                modo=modo_passo(c,p); cnt[modo]+=1
                ids=p['componentes']; docs=[REFERENCIAS[n]['documento'] for n in ids]
                mapa.append(dict(rodada=rodada,ambiente=dados['ambiente'],lote=lote,ordem_no_lote=ordem,
                     etapa=p['id'],acao=p['nome_acao'],ge_alvo=p['grupo'] if p['grupo'] is not None else '',
                     tipo_ge=p['tipo_grupo'] if p['tipo_grupo'] is not None else '',ges_secundarios=','.join(map(str,p['grupos_secundarios'])),
                     cclub_cli=','.join(map(str,ids)),documentos='; '.join(docs),esperado_motor=p['esperado_motor'],
                     preparo=modo,verificar_recusa='SIM' if check and p['passo']==1 else '',bloqueios=' | '.join(p['bloqueios'])))
        res.append({'rodada':rodada,'ambiente':dados['ambiente'],'casos':len(casos),'etapas':dados['quantidade_etapas'],
                    'lotes':len(lotes),'verificacoes':sum(len(l['verificar_recusas']) for l in lotes),**dict(cnt)})
    with (destino/'mapa_solicitacoes.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(mapa[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(mapa)
    (destino/'resumo_lotes.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return res

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--origem',default=str(ROOT/'preparo_massas'/'rodadas'));p.add_argument('--destino',default=str(ROOT/'rodadas'));a=p.parse_args()
    print(json.dumps(gerar(a.origem,a.destino),ensure_ascii=False,indent=2))
