"""Plano offline com identidades originais; particionamento determinístico de lotes."""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import json

from preparo_massas.preparar_massa import REFS

ROOT = Path(__file__).resolve().parent
REFERENCIAS = {int(k): v for k, v in REFS.items()}
IDS_PF = frozenset(range(101, 300, 2))
IDS_PJ = frozenset(range(62, 261, 2))
# 54 vínculos da fixture dados_quadro_societario.py; MEI e outros vínculos
# são conferidos no baseline físico antes de qualquer escrita.
QSA_BASE = ((66,105),(66,107),(66,111),(72,113),(72,115),(82,62),(82,105),
 (84,64),(84,107),(88,68),(90,62),(90,113),(92,115),(92,68),(94,117),
 (94,115),(96,119),(96,64),(96,105),(102,123),(102,107),(104,105),
 (104,111),(106,68),(106,113),(108,115),(108,105),(108,107),(110,62),
 (110,68),(112,64),(114,111),(116,68),(116,64),(118,115),(118,113),
 (120,62),(120,105),(120,113),(74,117),(74,119),(98,62),(98,121),
 (122,123),(124,117),(124,119),(124,121),(126,68),(126,123),
 (128,62),(128,64),(130,119),(132,117),(132,121))
GRUPOS_BASE = defaultdict(set)
for i, r in REFERENCIAS.items():
    if r['grupo_base'] is not None:
        GRUPOS_BASE[r['grupo_base']].add(i)


def ler_rodada(rodada):
    if rodada not in {f'R{i:02d}' for i in range(1, 10)}:
        raise ValueError('Informe R01 a R09.')
    dados = json.loads((ROOT / 'rodadas' / f'{rodada}.json').read_text(encoding='utf-8'))
    if dados.get('rodada') != rodada or dados.get('versao') != '1.3':
        raise ValueError('JSON de rodada incompatível; utilizar exclusivamente v1.3.')
    return dados


def ids_e_grupos(caso):
    ids, grupos = set(), set()
    for p in caso['passos']:
        for k in ('componentes', 'vinculos_antes', 'vinculos_secundario_antes'):
            ids.update(p.get(k) or [])
        grupos.update(g for g in [p['grupo'], *p['grupos_secundarios']] if g is not None)
        for q in p['qsa']:
            ids.add(q['titular']); ids.update(s['id'] for s in q['socios'])
        for k in ('cadastro', 'responsabilidade', 'vinculos', 'acoes_mesmo_pedido'):
            for x in p[k]:
                ids.add(x['id'])
                grupos.update(g for g in (x.get('grupo'), x.get('grupo_destino_inclusao')) if g is not None)
    if not ids <= REFERENCIAS.keys():
        raise ValueError('Cliente sem documento de referência confirmado.')
    grupos.update(REFERENCIAS[i]['grupo_base'] for i in ids if REFERENCIAS[i]['grupo_base'] is not None)
    ids.update(i for g in grupos for i in GRUPOS_BASE[g])
    return ids, grupos


def escopo(caso, qsa_base=QSA_BASE, documentos=None):
    """Escopo conservador: GE completo, clientes e dependências QSA diretas.
    Dependências somente de leitura podem coexistir quando o preparo coincide.
    """
    ids, grupos = ids_e_grupos(caso)
    mutaveis = {('cliente', i) for i in ids} | {('ge', g) for g in grupos}
    dependencias = {j for a,b in qsa_base for i,j in ((a,b),(b,a)) if i in ids}
    leitura = mutaveis | {('cliente', i) for i in dependencias}
    docs = documentos or {i:r['documento'] for i,r in REFERENCIAS.items()}
    # O enriquecimento de responsabilidade faz join pela raiz, sem tipo.
    for i in ids:
        if i in docs:
            k = ('raiz_resp', int(docs[i][:8]))
            leitura.add(k); mutaveis.add(k)
    return leitura, mutaveis


def chave_json(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def assinatura(caso, qsa_base=QSA_BASE):
    """Representa a primeira preparação por recurso, inclusive sócios removidos.
    Ausência de alteração é diferente de um overlay explícito (mesmo se redundante).
    """
    p = caso['passos'][0]
    out = defaultdict(set)
    for q in p['qsa']:
        sig = ('qsa', chave_json(q))
        out['cliente', q['titular']].add(sig)
        socios = {s['id'] for s in q['socios']} | {b for a,b in qsa_base if a == q['titular']}
        for i in socios: out['cliente', i].add(sig)
    for k in ('cadastro', 'responsabilidade', 'vinculos'):
        for x in p[k]:
            sig = (k, chave_json(x))
            out['cliente', x['id']].add(sig)
            if 'grupo' in x: out['ge', x['grupo']].add(sig)
            if k == 'responsabilidade': out['raiz_resp', int(x['documento'][:8])].add(sig)
    if p.get('cadastro_padrao'):
        for i in p['componentes']: out['cliente', i].add(('cadastro_padrao', p['cadastro_padrao']))
    return {k:frozenset(v) for k,v in out.items()}


def recusa_simples(caso):
    p = caso['passos'][0]
    return (len(caso['passos']) == 1 and p['esperado_motor'] == 'REPROVADO'
            and caso['cenario'] not in {'E30','U10','U18','U20'}
            and not caso['cenario'].startswith(('P','C')))


def conflito(a, b, qsa_base=QSA_BASE, documentos=None):
    if a['cenario'].startswith('P') or b['cenario'].startswith('P'):
        return True  # Ensaios técnicos podem ter efeitos globais ou concorrência intencional.
    ra, ma = escopo(a, qsa_base, documentos)
    rb, mb = escopo(b, qsa_base, documentos)
    comuns = ra & rb
    if not comuns: return False
    sa, sb = assinatura(a,qsa_base), assinatura(b,qsa_base)
    if any(sa.get(k, frozenset()) != sb.get(k, frozenset()) for k in comuns): return True
    # Recusas simples são executadas primeiro, com prova de ausência de mudança.
    # Dois casos que podem alterar o mesmo escopo não compartilham lote.
    if recusa_simples(a) or recusa_simples(b): return False
    if len(a['passos']) > 1 or len(b['passos']) > 1: return True
    return bool((ma | mb) & comuns)


def verificacoes(casos, qsa_base=QSA_BASE, documentos=None):
    # Se há sobreposição, todas as recusas simples do lote são verificadas
    # ANTES dos casos mutantes. Não pressupõe que uma recusa real seja atômica.
    return [c['passos'][0]['id'] for c in casos if recusa_simples(c) and any(
        d is not c and escopo(c,qsa_base,documentos)[0] & escopo(d,qsa_base,documentos)[0]
        for d in casos)]


def planejar_lotes(casos):
    """Coloração gulosa determinística DSATUR; não promete mínimo global."""
    ativos = [c for c in casos if not c['passos'][0]['bloqueios']]
    por_id = {c['cenario']:c for c in ativos}
    adj = {k:set() for k in por_id}
    for a,b in combinations(ativos,2):
        if conflito(a,b):
            adj[a['cenario']].add(b['cenario']); adj[b['cenario']].add(a['cenario'])
    ordem = {c['cenario']:i for i,c in enumerate(casos)}
    cores = {}
    while len(cores) < len(ativos):
        x = max((k for k in por_id if k not in cores), key=lambda k:(
            len({cores[v] for v in adj[k] if v in cores}),len(adj[k]),-ordem[k]))
        proibidas={cores[v] for v in adj[x] if v in cores}
        cor=0
        while cor in proibidas: cor+=1
        cores[x]=cor
    lotes=[]
    for cor in sorted(set(cores.values())):
        cs=[por_id[k] for k in por_id if cores[k]==cor]
        checks=set(verificacoes(cs))
        cs.sort(key=lambda c:(c['passos'][0]['id'] not in checks, ordem[c['cenario']]))
        lotes.append(cs)
    # Priorizar o lote que contém o primeiro caso da rodada.
    lotes.sort(key=lambda cs:min(ordem[c['cenario']] for c in cs))
    return [{'lote':i+1,'casos':cs,'verificar_recusas':verificacoes(cs)} for i,cs in enumerate(lotes)]


def modo_passo(caso, p):
    if p['bloqueios']: return 'BLOQUEADO'
    if p['passo']==1: return 'PREPARO_LOTE'
    if p['cenario']=='P14': return 'CONCORRENTE_SEM_UPDATE'
    # Não repetir alteração já aplicada se os dados de origem são idênticos.
    anterior = caso['passos'][p['passo']-2]
    campos=('qsa','cadastro','responsabilidade','vinculos','cadastro_padrao')
    if not any(p.get(k) for k in campos): return 'SEM_UPDATE'
    if not p['vinculos'] and all(p.get(k)==anterior.get(k) for k in campos): return 'SEM_UPDATE'
    return 'UPDATE_INTERMEDIARIO'


def validar_plano(p):
    grupos=[p.get('grupo'),*p.get('grupos_secundarios',[])]
    grupos.extend(x.get('grupo') for x in p.get('vinculos',[]))
    grupos.extend(x.get('grupo_destino_inclusao') for x in p.get('acoes_mesmo_pedido',[]))
    if any(g is not None and g!=9999999 and g not in GRUPOS_BASE for g in grupos):
        raise ValueError('GE fora do catálogo original.')
    for i in p.get('componentes',[]):
        if i not in REFERENCIAS: raise ValueError('Cliente fora do catálogo original.')
    for k in ('cadastro','responsabilidade','vinculos','acoes_mesmo_pedido'):
        for x in p.get(k,[]):
            if REFERENCIAS[x['id']]['documento']!=x['documento']:
                raise ValueError('Documento divergente do catálogo original.')
            if k=='cadastro' and x['campo'] not in ('cindcd_cpf_valid','cindcd_cnpj_valid','rsit_docto_recta','rscit','rmtriz_flial_cnpj','rnatur_jurid'):
                raise PermissionError('Identidades cadastrais são imutáveis; não excluir PF/PJ.')
    for q in p.get('qsa',[]):
        if REFERENCIAS[q['titular']]['documento']!=q['documento']: raise ValueError('Titular divergente.')
        for s in q['socios']:
            if REFERENCIAS[s['id']]['documento']!=s['documento']: raise ValueError('Sócio divergente.')
