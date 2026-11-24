import csv
import json
import sys
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dados_rodadas import documento, digito, id_cliente, id_grupo, remapear, ler_rodada, sementes, fechamento
from massa_rodada import MassaRodada
from preparo_massas.preparar_massa import DATA, REFS, ROLES, MassaGRUP


def rodadas(): return [ler_rodada(f'R{i:02d}') for i in range(1,10)]


def refs(slot,tag):
    return {k:{**x,'id':id_cliente(slot,x['id']),'documento':documento(slot,x['id'],x['tipo'],x['documento'][8:12] if x['tipo']=='PJ' else '0001'),'nome':f'{tag} {x["id"]}'} for k,x in REFS.items()}


class PlanosTest(unittest.TestCase):
    def test_cobertura(self):
        rs=rodadas(); cases=[c for r in rs for c in r['casos']]; steps=[p for c in cases for p in c['passos']]
        self.assertEqual((len(cases),len(steps)),(269,295))
        self.assertEqual(len({c['slot'] for c in cases}),269)
        dv=[p['id'] for r in rs[:7] for c in r['casos'] for p in c['passos']]
        self.assertEqual(len(dv),237); self.assertEqual(set(dv),set(DATA['etapas']))
        for p in steps: self.assertEqual(p,DATA['etapas'][p['id']])

    def test_identidades(self):
        clientes,docs,ges=set(),set(),set()
        for r in rodadas():
            for c in r['casos']:
                rr=refs(c['slot'],c['cenario'])
                for x in rr.values():
                    self.assertNotIn(x['id'],clientes); clientes.add(x['id'])
                    d=x['documento']; self.assertNotIn(d,docs); docs.add(d)
                    if x['tipo']=='PF': self.assertEqual(d[-2:],digito(d[:9],range(10,1,-1))+digito(d[:10],range(11,1,-1)))
                    else: self.assertEqual(d[-2:],digito(d[:12],[5,4,3,2,9,8,7,6,5,4,3,2])+digito(d[:13],[6,5,4,3,2,9,8,7,6,5,4,3,2]))
                for g in {a['grupo_base'] for a in REFS.values() if a['grupo_base']}:
                    novo=id_grupo(c['slot'],g); self.assertNotIn(novo,ges);ges.add(novo)
        self.assertEqual(id_grupo(101,9999999),9999999)

    def test_overlays_remapeados(self):
        for r in rodadas():
            for c in r['casos']:
                rr=refs(c['slot'],c['cenario']); ids,gs=sementes(c['passos'])
                self.assertTrue(ids<=set(map(int,REFS)))
                for p in c['passos']:
                    q=remapear(p,c['slot'],rr)
                    self.assertEqual(q['esperado_motor'],p['esperado_motor']); self.assertFalse(q['restaurar_antes'])
                    self.assertEqual(q['grupo'],id_grupo(c['slot'],p['grupo']))
                    self.assertEqual(q['componentes'],[rr[str(i)]['id'] for i in p['componentes']])
                    self.assertEqual([[s['percentual'] for s in x['socios']] for x in q['qsa']],[[s['percentual'] for s in x['socios']] for x in p['qsa']])
                    for k in ('cadastro','responsabilidade','vinculos','acoes_mesmo_pedido'):
                        for a,b in zip(p[k],q[k]): self.assertEqual(b['documento'],rr[str(a['id'])]['documento'])

    def test_conflitos_qsa(self):
        c={x['cenario']:x for x in ler_rodada('R03')['casos']}
        titulares=[];docs=[];pcts=[]
        for k in ('B01','B02','B03'):
            x=c[k]; p=remapear(x['passos'][0],x['slot'],refs(x['slot'],k)); titulares.append(p['qsa'][0]['documento']);docs.append(p['componentes'][0]);pcts.append(p['qsa'][0]['socios'][1]['percentual'])
        self.assertEqual((len(set(titulares)),len(set(docs))),(3,3)); self.assertEqual(pcts,['50.00','49.99','50.01'])

    def test_fechamento(self):
        ids,gs=fechamento({1},set(),[(10,1),(10,2),(20,4)],[(2,3),(4,3),(9,8)])
        self.assertEqual(ids,{1,2,3,4});self.assertEqual(gs,{10,20})

    def test_csv_e_job(self):
        with (ROOT/'rodadas/mapa_solicitacoes.csv').open(encoding='utf-8') as f: rows=list(csv.DictReader(f,delimiter=';'))
        self.assertEqual(Counter(x['preparo'] for x in rows),{'PREPARO_RODADA':251,'BLOQUEADO':22,'UPDATE_INTERMEDIARIO':15,'SEM_UPDATE':5,'CONCORRENCIA_P14':2})
        by={(r['rodada'],p['id']):(c,p) for r in rodadas() for c in r['casos'] for p in c['passos']}
        for x in rows:
            c,p=by[x['rodada'],x['etapa']];rr=refs(c['slot'],c['cenario']);q=remapear(p,c['slot'],rr)
            self.assertEqual(x['documentos_novos'],','.join(rr[str(i)]['documento'] for i in p['componentes']))
            self.assertEqual(x['ids_novos'],','.join(map(str,q['componentes'])))
        j=json.loads((ROOT/'job_rodadas.example.json').read_text());self.assertEqual(j['max_concurrent_runs'],1)
        self.assertEqual([t['notebook_task']['base_parameters'] for t in j['tasks']],[{'rodada':f'R{i:02d}'} for i in range(1,10)])
        self.assertEqual(len({t['notebook_task']['notebook_path'] for t in j['tasks']}),1)
        self.assertTrue(all(t['max_retries']==0 and 'depends_on' not in t for t in j['tasks']))
        self.assertNotIn('schedule',j)


class Schema:
    def __init__(self,fields): self.fields=fields
    def fieldNames(self): return self.fields


class FakeM:
    """Adapter de tipos em memoria; sem Spark/Delta, nao representa o schema corporativo."""
    def __init__(self):
        self.cfg={'valores':{'cpf_valido':1,'cnpj_valido':1,'pj_ativa':'ATIVA','pj_matriz':1}}
        self.schemas={'qsa':Schema(['titular','id_socio','documento_socio','nome_socio','percentual']), 'componentes':Schema(['grupo','documento','nome','tipo'])}
    _cad_ops=MassaGRUP._cad_ops
    def _ref(self,i):return self._refs[str(i)]
    def _col(self,r,k):return 'rsit_docto_recta' if k=='rscit' else k
    def _value(self,r,k,v):return v
    def _typed(self,r,k,v):return self._col(r,k),v
    def _check_manual(self,p): assert not p['bloqueios']
    def _qsa_rows(self,q):return [(q['documento'],s['id'],s['documento'],self._ref(s['id'])['nome'],Decimal(s['percentual'])) for s in q['socios']]
    def _link_row(self,x):return (x['grupo'],x['documento'],x['nome'],'J' if self._ref(x['id'])['tipo']=='PJ' else 'F')


def fixture():
    m=MassaRodada.__new__(MassaRodada);m.m=FakeM();m.clone={'raiz_pf_digitos':9,'tipo_responsabilidade_pf':'F'};m.val={'tipo_responsabilidade_pj':'J','tipo_componente_pj':'J','tipo_componente_pf':'F'};m.nomes={'pf':'nome','pj':'nome','grupos':'nome'}
    m.cad={int(k):(x['tipo'].lower(),{'id':x['id'],'documento':x['documento'],'nome':x['nome'],'rsit_docto_recta':'ATIVA'},x['documento']) for k,x in REFS.items()}
    m.groups={x['grupo_base']:{'id':x['grupo_base'],'nome':'base','tipo':x['tipo_grupo']} for x in REFS.values() if x['grupo_base']}
    m.links=[(x['grupo_base'],x['id'],{'grupo':x['grupo_base'],'documento':x['documento'],'nome':x['nome'],'tipo':'J' if x['tipo']=='PJ' else 'F'}) for x in REFS.values() if x['grupo_base']]
    # Simula QSA/contrato basicos para testar transformacoes; nao e a massa de R00 real.
    m.qsa=[(74,107,{'titular':REFS['74']['documento'],'id_socio':107,'documento_socio':REFS['107']['documento'],'nome_socio':'base','percentual':Decimal('100')})]
    m.resp=[(74,{'raiz':int(REFS['74']['documento'][:8]),'filial':1,'tipo':'J','centro':1,'carteira':1,'operacao':'9702000001','versao':datetime(2026,5,5),'atualizacao':'I'})];m.ops={'9702000001':1}
    return m


class CompilacaoTest(unittest.TestCase):
    def test_251_primeiros_passos_sem_colisao(self):
        m=fixture(); n=0
        for r in rodadas():
            seen=set()
            for c in r['casos']:
                if c['passos'][0]['bloqueios']:continue
                rr,rows,ps=m.compilar(c);p=ps[0]
                keys={k for role in ROLES for row in rows[role] for k in m.chaves(role,row)}
                self.assertFalse(keys&seen,c['cenario']);seen|=keys
                m.aplicar_inicial(rr,rows,p);n+=1
        self.assertEqual(n,251)

    def test_b29_preserva_historico(self):
        m=fixture();c=next(x for x in ler_rodada('R04')['casos'] if x['cenario']=='B29');rr,rows,ps=m.compilar(c);m.aplicar_inicial(rr,rows,ps[0]);self.assertEqual([r['atualizacao'] for r in rows['responsabilidade']],['I','D']);self.assertGreater(rows['responsabilidade'][1]['versao'],rows['responsabilidade'][0]['versao'])


if __name__=='__main__': unittest.main()
