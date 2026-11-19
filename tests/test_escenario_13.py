"""Pruebas sintéticas del escenario provisional y de supresión."""
import importlib.util
from pathlib import Path
import sys
import unittest

raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz / 'scripts'))
spec = importlib.util.spec_from_file_location('escenario_13', raiz / 'scripts' / 'escenario_13.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SeleccionTest(unittest.TestCase):
    def test_limites(self):
        for c, grupo in [(0,'A'), (99,'A'), (100,'B'), (129,'B'), (130,'fuera')]:
            self.assertEqual(mod.clasificar(c,100,130), grupo)

    def test_invalidos(self):
        for valores in [(None,1,2),(-1,1,2),(1,float('nan'),2),(1,3,2),(1,1,float('inf'))]:
            self.assertEqual(mod.clasificar(*valores), 'no evaluable')

    def test_supresion(self):
        self.assertTrue(mod.publicable([0, 10, 25], 10))
        self.assertFalse(mod.publicable([1, 10, 25], 10))

    def test_percentiles(self):
        self.assertEqual(mod.percentil([4,1,2,3], .5), 2.5)

    def test_grafico_brecha_negativa_con_eje_cero(self):
        grafico = mod.figura('Brecha', [('negativa', -10, '#0033A0'), ('positiva', 10, '#0033A0')])
        self.assertIn('x="230.00"', grafico)
        self.assertIn('x="440.00"', grafico)
        self.assertIn('stroke="#0033A0"', grafico)


if __name__ == '__main__': unittest.main()
