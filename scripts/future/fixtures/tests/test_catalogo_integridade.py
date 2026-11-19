"""Validação offline das fixtures e dos 217 cenários documentados.

Executar: python -m unittest discover -s scripts/future/fixtures/tests -v
Não usa Spark nem acessa tabela/serviço externo.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

FIXTURES = Path(__file__).resolve().parents[1]
DOCS = FIXTURES / "docs"
sys.path.insert(0, str(FIXTURES))

from dados_grupos_ativos import DADOS_GRUPOS_ATIVOS
from dados_componentes_ativos import DADOS_COMPONENTES_ATIVOS
from dados_quadro_societario import DADOS_QSA_OUTROS_PJ
from dados_responsabilidade import DADOS_RESPONSABILIDADE
from dados_pf_cenarios import DADOS_PF_CENARIOS

EXPECTED = {"F":48, "I":18, "E":30, "U":21, "C":16, "P":18, "B":36,
            "FX":14, "UX":9, "EX":5, "IX":2}

def carregar():
    with (DOCS / "catalogo_total.json").open(encoding="utf-8") as stream:
        return json.load(stream)

def prefixo(case_id):
    return next((x for x in ("FX","UX","EX","IX") if case_id.startswith(x)), case_id[0])

class TestMassaSintetica(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalogo = carregar()
        cls.casos = cls.catalogo["casos"]
        cls.ge_types = {r[0]: r[1] for r in DADOS_GRUPOS_ATIVOS}
        cls.ge_docs = defaultdict(list)
        for row in DADOS_COMPONENTES_ATIVOS:
            cls.ge_docs[row[0]].append(row)

    def test_cardinalidades_e_identificadores(self):
        self.assertEqual(len(DADOS_GRUPOS_ATIVOS), 18)
        self.assertEqual(len(DADOS_COMPONENTES_ATIVOS), 48)
        self.assertEqual(Counter(r[1] for r in DADOS_GRUPOS_ATIVOS), {1:6, 5:6, 6:6})
        self.assertEqual(Counter(r[3] for r in DADOS_COMPONENTES_ATIVOS), {"J":30, "F":18})
        self.assertEqual(len({r[1] for r in DADOS_COMPONENTES_ATIVOS}), 48)

    def test_qsa_integridade_e_majoritario_isolados(self):
        self.assertEqual(len(DADOS_QSA_OUTROS_PJ), 54)
        totals = defaultdict(lambda: Decimal("0.00"))
        per_titular = defaultdict(list)
        for row in DADOS_QSA_OUTROS_PJ:
            cnpj, pct, indicador, nome, fim, cclub, socio, origem = row
            self.assertEqual(indicador, 1)
            self.assertEqual(len(cnpj), 14)
            self.assertIn(len(socio), (11,14))
            self.assertEqual((cclub % 2 == 0), len(socio) == 14)
            self.assertGreater(pct, 0)
            totals[cnpj] += pct
            per_titular[cnpj].append((socio, pct))
        self.assertEqual(len(totals), 27)
        self.assertTrue(all(x == Decimal("100.00") for x in totals.values()))
        for ge, tipo in self.ge_types.items():
            if tipo != 5:
                continue
            pj = next(r[1] for r in self.ge_docs[ge] if r[3] == "J")
            pf = next(r[1] for r in self.ge_docs[ge] if r[3] == "F")
            self.assertTrue(
                any(socio == pf and pct >= 50 for socio, pct in per_titular[pj]),
                f"PF ativa do isolado {ge} precisa ser majoritaria na PJ"
            )

    def test_responsabilidade_70_clientes_unicos(self):
        rows = DADOS_RESPONSABILIDADE
        self.assertEqual(len(rows), 70)
        self.assertEqual(Counter(r[0] for r in rows), {"PF":40, "PJ":30})
        self.assertEqual(len({(r[0], r[1]) for r in rows}), 70)
        self.assertEqual(len({r[2] for r in rows}), 70)
        for tipo, club, oper, inicio, fim, situacao in rows:
            self.assertEqual(club % 2, 1 if tipo == "PF" else 0)
            self.assertLess(date.fromisoformat(inicio), date(2025,1,1))
            self.assertEqual(fim, "2027-11-19")
            self.assertEqual(situacao, "ABERTO")
            self.assertTrue(oper.isdigit())

    def test_pf_reservadas_dentro_da_faixa_e_documentos_validos(self):
        rows = DADOS_PF_CENARIOS
        self.assertEqual(len(rows), 10)
        self.assertEqual({r[0] for r in rows}, set(range(281,300,2)))
        docs = [r[1] for r in rows]
        self.assertEqual(len(set(docs)), 10)
        self.assertTrue(all(len(d) == 11 and d.isdigit() for d in docs))

    def test_catalogo_completo(self):
        self.assertEqual(self.catalogo["total"], 217)
        self.assertEqual(len(self.casos), 217)
        ids = [c["id"] for c in self.casos]
        self.assertEqual(len(set(ids)), 217)
        self.assertEqual(Counter(prefixo(cid) for cid in ids), EXPECTED)
        self.assertEqual({c["id"] for c in self.casos if c["id"].startswith("I") and c["id"][1:].isdigit()},
                         {"I"+str(x).zfill(2) for x in range(1,19)})

    def test_referencias_grupos_e_documentos(self):
        ge_validos = set(self.ge_types)
        for c in self.casos:
            ge = c.get("grupo_alvo", c.get("grupo_primario", c.get("grupo_base")))
            if ge is not None and ge != 9999999:
                self.assertIn(ge, ge_validos, c["id"])
            for key in ("grupo_secundario",):
                outro = c.get(key)
                if outro is not None:
                    self.assertIn(outro, ge_validos, c["id"])
            for d in c.get("documentos_solicitados", []):
                self.assertEqual(len(d["documento"]), 11 if d["tipo"]=="PF" else 14,
                                 c["id"])
                self.assertEqual(d["cclub_cli"] % 2, 1 if d["tipo"]=="PF" else 0)

    def test_formalizacao_tres_tipos_quatro_por_quatro(self):
        form = [c for c in self.casos if re.fullmatch(r"F\d{2}", c["id"])]
        matrix = set()
        for c in form:
            tipo = c["tipo_grupo_solicitado"]
            ids = c["componentes_solicitados"]
            qpj = sum(id % 2 == 0 for id in ids)
            qpf = sum(id % 2 != 0 for id in ids)
            matrix.add((tipo,qpj,qpf))
            approved = (tipo == 5 and qpj == 1 and 1 <= qpf <= 2) or (
                tipo == 1 and qpj >= 2 and 1 <= qpf <= 2
            )
            self.assertEqual(c["resultado_esperado"], "APROVA" if approved else "RECUSA",
                             c["id"])
        self.assertEqual(len(matrix), 48)

    def test_inclusao_livres_e_recusas_dedicadas(self):
        cases = {c["id"]:c for c in self.casos}
        member_docs = {r[1] for r in DADOS_COMPONENTES_ATIVOS}
        for id in ("I01","I02","I03","I04","I05","I06","I10","I11","I12",
                   "I13","I14","I15","I16","I17","I18"):
            c = cases[id]
            self.assertTrue(all(d["documento"] not in member_docs
                                for d in c["documentos_solicitados"]), id)
        self.assertEqual(cases["I07"]["grupo_alvo"], 910101)
        self.assertEqual(cases["I07"]["componentes_solicitados"], [62])
        self.assertEqual(cases["I08"]["grupo_alvo"], 910102)
        self.assertEqual(cases["I08"]["componentes_solicitados"], [64])
        self.assertEqual(cases["I18"]["componentes_solicitados"], [112,112])

    def test_exclusao_componentes_existentes_salvo_negativas(self):
        for c in self.casos:
            if not re.fullmatch(r"E\d{2}",c["id"]):
                continue
            if c["id"] in ("E21","E22"):
                continue
            inicial = c["componentes_iniciais"]
            for x in c["componentes_solicitados"]:
                self.assertIn(x, inicial, c["id"])

    def test_overlay_qsa_positivo_total_100(self):
        for c in self.casos:
            if c.get("resultado_esperado") != "APROVA":
                continue
            qsa = c.get("preparo",{}).get("qsa_substituir",[])
            for titular in qsa:
                self.assertEqual(round(sum(float(s[1]) for s in titular["socios"]),2),100.0,
                                 c["id"])

    def test_matriz_md_corresponde_ao_json(self):
        texto=(DOCS/"MATRIZ_DETALHADA.md").read_text(encoding="utf-8")
        linhas=[line for line in texto.splitlines() if re.match(
            r"^\|\s*(?:F\d{2}|I\d{2}|E\d{2}|U\d{2}|C\d{2}|P\d{2}|"
            r"B\d{2}|FX\d{2}|UX\d{2}|EX\d{2}|IX\d{2})\s*\|", line)]
        self.assertEqual(len(linhas),217)

if __name__=="__main__":
    unittest.main()
