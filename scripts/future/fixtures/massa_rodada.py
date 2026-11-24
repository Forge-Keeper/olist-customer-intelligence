"""Executa um lote da rodada, reutilizando MassaGRUP. Nunca cria clientes."""
from copy import deepcopy
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import json

from dados_rodadas import (IDS_PF, IDS_PJ, REFERENCIAS, QSA_BASE, ler_rodada,
                           conflito, verificacoes, modo_passo, validar_plano, chave_json)
from preparo_massas.preparar_massa import MassaGRUP, ROLES, dump_json, load_json, ROOT as PREPARO_ROOT


def selecionar(data, lote, caso=''):
    l = next((x for x in data['lotes'] if x['lote']==lote), None)
    if l is None: raise ValueError('Lote não pertence à rodada.')
    if caso and caso not in l['casos']: raise ValueError('Caso não pertence ao lote.')
    nomes=[caso] if caso else l['casos']
    por_id={c['cenario']:c for c in data['casos']}
    cs=[por_id[n] for n in nomes]
    if any(c['passos'][0]['bloqueios'] for c in cs): raise PermissionError('Caso bloqueado.')
    return cs


def consolidar(massa, casos, rodada, lote):
    """União das alterações iniciais; uma única restauração antes do lote."""
    p=deepcopy(casos[0]['passos'][0])
    p.update(id=f'{rodada}-L{lote:02d}', cenario='LOTE', passo=1,
             componentes=[], qsa=[], cadastro=[], responsabilidade=[], vinculos=[],
             acoes_mesmo_pedido=[], bloqueios=[], avisos=[], cadastro_padrao=None,
             restaurar_antes=True, esperado_motor=None)
    mapas={k:{} for k in ('cadastro','qsa','responsabilidade','vinculos')}
    for c in casos:
        a=c['passos'][0]; validar_plano(a)
        ops={'cadastro':massa._cad_ops(a),'qsa':a['qsa'],
             'responsabilidade':a['responsabilidade'],'vinculos':a['vinculos']}
        for k, linhas in ops.items():
            for x in linhas:
                if k=='cadastro':
                    role=REFERENCIAS[x['id']]['tipo'].lower()
                    col, val=massa._typed(role,x['campo'],x['valor'])
                    if col in (massa._col(role,'id'),massa._col(role,'documento')):
                        raise PermissionError('Mapeamento físico tenta alterar identidade.')
                    chave=(x['id'],col); sig=str(val)
                elif k=='qsa': chave=x['titular'];sig=chave_json(x)
                elif k=='responsabilidade': chave=x['id'];sig=chave_json(x)
                else: chave=(x['grupo'],x['id']);sig=chave_json(x)
                antigo=mapas[k].get(chave)
                if antigo is not None and antigo[0]!=sig: raise ValueError('Overlays incompatíveis no lote.')
                mapas[k][chave]=(sig,deepcopy(x))
    for k in mapas:p[k]=[x[1] for x in mapas[k].values()]
    validar_plano(p)
    return p


def documento_normalizado(valor, tamanho):
    s=str(valor)
    if not s.isdigit() or len(s)>tamanho: raise ValueError('Documento cadastral inválido.')
    return s.zfill(tamanho)


class MassaRodada:
    def __init__(self,spark,config):
        self.m=MassaGRUP(spark,config); self.cfg=self.m.cfg
        self.baseline=self.m._baseline()
        self.estado=Path(self.cfg.get('estado_arquivo',''))
        base=Path(self.cfg['baseline_arquivo'])
        if not self.estado.is_absolute() or not base.is_absolute() or self.estado==base:
            raise ValueError('Informe caminhos absolutos, persistentes e distintos para baseline e estado.')
        self.identidade=sha256(base.read_bytes()+(PREPARO_ROOT/'cenarios.json').read_bytes()+chave_json(self.cfg).encode()+b''.join((PREPARO_ROOT.parent/'rodadas'/f'R{i:02d}.json').read_bytes() for i in range(1,10))).hexdigest()

    def _historico(self,role):
        return self.m.spark.read.option('versionAsOf',self.baseline['tabelas'][role]['versao']).table(self.m._table(role))

    def _cadastros(self, historico):
        out={}
        for role,ids,n in (('pf',IDS_PF,11),('pj',IDS_PJ,14)):
            df=self._historico(role) if historico else self.m._df(role)
            rows=df.select(self.m._col(role,'id'),self.m._col(role,'documento')).collect()
            if len(rows)!=100 or {int(r[0]) for r in rows}!=ids:
                raise ValueError('Os 100 PF e 100 PJ originais devem existir; não corrigir por clonagem.')
            docs={int(r[0]):documento_normalizado(r[1],n) for r in rows}
            if len(set(docs.values()))!=100:raise ValueError('Documentos duplicados.')
            out.update(docs)
        if any(out[i]!=r['documento'] for i,r in REFERENCIAS.items()):
            raise ValueError('Divergência entre cadastro e catálogo; reconciliar com Backend/Frontend, sem substituir documentos.')
        return out

    def _identidades(self):
        base=self._cadastros(True)
        if self._cadastros(False)!=base: raise PermissionError('Cadastro atual diverge do R00; não executar RESTORE nem inserir clientes.')
        return base

    def _qsa_base(self,docs):
        df=self._historico('qsa'); m=self.m
        edges=set(QSA_BASE)
        bydoc={d:i for i,d in docs.items()}
        for a,b,socio in df.select(m._col('qsa','titular'),m._col('qsa','id_socio'),m._col('qsa','documento_socio')).collect():
            if str(a) in ('0','00000000000000','SEM INFORMAÇÃO') or str(socio) in ('0','00000000000','SEM INFORMAÇÃO'): continue
            titular=bydoc.get(documento_normalizado(a,14))
            try: i=int(b)
            except (TypeError,ValueError):raise ValueError('Sócio sem identidade conciliada no QSA do R00.')
            if titular not in IDS_PJ or i not in docs or documento_normalizado(socio,len(docs[i]))!=docs[i]:
                raise ValueError('QSA do R00 fora do cadastro conciliado; revisar fonte MEI e não inventar identidade.')
            edges.add((titular,i))
        return tuple(sorted(edges))

    def _digest(self):
        # Massa sintética pequena; compara conteúdo, não versão do Delta.
        return {r:sha256('\n'.join(sorted(chave_json(json.loads(x)) for x in self.m._df(r).toJSON().collect())).encode()).hexdigest() for r in ROLES}

    def preparar(self,rodada,*,lote=1,caso='',modo='preparar',etapa='',aplicar=False,
                 sem_processamento_pendente=False,anterior_concluido=False,evidencia_anterior='',recuperar=False):
        data=ler_rodada(rodada)
        if data['ambiente']!=self.cfg['ambiente']:raise ValueError('Ambiente divergente.')
        if modo not in ('preparar','conferir','intermediario'):raise ValueError('Modo inválido.')
        cs=selecionar(data,lote,caso)
        docs=self._identidades(); qsa=self._qsa_base(docs)
        for a,b in combinations(cs,2):
            if conflito(a,b,qsa,docs):
                raise ValueError('Dependência adicional no R00: execute este lote por caso (parâmetro caso), não altere a massa.')
        checks=verificacoes(cs,qsa,docs)
        cs=sorted(cs,key=lambda c:c['passos'][0]['id'] not in checks)
        checks=verificacoes(cs,qsa,docs)
        chave={'identidade':self.identidade,'ambiente':data['ambiente'],'rodada':rodada,'lote':lote,'casos':[c['cenario'] for c in cs]}
        planos={p['id']:(c,p) for c in cs for p in c['passos']}
        if modo=='preparar':
            if etapa:raise ValueError('Não informar etapa ao preparar lote.')
            merged=consolidar(self.m,cs,rodada,lote)
            preview={**chave,'status':'PREVIEW','verificar_recusas':checks,'alteracoes':{k:len(merged[k]) for k in ('cadastro','qsa','responsabilidade','vinculos')},'execucoes':[{ 'id':p['id'],'preparo':modo_passo(c,p),'componentes':p['componentes'],'grupo':p['grupo'],'esperado_motor':p['esperado_motor']} for c in cs for p in c['passos']]}
            if not aplicar:return preview
        else:
            if etapa not in planos:raise ValueError('Etapa não pertence ao lote selecionado.')
            c,p=planos[etapa]
            if modo=='intermediario' and modo_passo(c,p)!='UPDATE_INTERMEDIARIO':raise ValueError('Etapa não requer update intermediário ou está bloqueada.')
            if modo=='conferir' and etapa not in checks:raise ValueError('Etapa não exige conferência compartilhada.')
            if not aplicar:return {**chave,'status':'PREVIEW','modo':modo,'plano':p}
        if not sem_processamento_pendente:raise PermissionError('Confirme ambiente ocioso, Frontend, Backend, Motor e consumidores.')
        state=load_json(self.estado) if self.estado.exists() else None
        if state and (state.get('identidade')!=self.identidade or state.get('ambiente')!=data['ambiente']):
            raise PermissionError('Estado de outro ambiente/baseline. Use o caminho da campanha correta.')
        if modo=='preparar':
            if state:
                if not anterior_concluido or not evidencia_anterior.strip():raise PermissionError('Confirme conclusão/reconciliação do lote anterior e evidência.')
                if not recuperar and (state.get('status')!='PREPARADA' or state.get('pendentes') or state.get('updates_pendentes')):
                    raise PermissionError('Lote anterior interrompido ou incompleto; concluir ou recuperar explicitamente.')
            elif recuperar:raise ValueError('Não há estado anterior para recuperar.')
            st={**chave,'status':'EM_PREPARO','pendentes':checks,'updates_pendentes':[p['id'] for c in cs for p in c['passos'] if modo_passo(c,p)=='UPDATE_INTERMEDIARIO'], 'evidencia_anterior':evidencia_anterior}
            dump_json(self.estado,st)
            try:
                # preparar restaura o R00 uma vez e aplica o overlay consolidado.
                self.m.preparar(merged['id'],aplicar=True,sem_processamento_pendente=True,plano_lote=merged)
                self._identidades()
                st['digest']=self._digest() if checks else {};st['status']='PREPARADA';dump_json(self.estado,st)
            except Exception:
                st['status']='FALHA';dump_json(self.estado,st);raise
            return {**preview,'status':'PREPARADA'}
        if not state or any(state.get(k)!=v for k,v in chave.items()) or state.get('status')!='PREPARADA':
            raise PermissionError('Lote ativo não corresponde à rodada/caso selecionado.')
        if not anterior_concluido or not evidencia_anterior.strip():raise PermissionError('Confirme passo concluído e registre evidência.')
        if modo=='conferir':
            if not state['pendentes'] or state['pendentes'][0]!=etapa:raise PermissionError('Conferir as recusas na ordem publicada.')
            if self._digest()!=state['digest']:
                state['status']='FALHA';dump_json(self.estado,state)
                raise RuntimeError('Recusa alterou a massa: interromper lote, registrar defeito e reconciliar antes de recomeçar.')
            state['pendentes'].pop(0);state.setdefault('evidencias',{})[etapa]=evidencia_anterior;dump_json(self.estado,state)
            return {**chave,'status':'RECUSA_SEM_ALTERACAO','etapa':etapa,'pendentes':state['pendentes']}
        if state['pendentes']:raise PermissionError('Conclua as recusas compartilhadas antes de qualquer caso que altere estado.')
        if etapa not in state['updates_pendentes']:raise PermissionError('Update já executado ou não previsto.')
        prev=f"E2E-{p['cenario']}-{p['passo']-1:02d}"
        state['status']='EM_PREPARO';dump_json(self.estado,state)
        try:
            self.m.retomar_sequencia(etapa,prev,evidencia_anterior)
            plano=deepcopy(p);plano['restaurar_antes']=False
            resultado=self.m.preparar(etapa,aplicar=True,sem_processamento_pendente=True,passo_anterior_concluido=True,plano_lote=plano)
            self._identidades();state['updates_pendentes'].remove(etapa);state.setdefault('evidencias',{})[etapa]=evidencia_anterior
            state['status']='PREPARADA';dump_json(self.estado,state)
            return resultado
        except Exception:
            state['status']='FALHA';dump_json(self.estado,state);raise
