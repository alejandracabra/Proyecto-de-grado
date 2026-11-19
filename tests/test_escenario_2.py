"""Controles de límites y registros incoherentes con datos sintéticos."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from escenario_2 import C, K1, K13, K2, clasificar


def test_limites_transiciones_y_no_evaluables():
    d = pd.DataFrame({C: [99, 100, 129, 130, 199, 200, 100, np.nan],
                      K1: [100]*8, K13: [130]*8,
                      K2: [200, 200, 200, 200, 200, 200, 120, 200]})
    clasificar(d)
    assert d.grupo.tolist() == ['A', 'B', 'B', 'B', 'B', 'fuera', 'no evaluable', 'no evaluable']
    assert d.seleccion_1.sum() == 1
    assert d.seleccion_13.sum() == 3
    assert d.seleccion_2.sum() == 5
    assert d.loc[6, K2] == 120
    assert pd.isna(d.loc[7, 'brecha_2'])
