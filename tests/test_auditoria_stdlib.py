"""Pruebas de utilidades de auditoría sin acceso a datos reales."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location("auditoria_local", Path(__file__).resolve().parents[1] / "scripts" / "auditoria_local.py")
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


class AuditoriaTest(unittest.TestCase):
    def test_columnas_excel(self):
        self.assertEqual(modulo.indice_columna("A1"), 0)
        self.assertEqual(modulo.indice_columna("AA7"), 26)

    def test_filtrado_identificadores(self):
        fila = ET.fromstring(f'<row xmlns="{modulo.M[1:-1]}"><c r="A2"><v>123456789</v></c><c r="B2"><v>40</v></c></row>')
        self.assertEqual(list(modulo.valores_fila(fila, {1: "edad"})), [(1, "n", "40")])

    def test_cuantiles(self):
        self.assertEqual(modulo.cuantiles([4, 1, 3, 2]), [1.75, 2.5, 3.25])

    def test_universo_y_confirmaciones(self):
        kwargs = dict(unidad_confirmada=True, sin_duplicados_confirmado=True, retiro_confirmado=True)
        modulo.validar_universo(95011, 95011, **kwargs)
        with self.assertRaises(ValueError):
            modulo.validar_universo(95010, 95010, **kwargs)
        with self.assertRaises(ValueError):
            modulo.validar_universo(95011, 95010, **kwargs)
        for nombre in kwargs:
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                modulo.validar_universo(95011, 95011, **(kwargs | {nombre: False}))


if __name__ == "__main__":
    unittest.main()
