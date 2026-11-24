"""Preparacao por rodada: clona somente dependencias de cada caso do R00.
Reutiliza as operacoes de MassaGRUP; nao altera o baseline nem cenarios anteriores.
"""
from collections import Counter
from pathlib import Path
from datetime import timedelta
from preparo_massas.preparar_massa import MassaGRUP, ROLES, REFS, load_json, dump_json
from dados_rodadas import ler_rodada, documento, id_cliente, id_grupo, remapear, sementes, fechamento


def normalizar(valor, tamanho):
    s = str(valor)
    if not s.isdigit() or len(s) > tamanho: raise ValueError(f'Documento invalido: {valor}')
    return s.zfill(tamanho)


class MassaRodada:
    def __init__(self, spark, config):
        self.m = MassaGRUP(spark, config)
        self.cfg = self.m.cfg
        self.clone = self.cfg['clonagem']
        if not self.clone.get('confirmada'): raise PermissionError('Confirme contratos de clonagem e faixas reservadas.')
        if not Path(self.cfg['baseline_arquivo']).is_absolute(): raise ValueError('Use baseline_arquivo absoluto e persistente.')
        self.baseline = self.m._baseline()
        self.roles = ROLES
        self.cols = self.cfg['colunas']
        self.val = self.cfg['valores']
        self.nomes = self.clone['nomes']
        for role in ('pf','pj','grupos'):
            if not self.nomes.get(role): raise ValueError(f'Mapeie a coluna de nome: {role}')
        # Colunas extras precisam ser declaradas como nao identitarias ou remapeadas.
        for role in ROLES:
            if role not in ('pf','pj','componentes') and self.clone.get('derivadas',{}).get(role): raise ValueError(f'Derivadas nao implementadas em {role}.')
            schema = set(self.m.schemas[role].fieldNames())
            known = {c for c in self.cols[role].values() if c} | set(self.clone.get('preservar',{}).get(role,[]))
            known |= set(self.clone.get('derivadas',{}).get(role,{}))
            if role in self.nomes: known.add(self.nomes[role])
            if not schema <= known: raise ValueError(f'Colunas sem contrato de clonagem em {role}: {schema-known}')
        if self.clone.get('raiz_pf_digitos') not in (8,9,11): raise ValueError('Confirme comprimento da chave PF na responsabilidade.')
        if not self.clone.get('tipo_responsabilidade_pf') or self.clone['tipo_responsabilidade_pf']==self.val['tipo_responsabilidade_pj']: raise ValueError('Confirme tipo PF de responsabilidade.')
        self.base = {r:[x.asDict() for x in self.m.spark.read.option('versionAsOf',self.baseline['tabelas'][r]['versao']).table(self.m._table(r)).collect()] for r in ROLES}
        self.indexar()

    def col(self,r,k): return self.m._col(r,k)
    def get(self,r,row,k): return row[self.col(r,k)]
    def put(self,r,row,k,v):
        c=self.col(r,k); row[c]=self.m._value(r,c,v)
    def nome(self,r,row,v):
        c=self.nomes[r]; row[c]=self.m._value(r,c,v)
    def derivadas(self,r,row,doc):
        vals={'raiz':doc[:9] if len(doc)==11 else doc[:8], 'filial':'0' if len(doc)==11 else doc[8:12], 'controle':doc[-2:]}
        for c,k in self.clone.get('derivadas',{}).get(r,{}).items():
            if r not in ('pf','pj','componentes'): raise ValueError('Derivadas permitidas somente em cadastro/componentes; revisar contrato.')
            row[c]=self.m._value(r,c,vals[k])

    def indexar(self):
        self.cad={}; self.doc={}; self.groups={}; self.links=[]; self.qsa=[]; self.resp=[]; self.raizes={}
        for role in ('pf','pj'):
            if len(self.base[role])!=100: raise ValueError('R00 deve conter 100 PF e 100 PJ.')
            tipo=role.upper(); n=11 if role=='pf' else 14
            for row in self.base[role]:
                i=int(self.get(role,row,'id')); d=normalizar(self.get(role,row,'documento'),n)
                if i in self.cad or d in self.doc or not 0<i<1000: raise ValueError('Cadastro base duplicado ou fora da faixa.')
                self.cad[i]=(role,row,d); self.doc[d]=i
                raiz=d[:self.clone['raiz_pf_digitos']] if role=='pf' else d[:8]
                t=self.clone['tipo_responsabilidade_pf'] if role=='pf' else self.val['tipo_responsabilidade_pj']
                # Matrizes/filiais que compartilham raiz precisam de outro contrato.
                key=(str(t),int(raiz));
                if key in self.raizes: raise ValueError('Raiz compartilhada no baseline; revisar remapeamento de filiais.')
                self.raizes[key]=i
        for k, ref in REFS.items():
            i=int(k)
            if i not in self.cad or self.cad[i][0].upper()!=ref['tipo'] or self.cad[i][2]!=ref['documento']: raise ValueError(f'Cadastro de referencia divergente: {i}')
        for row in self.base['grupos']:
            g=int(self.get('grupos',row,'id'))
            if g in self.groups: raise ValueError('GE duplicado no baseline.')
            id_grupo(101,g); self.groups[g]=row
        if len(self.groups)!=18: raise ValueError('Baseline deve conter 18 GEs.')
        for row in self.base['componentes']:
            g=int(self.get('componentes',row,'grupo')); t=str(self.get('componentes',row,'tipo'))
            if t==str(self.val['tipo_componente_pf']): n=11
            elif t==str(self.val['tipo_componente_pj']): n=14
            else: raise ValueError('Tipo de componente desconhecido.')
            i=self.doc[normalizar(self.get('componentes',row,'documento'),n)]
            if g not in self.groups: raise ValueError('Componente sem GE.')
            self.links.append((g,i,row))
        for row in self.base['qsa']:
            a=self.doc[normalizar(self.get('qsa',row,'titular'),14)]; b=int(self.get('qsa',row,'id_socio'))
            if b not in self.cad or normalizar(self.get('qsa',row,'documento_socio'),len(self.cad[b][2]))!=self.cad[b][2]: raise ValueError('Socio QSA nao conciliado com cadastro sintetico.')
            self.qsa.append((a,b,row))
        for row in self.base['responsabilidade']:
            key=(str(self.get('responsabilidade',row,'tipo')),int(self.get('responsabilidade',row,'raiz')))
            if key not in self.raizes: raise ValueError('Responsabilidade sem cliente sintetico correspondente.')
            self.resp.append((self.raizes[key],row))
        self.ops={op:i+1 for i,op in enumerate(sorted({str(self.get('responsabilidade',r,'operacao')) for _,r in self.resp}))}
        if len(self.ops)>=1000: raise ValueError('Operacoes fora da faixa reservada.')
        if Counter((g,i) for g,i,_ in self.links)!=Counter((a['grupo_base'],a['id']) for a in REFS.values() if a['grupo_base']): raise ValueError('Vinculos do baseline divergentes do catalogo.')

    def compilar(self, caso):
        slot=caso['slot']; label=caso['cenario']; passos=caso['passos']
        ids, gs=fechamento(*sementes(passos),[(g,i) for g,i,_ in self.links],[(a,b) for a,b,_ in self.qsa])
        refs={}; rows={r:[] for r in ROLES}; tag=f"{caso['rodada']}-{label}"
        for i in sorted(ids):
            role,row,doc=self.cad[i]; novo=documento(slot,i,role.upper(),doc[8:12] if role=='pj' else '0001')
            nome=f'{tag} {i}'
            refs[str(i)]={'id':id_cliente(slot,i),'tipo':role.upper(),'documento':novo,'nome':nome,'grupo_base':None}
            x=dict(row); self.put(role,x,'id',refs[str(i)]['id']); self.put(role,x,'documento',novo); self.nome(role,x,nome); self.derivadas(role,x,novo); rows[role].append(x)
        for g in sorted(gs):
            x=dict(self.groups[g]); self.put('grupos',x,'id',id_grupo(slot,g)); self.nome('grupos',x,f'{tag} GE {g}'); rows['grupos'].append(x)
        for g,i,row in self.links:
            if g not in gs: continue
            a=refs[str(i)]; a['grupo_base']=id_grupo(slot,g); x=dict(row); self.put('componentes',x,'grupo',a['grupo_base']); self.put('componentes',x,'documento',a['documento']); self.put('componentes',x,'nome',a['nome']); self.derivadas('componentes',x,a['documento']); rows['componentes'].append(x)
        for a,b,row in self.qsa:
            if a not in ids: continue
            x=dict(row); titular,socio=refs[str(a)],refs[str(b)]; self.put('qsa',x,'titular',titular['documento']); self.put('qsa',x,'id_socio',socio['id']); self.put('qsa',x,'documento_socio',socio['documento']); self.put('qsa',x,'nome_socio',socio['nome']); rows['qsa'].append(x)
        for i,row in self.resp:
            if i not in ids: continue
            x=dict(row); a=refs[str(i)]; d=a['documento']; raiz=d[:self.clone['raiz_pf_digitos']] if a['tipo']=='PF' else d[:8]
            self.put('responsabilidade',x,'raiz',raiz); self.put('responsabilidade',x,'operacao',9800000000+slot*1000+self.ops[str(self.get('responsabilidade',row,'operacao'))]); rows['responsabilidade'].append(x)
        return refs, rows, [remapear(p,slot,refs) for p in passos]

    def chaves(self, role, row):
        # Detecta resquicios mesmo quando cadastro/grupo ja nao existe.
        g=lambda k:self.get(role,row,k)
        if role in ('pf','pj'):
            doc=normalizar(g('documento'),11 if role=='pf' else 14)
            return [('cliente',int(g('id'))),('doc',doc),('raiz_doc',role,doc[:9 if role=='pf' else 8])]
        if role=='grupos': return [('ge',int(g('id')))]
        if role=='componentes':
            n=11 if str(g('tipo'))==str(self.val['tipo_componente_pf']) else 14
            return [('ge',int(g('grupo'))),('doc',normalizar(g('documento'),n))]
        if role=='qsa': return [('doc',normalizar(g('titular'),14)),('cliente',int(g('id_socio')))]
        return [('raiz_resp',str(g('tipo')),int(g('raiz'))),('operacao',str(g('operacao')))]

    def preflight(self, refs, p):
        self.m._refs={str(a['id']):a for a in refs.values()}
        self.m._check_manual(p)
        for x in self.m._cad_ops(p):
            if x['campo']!='remover_cadastro': self.m._typed(self.m._ref(x['id'])['tipo'].lower(),x['campo'],x['valor'])
        for q in p['qsa']: self.m._qsa_rows(q)
        for x in p['vinculos']:
            if x['operacao']=='ADICIONAR': self.m._link_row(x)

    def aplicar_inicial(self, refs, rows, p):
        """Aplica os mesmos overlays em memoria antes dos seis appends Delta."""
        self.preflight(refs,p)
        for x in self.m._cad_ops(p):
            role=self.m._ref(x['id'])['tipo'].lower()
            encontrados=[r for r in rows[role] if int(self.get(role,r,'id'))==x['id']]
            if len(encontrados)!=1: raise ValueError('Cadastro do overlay nao encontrado de forma unica.')
            if x['campo']=='remover_cadastro': rows[role].remove(encontrados[0])
            else: self.put(role,encontrados[0],x['campo'],x['valor'])
        for q in p['qsa']:
            rows['qsa']=[r for r in rows['qsa'] if normalizar(self.get('qsa',r,'titular'),14)!=q['documento']]
            rows['qsa'].extend(dict(zip(self.m.schemas['qsa'].fieldNames(),x)) for x in self.m._qsa_rows(q))
        for x in p['vinculos']:
            role='componentes'; doc=x['documento']; g=x['grupo']
            tipo=self.val['tipo_componente_pj'] if self.m._ref(x['id'])['tipo']=='PJ' else self.val['tipo_componente_pf']
            found=[r for r in rows[role] if int(self.get(role,r,'grupo'))==g and str(self.get(role,r,'tipo'))==str(tipo) and normalizar(self.get(role,r,'documento'),len(doc))==doc]
            if x['operacao']=='REMOVER':
                if len(found)!=1: raise ValueError('Vinculo a remover nao e unico.')
                rows[role].remove(found[0])
            else:
                if found or not any(int(self.get('grupos',r,'id'))==g for r in rows['grupos']): raise ValueError('Vinculo a adicionar invalido.')
                rows[role].append(dict(zip(self.m.schemas[role].fieldNames(),self.m._link_row(x))))
        for x in p['responsabilidade']:
            self.responsabilidade_inicial(rows['responsabilidade'],x)

    def responsabilidade_inicial(self, rows, x):
        role='responsabilidade'
        def g(r,k): return self.get(role,r,k)
        raiz=int(x['documento'][:8]); tipo=str(self.val['tipo_responsabilidade_pj'])
        def escopo(r): return int(g(r,'raiz'))==raiz and int(g(r,'filial'))==1
        def pj(r): return escopo(r) and str(g(r,'tipo'))==tipo
        def latest(rs):
            seen={}; versoes=set()
            for r in rs:
                key=tuple(g(r,k) for k in ('raiz','tipo','centro','carteira','operacao'))
                kv=(*key,g(r,'versao'))
                if kv in versoes: raise ValueError('Empate de versao na responsabilidade.')
                versoes.add(kv)
                if key not in seen or g(r,'versao')>g(seen[key],'versao'): seen[key]=r
            return list(seen.values())
        def ativa(rs): return any(g(r,'atualizacao') is not None and g(r,'atualizacao')!='D' for r in latest(rs))
        modo=x['modo']; atuais=[r for r in rows if pj(r)]
        if modo=='EXIGIR_ATIVA':
            if not ativa(atuais): raise ValueError('Operacao ativa esperada ausente no baseline.')
        elif modo=='SEM_REGISTRO': rows[:]=[r for r in rows if not pj(r)]
        elif modo=='ULTIMA_VERSAO_D':
            if not ativa(atuais): raise ValueError('B29 exige operacao historica ativa.')
            for r in latest(atuais):
                novo=dict(r); self.put(role,novo,'versao',g(r,'versao')+timedelta(seconds=1)); self.put(role,novo,'atualizacao','D'); rows.append(novo)
        else: raise ValueError('Modo de responsabilidade bloqueado.')
        if ativa([r for r in rows if escopo(r)])!=x['flag_esperada']: raise ValueError('Responsabilidade derivada divergente.')

    def preparar(self, rodada, *, aplicar=False, etapa='', evidencia_anterior='', sem_processamento_pendente=False):
        data=ler_rodada(rodada)
        if data['ambiente']!=self.cfg['ambiente']: raise ValueError('Ambiente divergente.')
        if aplicar and not sem_processamento_pendente: raise PermissionError('Confirme sistemas ociosos e ambiente exclusivo.')
        saida=Path(self.clone['diretorio_saida'])
        if not saida.is_absolute(): raise ValueError('Use diretorio_saida absoluto e persistente.')
        rel=saida/f"{data['ambiente']}_{rodada}.json"
        if etapa:
            casos=[c for c in data['casos'] if any(p['id']==etapa for p in c['passos'])]
            if len(casos)!=1: raise ValueError('Etapa nao pertence a rodada.')
            c=casos[0]; refs,_,planos=self.compilar(c); p=next(x for x in planos if x['id']==etapa)
            if p['passo']<=1 or p['cenario']=='P14' or not p['alteracoes_fisicas']: raise ValueError('Etapa nao exige update intermediario.')
            if p['bloqueios']: raise ValueError('Etapa bloqueada: '+str(p['bloqueios']))
            if not aplicar: return p
            if not evidencia_anterior.strip(): raise PermissionError('Informe evidencia do passo anterior concluido.')
            manifesto=load_json(rel)
            if manifesto['status']!='PREPARADA' or manifesto['baseline']!=self.m._baseline() or not any(x['cenario']==c['cenario'] and x['status']=='PREPARADO' for x in manifesto['casos']): raise PermissionError('Rodada/caso nao preparado neste baseline.')
            item=next(x for x in manifesto['casos'] if x['cenario']==c['cenario'])
            if etapa in item.get('updates',{}): raise PermissionError('Update intermediario ja iniciado; nao repetir.')
            self.preflight(refs,p)
            item.setdefault('updates',{})[etapa]={'status':'EM_PREPARO','evidencia_anterior':evidencia_anterior}
            dump_json(rel,manifesto)
            self.m._ultimo=f"E2E-{p['cenario']}-{p['passo']-1:02d}"
            try:
                result=self.m.preparar(etapa,aplicar=True,sem_processamento_pendente=True,passo_anterior_concluido=True,plano_isolado=p)
                item['updates'][etapa]['status']='PREPARADO'; dump_json(rel,manifesto); return result
            except Exception:
                item['updates'][etapa]['status']='FALHA'; manifesto['status']='FALHA'; dump_json(rel,manifesto); raise
        lote={r:[] for r in ROLES}; report=[]; alocadas=set()
        for c in data['casos']:
            refs,rows,planos=self.compilar(c); p=planos[0]
            item={'cenario':c['cenario'],'slot':c['slot'],'passos':planos,'referencias':refs,'status':'BLOQUEADO' if p['bloqueios'] else 'PREVISTO'}; report.append(item)
            if p['bloqueios']: continue
            keys={k for r in ROLES for row in rows[r] for k in self.chaves(r,row)}
            for a in refs.values():
                pf=a['tipo']=='PF'; t=self.clone['tipo_responsabilidade_pf'] if pf else self.val['tipo_responsabilidade_pj']; n=self.clone['raiz_pf_digitos'] if pf else 8
                keys.add(('raiz_resp',str(t),int(a['documento'][:n])))
            if keys & alocadas: raise ValueError('Colisao de identidades entre casos.')
            alocadas |= keys
            self.aplicar_inicial(refs,rows,p)
            for r in ROLES: lote[r].extend(rows[r])
        out={'rodada':rodada,'ambiente':data['ambiente'],'baseline':self.m._baseline(),'status':'PREVIEW','casos':report,'linhas':{r:len(lote[r]) for r in ROLES}}
        if not aplicar: return out
        if rel.exists(): raise PermissionError('Rodada ja iniciada; nao repetir carga sobre identidades existentes.')
        if self.m._df('grupos').filter(self.m._eq('grupos','id',9999999)).limit(1).count(): raise ValueError('GE propositalmente ausente existe no ambiente.')
        for r in ROLES:
            for row in self.m._df(r).collect():
                if set(self.chaves(r,row.asDict())) & alocadas: raise ValueError(f'Colisao com dados existentes em {r}.')
        dfs={r:self.m.spark.createDataFrame([tuple(x[f.name] for f in self.m.schemas[r].fields) for x in lote[r]],self.m.schemas[r]) for r in ROLES if lote[r]}
        out['status']='EM_PREPARO'; dump_json(rel,out)
        try:
            for r in ROLES:
                if r in dfs: dfs[r].write.format('delta').mode('append').saveAsTable(self.m._table(r))
            # Compara somente as identidades desta rodada, preservando duplicidades propositais.
            for r in ROLES:
                nomes=self.m.schemas[r].fieldNames()
                def chave(row): return tuple(str(row[n]) for n in nomes)
                atual=Counter(chave(x.asDict()) for x in self.m._df(r).collect() if set(self.chaves(r,x.asDict())) & alocadas)
                if atual!=Counter(chave(x) for x in lote[r]): raise ValueError(f'Validacao pos-carga divergente em {r}.')
            for item in report:
                if item['status']=='PREVISTO': item['status']='PREPARADO'
            out['status']='PREPARADA'; dump_json(rel,out)
        except Exception:
            out['status']='FALHA'; dump_json(rel,out); raise
        return out
