"""Ingesta limitada a registros sintéticos expresamente proporcionados en memoria."""
from collections.abc import Mapping, Sequence
import pandas as pd
from .config import VARIABLES


def leer_sinteticos(registros: Sequence[Mapping[str, object]], mapeo: Mapping[str, str]) -> pd.DataFrame:
    """Proyecta exclusivamente campos lógicos permitidos y asigna IDs efímeros.

    Este punto de entrada es solo para datos sintéticos. No lee archivos reales.
    El mapeo relaciona nombres lógicos con columnas sintéticas de origen.
    """
    if not set(mapeo).issubset(VARIABLES):
        raise ValueError("El mapeo contiene variables lógicas no autorizadas")
    if len(set(mapeo.values())) != len(mapeo):
        raise ValueError("Una columna de origen no puede mapearse dos veces")
    # Prohibir explícitamente identificadores incluso si se intentan mapear.
    prohibidos = ("cedula", "cédula", "documento", "nombre", "telefono", "teléfono", "direccion", "dirección", "correo", "email", "cuenta_bancaria", "identificacion", "identificación")
    if any(any(p in str(origen).casefold() for p in prohibidos) for origen in mapeo.values()):
        raise ValueError("El mapeo contiene una columna identificadora prohibida")
    filas = []
    for registro in registros:
        if not all(origen in registro for origen in mapeo.values()):
            raise ValueError("Falta una columna mapeada")
        filas.append({destino: registro[origen] for destino, origen in mapeo.items()})
    resultado = pd.DataFrame(filas, columns=list(mapeo))
    resultado.insert(0, "id_tecnico", range(1, len(resultado) + 1))
    return resultado
