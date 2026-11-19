"""Verificação do materializador lógico dos casos."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from materializar_cenario import materializar

class TestMaterializador(unittest.TestCase):
    def test_todos_os_casos_geram_snapshot_logico(self):
        from materializar_cenario import catalogo
        for caso in catalogo()["casos"]:
            with self.subTest(id=caso["id"]):
                out = materializar(caso["id"])
                self.assertEqual(out["id_cenario"], caso["id"])
                self.assertIn("tabela_verdade", out)
                self.assertIn("snapshot", out)

    def test_decisoes_binarias_materializadas(self):
        for id in ("I03", "I18", "E30", "U10", "C06", "P14", "B35"):
            with self.subTest(id=id):
                caso = materializar(id)
                verdade = caso["tabela_verdade"]
                self.assertIn(verdade["resultado_esperado"], {"APROVADO","REPROVADO"})
                for componente in verdade["decisoes_por_componente"]:
                    self.assertIn(componente["resultado_esperado"], {"APROVADO","REPROVADO"})
                for etapa in verdade["resultados_por_passo"]:
                    self.assertIn(etapa["resultado_esperado"], {"APROVADO","REPROVADO"})

    def test_inclusao_positiva(self):
        item = materializar("I01")
        self.assertEqual(item["solicitacao_esqueleto"]["cGrpEconm"], 910101)
        self.assertEqual(item["solicitacao_esqueleto"]["componentes"][0]["cclub_cli"], 112)
        self.assertEqual(item["tabela_verdade"]["resultado_esperado"], "APROVADO")

    def test_regras_qsa_de_inclusao(self):
        item = materializar("I02")
        doc = "75538340000108"
        socios = item["snapshot"]["qsa_nao_mei"][doc]
        self.assertEqual(sum(float(s["percentual"]) for s in socios), 100.0)
        self.assertIn("73002900354", [s["documento_socio"] for s in socios])

    def test_unificacao_nao_repete_mei(self):
        item = materializar("U01")
        secundario = item["snapshot"]["grupos_ativos"][910102]["componentes"]
        self.assertNotIn(68, secundario)
        self.assertIn(112, secundario)
        self.assertEqual(len(secundario), 3)

    def test_exclusao_responsabilidade(self):
        item = materializar("E27")
        flags = item["snapshot"]["cadastro_override"]
        self.assertTrue(flags[0]["flag_resp_empr"])
        self.assertEqual(item["tabela_verdade"]["resultado_esperado"], "REPROVADO")

    def test_formalizacao_sem_grupo_existente(self):
        item = materializar("F22")
        self.assertIsNone(item["solicitacao_esqueleto"]["cGrpEconm"])
        self.assertEqual(item["tabela_verdade"]["resultado_esperado"], "APROVADO")

if __name__=="__main__":
    unittest.main()
