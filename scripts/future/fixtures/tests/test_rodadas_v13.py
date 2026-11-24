"""Offline: planejamento, invariantes de identidade e execução simulada."""
import copy
import csv
import json
import sys
import tempfile
import unittest
from collections import Counter
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dados_rodadas import (ROOT, REFERENCIAS, IDS_PF, IDS_PJ, QSA_BASE,
                           ler_rodada, conflito, verificacoes, planejar_lotes, modo_passo, validar_plano)
from massa_rodada import MassaRodada, consolidar, selecionar, documento_normalizado
from preparo_massas.preparar_massa import MassaGRUP, REFS, DATA, plano


class Catalogo(unittest.TestCase):
    def test_identidades(self):
        self.assertEqual(len(IDS_PF),100);self.assertEqual(len(IDS_PJ),100)
        self.assertFalse(IDS_PF & IDS_PJ)
        for i,r in REFERENCIAS.items():
            self.assertIn(i,IDS_PF if r['tipo']=='PF' else IDS_PJ)
            self.assertEqual(len(r['documento']),11 if r['tipo']=='PF' else 14)
        self.assertEqual(len(REFERENCIAS),61)
        self.assertEqual(len(QSA_BASE),54)

    def test_cobertura_e_oraculos(self):
        dv=[];ho=[];cont=Counter()
        for i in range(1,10):
            d=ler_rodada(f'R{i:02d}')
            for c in d['casos']:
                for p in c['passos']:
                    original=DATA['etapas'][p['id']]
                    for k,v in original.items():
                        if k!='bloqueios': self.assertEqual(p[k],v,(p['id'],k))
                    self.assertEqual(set(original['bloqueios'])-set(p['bloqueios']),set())
                    if p['id']!='E2E-B06-01':self.assertEqual(p['bloqueios'],original['bloqueios'])
                    if not p['bloqueios']:validar_plano(p)
                    (dv if i<=7 else ho).append(p['id']);cont[modo_passo(c,p)]+=1
        self.assertEqual(len(dv),237);self.assertEqual(set(dv),set(DATA['etapas']))
        self.assertEqual(len(ho),58);self.assertEqual(len(set(ho)),58)
        self.assertEqual(cont,{'PREPARO_LOTE':250,'UPDATE_INTERMEDIARIO':11,'SEM_UPDATE':9,'CONCORRENTE_SEM_UPDATE':2,'BLOQUEADO':23})

    def test_lotes_completos_sem_conflito(self):
        for i in range(1,10):
            d=ler_rodada(f'R{i:02d}');at=[]
            for l in d['lotes']:
                cs=selecionar(d,l['lote']);at+=l['casos']
                self.assertEqual(l['verificar_recusas'],verificacoes(cs))
                for a,b in combinations(cs,2):self.assertFalse(conflito(a,b),(i,a['cenario'],b['cenario']))
                self.assertEqual([c['cenario'] for c in cs][:len(l['verificar_recusas'])],[x.split('-')[1] for x in l['verificar_recusas']])
            self.assertCountEqual(at,[c['cenario'] for c in d['casos'] if not c['passos'][0]['bloqueios']])
            self.assertEqual(len(at),len(set(at)))
            self.assertEqual(d['lotes'],[{'lote':l['lote'],'casos':[c['cenario'] for c in l['casos']],'verificar_recusas':l['verificar_recusas']} for l in planejar_lotes(d['casos'])])

    def test_limites_qsa_separados(self):
        d=ler_rodada('R03');l={c:v['lote'] for v in d['lotes'] for c in v['casos']}
        self.assertEqual(len({l[c] for c in ('B01','B02','B03','B04')}),4)

    def test_mapa_e_documentos(self):
        with (ROOT/'rodadas/mapa_solicitacoes.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f,delimiter=';'))
        self.assertEqual(len(rows),295);self.assertEqual(len({(r['rodada'],r['etapa']) for r in rows}),295)
        for r in rows:
            p=DATA['etapas'][r['etapa']];self.assertEqual(r['cclub_cli'],','.join(map(str,p['componentes'])))
            self.assertEqual(r['documentos'],'; '.join(REFERENCIAS[i]['documento'] for i in p['componentes']))
            self.assertEqual(r['esperado_motor'],p['esperado_motor'])
            self.assertEqual(r['ge_alvo'],str(p['grupo']) if p['grupo'] is not None else '')
        row=next(r for r in rows if r['rodada']=='R01' and r['etapa']=='E2E-F22-01')
        self.assertEqual(row['cclub_cli'],'112,281')
        self.assertEqual(row['documentos'],'20010176000131; 73002725765')

    def test_protecoes_identidade(self):
        p=plano('B01');p['qsa'][0]['documento']='00000000000000'
        with self.assertRaises(ValueError):validar_plano(p)
        with self.assertRaises(PermissionError):validar_plano(plano('B06'))
        p=plano('F22');p['componentes'][0]=1101112
        with self.assertRaises(ValueError):validar_plano(p)
        m=MassaGRUP.__new__(MassaGRUP);m._refs=REFS
        with self.assertRaises(PermissionError):m.preparar('B06',aplicar=True)
        with self.assertRaises(PermissionError):m.preparar('B01',plano_isolado=plano('B01'))
        self.assertEqual(documento_normalizado(8765432100012,14),'08765432100012')

    def test_job_nove_tasks(self):
        j=json.loads((ROOT/'job_rodadas.example.json').read_text());self.assertEqual(j['max_concurrent_runs'],1)
        self.assertNotIn('schedule',j);self.assertEqual(len(j['tasks']),9)
        self.assertEqual([t['notebook_task']['base_parameters']['rodada'] for t in j['tasks']],[f'R{i:02d}' for i in range(1,10)])
        self.assertEqual(len({t['notebook_task']['notebook_path'] for t in j['tasks']}),1)
        self.assertTrue(all('depends_on' not in t and t['max_retries']==0 for t in j['tasks']))


class FakeMassa:
    def __init__(self):
        self.cfg=json.loads((ROOT/'config_rodadas.example.json').read_text());self._refs=REFS
        self.calls=[];self.fail=False
    _cad_ops=MassaGRUP._cad_ops
    _ref=MassaGRUP._ref
    def _col(self,role,key):return self.cfg['colunas'][role].get(key) or key
    def _typed(self,role,key,value):return self._col(role,key),value
    def preparar(self,etapa,**kwargs):
        self.calls.append((etapa,copy.deepcopy(kwargs)))
        if self.fail:raise RuntimeError('falha simulada')
        return {'id':etapa,'preparo_aplicado':True}
    def retomar_sequencia(self,*args):self.calls.append(('retomar',args))


class ExecucaoSimulada(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.a=MassaRodada.__new__(MassaRodada);self.a.m=FakeMassa();self.a.cfg=self.a.m.cfg
        self.a.cfg['ambiente']='DV';self.a.estado=Path(self.tmp.name)/'estado.json';self.a.identidade='teste'
        self.a._identidades=lambda:{i:r['documento'] for i,r in REFERENCIAS.items()}
        self.a._qsa_base=lambda docs:QSA_BASE;self.a._digest=lambda:{'massa':'igual'}
        d=ler_rodada('R01');self.lote=next(l['lote'] for l in d['lotes'] if l['verificar_recusas'])
    def run_step(self,r='R01',lote=None,**kw):
        opts=dict(lote=lote or self.lote,aplicar=True,sem_processamento_pendente=True)
        opts.update(kw);return self.a.preparar(r,**opts)
    def estado(self):return json.loads(self.a.estado.read_text())
    def test_preview_sem_escrita(self):
        self.assertEqual(self.run_step(aplicar=False)['status'],'PREVIEW');self.assertFalse(self.a.estado.exists());self.assertFalse(self.a.m.calls)
    def test_um_preparo_por_lote(self):
        r=self.run_step();self.assertEqual(r['status'],'PREPARADA');self.assertEqual(len(self.a.m.calls),1)
        p=self.a.m.calls[0][1]['plano_lote'];self.assertTrue(p['restaurar_antes']);validar_plano(p)
        self.assertEqual(len({q['titular'] for q in p['qsa']}),len(p['qsa']))
    def test_recusa_compartilhada_e_proximo_lote(self):
        self.run_step();s=self.estado();self.assertTrue(s['pendentes'])
        with self.assertRaises(PermissionError):self.run_step(anterior_concluido=True,evidencia_anterior='e')
        for etapa in list(s['pendentes']):self.run_step(modo='conferir',etapa=etapa,anterior_concluido=True,evidencia_anterior='e')
        self.assertFalse(self.estado()['pendentes'])
        with self.assertRaises(PermissionError):self.run_step()
        self.run_step(anterior_concluido=True,evidencia_anterior='fim do lote')
    def test_recusa_com_mutacao_interrompe(self):
        self.run_step();etapa=self.estado()['pendentes'][0];self.a._digest=lambda:{'massa':'diferente'}
        with self.assertRaises(RuntimeError):self.run_step(modo='conferir',etapa=etapa,anterior_concluido=True,evidencia_anterior='e')
        self.assertEqual(self.estado()['status'],'FALHA')
    def test_sequencia_sem_restaurar(self):
        d=ler_rodada('R06');l=next(x['lote'] for x in d['lotes'] if 'C03' in x['casos'])
        self.run_step('R06',l);self.assertIn('E2E-C03-02',self.estado()['updates_pendentes'])
        with self.assertRaises(PermissionError):self.run_step('R06',l,modo='intermediario',etapa='E2E-C03-02')
        self.run_step('R06',l,modo='intermediario',etapa='E2E-C03-02',anterior_concluido=True,evidencia_anterior='C03 passo 1')
        self.assertFalse(self.a.m.calls[-1][1]['plano_lote']['restaurar_antes'])
        self.assertNotIn('E2E-C03-02',self.estado()['updates_pendentes'])
        with self.assertRaises(PermissionError):self.run_step('R06',l,modo='intermediario',etapa='E2E-C03-02',anterior_concluido=True,evidencia_anterior='repeticao')
    def test_falha_e_recuperacao(self):
        self.a.m.fail=True
        with self.assertRaises(RuntimeError):self.run_step()
        self.assertEqual(self.estado()['status'],'FALHA');self.a.m.fail=False
        with self.assertRaises(PermissionError):self.run_step(anterior_concluido=True,evidencia_anterior='e')
        self.run_step(anterior_concluido=True,evidencia_anterior='reconciliado',recuperar=True)
    def test_ambiente_e_processamento(self):
        with self.assertRaises(PermissionError):self.run_step(sem_processamento_pendente=False)
        with self.assertRaises(ValueError):self.run_step('R08',1)
    def test_mapeamento_identidade_recusado(self):
        self.a.m.cfg['colunas']['pj']['cindcd_cnpj_valid']='cclub_cli'
        d=ler_rodada('R01');l=next(x['lote'] for x in d['lotes'] if 'F22' in x['casos'])
        with self.assertRaises(PermissionError):self.run_step('R01',l)

if __name__=='__main__':unittest.main()
