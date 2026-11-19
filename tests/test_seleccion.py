import pandas as pd
import pytest
from actuarial.ingesta import leer_sinteticos
from actuarial.seleccion import capital_disponible, capital_dos, seleccionar
from actuarial.validacion import posibles_duplicados


@pytest.fixture
def datos():
    return leer_sinteticos([{"s": x, "b": 10, "k": 100, "k2": 200, "cedula": "NO USAR"} for x in (0, 100, 199, 200)],
                           {"capital_cuenta": "s", "bono": "b", "capital_1": "k", "capital_2": "k2"})


def test_limites_y_privacidad(datos):
    assert "cedula" not in datos
    assert seleccionar(datos, incluir_bono=False, metodo="observado")["grupo"].tolist() == ["A", "B", "B", "fuera"]
    assert capital_disponible(datos, True).tolist() == [10, 110, 209, 210]


def test_bloqueo_y_metodos(datos):
    with pytest.raises(ValueError):
        seleccionar(datos, incluir_bono=False, metodo="lineal_provisional", definitivo=True, validado=True)
    with pytest.raises(ValueError):
        seleccionar(datos, incluir_bono=False, metodo="observado", definitivo=True)
    with pytest.raises(ValueError):
        capital_dos(datos, "lineal_provisional")
    assert seleccionar(datos, incluir_bono=False, metodo="autorizado", calculador=lambda x: x.capital_1 * 3)["grupo"].tolist() == ["A", "B", "B", "B"]


@pytest.mark.parametrize("valor", [-1, float('nan'), float('inf'), 'invalido'])
def test_capital_invalido(datos, valor):
    datos.loc[0, "capital_1"] = valor
    with pytest.raises(ValueError):
        seleccionar(datos, incluir_bono=False, metodo="observado")


def test_identificador_prohibido():
    with pytest.raises(ValueError):
        leer_sinteticos([{"cedula": 1}], {"capital_1": "cedula"})
    with pytest.raises(ValueError):
        leer_sinteticos([{"cc": 1}], {"capital_1": "cc"})


def test_duplicados_y_orden_incoherente(datos):
    assert posibles_duplicados(datos, ("capital_1",)) == 4
    datos["capital_2"] = 50
    with pytest.raises(ValueError):
        seleccionar(datos, incluir_bono=False, metodo="observado")
