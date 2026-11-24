"""Preparo operacional das massas GRUP; não cria pedidos nem executa o Motor.

Importável no Databricks. CLI offline: listar/planejar. Escrita exige configuração,
Delta sintético exclusivo, baseline e confirmação de ausência de processamento.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'cenarios.json').read_text(encoding='utf-8'))
REFS = DATA['referencias']
ROLES = ('pf', 'pj', 'qsa', 'responsabilidade', 'grupos', 'componentes')
IDENT = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*$')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')
    tmp.replace(path)


def quote(name):
    if not isinstance(name, str) or not IDENT.fullmatch(name):
        raise ValueError(f'Identificador inválido: {name!r}')
    return f'`{name}`'


def qualified(name):
    if not isinstance(name, str) or len(name.split('.')) != 3:
        raise ValueError(f'Informe catalog.schema.table: {name!r}')
    return '.'.join(quote(x) for x in name.split('.'))


def ref(i):
    return REFS[str(i)]


def plano(cenario, passo=1):
    key = cenario.upper() if cenario.upper().startswith('E2E-') else f'E2E-{cenario.upper()}-{int(passo):02d}'
    if key not in DATA['etapas']:
        raise KeyError(f'Etapa não encontrada: {key}')
    return copy.deepcopy(DATA['etapas'][key])


def rodada(nome):
    if not re.fullmatch(r'R0[0-9]', nome.upper()):
        raise ValueError('Rodada deve ser R00–R09')
    return load_json(ROOT / 'rodadas' / (nome.upper()+'.json'))


def preflight_config(cfg):
    if cfg.get('ambiente') not in ('DV', 'HO'):
        raise ValueError('Somente DV e HO.')
    if not cfg.get('massa_exclusiva_confirmada') or not cfg.get('contratos_confirmados'):
        raise ValueError('Confirme isolamento exclusivo e contratos físicos antes de usar Spark.')
    tables = cfg.get('tabelas', {})
    if set(tables) != set(ROLES) or len(set(tables.values())) != len(ROLES):
        raise ValueError('Configure seis tabelas distintas, sem nomes vazios.')
    allowed = cfg.get('namespace_autorizados', [])
    for name in tables.values():
        qualified(name)
        catalog, schema, _ = name.split('.')
        if not schema.lower().endswith('_wks') or f'{catalog}.{schema}' not in allowed:
            raise PermissionError(f'Namespace fora da allowlist *_wks: {name}')
        if any(re.search(r'(^|_)(pr|prd|prod|production|producao)(_|$)', x.lower()) for x in (catalog,schema)):
            raise PermissionError(f'Nome sugere produção: {name}')
    if cfg['valores'].get('qsa_escala') not in ('percentual_0_100','fracao_0_1'):
        raise ValueError('Confirme escala física do percentual QSA.')
    if cfg['valores'].get('responsabilidade_exclusao') != 'D':
        raise ValueError('Revisar implementação: código recuperado considera D como exclusão.')
    if not cfg.get('baseline_arquivo'):
        raise ValueError('Informe caminho persistente do manifesto de baseline.')


class MassaGRUP:
    """Operador de massa, para uso manual em notebook com Spark já disponível."""
    def __init__(self, spark, config):
        self.spark = spark
        self.cfg = load_json(config) if isinstance(config, (str, Path)) else copy.deepcopy(config)
        preflight_config(self.cfg)
        from pyspark.sql import functions as F, types as T, Window
        self.F, self.T, self.Window = F, T, Window
        self.schemas = {}
        self.meta = {}
        self._ultimo = None
        self._refs = REFS
        self._validar_destinos()

    def _ref(self, i):
        return self._refs[str(i)]

    def _table(self, role):
        return self.cfg['tabelas'][role]

    def _df(self, role):
        return self.spark.table(self._table(role))

    def _col(self, role, logical):
        name = self.cfg['colunas'].get(role, {}).get(logical)
        if not name:
            raise ValueError(f'Mapeamento físico pendente: {role}.{logical}')
        quote(name)
        if name not in self.schemas[role].fieldNames():
            raise ValueError(f'Coluna não encontrada: {role}.{logical} -> {name}')
        return name

    def _validar_destinos(self):
        preflight_config(self.cfg)
        for role in ROLES:
            name = self._table(role)
            detail = self.spark.sql(f'DESCRIBE DETAIL {qualified(name)}').first().asDict()
            if str(detail.get('format','')).lower() != 'delta':
                raise PermissionError(f'Não é Delta: {name}')
            if str((detail.get('properties') or {}).get('mock.synthetic','')).lower() != 'true':
                raise PermissionError(f'Tabela sem selo mock.synthetic=true: {name}')
            if not detail.get('id'):
                raise ValueError(f'Identidade Delta indisponível: {name}')
            self.schemas[role] = self._df(role).schema
            self.meta[role] = {'tabela':name,'id':detail['id'],'schema':self.schemas[role].json()}
        # All structural columns must be confirmed before any writes.
        required = {'pf':['id','documento'], 'pj':['id','documento'],
                    'qsa':['titular','percentual','indicador','nome_socio','fim','id_socio','documento_socio','data_origem'],
                    'responsabilidade':['raiz','filial','tipo','centro','carteira','operacao','versao','atualizacao'],
                    'grupos':['id','tipo'], 'componentes':['grupo','documento','nome','tipo']}
        for role, fields in required.items():
            for field in fields:self._col(role,field)

    def _version(self, role):
        return int(self.spark.sql(f'DESCRIBE HISTORY {qualified(self._table(role))} LIMIT 1').first()['version'])

    def _dtype(self, role, name):
        return self.schemas[role][name].dataType

    def _value(self, role, name, value):
        field = self.schemas[role][name]
        t = field.dataType; T = self.T
        if value is None or value == 'null':
            if not field.nullable:raise ValueError(f'{role}.{name} não aceita NULL')
            return None
        if isinstance(t,T.StringType):return str(value)
        if isinstance(t,T.BooleanType):
            if str(value).lower() not in ('true','false','0','1'):raise ValueError(f'Booleano inválido: {value}')
            return str(value).lower() in ('true','1')
        if isinstance(t,(T.ByteType,T.ShortType,T.IntegerType,T.LongType)):
            v=Decimal(str(value))
            if v != v.to_integral_value():raise ValueError(f'Inteiro não exato: {value}')
            i=int(v);bits={T.ByteType:8,T.ShortType:16,T.IntegerType:32,T.LongType:64}[type(t)]
            if not -(2**(bits-1)) <= i < 2**(bits-1):raise ValueError(f'Overflow {role}.{name}')
            return i
        if isinstance(t,T.DecimalType):
            v=Decimal(str(value));q=v.quantize(Decimal(1).scaleb(-t.scale))
            if q!=v or abs(q)>=Decimal(10)**(t.precision-t.scale):raise ValueError(f'Precisão insuficiente: {role}.{name}={value}')
            return q
        if isinstance(t,(T.DoubleType,T.FloatType)):return float(value)
        if isinstance(t,T.DateType):return date.fromisoformat(str(value)) if not isinstance(value,date) else value
        if isinstance(t,T.TimestampType) or type(t).__name__=='TimestampNTZType':
            return value if isinstance(value,datetime) else datetime.fromisoformat(str(value))
        raise TypeError(f'Tipo não suportado para alteração explícita: {role}.{name} ({t})')

    def _typed(self, role, logical, value):
        name=self._col(role,logical)
        return name,self._value(role,name,value)

    def _eq(self, role, logical, value):
        name,v=self._typed(role,logical,value)
        return self.F.col(name).eqNullSafe(self.F.lit(v))

    def _doc_eq(self, role, logical, doc):
        # CPF/CNPJ podem estar em coluna string ou numérica. Não alterar o documento.
        name=self._col(role,logical)
        raw=self.F.col(name).cast('string')
        return (self.F.length(raw)<=len(doc)) & raw.rlike('^[0-9]+$') & (self.F.lpad(raw,len(doc),'0')==doc)

    def _cad_pred(self, i, doc):
        role=self._ref(i)['tipo'].lower()
        return role,self._eq(role,'id',i)&self._doc_eq(role,'documento',doc)

    def _check_baseline_data(self):
        # Valida toda a referência disponível; não presume documentos dos demais cadastros.
        for role in ('pf','pj'):
            df=self._df(role); idc=self._col(role,'id'); dc=self._col(role,'documento'); n=11 if role=='pf' else 14
            rows=df.select(idc,dc).collect()
            if len(rows)!=100 or {int(r[0]) for r in rows} != set(range(101,300,2) if role=='pf' else range(62,261,2)):
                raise ValueError(f'Baseline {role}: esperados 100 cadastros únicos.')
            docs={int(r[0]):str(r[1]).zfill(n) for r in rows}
            if len(set(docs.values()))!=100 or any(len(d)!=n or not d.isdigit() for d in docs.values()):
                raise ValueError(f'Baseline {role}: documentos inválidos ou duplicados.')
            for x in REFS.values():
                if x['tipo'].lower()==role and docs.get(x['id'])!=x['documento']:
                    raise ValueError(f'Documento não conciliado: {role} cclub_cli={x["id"]}')
        expected_groups={int(x['grupo_base']):int(x['tipo_grupo']) for x in REFS.values() if x['grupo_base']}
        groups=self._df('grupos').select(self._col('grupos','id'),self._col('grupos','tipo')).collect()
        if len(groups)!=18 or {int(r[0]):int(r[1]) for r in groups}!=expected_groups:
            raise ValueError('Baseline de grupos não corresponde aos 18 GEs planejados.')
        expected=Counter((int(x['grupo_base']),x['documento']) for x in REFS.values() if x['grupo_base'])
        df=self._df('componentes');gc=self._col('componentes','grupo');dc=self._col('componentes','documento');tc=self._col('componentes','tipo')
        vals=self.cfg['valores']; actual=Counter()
        for g,d,t in df.select(gc,dc,tc).collect():
            if str(t)==str(vals['tipo_componente_pj']):n=14
            elif str(t)==str(vals['tipo_componente_pf']):n=11
            else:raise ValueError(f'Tipo de componente desconhecido: {t}')
            actual[(int(g),str(d).zfill(n))]+=1
        if actual!=expected:raise ValueError('Baseline de componentes não corresponde aos 48 vínculos planejados.')
        # A fonte recuperada contém 70 operações lógicas, mas o contrato físico pode ter histórico.
        # Conferir QSA MEI e responsabilidade no R00 antes de confirmar o baseline.

    def capturar_baseline(self, *, r00_conferido=False, sem_processamento_pendente=False):
        if not r00_conferido or not sem_processamento_pendente:
            raise PermissionError('Conclua R00 (inclusive QSA/70 operações) e confirme ausência de processamento.')
        self._validar_destinos();self._check_baseline_data()
        path=Path(self.cfg['baseline_arquivo'])
        if path.exists():raise FileExistsError('Baseline já existe. Não sobrescrever; use outro manifesto após nova carga.')
        manifest={'ambiente':self.cfg['ambiente'],'capturado_utc':datetime.now(timezone.utc).isoformat(),'tabelas':{r:{**self.meta[r],'versao':self._version(r)} for r in ROLES}}
        dump_json(path,manifest)
        return manifest

    def _baseline(self):
        self._validar_destinos()
        m=load_json(self.cfg['baseline_arquivo'])
        if m['ambiente']!=self.cfg['ambiente'] or set(m['tabelas'])!=set(ROLES):raise ValueError('Baseline incompatível com ambiente/configuração.')
        for r in ROLES:
            if any(m['tabelas'][r][k]!=self.meta[r][k] for k in ('tabela','id','schema')):raise ValueError(f'Tabela ou schema mudou desde baseline: {r}')
            v=m['tabelas'][r]['versao']
            if not isinstance(v,int) or v<0:raise ValueError('Versão inválida')
        return m

    def restaurar(self, *, sem_processamento_pendente=False, confirmar=False):
        if not confirmar or not sem_processamento_pendente:raise PermissionError('Restauração exige confirmação explícita e ambiente ocioso.')
        self._ultimo=None
        m=self._baseline()
        # Verify historical snapshots are readable before starting multi-table restoration.
        for r in ROLES:
            v=m['tabelas'][r]['versao']
            self.spark.read.option('versionAsOf',v).table(self._table(r)).count()
        for r in ROLES:
            v=m['tabelas'][r]['versao']
            if self._version(r)!=v:self.spark.sql(f'RESTORE TABLE {qualified(self._table(r))} TO VERSION AS OF {v}').collect()
        self._check_baseline_data()
        self._ultimo=None
        return {'ambiente':self.cfg['ambiente'],'restaurado':True,'versoes_baseline':{r:m['tabelas'][r]['versao'] for r in ROLES}}

    def _row(self, role, logical_values, defaults):
        raw=dict(defaults)
        for logical,value in logical_values.items():raw[self._col(role,logical)]=value
        schema=self.schemas[role]
        if set(raw)!=set(schema.fieldNames()):
            raise ValueError(f'Complete defaults explícitos para {role}; faltantes={set(schema.fieldNames())-set(raw)}, extras={set(raw)-set(schema.fieldNames())}')
        return tuple(self._value(role,f.name,raw[f.name]) for f in schema.fields)

    def _qsa_rows(self, patch):
        vals=self.cfg['valores'];rows=[]
        for socio in patch['socios']:
            pct=Decimal(socio['percentual'])
            if vals['qsa_escala']=='fracao_0_1':pct/=100
            rows.append(self._row('qsa',{'titular':patch['documento'],'percentual':pct,'indicador':vals['qsa_indicador'],'nome_socio':self._ref(socio['id'])['nome'],'fim':vals['qsa_fim'],'id_socio':socio['id'],'documento_socio':socio['documento'],'data_origem':vals['qsa_data_origem']},self.cfg.get('defaults_qsa',{})))
        return rows

    def _link_row(self, patch):
        vals=self.cfg['valores'];i=patch['id']
        defaults=dict(self.cfg.get('defaults_componentes',{}))
        doc=patch['documento']; partes={'raiz':doc[:9] if len(doc)==11 else doc[:8], 'filial':'0' if len(doc)==11 else doc[8:12], 'controle':doc[-2:]}
        for campo,parte in self.cfg.get('clonagem',{}).get('derivadas',{}).get('componentes',{}).items():
            defaults[campo]=partes[parte]
        return self._row('componentes',{'grupo':patch['grupo'],'documento':patch['documento'],'nome':patch['nome'],'tipo':vals['tipo_componente_pj'] if self._ref(i)['tipo']=='PJ' else vals['tipo_componente_pf']},defaults)

    def _delta(self, role):
        from delta.tables import DeltaTable
        return DeltaTable.forName(self.spark,self._table(role))

    def _replace_qsa(self, pred, rows):
        # DELETE scoped by titular + append; no table overwrite, no deduplication.
        # Two commits: a failure between them requires restoring the baseline.
        df=self.spark.createDataFrame(rows,self.schemas['qsa']) if rows else None
        self._delta('qsa').delete(pred)
        if df is not None:df.write.format('delta').mode('append').saveAsTable(self._table('qsa'))

    def _resp_root(self, patch):
        role='responsabilidade'
        return (self.F.col(self._col(role,'raiz')).cast('long')==int(patch['documento'][:8])) & (self.F.col(self._col(role,'filial')).cast('int')==1)

    def _resp_scope(self, patch):
        role='responsabilidade';vals=self.cfg['valores']
        # Source recovered joins the eight-digit CNPJ root as integer, filters filial=1.
        return self._resp_root(patch) & self._eq(role,'tipo',vals['tipo_responsabilidade_pj'])

    def _resp_latest(self, patch):
        r='responsabilidade';F=self.F
        keys=[self._col(r,k) for k in ('raiz','tipo','centro','carteira','operacao')]
        version=self._col(r,'versao')
        df=self._df(r).filter(self._resp_scope(patch))
        # Tied versions would make the recovered row_number nondeterministic.
        if df.groupBy(*keys,version).count().filter(F.col('count')>1).limit(1).count():raise ValueError('Responsabilidade com empate de versão: corrigir massa-base.')
        return df.withColumn('__grup_n',F.row_number().over(self.Window.partitionBy(*keys).orderBy(F.col(version).desc()))).filter(F.col('__grup_n')==1).drop('__grup_n')

    def _resp_active(self, patch):
        # The recovered join is by root and does not use ctpo_pssoa in the join.
        # Check all matching roots/filial, not just PJ, to detect unexpected collisions.
        r='responsabilidade';F=self.F;keys=[self._col(r,k) for k in ('raiz','tipo','centro','carteira','operacao')];v=self._col(r,'versao');a=self._col(r,'atualizacao')
        df=self._df(r).filter(self._resp_root(patch))
        if df.groupBy(*keys,v).count().filter(F.col('count')>1).limit(1).count():raise ValueError('Responsabilidade com empate de versão.')
        return bool(df.withColumn('__grup_n',F.row_number().over(self.Window.partitionBy(*keys).orderBy(F.col(v).desc()))).filter((F.col('__grup_n')==1)&(F.col(a)!='D')).limit(1).count())

    def _apply_resp(self, patch):
        r='responsabilidade';mode=patch['modo'];F=self.F
        if mode=='EXIGIR_ATIVA':
            a=self._col(r,'atualizacao')
            if not self._resp_latest(patch).filter(F.col(a)!='D').limit(1).count() or not self._resp_active(patch):raise ValueError('Operação ativa esperada ausente. Reconciliar massa de responsabilidade, não inventar contrato.')
        elif mode=='SEM_REGISTRO':
            self._delta(r).delete(self._resp_scope(patch))
        elif mode=='ULTIMA_VERSAO_D':
            latest=self._resp_latest(patch);v=self._col(r,'versao');a=self._col(r,'atualizacao')
            if not latest.limit(1).count():raise ValueError('B29 requer operação histórica existente.')
            if not self._resp_active(patch):raise ValueError('B29 requer responsabilidade ativa antes do encerramento lógico.')
            if type(self._dtype(r,v)).__name__ not in ('TimestampType','TimestampNTZType'):raise ValueError('B29: confirmar tipo timestamp da versão.')
            rows=[tuple((row[f.name]+timedelta(seconds=1) if f.name==v else self._value(r,a,'D') if f.name==a else row[f.name]) for f in self.schemas[r].fields) for row in latest.collect()]
            self.spark.createDataFrame(rows,self.schemas[r]).write.format('delta').mode('append').saveAsTable(self._table(r))
        else:raise ValueError(f'Responsabilidade sem operação física definida: {mode}')
        if self._resp_active(patch)!=patch['flag_esperada']:raise ValueError('Flag derivada de responsabilidade não corresponde à pré-condição.')

    def _cad_ops(self, p):
        # Explicit baseline condition for F01–F48 from catalog; not a new oracle.
        ops=copy.deepcopy(p['cadastro']);v=self.cfg['valores']
        if p.get('cadastro_padrao')=='VALIDO_ATIVO_MATRIZ_SE_PJ':
            for i in p['componentes']:
                x=self._ref(i);fields={'cindcd_cpf_valid':v['cpf_valido']} if x['tipo']=='PF' else {'cindcd_cnpj_valid':v['cnpj_valido'],'rsit_docto_recta':v['pj_ativa'],'rmtriz_flial_cnpj':v['pj_matriz']}
                ops.extend({'id':i,'documento':x['documento'],'campo':k,'valor':value} for k,value in fields.items())
        return ops

    def _check_manual(self, p):
        # Unsupported logical cases cannot be unlocked with an acknowledgement.
        if any(x['modo'] in ('INDEFINIDO','VENCIMENTO_A_CONFIRMAR') for x in p['responsabilidade']):
            raise ValueError('Cenário exige revisão do contrato/oráculo de responsabilidade; não há operação física segura definida.')
        if not p['bloqueios']:return
        confirmation=self.cfg.get('confirmacoes_cenarios',{}).get(p['id'],{})
        if not isinstance(confirmation,dict) or not str(confirmation.get('justificativa','')).strip():
            raise ValueError('Pendência de definição: '+' | '.join(p['bloqueios']))
        c=p['cenario']
        if c in ('B24','B25','B26'):
            if confirmation.get('tipo_grupo') not in (1,5,6):raise ValueError('Informe tipo_grupo confirmado (1,5,6).')
            p['tipo_grupo']=confirmation['tipo_grupo']
        if c in ('E29','B32','EX05'):
            dest=confirmation.get('grupo_destino_inclusao')
            if type(dest) is not int or dest not in {x['grupo_base'] for x in self._refs.values()} or dest==p['grupo']:
                raise ValueError('Informe grupo_destino_inclusao existente e distinto do GE de exclusão.')
            for a in p['acoes_mesmo_pedido']:
                if a['inclusao']:a['grupo_destino_inclusao']=dest
        if c in ('B20','B33','B34'):
            if confirmation.get('grupos_secundarios')!=p['grupos_secundarios']:
                raise ValueError('Confirme explicitamente a lista de GEs secundários inferida; divergência exige revisar catálogo.')
        # P03/P04/P05/C05/C13: justificativa deve confirmar os dados existentes.
        # P07/P15/P16: somente a massa de referência é preparada; injeção manual autorizada.

    def retomar_sequencia(self, etapa, anterior, evidencia):
        """Retoma controle de sessao apos validacao do estado persistido pelo Job."""
        p=plano(etapa)
        if p['passo'] <= 1 or p['restaurar_antes'] or anterior != f"E2E-{p['cenario']}-{p['passo']-1:02d}" or not evidencia.strip():
            raise PermissionError('Retomada exige passo anterior correspondente e evidencia de conclusao.')
        self._baseline()
        self._ultimo=anterior

    def preparar(self, cenario, passo=1, *, aplicar=False, sem_processamento_pendente=False, passo_anterior_concluido=False, plano_isolado=None, plano_lote=None):
        if plano_isolado is not None or self._refs != REFS:
            raise PermissionError('Clonagem de identidades desativada na v1.3.')
        p=plano(cenario,passo) if plano_lote is None else copy.deepcopy(plano_lote)
        if plano_lote is not None:
            from dados_rodadas import validar_plano
            validar_plano(p)
        if any(x['campo'] == 'remover_cadastro' for x in p['cadastro']):
            raise PermissionError('Não excluir cadastros dos 200 clientes; B06 bloqueado em E2E.')
        p['cadastro_efetivo']=self._cad_ops(p)
        if not aplicar:return p
        if not sem_processamento_pendente:raise PermissionError('Aguarde jobs, eventos e consumidores antes de alterar massa.')
        self._check_manual(p)
        if p['cenario']=='P14' and p['passo']==2:raise ValueError('P14: preparar somente passo 1 e enviar ambos os pedidos concorrentemente.')
        if p['passo']>1 and (not passo_anterior_concluido or self._ultimo!=f"E2E-{p['cenario']}-{p['passo']-1:02d}"):
            raise PermissionError('Confirme conclusão e evidência do passo anterior preparado nesta sessão; não restaurar a massa.')
        self._baseline()
        # Compile typed rows and check mapped fields before any writes, including RESTORE.
        cad=defaultdict(dict);remover=set()
        for x in p['cadastro_efetivo']:
            i=x['id'];role=self._ref(i)['tipo'].lower()
            if x['campo']=='remover_cadastro':remover.add(i)
            else:
                name,value=self._typed(role,x['campo'],x['valor'])
                if name in (self._col(role,'id'),self._col(role,'documento')):
                    raise PermissionError('Mapeamento físico tenta alterar identidade cadastral.')
                cad[i][name]=value
        qrows=[(q,self._qsa_rows(q)) for q in p['qsa']]
        links=[(x,self._link_row(x) if x['operacao']=='ADICIONAR' else None) for x in p['vinculos']]
        for x in p['responsabilidade']:
            self._resp_scope(x)
            if x['modo']=='ULTIMA_VERSAO_D' and type(self._dtype('responsabilidade',self._col('responsabilidade','versao'))).__name__ not in ('TimestampType','TimestampNTZType'):raise ValueError('B29 exige versão timestamp.')
        if p['restaurar_antes']:self.restaurar(confirmar=True,sem_processamento_pendente=True)
        self._ultimo=None
        # From this point failure may leave partial changes across tables; stop and restore explicitly.
        try:
            for i in set(cad)|remover:
                role,pred=self._cad_pred(i,self._ref(i)['documento'])
                if self._df(role).filter(pred).count()!=1:raise ValueError(f'Cadastro {i} não localizado de forma única.')
                if i in remover:self._delta(role).delete(pred)
                else:self._delta(role).update(condition=pred,set={k:self.F.lit(v).cast(self._dtype(role,k)) for k,v in cad[i].items()})
                if i in remover:
                    if self._df(role).filter(pred).count():raise ValueError(f'Cadastro {i} não removido.')
                else:
                    row=self._df(role).filter(pred).first()
                    if row is None or any(row[k]!=v for k,v in cad[i].items()):raise ValueError(f'Cadastro {i} não corresponde ao overlay.')
            for q,rows in qrows:
                # Empty QSA deletes only the titular; duplicates intentionally preserved.
                pred=self._doc_eq('qsa','titular',q['documento'])
                self._replace_qsa(pred,rows)
                df=self._df('qsa').filter(pred)
                expected=Counter(rows)
                if Counter(tuple(r[f.name] for f in self.schemas['qsa'].fields) for r in df.collect())!=expected:raise ValueError(f'QSA divergente: {q["titular"]}')
            for x,row in links:
                role='componentes';vals=self.cfg['valores'];tipo=vals['tipo_componente_pj'] if self._ref(x['id'])['tipo']=='PJ' else vals['tipo_componente_pf']
                pred=self._eq(role,'grupo',x['grupo'])&self._doc_eq(role,'documento',x['documento'])&self._eq(role,'tipo',tipo)
                n=self._df(role).filter(pred).count()
                if x['operacao']=='REMOVER':
                    if n!=1:raise ValueError('Vínculo a remover não é único.')
                    self._delta(role).delete(pred)
                    if self._df(role).filter(pred).count()!=0:raise ValueError('Vínculo não removido.')
                else:
                    if n:raise ValueError('Vínculo a adicionar já existe.')
                    if self._df('grupos').filter(self._eq('grupos','id',x['grupo'])).count()!=1:raise ValueError('Grupo alvo de vínculo inexistente.')
                    self.spark.createDataFrame([row],self.schemas[role]).write.format('delta').mode('append').saveAsTable(self._table(role))
                    if self._df(role).filter(pred).count()!=1:raise ValueError('Vínculo não inserido.')
            for x in p['responsabilidade']:self._apply_resp(x)
        except Exception as e:
            raise RuntimeError(f'Preparo {p["id"]} interrompido; NÃO enviar pedido. Estado pode estar parcialmente alterado. Isole e reconcilie o cenário; não restaure outras rodadas sem autorização.') from e
        self._ultimo=p['id']
        return {'id':p['id'],'ambiente':self.cfg['ambiente'],'preparo_aplicado':True,'versoes':{r:self._version(r) for r in ROLES},'solicitacao':{k:p.get(k) for k in ('acao','grupo','tipo_grupo','grupos_secundarios','grupo_dinamico','componentes','acoes_mesmo_pedido')},'esperado_motor':p['esperado_motor'],'avisos':p['avisos']+p['bloqueios'],'proximo':'Conferir pré-condições e enviar pelo Frontend. Não é resultado E2E.'}


def main():
    parser=argparse.ArgumentParser(description='Planejamento offline de alterações GRUP; nunca escreve em Spark.')
    sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('plano');p.add_argument('cenario');p.add_argument('--passo',type=int,default=1)
    r=sub.add_parser('rodada');r.add_argument('nome')
    args=parser.parse_args()
    print(json.dumps(plano(args.cenario,args.passo) if args.cmd=='plano' else rodada(args.nome),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
