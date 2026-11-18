"""Verificações de integridade das fixtures estáticas, sem acesso ao Databricks."""
import unittest
from collections import Counter
from dados_nomes_pj import NOMES_PJ_POR_CCLUB
from dados_grupos_ativos import DADOS_GRUPOS_ATIVOS
from dados_componentes_ativos import DADOS_COMPONENTES_ATIVOS

class TestStaticFixtures(unittest.TestCase):
    def test_names(self):
        self.assertEqual(set(NOMES_PJ_POR_CCLUB),set(range(62,261,2)))
        self.assertEqual(len(set(NOMES_PJ_POR_CCLUB.values())),100)
    def test_groups(self):
        self.assertEqual(Counter(r[1] for r in DADOS_GRUPOS_ATIVOS),{1:6,5:6,6:6})
        self.assertEqual(len(set(r[0] for r in DADOS_GRUPOS_ATIVOS)),18)
    def test_components(self):
        self.assertEqual(Counter(r[3] for r in DADOS_COMPONENTES_ATIVOS),{'J':30,'F':18})
        self.assertEqual(len(set(r[1] for r in DADOS_COMPONENTES_ATIVOS)),48)
        types={r[0]:r[1] for r in DADOS_GRUPOS_ATIVOS}
        self.assertEqual(set(types),{r[0] for r in DADOS_COMPONENTES_ATIVOS})
        for gid,t in types.items():
            self.assertEqual(Counter(r[3] for r in DADOS_COMPONENTES_ATIVOS if r[0]==gid),{'J':1 if t==5 else 2,'F':1})

if __name__=='__main__':unittest.main()
