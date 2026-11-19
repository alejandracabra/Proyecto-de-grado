"""Escenario real local de selección K(1,3): solo exporta agregados protegidos."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
from html import escape
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from visualization.proteccion_style import AZUL, BLANCO, COLORES, ESTILO_HTML, TIPOGRAFIA
from auditoria_local import M, CORTE, UNIVERSO, valores_fila, validar_universo

GRUPOS = ("A", "B", "fuera", "no evaluable")
CAP = ("Capital +Bono", "capital_necesario_sm", "capital_necesario_1.3_sm")
NUM = CAP + ("capital", "Capital mes anterior", "capital_necesario_def", "Edad", "mesada", "nmesadas")
CAT = ("Riesgo", "Riesgo 3", "Rango de Mesada", "tipo1", "estado1", "tipo2", "estado2", "tipo3", "estado3", "Descapitalizado", "Desfinanciado")


def clasificar(c, k1, k13):
    """Clasifica solo capitales numéricos, finitos, no negativos y ordenados."""
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in (c, k1, k13)) or k13 < k1:
        return "no evaluable"
    if c < k1:
        return "A"
    if c < k13:
        return "B"
    return "fuera"


def publicable(conteos, umbral):
    """Suprime una tabla completa si tiene una celda positiva pequeña."""
    return all(n == 0 or n >= umbral for n in conteos)


def percentil(datos, p):
    datos = sorted(datos)
    i = (len(datos)-1)*p
    a, b = math.floor(i), math.ceil(i)
    return datos[a] if a == b else datos[a]*(b-i)+datos[b]*(i-a)


def figura(titulo, filas, unidad=""):
    """Barras SVG de datos agregados; estilo provisional, sin dependencia gráfica."""
    ancho, alto = 1000, 125 + 45 * len(filas)
    maximo = max((abs(v) for _, v, _ in filas), default=1) or 1
    lineas = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{escape(titulo, quote=True)}">',
              f'<rect width="100%" height="100%" fill="{BLANCO}"/>',
              f'<g font-family="{TIPOGRAFIA}" font-size="14" fill="{AZUL}"><text x="20" y="28" font-size="18">{escape(titulo)}</text>']
    for i, (nombre, valor, color) in enumerate(filas):
        y = 55 + i*45
        ancho_barra = abs(valor)/maximo*210
        x = 440 if valor >= 0 else 440-ancho_barra
        lineas.append(f'<text x="20" y="{y+16}">{escape(nombre)}</text><rect x="{x:.2f}" y="{y}" width="{ancho_barra:.2f}" height="20" fill="{color}" stroke="{AZUL}"/><text x="680" y="{y+16}">{valor:,.2f} {escape(unidad)}</text>')
    lineas.append(f'<line x1="440" y1="42" x2="440" y2="{alto-45}" stroke="{AZUL}"/><text x="20" y="{alto-15}" font-size="11">Fuente: base de control de saldos; corte: {CORTE}. Agregados; unidades de origen.</text></g></svg>')
    return ''.join(lineas)


def tabla(titulo, columnas, filas):
    return '<h2>' + escape(titulo) + '</h2><table><thead><tr>' + ''.join('<th>'+escape(str(x))+'</th>' for x in columnas) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+escape(str(x))+'</td>' for x in fila)+'</tr>' for fila in filas) + '</tbody></table>'


def ejecutar(archivo, umbral):
    with ZipFile(archivo) as z:
        libro = ET.fromstring(z.read('xl/workbook.xml'))
        if len(libro.findall(M+'sheets/'+M+'sheet')) != 1 or 'xl/worksheets/sheet1.xml' not in z.namelist():
            raise ValueError('Estructura no admitida')
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _, row in ET.iterparse(f, events=('end',)):
                if row.tag == M+'row':
                    cab = {col: int(v) for col, t, v in valores_fila(row) if t == 's'}
                    break
        nombres = {}
        with z.open('xl/sharedStrings.xml') as f:
            i = 0
            for _, e in ET.iterparse(f, events=('end',)):
                if e.tag == M+'si':
                    if i in cab.values(): nombres[i] = ''.join(e.itertext()).strip()
                    e.clear(); i += 1
        campos = {col: nombres.get(i) for col, i in cab.items() if nombres.get(i) in NUM+CAT}
        if any(list(campos.values()).count(campo) != 1 for campo in CAP):
            raise ValueError('Falta o está repetida una columna de capital requerida')
        acumulados = {g: {n: [] for n in NUM + ('brecha_1', 'brecha_13')} for g in GRUPOS}
        categorias = {g: {c: Counter() for c in CAT} for g in GRUPOS}
        conteos = Counter()
        total = con_datos = 0
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _, row in ET.iterparse(f, events=('end',)):
                if row.tag != M+'row': continue
                if row.get('r') == '1': row.clear(); continue
                total += 1
                valores, categorias_fila = {}, {}
                for col, tipo, texto in valores_fila(row, campos):
                    nombre = campos[col]
                    if nombre in NUM and tipo == 'n':
                        try:
                            n = float(texto)
                            if math.isfinite(n) and n >= 0: valores[nombre] = n
                        except ValueError: pass
                    elif nombre in CAT and tipo in ('s', 'n', 'str'):
                        categorias_fila[nombre] = (tipo, texto)
                if valores or categorias_fila: con_datos += 1
                grupo = clasificar(*(valores.get(k) for k in CAP))
                conteos[grupo] += 1
                for nombre, valor in valores.items(): acumulados[grupo][nombre].append(valor)
                if grupo != 'no evaluable':
                    acumulados[grupo]['brecha_1'].append(valores[CAP[0]]-valores[CAP[1]])
                    acumulados[grupo]['brecha_13'].append(valores[CAP[0]]-valores[CAP[2]])
                for nombre, valor in categorias_fila.items(): categorias[grupo][nombre][valor] += 1
                row.clear()
        validar_universo(total, con_datos, unidad_confirmada=True, sin_duplicados_confirmado=True, retiro_confirmado=True)
        indices = {int(v) for g in GRUPOS for c in CAT for (t,v) in categorias[g][c] if t == 's'}
        etiquetas = {}
        with z.open('xl/sharedStrings.xml') as f:
            i = 0
            for _, e in ET.iterparse(f, events=('end',)):
                if e.tag == M+'si':
                    if i in indices: etiquetas[i] = ''.join(e.itertext()).strip()
                    e.clear(); i += 1
    return conteos, acumulados, categorias, etiquetas


def main():
    p = argparse.ArgumentParser()
    p.add_argument('archivo', type=Path)
    p.add_argument('--autorizado', action='store_true')
    p.add_argument('--confirmar-corte', action='store_true', help='Confirma las condiciones institucionales del corte 30-09-2026')
    p.add_argument('--umbral', type=int, default=10)
    args = p.parse_args()
    if not args.autorizado or not args.confirmar_corte or args.umbral < 10:
        p.error('Se requieren autorización, confirmación del corte y umbral >= 10')
    conteos, datos, cats, etiquetas = ejecutar(args.archivo, args.umbral)
    destino = Path('reports/generated') / ('escenario_13_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    destino.mkdir(parents=True, exist_ok=False)
    aviso = ('Escenario provisional de selección con K(1,3). No corresponde al criterio definitivo de elegibilidad. '
             'K(2) se calculará posteriormente mediante la metodología actuarial institucional; los resultados pueden cambiar. '
             'Universo reportado: 95.011 afiliados en retiro programado, corte 30 de septiembre de 2026. Datos reales.')
    tablas, graficos = [], []
    protege = not publicable([conteos[g] for g in GRUPOS], args.umbral)
    if protege:
        tablas.append(tabla('Segmentos', ['Resultado'], [['Resultados suprimidos por confidencialidad']]))
    else:
        resumen = [[g, conteos[g], f'{100*conteos[g]/UNIVERSO:.2f}%'] for g in GRUPOS]
        seleccionados = conteos['A'] + conteos['B']
        resumen.append(['A + B seleccionados', seleccionados, f'{100*seleccionados/UNIVERSO:.2f}%'])
        tablas.append(tabla('Distribución de segmentos', ['Segmento', 'Afiliados', '% del universo'], resumen))
        with (destino/'segmentos.csv').open('x', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['segmento','afiliados','porcentaje_universo']); w.writerows(resumen)
        graficos.append(('segmentos.svg', figura('Escenario provisional: distribución de segmentos', [(g, conteos[g], COLORES[g]) for g in GRUPOS], 'afiliados')))
        filas = []
        for g in GRUPOS:
            for variable, valores in datos[g].items():
                faltan = conteos[g] - len(valores)
                if len(valores) >= args.umbral and publicable([faltan], args.umbral):
                    filas.append([g, variable, len(valores), f'{sum(valores):.2f}', *[f'{percentil(valores,p):.2f}' for p in (.10,.25,.50,.75,.90)]])
        tablas.append(tabla('Capitales, brechas y caracterización numérica', ['Segmento','Variable','N válido','Suma','P10','P25','Mediana','P75','P90'], filas))
        with (destino/'estadisticos.csv').open('x', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['segmento','variable','n_valido','suma','p10','p25','mediana','p75','p90']); w.writerows(filas)
        categorias_exportables = []
        for g in ('A','B'):
            for c in CAT:
                cont = cats[g][c]; faltan = conteos[g] - sum(cont.values())
                # Se suprime toda la tabla ante celdas pequeñas; ninguna etiqueta representa un identificador.
                if cont and publicable([*cont.values(), faltan], args.umbral):
                    filas_cat = [[etiquetas.get(int(v), '[sin etiqueta]') if t == 's' else v, n] for (t,v), n in cont.items()]
                    tablas.append(tabla(f'{g}: {c}', ['Categoría','Afiliados'], filas_cat))
                    categorias_exportables.extend([[g, c, valor, n] for valor, n in filas_cat])
                    if c == 'Riesgo' and len(filas_cat) <= 12:
                        graficos.append((f'riesgo_{g}.svg', figura('Riesgo — grupo '+g, [(str(valor), n, COLORES[g]) for valor, n in filas_cat], 'afiliados')))
                else:
                    tablas.append(tabla(f'{g}: {c}', ['Resultado'], [['Suprimido o no disponible']]))
        with (destino/'categorias.csv').open('x', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['segmento','variable','categoria','afiliados']); w.writerows(categorias_exportables)
        for variable, titulo in ((CAP[1], 'Capital disponible frente a K(1)'), (CAP[2], 'Capital disponible frente a K(1,3)'), ('brecha_1', 'Brecha agregada frente a K(1)'), ('brecha_13', 'Brecha agregada frente a K(1,3)')):
            filas_fig = []
            for g in ('A','B','fuera'):
                if conteos[g] >= args.umbral and len(datos[g][variable]) == conteos[g] and len(datos[g][CAP[0]]) == conteos[g]:
                    if variable in CAP: filas_fig.append((g+' disponible',sum(datos[g][CAP[0]]),COLORES[g]))
                    filas_fig.append((g+' '+variable,sum(datos[g][variable]),COLORES[g]))
            if filas_fig: graficos.append((f'grafico_{len(graficos)+1}.svg', figura(titulo, filas_fig, 'unidades monetarias')))
        bins = ((0,60),(60,70),(70,80),(80,200))
        for g in ('A','B'):
            edades = datos[g]['Edad']; recuentos = [sum(a <= x < b for x in edades) for a,b in bins]
            if conteos[g] >= args.umbral and len(edades) == sum(recuentos) and publicable(recuentos+[conteos[g]-len(edades)], args.umbral):
                graficos.append((f'edades_{g}.svg', figura('Edades — grupo '+g, [(f'{a}–{b-1}',n,COLORES[g]) for (a,b),n in zip(bins,recuentos)], 'afiliados')))
    for nombre, svg in graficos:
        (destino/nombre).write_text(svg, encoding='utf-8')
    limite = ('Las brechas son C menos K por afiliado y su suma; no son valoración actuarial de la bolsa. '
              'Capital +Bono es el campo indicado, sujeto a confirmar disponibilidad del bono, unidades y ausencia de doble conteo. '
              'Se excluyen de la evaluación valores faltantes, no numéricos, no finitos, negativos o K(1,3) menor que K(1). '
              'Sexo del titular no se presenta: sexo1 no está validado. Riesgo, beneficiarios y clasificaciones requieren confirmar sus definiciones. '
              'La supresión de celdas pequeñas es provisional y no sustituye la revisión institucional. '
              'Los totales numéricos usan valores disponibles por variable; las brechas usan exclusivamente evaluables. La identidad gráfica sigue las indicaciones del proyecto.')
    estilo = '<style>body{max-width:1100px;margin:auto;padding:24px}</style>' + ESTILO_HTML
    imagenes = ''.join(f'<img src="{escape(n)}" alt="Gráfico agregado del escenario provisional">' for n,_ in graficos)
    base = '<!doctype html><html lang="es"><meta charset="utf-8">'+estilo+'<h1>Escenario provisional de selección con K(1,3)</h1><p>'+escape(aviso)+'</p>'
    (destino/'ejecutivo.html').write_text(base+tablas[0]+imagenes+'<h2>Limitaciones</h2><p>'+escape(limite)+'</p></html>', encoding='utf-8')
    (destino/'tecnico.html').write_text(base+''.join(tablas)+imagenes+'<h2>Método y limitaciones</h2><p>'+escape(limite)+'</p><p>A: C &lt; K(1); B: K(1) ≤ C &lt; K(1,3); fuera: C ≥ K(1,3); demás: no evaluable. Porcentajes sobre el universo completo. Percentiles interpolados linealmente. Sin extrapolación de K(2).</p></html>', encoding='utf-8')
    print('Informes y agregados locales:', destino)


if __name__ == '__main__':
    main()
