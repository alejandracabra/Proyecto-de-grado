"""Criterio preliminar y convenciones explícitas de capital."""
from collections.abc import Callable
import pandas as pd
from .validacion import validar_capitales


def capital_disponible(datos: pd.DataFrame, incluir_bono: bool) -> pd.Series:
    """Calcula capital con una convención explícita sobre el bono."""
    columnas = ("capital_cuenta", "bono") if incluir_bono else ("capital_cuenta",)
    validar_capitales(datos, columnas)
    capital = pd.to_numeric(datos["capital_cuenta"])
    return capital + pd.to_numeric(datos["bono"]) if incluir_bono else capital.copy()


def capital_dos(datos: pd.DataFrame, metodo: str, calculador: Callable[[pd.DataFrame], pd.Series] | None = None) -> pd.Series:
    """Obtiene K(2) observado, autorizado o una aproximación lineal provisional."""
    if metodo == "observado":
        validar_capitales(datos, ("capital_2",))
        resultado = pd.to_numeric(datos["capital_2"])
    elif metodo == "lineal_provisional":
        validar_capitales(datos, ("capital_1",))
        resultado = 2 * pd.to_numeric(datos["capital_1"])
    elif metodo == "autorizado" and calculador is not None:
        resultado = calculador(datos.copy())
        if not isinstance(resultado, pd.Series) or not resultado.index.equals(datos.index):
            raise ValueError("El cálculo autorizado debe devolver una serie con el mismo índice")
    else:
        raise ValueError("Método K(2) no disponible")
    validar_capitales(pd.DataFrame({"capital_2": resultado}), ("capital_2",))
    return resultado


def seleccionar(datos: pd.DataFrame, *, incluir_bono: bool, metodo: str,
                definitivo: bool = False, validado: bool = False,
                calculador: Callable[[pd.DataFrame], pd.Series] | None = None) -> pd.DataFrame:
    """Clasifica A, B o fuera, bloqueando decisiones no validadas."""
    if definitivo and (not validado or metodo == "lineal_provisional"):
        raise ValueError("Selección definitiva requiere metodología validada y no provisional")
    validar_capitales(datos, ("capital_1",))
    disponible = capital_disponible(datos, incluir_bono)
    k1 = pd.to_numeric(datos["capital_1"])
    k2 = capital_dos(datos, metodo, calculador)
    if (k2 < k1).any():
        raise ValueError("K(2) no puede ser inferior a K(1) en este criterio")
    salida = pd.DataFrame({"id_tecnico": datos["id_tecnico"], "capital_disponible": disponible, "capital_1": k1, "capital_2": k2})
    salida["grupo"] = "fuera"
    salida.loc[disponible < k2, "grupo"] = "B"
    salida.loc[disponible < k1, "grupo"] = "A"
    salida.attrs.update({"caracter": "definitivo" if definitivo else "exploratorio", "metodo_k2": metodo})
    return salida
