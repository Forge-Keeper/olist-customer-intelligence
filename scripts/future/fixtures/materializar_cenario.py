"""Materialização lógica, sem Spark e sem escrita, dos 217 casos do catálogo.

Uso:
  python scripts/future/fixtures/materializar_cenario.py I01
  python scripts/future/fixtures/materializar_cenario.py U01 --saida /tmp/U01.json

O formato é uma estrutura de preparação/oráculo; NÃO substitui o payload
MongoDB nem a definição física do contrato Delta, que dependem do ambiente.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from dados_grupos_ativos import DADOS_GRUPOS_ATIVOS
from dados_componentes_ativos import DADOS_COMPONENTES_ATIVOS
from dados_quadro_societario import DADOS_QSA_OUTROS_PJ
from dados_nomes_pj import NOMES_PJ_POR_CCLUB
from dados_responsabilidade import DADOS_RESPONSABILIDADE
from dados_pf_cenarios import DADOS_PF_CENARIOS

ROOT = Path(__file__).resolve().parent
CATALOGO = ROOT / "docs" / "catalogo_total.json"
PJS_ADICIONAIS = {
    112: "20010176000131",
    118: "52592529000145",
    120: "45639543000191",
}

def catalogo():
    return json.loads(CATALOGO.read_text(encoding="utf-8"))

def montar_referencias():
    docs_por_id = dict(PJS_ADICIONAIS)
    docs_por_id.update((int(i), doc) for i, doc, _ in DADOS_PF_CENARIOS)
    grupos = {int(r[0]): {"tipo": int(r[1]), "componentes": []}
              for r in DADOS_GRUPOS_ATIVOS}
    nomes_para_id = {nome: club for club, nome in NOMES_PJ_POR_CCLUB.items()}
    gids = sorted(grupos)
    for ge, documento, nome, natureza in DADOS_COMPONENTES_ATIVOS:
        if natureza == "J":
            club = nomes_para_id[nome]
        else:
            club = 101 + 2 * gids.index(int(ge))
        existente = docs_por_id.get(club)
        if existente is not None and existente != documento:
            raise ValueError(f"Documento de cliente {club} divergente")
        docs_por_id[club] = documento
        grupos[int(ge)]["componentes"].append(club)
    qsa = defaultdict(list)
    for cnpj, pct, indicador, nome, fim, socio_id, socio_doc, origem in DADOS_QSA_OUTROS_PJ:
        existente = docs_por_id.get(socio_id)
        if existente is not None and existente != socio_doc:
            raise ValueError(f"QSA do sócio {socio_id} diverge do cadastral")
        docs_por_id[socio_id] = socio_doc
        qsa[cnpj].append({"socio": socio_id, "documento_socio": socio_doc,
                          "percentual": str(pct), "indicador": indicador})
    resp = [{"tipo": tipo, "cclub_cli": club, "noper_cli": oper,
             "inicio": inicio, "fim": fim, "situacao": situacao}
            for tipo, club, oper, inicio, fim, situacao in DADOS_RESPONSABILIDADE]
    return docs_por_id, grupos, dict(qsa), resp

def materializar(caso_id):
    ids = {c["id"]: c for c in catalogo()["casos"]}
    if caso_id not in ids:
        raise KeyError(f"Caso desconhecido: {caso_id}")
    caso = ids[caso_id]
    docs, grupos, qsa, resp = montar_referencias()
    grupos = {k: {"tipo": v["tipo"], "componentes": list(v["componentes"])}
              for k, v in grupos.items()}
    qsa = {k: [dict(x) for x in rows] for k, rows in qsa.items()}
    preparo = caso.get("preparo") or {}
    avisos = []

    ge = caso.get("grupo_alvo")
    if ge is not None and ge in grupos:
        add = caso.get("componentes_preparo_add") or []
        rem = caso.get("componentes_preparo_rem") or []
        grupos[ge]["componentes"] = sorted(set(
            [c for c in grupos[ge]["componentes"] if c not in rem] + add
        ))
    secundario = caso.get("grupo_secundario")
    if secundario is not None and secundario in grupos:
        rem = preparo.get("componentes_secundario_rem") or []
        add = preparo.get("componentes_secundario_add") or []
        grupos[secundario]["componentes"] = sorted(set(
            [c for c in grupos[secundario]["componentes"] if c not in rem] + add
        ))

    patch_qsa = preparo.get("qsa_substituir") or []
    for patch in patch_qsa:
        titular_id = patch["titular"]
        titular_doc = docs.get(titular_id)
        if titular_doc is None:
            raise ValueError(f"Documento do titular PJ {titular_id} indisponível")
        novas = []
        for socio_id, pct in patch["socios"]:
            socio_doc = docs.get(socio_id)
            if socio_doc is None:
                raise ValueError(f"Documento do sócio {socio_id} indisponível")
            novas.append({"socio": socio_id, "documento_socio": socio_doc,
                          "percentual": str(pct), "indicador": 1})
        qsa[titular_doc] = novas

    if isinstance(caso.get("preparo_qsa"), str) and caso["preparo_qsa"]:
        avisos.append("preparo_qsa de borda é descritivo: confirmar override manual")
    if isinstance(caso.get("preparo_cadastro"), str) and caso["preparo_cadastro"]:
        avisos.append("preparo_cadastro de borda é descritivo: confirmar flags manualmente")
    if caso.get("classe") in ("INTEGRACAO", "SEQUENCIA"):
        avisos.append("Passos sequenciais dependem da execução real anterior; não calcular estado intermediário fictício")
    if ge is None and caso.get("codigo_acao") == 1:
        avisos.append("GE é criado pelo motor; não existe código fixo anterior")
    if caso.get("resultado_esperado") in ("CONDICIONAL", "PENDENTE"):
        avisos.append("Oráculo funcional não homologado")
    if caso.get("resultado_esperado") in ("PENDENTE_CONTRATO_DE_SEQUENCIA", "A_DEFINIR_ORACULO_DE_INTEGRACAO"):
        avisos.append("Oráculo de integração exige contrato e evidência E2E")

    solicitados = caso.get("componentes_solicitados", caso.get("componentes_involvidos", []))
    req = [{"cclub_cli": club, "tipo": "PF" if club % 2 else "PJ",
            "documento": docs.get(club)} for club in solicitados]
    if any(x["documento"] is None for x in req):
        avisos.append("Existe componente sem documento resolvido na base de referência")
    flags = preparo.get("cadastro_override") or []
    return {
        "id_cenario": caso_id,
        "acao": caso.get("codigo_acao", caso.get("acao")),
        "solicitacao_esqueleto": {
            "cAcaoGrpEconm": caso.get("codigo_acao", caso.get("acao")),
            "cGrpEconm": caso.get("grupo_alvo", caso.get("grupo_primario")),
            "componentes": req,
            "passos": caso.get("passos", []),
        },
        "snapshot": {
            "grupos_ativos": grupos,
            "qsa_nao_mei": qsa,
            "responsabilidade": resp,
            "cadastro_override": flags,
            "preparo": preparo,
        },
        "tabela_verdade": {
            "regra": caso.get("regra_alvo"),
            "resultado_esperado": caso.get("resultado_esperado"),
            "componentes_finais": caso.get("componentes_finais_esperados"),
            "efeito_esperado": caso.get("efeito_esperado", caso.get("evento_esperado", caso.get("evento_grupo_esperado"))),
        },
        "avisos": avisos,
        "observacao": caso.get("observacao", caso.get("descricao", "")),
    }

def main():
    parser = argparse.ArgumentParser(description="Materializa um caso sintético sem escrever em tabelas")
    parser.add_argument("caso_id", help="Identificador do caso, por exemplo I01")
    parser.add_argument("--saida", help="Caminho de arquivo JSON, opcional")
    args = parser.parse_args()
    result = json.dumps(materializar(args.caso_id), ensure_ascii=False, indent=2)
    if args.saida:
        Path(args.saida).write_text(result + "\n", encoding="utf-8")
    else:
        print(result)

if __name__ == "__main__":
    main()
