"""Cifras ficticias únicamente para comprobar la matemática del motor."""
from datetime import date
import math
import pytest
from actuarial.valoracion import Parametros, Estado, Beneficiario, valorar


def params(**cambios):
    p=dict(fecha_valoracion=date(2026,9,30),tasa_efectiva_periodica=0.0,
        horizonte_periodos=1,fuente_mortalidad='fixture',reglas_sobrevivencia='fixture',
        gastos_por_periodo=[2],supuestos_confirmados=True,edad_titular=65,sexo_titular='F',
        mesada_referencia=100,mesadas_anuales=12,regla_reajuste='fixture',
        situacion_beneficiarios_confirmada=True,coherencia_supervivencia_confirmada=True,
        tratamiento_cola='fixture', beneficiarios=(Beneficiario(60,'M',True),))
    p.update(cambios); return Parametros(**p)


def test_obligaciones_por_estado_conjunto():
    r=valorar(params(),[{'titular':Estado(.6,100,0),'sobreviviente':Estado(.2,0,50),
                          'sin_derecho':Estado(.2,0,0)}])
    assert r=={'titular':60,'sobrevivientes':10,'obligaciones':70,'gastos':2,'total_con_gastos':72}


def test_sobreviviente_sin_derecho_no_recibe_pago():
    sin_derecho=params(beneficiarios=(Beneficiario(None,None,False),))
    r=valorar(sin_derecho,[{'titular':Estado(.5,100,0),'sin_derecho':Estado(.5,0,0)}])
    assert r['sobrevivientes']==0
    with pytest.raises(ValueError): valorar(sin_derecho,[{'s':Estado(1,0,20)}])


@pytest.mark.parametrize('changes',[{'fuente_mortalidad':None},{'reglas_sobrevivencia':None},
    {'tasa_efectiva_periodica':None},{'supuestos_confirmados':False},{'gastos_por_periodo':None},
    {'situacion_beneficiarios_confirmada':False},{'edad_titular':121},{'sexo_titular':'X'},
    {'regla_reajuste':None},{'tratamiento_cola':None},{'beneficiarios':None},
    {'beneficiarios':(Beneficiario(None,None,None),)},
    {'beneficiarios':(Beneficiario(None,'M',True),)}])
def test_bloquea_datos_incompletos(changes):
    with pytest.raises(ValueError): valorar(params(**changes),[{'s':Estado(1,1,0)}])


@pytest.mark.parametrize('p',[-.1,1.1,math.nan])
def test_probabilidades_invalidas(p):
    with pytest.raises(ValueError): valorar(params(),[{'s':Estado(p,1,0)}])


def test_probabilidades_deben_sumar_uno():
    with pytest.raises(ValueError): valorar(params(),[{'s':Estado(.5,1,0)}])
