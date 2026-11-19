"""Identidad gráfica configurada según las indicaciones del proyecto."""
from pathlib import Path
AZUL = "#0033A0"
BLANCO = "#FFFFFF"
LIMA = "#E3E829"
AMARILLO = "#FFE946"
FONDO_AZUL = "#EEF7FA"
FONDO_LIMA = "#F6F8E8"
COLORES = {"A": AZUL, "B": LIMA, "fuera": AMARILLO, "no evaluable": FONDO_AZUL}
TIPOGRAFIA = "Sura Sans, Arial, sans-serif"
ESTILO_HTML = f"""<style id="identidad-proyecto">
body {{ font: 16px 'Sura Sans', Arial, sans-serif; color: {AZUL}; background: {BLANCO}; }}
h1, h2, h3, h4 {{ color: {AZUL}; }}
table {{ border-collapse: collapse; margin-bottom: 24px; }}
th, td {{ border-bottom: 1px solid {AZUL}; padding: 7px; text-align: left; }}
th {{ background: {FONDO_AZUL}; color: {AZUL}; }}
tr:nth-child(even) td {{ background: {FONDO_LIMA}; }}
a {{ color: {AZUL}; }} img {{ max-width: 100%; }}
</style>"""


def configurar() -> None:
    """Aplica tipografía genérica y parámetros de legibilidad."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": ["Sura Sans", "DejaVu Sans"], "axes.titlesize": 14,
                         "axes.labelsize": 11, "figure.dpi": 120,
                         "savefig.dpi": 300, "savefig.bbox": "tight",
                         "text.color": AZUL, "axes.labelcolor": AZUL,
                         "axes.edgecolor": AZUL, "xtick.color": AZUL,
                         "ytick.color": AZUL, "figure.facecolor": BLANCO,
                         "axes.facecolor": BLANCO})


def miles(valor: float, posicion: int | None = None) -> str:
    """Representa miles con punto y sin decimales."""
    return f"{valor:,.0f}".replace(",", ".")


def formatear_eje(eje, *, porcentaje: bool = False, unidad: str = "") -> None:
    """Configura escala porcentual o monetaria; la unidad la define el usuario."""
    from matplotlib.ticker import FuncFormatter, PercentFormatter
    eje.yaxis.set_major_formatter(PercentFormatter(1) if porcentaje else FuncFormatter(miles))
    if unidad:
        eje.set_ylabel(unidad)


def exportar(figura, destino: str | Path) -> None:
    """Exporta los tres formatos requeridos con un nombre base común."""
    base = Path(destino)
    base.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg", "pdf"):
        figura.savefig(base.with_suffix("." + extension))
