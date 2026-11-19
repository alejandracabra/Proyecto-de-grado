"""Reporte exclusivamente de demostración con datos sintéticos."""
from .ingesta import leer_sinteticos
from .seleccion import seleccionar


def ejemplo() -> str:
    """Produce un resultado agregado de un ejemplo sintético no institucional."""
    filas = [{"saldo": saldo, "k1": 100, "k2": 200} for saldo in (50, 100, 150, 200, 250)]
    datos = leer_sinteticos(filas, {"capital_cuenta": "saldo", "capital_1": "k1", "capital_2": "k2"})
    resultado = seleccionar(datos, incluir_bono=False, metodo="observado")
    conteos = resultado["grupo"].value_counts()
    return ("EJEMPLO SINTÉTICO — exploratorio; valores arbitrarios\n"
            f"A: {conteos.get('A', 0)}; B: {conteos.get('B', 0)}; fuera: {conteos.get('fuera', 0)}\n"
            "K(2) proporcionado en el ejemplo; bono excluido. No son resultados institucionales.")


if __name__ == "__main__":
    print(ejemplo())
