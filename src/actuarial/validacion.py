"""Validaciones sin exposición de filas individuales."""
import numpy as np
import pandas as pd


def mascara_capital(valores: pd.Series) -> pd.Series:
    """Válido para comparación de capital: numérico, finito y no negativo."""
    numeros = pd.to_numeric(valores, errors='coerce')
    return np.isfinite(numeros) & (numeros >= 0)


def validar_capitales(datos: pd.DataFrame, columnas: tuple[str, ...]) -> None:
    """Exige columnas numéricas, finitas y no negativas; no imprime valores."""
    for columna in columnas:
        if columna not in datos:
            raise ValueError(f"Falta la variable requerida: {columna}")
        if not mascara_capital(datos[columna]).all():
            raise ValueError(f"Variable inválida: {columna}")


def posibles_duplicados(datos: pd.DataFrame, campos: tuple[str, ...]) -> int:
    """Cuenta coincidencias por variables autorizadas; no prueba duplicidad real."""
    if not campos or any(c not in datos or c == "id_tecnico" for c in campos):
        raise ValueError("Defina campos analíticos existentes para la revisión")
    return int(datos.duplicated(subset=list(campos), keep=False).sum())
