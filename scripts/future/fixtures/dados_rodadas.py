"""Identidades deterministicas e planos de rodadas; sem Spark ou escrita."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digito(s, pesos):
    r = sum(int(c) * p for c, p in zip(s, pesos)) % 11
    return str(0 if r < 2 else 11 - r)


def documento(slot, cliente, tipo, filial='0001'):
    if not 101 <= slot <= 999 or not 0 < cliente < 1000:
        raise ValueError('Slot ou cliente fora da faixa reservada.')
    if tipo == 'PF':
        s = str(720000000 + slot * 1000 + cliente)
        s += digito(s, range(10, 1, -1))
        return s + digito(s, range(11, 1, -1))
    if tipo != 'PJ' or len(filial) != 4 or not filial.isdigit():
        raise ValueError('Tipo ou filial invalido.')
    s = str(83000000 + slot * 1000 + cliente) + filial
    s += digito(s, [5,4,3,2,9,8,7,6,5,4,3,2])
    return s + digito(s, [6,5,4,3,2,9,8,7,6,5,4,3,2])


def id_cliente(slot, cliente):
    return 1000000 + slot * 1000 + cliente


def id_grupo(slot, grupo):
    if grupo is None or grupo == 9999999:
        return grupo
    tipo, ordem = divmod(grupo - 910000, 100)
    if tipo not in (1, 5, 6) or not 1 <= ordem <= 6:
        raise ValueError(f'GE base desconhecido: {grupo}')
    return 920000 + slot * 50 + (1, 5, 6).index(tipo) * 6 + ordem


def ler_rodada(rodada):
    if rodada not in {f'R{i:02d}' for i in range(1, 10)}:
        raise ValueError('Informe R01 a R09.')
    data = json.loads((ROOT / 'rodadas' / f'{rodada}.json').read_text(encoding='utf-8'))
    if data['rodada'] != rodada:
        raise ValueError('JSON de rodada incorreto.')
    return data


def remapear(plano, slot, refs):
    """Remapeia campos estruturados; textos historicos conservam IDs de origem."""
    p = copy.deepcopy(plano)
    def cliente(i): return refs[str(i)]['id']
    def ge(g): return id_grupo(slot, g)
    def pessoa(x):
        a = refs[str(x['id'])]
        x.update(id=a['id'], documento=a['documento'])
        if 'nome' in x: x['nome'] = a['nome']
    p['grupo'] = ge(p['grupo'])
    p['grupos_secundarios'] = [ge(g) for g in p['grupos_secundarios']]
    for k in ('componentes', 'vinculos_antes', 'vinculos_secundario_antes'):
        if p.get(k) is not None: p[k] = [cliente(i) for i in p[k]]
    for q in p['qsa']:
        a = refs[str(q['titular'])]
        q.update(titular=a['id'], documento=a['documento'])
        for s in q['socios']: pessoa(s)
    for k in ('cadastro', 'responsabilidade', 'acoes_mesmo_pedido', 'vinculos'):
        for x in p[k]:
            pessoa(x)
            if 'grupo' in x: x['grupo'] = ge(x['grupo'])
            if 'grupo_destino_inclusao' in x: x['grupo_destino_inclusao'] = ge(x['grupo_destino_inclusao'])
    p['restaurar_antes'] = False
    return p


def sementes(passos):
    ids, grupos = set(), set()
    for p in passos:
        for k in ('componentes','vinculos_antes','vinculos_secundario_antes'):
            ids.update(p.get(k) or [])
        grupos.update(g for g in [p['grupo'], *p['grupos_secundarios']] if g not in (None, 9999999))
        for q in p['qsa']:
            ids.add(q['titular']); ids.update(s['id'] for s in q['socios'])
        for k in ('cadastro','responsabilidade','vinculos','acoes_mesmo_pedido'):
            for x in p[k]:
                ids.add(x['id'])
                grupos.update(g for g in (x.get('grupo'), x.get('grupo_destino_inclusao')) if g not in (None,9999999))
    return ids, grupos


def fechamento(ids, grupos, vinculos, qsa):
    """Preserva grupos completos e relacoes societarias nos dois sentidos."""
    ids, grupos = set(ids), set(grupos)
    while True:
        antes = (len(ids), len(grupos))
        for g, i in vinculos:
            if g in grupos or i in ids: grupos.add(g); ids.add(i)
        for a, b in qsa:
            if a in ids or b in ids: ids.update((a,b))
        if antes == (len(ids),len(grupos)): return ids, grupos
