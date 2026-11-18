"""Verificação da fixture QSA estática (sem Spark)."""
from collections import Counter, defaultdict
from decimal import Decimal
import unittest

from dados_quadro_societario import DADOS_QSA_OUTROS_PJ
from dados_componentes_ativos import DADOS_COMPONENTES_ATIVOS
from dados_nomes_pj import NOMES_PJ_POR_CCLUB

class TestQuadroSocietario(unittest.TestCase):
    def test_estrutura_e_percentuais(self):
        self.assertEqual(len(DADOS_QSA_OUTROS_PJ), 54)
        totals = defaultdict(lambda: Decimal("0.00"))
        owners = set()
        for cnpj, pct, indicador, nome, dtfim, cclub, socio, dtorigem in DADOS_QSA_OUTROS_PJ:
            self.assertEqual(indicador, 1)
            self.assertTrue(len(cnpj) == 14)
            self.assertIn(len(socio), (11, 14))
            self.assertEqual((cclub % 2 == 0), (len(socio) == 14))
            self.assertTrue(nome)
            self.assertGreater(pct, Decimal("0"))
            self.assertNotIn((cnpj,socio),owners)
            owners.add((cnpj,socio))
            totals[cnpj] += pct
            if len(socio)==14:
                self.assertEqual(nome, NOMES_PJ_POR_CCLUB[cclub])
        self.assertEqual(len(totals), 27)
        self.assertTrue(all(v == Decimal("100.00") for v in totals.values()))
    def test_requisitos_especificos(self):
        rows=DADOS_QSA_OUTROS_PJ
        pf_mei={105,107,111,113,115}
        self.assertTrue(pf_mei.issubset({r[5] for r in rows}))
        self.assertTrue({62,64,68}.issubset({r[5] for r in rows}))
        titulares=defaultdict(list)
        for r in rows: titulares[r[0]].append(r)
        self.assertTrue(any(len(itens)==3 and all(len(r[6])==11 and r[1]<Decimal("50") for r in itens) for itens in titulares.values()))
    def test_componentes_de_grupos_têm_qsa_ou_são_mei(self):
        member_docs={r[1] for r in DADOS_COMPONENTES_ATIVOS if r[3]=="J"}
        with_qsa={r[0] for r in DADOS_QSA_OUTROS_PJ}
        mei_docs={"39070293000119","47911744000121","93773779000169",
                  "31297282000164","82080682000154","60543423000180"}
        self.assertTrue(member_docs.issubset(with_qsa | mei_docs))
if __name__ == "__main__": unittest.main()
