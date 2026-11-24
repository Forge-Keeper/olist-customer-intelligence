import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preparar_massa import DATA, REFS, ROOT, ROLES, MassaGRUP, plano, rodada, preflight_config, qualified


def canonical_hash():
    enc=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'))
    lines=[]
    for s in DATA['etapas'].values():
        q=[[x['titular'],[[a['id'],a['percentual']] for a in x['socios']]] for x in s['qsa']]
        cad=[[x['id'],x['campo'],str(x['valor'])] for x in s['cadastro']]
        for x in s['responsabilidade']:
            if x['modo']=='VENCIMENTO_A_CONFIRMAR':cad.append([x['id'],'dt_fim_contrato',x['data']])
            else:cad.append([x['id'],'flag_resp_empr',str(x['flag_esperada']).lower() if x['flag_esperada'] is not None else 'null'])
        cad.extend([x['id'],'tem_acao_2','1' if x['inclusao'] else '0'] for x in s['acoes_mesmo_pedido'])
        links=[[x['grupo'],x['operacao'],x['id']] for x in s['vinculos']]
        lines.append(enc([s['cenario'],s['passo'],s['acao'],s['grupo'],s['componentes'],s['esperado_motor'],q,sorted(cad,key=enc),sorted(links,key=enc)]))
    h=2166136261
    for c in '\n'.join(sorted(lines)):h=((h^ord(c))*16777619)&0xffffffff
    return f'{h:08x}'


def config():
    c=json.loads((ROOT/'config.example.json').read_text())
    c.update(massa_exclusiva_confirmada=True,contratos_confirmados=True,namespace_autorizados=['dv_teste.grup_wks'])
    c['tabelas']={r:f'dv_teste.grup_wks.{r}' for r in ROLES}
    return c


class CatalogoTest(unittest.TestCase):
    def test_total_e_oraculo(self):
        self.assertEqual(len(DATA['etapas']),237)
        self.assertEqual(len({s['cenario'] for s in DATA['etapas'].values()}),217)
        self.assertEqual(Counter(s['esperado_motor'] for s in DATA['etapas'].values()),{'APROVADO':100,'REPROVADO':137})

    def test_hash_fonte(self):
        self.assertEqual(canonical_hash(),'48482347')

    def test_rodadas(self):
        counts=[(8,8),(63,64),(41,41),(40,40),(31,31),(16,32),(18,21),(40,41),(12,17)]
        all_dv=[];all_ho=[]
        for i,(c,n) in enumerate(counts,1):
            r=rodada(f'R{i:02d}');self.assertEqual((r['casos'],r['etapas']),(c,n))
            self.assertEqual(len(r['execucoes']),n)
            (all_dv if i<=7 else all_ho).extend(e['id'] for e in r['execucoes'])
        self.assertEqual(len(all_dv),237);self.assertEqual(set(all_dv),set(DATA['etapas']))
        self.assertEqual(len(all_ho),58);self.assertEqual(len(set(all_ho)),58)
        self.assertTrue(set(all_ho)<=set(all_dv))

    def test_documentos_e_vinculos_base(self):
        self.assertEqual(sum(bool(x['grupo_base']) for x in REFS.values()),48)
        self.assertEqual(len({x['grupo_base'] for x in REFS.values() if x['grupo_base']}),18)
        for s in DATA['etapas'].values():
            for i in s['componentes']:self.assertIn(str(i),REFS)
            for q in s['qsa']:
                self.assertEqual(q['documento'],REFS[str(q['titular'])]['documento'])
                for x in q['socios']:self.assertEqual(x['documento'],REFS[str(x['id'])]['documento'])
            for x in s['cadastro']+s['responsabilidade']+s['vinculos']:
                self.assertEqual(x['documento'],REFS[str(x['id'])]['documento'])

    def test_qsa_limites(self):
        self.assertEqual(plano('B01')['qsa'][0]['socios'][1]['percentual'],'50.00')
        self.assertEqual(plano('B02')['qsa'][0]['socios'][1]['percentual'],'49.99')
        self.assertEqual(plano('B03')['qsa'][0]['socios'][1]['percentual'],'50.01')
        self.assertEqual(plano('B14')['qsa'][0]['socios'],[])
        self.assertEqual([x['id'] for x in plano('B19')['qsa'][0]['socios']],[299,299])
        self.assertEqual([x['id'] for x in plano('U17')['qsa'][0]['socios']],[111,111,115])

    def test_flags_derivadas(self):
        for s in DATA['etapas'].values():
            self.assertFalse({'flag_resp_empr','tem_acao_2','dt_fim_contrato'} & {x['campo'] for x in s['cadastro']})
        self.assertEqual(plano('E27')['responsabilidade'][0]['modo'],'EXIGIR_ATIVA')
        self.assertEqual(plano('B29')['responsabilidade'][0]['modo'],'ULTIMA_VERSAO_D')
        self.assertTrue(plano('E29')['acoes_mesmo_pedido'][0]['inclusao'])

    def test_sequencias(self):
        for s in DATA['etapas'].values():self.assertEqual(s['restaurar_antes'],s['passo']==1)
        self.assertEqual(plano('C03',2)['grupo_dinamico'],'GE gerado no passo 1')
        self.assertFalse(plano('FX11',2)['restaurar_antes'])
        self.assertEqual(plano('P14',2)['oraculo_concorrencia'],['APROVADO','REPROVADO'])

    def test_vinculos_especiais(self):
        self.assertEqual(plano('E01')['vinculos'][0]['id'],112)
        self.assertEqual({(x['id'],x['operacao']) for x in plano('U01')['vinculos']},{(112,'ADICIONAR'),(68,'REMOVER')})
        self.assertEqual(plano('U19')['vinculos'][0]['id'],84)

    def test_plano_copia(self):
        p=plano('B01');p['qsa'].clear();self.assertTrue(plano('B01')['qsa'])
        with self.assertRaises(KeyError):plano('F99')
        with self.assertRaises(ValueError):rodada('../x')


class ProtecoesTest(unittest.TestCase):
    def test_config_exemplo_recusada(self):
        with self.assertRaises(ValueError):preflight_config(json.loads((ROOT/'config.example.json').read_text()))

    def test_config_sintetica(self):preflight_config(config())

    def test_ambiente_pr(self):
        c=config();c['ambiente']='PR'
        with self.assertRaises(ValueError):preflight_config(c)

    def test_allowlist(self):
        c=config();c['tabelas']['pf']='dv_teste.outro_wks.pf'
        with self.assertRaises(PermissionError):preflight_config(c)

    def test_prod_mesmo_com_allowlist(self):
        c=config();c['tabelas']['pf']='prod.grup_wks.pf';c['namespace_autorizados'].append('prod.grup_wks')
        with self.assertRaises(PermissionError):preflight_config(c)

    def test_identificador_invalido(self):
        with self.assertRaises(ValueError):qualified('x.y.z; DELETE')

    def test_tabelas_duplicadas(self):
        c=config();c['tabelas']['pf']=c['tabelas']['pj']
        with self.assertRaises(ValueError):preflight_config(c)

    def test_cadastro_padrao(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS
        ops=m._cad_ops(plano('F22'))
        self.assertEqual({(x['id'],x['campo']) for x in ops},{(112,'cindcd_cnpj_valid'),(112,'rsit_docto_recta'),(112,'rmtriz_flial_cnpj'),(281,'cindcd_cpf_valid')})

    def test_bloqueios_responsabilidade(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS
        for c in ('B30','B36'):
            m.cfg['confirmacoes_cenarios'][f'E2E-{c}-01']={'justificativa':'teste'}
            with self.assertRaises(ValueError):m._check_manual(plano(c))

    def test_troca_requer_destino(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS
        with self.assertRaises(ValueError):m._check_manual(plano('E29'))
        m.cfg['confirmacoes_cenarios']['E2E-E29-01']={'justificativa':'teste offline'}
        with self.assertRaises(ValueError):m._check_manual(plano('E29'))
        m.cfg['confirmacoes_cenarios']['E2E-E29-01']['grupo_destino_inclusao']=910105
        p=plano('E29');m._check_manual(p)
        self.assertEqual(p['acoes_mesmo_pedido'][0]['grupo_destino_inclusao'],910105)

    def test_tipo_grupo_pendente(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS
        m.cfg['confirmacoes_cenarios']['E2E-B24-01']={'justificativa':'teste offline','tipo_grupo':5}
        p=plano('B24');m._check_manual(p);self.assertEqual(p['tipo_grupo'],5)

    def test_sem_confirmacao_nao_escreve(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS;m._ultimo=None
        self.assertEqual(m.preparar('B01')['id'],'E2E-B01-01')
        with self.assertRaises(PermissionError):m.preparar('B01',aplicar=True)
        with self.assertRaises(PermissionError):m.restaurar()
        with self.assertRaises(PermissionError):m.capturar_baseline()

    def test_passo_anterior_obrigatorio(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS;m._ultimo='E2E-C02-01'
        with self.assertRaises(PermissionError):m.preparar('C03',2,aplicar=True,sem_processamento_pendente=True,passo_anterior_concluido=True)

    def test_p14_sem_segundo_preparo(self):
        m=MassaGRUP.__new__(MassaGRUP);m.cfg=config();m._refs=REFS;m._ultimo='E2E-P14-01'
        with self.assertRaises(ValueError):m.preparar('P14',2,aplicar=True,sem_processamento_pendente=True,passo_anterior_concluido=True)

if __name__=='__main__':unittest.main()
