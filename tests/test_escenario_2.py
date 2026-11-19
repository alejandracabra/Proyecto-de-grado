"""Pruebas de conciliación con registros artificiales aislados."""
import pandas as pd
from actuarial.seleccion import C,K1,K13,K2,clasificar_escenarios


def test_segmentos_suman_universo_sintetico():
    d=pd.DataFrame({C:[50,100,200,None,40],K1:[100,100,100,100,None],
                    K13:[None,130,130,130,130],K2:[200,200,200,200,200]})
    r=clasificar_escenarios(d)
    assert r.grupo.value_counts().sum()==len(d)
    assert r.seleccion_2.sum()==3
