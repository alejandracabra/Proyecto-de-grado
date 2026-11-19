"""Auditoría exploratoria local de XLSX con biblioteca estándar, sin exportar filas.

Los nombres de columnas son hipótesis pendientes de confirmación. No calcula K(2).
"""
import argparse
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from statistics import median
import math
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from visualization.proteccion_style import ESTILO_HTML

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NUM = ("mesada", "nmesadas", "capital", "Capital +Bono", "Capital mes anterior", "Edad", "capital_necesario_sm", "capital_necesario_1.3_sm", "capital_necesario_def", "Descapitalización", "Desfinanciación", "Expectativa de vida")
CAT = ("Riesgo", "Riesgo 3", "sexo1", "tipo1", "estado1", "tipo2", "estado2", "tipo3", "estado3", "Descapitalizado", "Desfinanciado")
CORTE = "30 de septiembre de 2026"
UNIVERSO = 95011


def validar_universo(total, con_datos, *, unidad_confirmada, sin_duplicados_confirmado, retiro_confirmado):
    """Exige controles computables y confirmaciones; no prueba unicidad sin identificadores."""
    if total != UNIVERSO or con_datos != total:
        raise ValueError("El número de filas o cobertura no coincide con el universo confirmado")
    if not all((unidad_confirmada, sin_duplicados_confirmado, retiro_confirmado)):
        raise ValueError("Faltan confirmaciones institucionales de unidad, duplicados o modalidad")


def indice_columna(ref):
    letras = re.match(r"[A-Z]+", ref).group()
    n = 0
    for letra in letras:
        n = n * 26 + ord(letra) - 64
    return n - 1


def valores_fila(row, seleccion=None):
    for c in row.findall(M + "c"):
        col = indice_columna(c.attrib["r"])
        if seleccion is not None and col not in seleccion:
            continue
        v = c.find(M + "v")
        if v is not None and v.text is not None:
            yield col, c.get("t", "n"), v.text


def cuantiles(valores):
    valores.sort()
    def q(p):
        i = (len(valores) - 1) * p
        lo, hi = math.floor(i), math.ceil(i)
        return valores[lo] * (hi - i) + valores[hi] * (i - lo) if lo != hi else valores[lo]
    return [q(.25), median(valores), q(.75)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("archivo", type=Path)
    p.add_argument("--autorizado", action="store_true")
    p.add_argument("--umbral", type=int, default=10)
    p.add_argument("--confirmar-unidad", action="store_true", help="Cada fila es un afiliado")
    p.add_argument("--confirmar-sin-duplicados", action="store_true", help="Confirmación institucional, no prueba computacional")
    p.add_argument("--confirmar-retiro-programado", action="store_true", help="Todos los afiliados están en retiro programado")
    args = p.parse_args()
    if not args.autorizado or args.umbral < 10:
        p.error("Se requiere autorización y un umbral de al menos 10")
    with ZipFile(args.archivo) as z:
        # Se exige una sola hoja y la primera fila como cabecera. Fallar ante otra estructura.
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = workbook.findall(M + "sheets/" + M + "sheet")
        if len(sheets) != 1 or "xl/worksheets/sheet1.xml" not in z.namelist():
            raise ValueError("Estructura no admitida: se requiere revisión manual")
        with z.open("xl/worksheets/sheet1.xml") as f:
            for _, row in ET.iterparse(f, events=("end",)):
                if row.tag == M + "row":
                    encabezados = {col: int(v) for col, t, v in valores_fila(row) if t == "s"}
                    break
        # Leer solo cadenas referenciadas en la cabecera.
        nombres = {}
        with z.open("xl/sharedStrings.xml") as f:
            i = 0
            for _, e in ET.iterparse(f, events=("end",)):
                if e.tag == M + "si":
                    if i in encabezados.values():
                        nombres[i] = "".join(e.itertext()).strip()
                    e.clear()
                    i += 1
        campos = {col: nombres.get(i, "") for col, i in encabezados.items() if nombres.get(i, "") in NUM + CAT}
        if not campos:
            raise ValueError("No se identificaron campos autorizados para auditoría")
        numeros = {nombre: [] for nombre in NUM if nombre in campos.values()}
        categorias = {nombre: Counter() for nombre in CAT if nombre in campos.values()}
        presentes = Counter()
        tipos = {nombre: Counter() for nombre in campos.values()}
        total = 0
        filas = 0
        con_faltantes = 0
        brechas = {x: [] for x in ("capital_necesario_sm", "capital_necesario_1.3_sm", "capital_necesario_def")}
        razones = []
        # Para evitar imprimir o cargar cadenas de datos, las categorías se cuentan por índice compartido.
        with z.open("xl/worksheets/sheet1.xml") as f:
            for _, row in ET.iterparse(f, events=("end",)):
                if row.tag != M + "row":
                    continue
                if row.get("r") == "1":
                    row.clear()
                    continue
                filas += 1
                vistos = set()
                fila_numerica = {}
                for col, tipo, texto in valores_fila(row, campos):
                    nombre = campos[col]
                    vistos.add(nombre)
                    presentes[nombre] += 1
                    tipos[nombre][tipo] += 1
                    if nombre in numeros:
                        try:
                            x = float(texto)
                            if math.isfinite(x):
                                numeros[nombre].append(x)
                                fila_numerica[nombre] = x
                        except ValueError:
                            pass
                    else:
                        categorias[nombre][(tipo, texto)] += 1
                if vistos:
                    total += 1
                    con_faltantes += len(vistos) < len(campos)
                    capital = fila_numerica.get("Capital +Bono")
                    if capital is not None:
                        for nombre in brechas:
                            if nombre in fila_numerica:
                                brechas[nombre].append(capital - fila_numerica[nombre])
                    k1 = fila_numerica.get("capital_necesario_sm")
                    k13 = fila_numerica.get("capital_necesario_1.3_sm")
                    if k1 is not None and k1 > 0 and k13 is not None:
                        razones.append(k13 / k1)
                row.clear()
        validar_universo(filas, total, unidad_confirmada=args.confirmar_unidad,
                         sin_duplicados_confirmado=args.confirmar_sin_duplicados,
                         retiro_confirmado=args.confirmar_retiro_programado)
        indices = {int(valor) for conteos in categorias.values() for tipo, valor in conteos if tipo == "s"}
        etiquetas = {}
        with z.open("xl/sharedStrings.xml") as f:
            i = 0
            for _, e in ET.iterparse(f, events=("end",)):
                if e.tag == M + "si":
                    if i in indices:
                        etiquetas[i] = "".join(e.itertext()).strip()
                    e.clear()
                    i += 1
    if total < args.umbral:
        raise ValueError("Universo demasiado pequeño para generar informe")
    partes = ["<h1>Auditoría exploratoria del universo reportado — datos reales</h1>",
              f"<p>Fecha de corte: {CORTE}. Universo reportado: {UNIVERSO:,} afiliados en retiro programado.</p>",
              "<p>Según confirmación institucional, cada fila corresponde a un afiliado y no existen duplicados. Los controles verifican conteo y cobertura y exigen confirmaciones; no demuestran unicidad ni modalidad sin información adicional autorizada.</p>",
              "<p>Los significados específicos de los campos siguen pendientes. No hay selección definitiva ni K(2). Sexo1 no se atribuye al titular sin confirmación.</p>",
              f"<p>Afiliados con algún campo analizado ausente: {con_faltantes if con_faltantes >= args.umbral and total-con_faltantes >= args.umbral else 'suprimido'}.</p>",
              "<h2>Calidad de campos seleccionados</h2><table><tr><th>Campo</th><th>Faltantes</th><th>Tipos XML observados</th><th>Valores numéricos válidos</th></tr>"]
    def seguro(n):
        return str(n) if n >= args.umbral and total-n >= args.umbral else "suprimido"
    for nombre in campos.values():
        faltan = total-presentes[nombre]
        pct = f"{faltan/total:.1%}" if args.umbral <= faltan <= total-args.umbral else "suprimido"
        partes.append(f"<tr><td>{escape(nombre)}</td><td>{pct}</td><td>{escape(', '.join(sorted(tipos[nombre])))}</td><td>{seguro(len(numeros[nombre])) if nombre in numeros else '—'}</td></tr>")
    partes.append("</table><h2>Estadísticos numéricos exploratorios</h2><p>Sumas y cuantiles se calculan solo sobre valores numéricos finitos disponibles, sin imputación; las unidades y comparabilidad requieren confirmación.</p><table><tr><th>Campo</th><th>Suma</th><th>P25</th><th>Mediana</th><th>P75</th></tr>")
    for nombre, valores in numeros.items():
        if len(valores) >= args.umbral:
            q = cuantiles(valores)
            partes.append(f"<tr><td>{escape(nombre)}</td><td>{sum(valores):,.2f}</td>" + "".join(f"<td>{x:,.2f}</td>" for x in q) + "</tr>")
    partes.append("</table><h2>Distribución del número de mesadas</h2>")
    pagos = Counter(numeros.get("nmesadas", []))
    if pagos and all(n >= args.umbral for n in pagos.values()) and total-sum(pagos.values()) not in range(1, args.umbral):
        partes.append("<ul>" + "".join(f"<li>{valor:g}: {n}</li>" for valor, n in sorted(pagos.items())) + "</ul>")
    else:
        partes.append("<p>Distribución suprimida o no disponible.</p>")
    partes.append("<h2>Brechas individuales exploratorias</h2><p>Capital +Bono menos capital requerido; solo pares numéricos completos. El sentido del bono y las unidades no están validados. Son comparaciones individuales, no déficit actuarial de una bolsa.</p><table><tr><th>Capital requerido</th><th>Pares</th><th>Suma de brechas</th><th>P25</th><th>Mediana</th><th>P75</th></tr>")
    for nombre, valores in brechas.items():
        if len(valores) >= args.umbral and (total-len(valores) == 0 or total-len(valores) >= args.umbral):
            partes.append(f"<tr><td>{escape(nombre)}</td><td>{len(valores)}</td><td>{sum(valores):,.2f}</td>" + "".join(f"<td>{x:,.2f}</td>" for x in cuantiles(valores)) + "</tr>")
    partes.append("</table>")
    if len(razones) >= args.umbral and (total-len(razones) == 0 or total-len(razones) >= args.umbral):
        partes.append("<p>Razón exploratoria K(1,3)/K(1), cuartiles: " + ", ".join(f"{x:.4f}" for x in cuantiles(razones)) + ". Esta observación no valida la extrapolación a K(2).</p>")
    partes.append("<h2>Distribuciones categóricas</h2><p>Si existe una categoría pequeña, toda la distribución se suprime para prevenir deducción.</p>")
    for nombre, conteos in categorias.items():
        partes.append(f"<h3>{escape(nombre)}</h3>")
        if not conteos or any(n < args.umbral for n in conteos.values()) or total-sum(conteos.values()) in range(1, args.umbral):
            partes.append("<p>Distribución suprimida o no disponible.</p>")
        else:
            partes.append("<ul>" + "".join(f"<li>{escape(etiquetas.get(int(valor), '[sin etiqueta]') if tipo == 's' else valor)}: {n}</li>" for (tipo, valor), n in conteos.items()) + "</ul>")
    partes.append("<h2>Limitaciones y decisiones pendientes</h2><p>Confirmar definiciones de campos, sexo1, moneda, bonos y ausencia de doble conteo. La comparación entre K(1) y K(1,3) no valida por sí sola proporcionalidad a K(2); faltan reglas de gastos y condiciones institucionales. Desfinanciación: insuficiencia frente a mesada actual. Descapitalización: insuficiencia frente a 1 SMMLV. Confirmar codificación y definición operacional de las columnas. No se han valorado obligaciones ni beneficiarios.</p>")
    destino = Path("reports/generated") / ("auditoria_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".html")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as f:
        f.write("<!doctype html><html lang='es'><meta charset='utf-8'><title>Auditoría exploratoria local</title>" + ESTILO_HTML + "<body>" + "\n".join(partes) + "</body></html>")
    print("Informe agregado local generado:", destino)
    print("Afiliados en el universo reportado:", total)
    print("K(2) y selección definitiva: pendientes de validación")


if __name__ == "__main__":
    main()
