"""Validación de cobertura con datos artificiales aislados."""
import pandas as pd
import numpy as np
from actuarial.ingesta_institucional import NUM,CAT,FECHAS
from actuarial.diagnostico import mascaras_validez


def test_edad_sexo_y_mesadas():
    d=pd.DataFrame({c:[None,None,None] for c in NUM+CAT+FECHAS})
    d['Edad']=[65,-1,121]; d['sexo1']=['F','M','X']; d['nmesadas']=[12,0,12.5]
    masks=mascaras_validez(d)
    assert masks['Edad'].tolist()==[True,False,False]
    assert masks['sexo1'].tolist()==[True,True,False]
    assert masks['nmesadas'].tolist()==[True,False,False]
    assert not masks['sexo2'].any()
