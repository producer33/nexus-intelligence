import unittest, sys, os, tempfile, json
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nexus import quant, sources, auditor, build

class Quant(unittest.TestCase):
    def test_retornos(self):
        for a, b in zip(quant.retornos([100, 110, 99]), [0.10, -0.10]):
            self.assertAlmostEqual(a, b)
    def test_acumulado(self):
        self.assertAlmostEqual(quant.retorno_acumulado([100, 150]), 0.5)
    def test_drawdown(self):
        self.assertAlmostEqual(quant.max_drawdown([100, 200, 100, 150]), -0.5)
    def test_vol_zero(self):
        self.assertEqual(quant.volatilidade_anual([0.01, 0.01, 0.01]), 0.0)
    def test_corr(self):
        self.assertAlmostEqual(quant.correlacao([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertIsNone(quant.correlacao([1, 1, 1], [1, 2, 3]))
    def test_var_poucos_dados(self):
        self.assertIsNone(quant.var_historico([0.01] * 5))

class Fontes(unittest.TestCase):
    def test_bcb(self):
        self.assertEqual(sources.parse_bcb([{"data": "02/01/2026", "valor": "15.00"}]), [["2026-01-02", 15.0]])
    def test_yahoo_ignora_nulos(self):
        raw = {"chart": {"result": [{"timestamp": [1767312000, 1767398400],
               "indicators": {"quote": [{"close": [10.0, None]}]}}]}}
        self.assertEqual(len(sources.parse_yahoo(raw)), 1)
    def test_coingecko(self):
        self.assertEqual(sources.parse_coingecko({"prices": [[1767312000000, 90000.5]]})[0][1], 90000.5)
    def test_erro_nao_inventa_dados(self):
        def falha(url): raise OSError("sem rede")
        r = sources.coletar(sources.CATALOGO[0], falha)
        self.assertEqual((r["status"], r["pontos"]), ("erro", []))
    def test_dedup_e_ordem(self):
        f = lambda u: [{"data": "03/01/2026", "valor": "2"}, {"data": "02/01/2026", "valor": "1"}, {"data": "03/01/2026", "valor": "3"}]
        self.assertEqual(sources.coletar(sources.CATALOGO[0], f)["pontos"], [["2026-01-02", 1.0], ["2026-01-03", 3.0]])

class Auditor(unittest.TestCase):
    def test_desatualizado(self):
        s = {"id": "ibov", "status": "ok", "referencia": "2026-01-01", "pontos": [["x", 1.0]] * 40}
        self.assertTrue(any(a[0] == "Moderado" for a in auditor.auditar(s, date(2026, 2, 1))))
    def test_sem_dados_e_alto(self):
        self.assertEqual(auditor.auditar({"status": "erro", "erro": "x"})[0][0], "Alto")

class Pipeline(unittest.TestCase):
    def test_falha_mantem_ultimo_dado_valido_marcado(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, "data.json")
        ok = lambda u: [{"data": "02/01/2026", "valor": "1"}, {"data": "05/01/2026", "valor": "2"}] if "bcdata" in u else (_ for _ in ()).throw(OSError("x"))
        build.main(ok, out)
        def falha(u): raise OSError("fora do ar")
        build.main(falha, out)
        ser = {s["id"]: s for s in json.load(open(out))["series"]}
        self.assertEqual(ser["selic_meta"]["status"], "desatualizado")
        self.assertEqual(ser["selic_meta"]["pontos"][-1][1], 2.0)
        self.assertEqual(ser["ibov"]["status"], "erro")

if __name__ == "__main__":
    unittest.main()
