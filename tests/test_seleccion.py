"""Pruebas sintéticas del contrato institucional de selección."""
import pandas as pd
from actuarial.seleccion import C,K1,K13,K2,clasificar_escenarios


def test_solo_usa_capital_mas_bono_para_seleccion():
    datos=pd.DataFrame({C:[100],K1:[100],K13:[130],K2:[200],
                        'capital_cuenta':[0], 'bono':[0]})
    assert clasificar_escenarios(datos).grupo.iloc[0]=='B'


def test_k1_ausente_no_impide_seleccion_k2():
    datos=pd.DataFrame({C:[50],K1:[None],K13:[None],K2:[200]})
    r=clasificar_escenarios(datos)
    assert r.seleccion_2.iloc[0]
    assert r.grupo.iloc[0]=='seleccionado sin grupo'
