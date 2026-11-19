"""Fixtures artificiales aislados; no se ejecutan sobre la base real."""
import numpy as np
import pandas as pd
import pytest
from actuarial.seleccion import C,K1,K13,K2,clasificar_escenarios
from actuarial.ingesta_institucional import Lector, CadenasSeleccionadas
from xml.sax.xmlreader import AttributesImpl


def test_seleccion_independiente_y_limites():
    df=pd.DataFrame({C:[0,100,199,200,50,50,-1,np.nan,99,0],
        K1:[100,100,100,100,np.nan,100,100,100,100,100],
        K13:[130,130,130,130,130,np.nan,130,130,300,130],
        K2:[200,200,200,200,200,200,200,200,200,0]})
    r=clasificar_escenarios(df)
    assert r.grupo.tolist()==['A','B','B','fuera','seleccionado sin grupo','A','no evaluable','no evaluable','A','fuera']
    assert r.seleccion_2.tolist()==[True,True,True,False,True,True,False,False,True,False]
    assert r.loc[8,'orden_inconsistente']
    assert pd.isna(r.loc[5,'brecha_13'])
    assert len(r)==r.grupo.value_counts().sum()


@pytest.mark.parametrize('v',[-1,np.nan,np.inf,'no numérico'])
def test_k2_invalido(v):
    r=clasificar_escenarios(pd.DataFrame({C:[5],K1:[10],K13:[13],K2:[v]}))
    assert r.grupo.iloc[0]=='no evaluable'


def test_columnas_intermedias_ausentes_no_bloquean_k2():
    r=clasificar_escenarios(pd.DataFrame({C:[5,20],K2:[10,10]}))
    assert r.seleccion_2.tolist()==[True,False]
    assert r.grupo.tolist()==['seleccionado sin grupo','fuera']
    assert not r.evaluables_1.any() and not r.evaluables_13.any()
    r2=clasificar_escenarios(pd.DataFrame({C:[5],K1:[10],K13:[13]}))
    assert r2.grupo.iloc[0]=='no evaluable'


def test_lector_descarta_columnas_no_autorizadas():
    h=Lector({2:'Riesgo'})
    h.startElement('row',AttributesImpl({'r':'2'}))
    for ref,value in [('A2','NO_LEER'),('B2','NO_LEER'),('C2','CATEGORIA')]:
        h.startElement('c',AttributesImpl({'r':ref,'t':'str'})); h.startElement('v',AttributesImpl({}))
        h.characters(value); h.endElement('v'); h.endElement('c')
    h.endElement('row')
    assert h.filas==[{'Riesgo':('literal','CATEGORIA')}]


def test_cadenas_no_referenciadas_no_se_retienen():
    h=CadenasSeleccionadas({1})
    for valor in ('DATO_NO_AUTORIZADO','F'):
        h.startElement('si',AttributesImpl({})); h.characters(valor); h.endElement('si')
    assert h.resultado=={1:'F'}
