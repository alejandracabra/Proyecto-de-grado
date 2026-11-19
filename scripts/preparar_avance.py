"""Genera un avance reproducible con agregados reales; no exporta microdatos."""
import csv
from datetime import datetime
from html import escape
from pathlib import Path
from statistics import fmean, stdev

from escenario_13 import (CAP, CAT, COLORES, CORTE, ESTILO_HTML, GRUPOS, NUM,
                          UNIVERSO, ejecutar, figura, percentil, publicable, tabla)


def fmt(x):
    return f'{x:,.2f}'


def proteger(n, umbral=10):
    return n == 0 or n >= umbral


def construir():
    conteos, datos, categorias, etiquetas = ejecutar(Path('xd.xlsx'), 10)
    if sum(conteos[g] for g in GRUPOS) != UNIVERSO:
        raise ValueError('La conciliación del universo falló')
    origen = Path('reports/generated/escenario_13_20261118_212228_984768/segmentos.csv')
    if origen.exists():
        with origen.open(encoding='utf-8-sig', newline='') as f:
            anterior = {r['segmento']: int(r['afiliados']) for r in csv.DictReader(f)}
        if any(anterior.get(g) != conteos[g] for g in GRUPOS):
            raise ValueError('Los conteos actuales difieren de la última ejecución anterior')
    if not publicable([conteos[g] for g in GRUPOS], 10):
        raise ValueError('La tabla de segmentos requiere supresión complementaria')
    destino = Path('reports/generated') / ('avance_integral_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    destino.mkdir(parents=True, exist_ok=False)
    selected = conteos['A'] + conteos['B']
    porc = lambda n: f'{100*n/UNIVERSO:.2f}%'
    seg = [[g, str(conteos[g]), porc(conteos[g])] for g in GRUPOS]
    seg.append(['A + B', str(selected), porc(selected)])
    with (destino/'segmentos_agregados.csv').open('x', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['segmento','afiliados','porcentaje_universo']); w.writerows(seg)

    indicadores = []
    for grupo in ('universo', 'A', 'B', 'fuera', 'no evaluable'):
        for nombre in NUM + ('brecha_1','brecha_13'):
            valores = ([x for g in GRUPOS for x in datos[g][nombre]] if grupo == 'universo' else datos[grupo][nombre])
            total = UNIVERSO if grupo == 'universo' else conteos[grupo]
            if len(valores) < 10 or not proteger(total-len(valores)):
                continue
            # P1 y P99 caracterizan colas sin divulgar valores extremos individuales.
            indicadores.append([grupo,nombre,len(valores),total-len(valores),fmt(fmean(valores)),fmt(stdev(valores)),
                                *[fmt(percentil(valores,p)) for p in (.01,.1,.25,.5,.75,.9,.99)],fmt(sum(valores))])
    cols = ['Grupo','Variable','Válidos','Faltantes o inválidos','Media','Desv. estándar','P1','P10','P25','Mediana','P75','P90','P99','Suma']
    with (destino/'indicadores_agregados.csv').open('x', encoding='utf-8-sig', newline='') as f:
        w=csv.writer(f); w.writerow(cols); w.writerows(indicadores)

    def distribucion(grupo, campo):
        from collections import Counter
        grupos = GRUPOS if grupo == 'universo' else (grupo,)
        c = Counter()
        for g in grupos: c.update(categorias[g][campo])
        total = UNIVERSO if grupo == 'universo' else conteos[grupo]
        faltan = total-sum(c.values())
        if not c or not publicable([*c.values(),faltan], 10):
            return None
        return sorted([(etiquetas.get(int(v),'[sin etiqueta]') if t == 's' else v,n) for (t,v),n in c.items()], key=lambda x: -x[1])

    distribuciones = []
    for g in ('universo','A','B'):
        for campo in CAT:
            distrib = distribucion(g,campo)
            if distrib is not None:
                distribuciones.extend([[g,campo,etiqueta,n] for etiqueta,n in distrib])
    with (destino/'categorias_agregadas.csv').open('x', encoding='utf-8-sig', newline='') as f:
        w=csv.writer(f); w.writerow(['grupo','campo','categoria','afiliados']); w.writerows(distribuciones)

    a,b=conteos['A'],conteos['B']
    edad_a=percentil(datos['A']['Edad'],.5); edad_b=percentil(datos['B']['Edad'],.5)
    brecha_a=percentil(datos['A']['brecha_1'],.5)
    brecha_b=percentil(datos['B']['brecha_13'],.5)
    gpm = next((n for etiqueta,n in (distribucion('A','Riesgo') or []) if etiqueta == 'GPM'),None)
    desc_a = dict(distribucion('A','Descapitalizado') or [])
    no_desc = desc_a.get('No')
    hallazgos = [
        f"{a:,} afiliados ({porc(a)}) tienen C inferior a K(1); {b:,} adicionales ({porc(b)}) se encuentran entre K(1) y K(1,3). En conjunto son {selected:,} ({porc(selected)}).",
        f"Fuera del escenario hay {conteos['fuera']:,} ({porc(conteos['fuera'])}); no evaluables: {conteos['no evaluable']:,}. Los cuatro segmentos suman {UNIVERSO:,}.",
        f"La mediana de edad es {edad_a:.0f} años en A y {edad_b:.0f} en B; la diferencia es descriptiva y no implica causalidad.",
        f"La mediana de C − K(1) en A es {fmt(brecha_a)} y la mediana de C − K(1,3) en B es {fmt(brecha_b)} unidades monetarias de origen. No representan déficit de la bolsa.",
    ]
    if gpm is not None:
        hallazgos.append(f"En A, la categoría registrada GPM tiene {gpm:,} afiliados ({100*gpm/a:.2f}% del grupo); su definición institucional debe confirmarse.")
    if no_desc is not None:
        hallazgos.append(f"En A, {no_desc:,} registros aparecen como 'No' en Descapitalizado pese a cumplir C < K(1): revisar definiciones, variables base y reglas institucionales antes de interpretar la discrepancia.")
    riesgos = ('Las unidades monetarias y escalas, la disponibilidad del bono y la ausencia de doble conteo no están verificadas; '
               'las diferencias de capital son exploratorias. Sexo1 no está validado como sexo del titular. '
               'Los campos tipo/estado no demuestran por sí solos derechos ni composición de beneficiarios. '
               'Las variables institucionales de descapitalización y desfinanciación requieren validación operacional. '
               'La ausencia de duplicados y pertenencia a retiro programado provienen de confirmación institucional; no se verificaron con identificadores. '
               'Los valores negativos o no numéricos se excluyen como inválidos; los cálculos no imputan ceros. '
               'El umbral de supresión de 10 es provisional y requiere aprobación. No se prueban causalidad ni sostenibilidad vitalicia.')
    diccionario = [['Capital +Bono','C: hipótesis de capital disponible; validar bono y unidades'],
                   ['capital_necesario_sm','K(1): capital institucional; validar definición'],
                   ['capital_necesario_1.3_sm','K(1,3): capital institucional; selección provisional'],
                   ['capital_necesario_def','Capital requerido asociado a mesada actual, sujeto a confirmación'],
                   ['capital / Capital mes anterior','Saldo y referencia anterior; confirmar fecha y unidades'],
                   ['Edad / mesada / nmesadas','Características registradas; validar unidad y cobertura'],
                   ['Riesgo / Riesgo 3 / Rango de Mesada','Categorías institucionales; validar codificación'],
                   ['tipo1–3 / estado1–3','Características registradas; no inferir titular ni derechos'],
                   ['Descapitalizado / Desfinanciado','Clasificaciones institucionales; contrastar reglas y definiciones']]
    metodologia = [
        ('1. Caracterización','Universo reportado con corte institucional; auditar calidad y presentar el escenario K(1,3) como preliminar.'),
        ('2. Población potencial','Calcular K(2) posteriormente con metodología institucional en Python; evaluar C < K(2). No extrapolar K(1).'),
        ('3. Valoración individual','Valorar 1 SMMLV, mesadas, reajustes, supervivencia del titular y beneficiarios, gastos y descuento durante todo el horizonte vitalicio; contrastar capitales institucionales y datos de beneficiarios.'),
        ('4. Bolsa colectiva','Proyectar capital inicial y aportes, rendimientos, prestaciones, gastos y activos; valorar obligaciones remanentes y respaldo, incluso después del horizonte explícito. La no heredabilidad del saldo requiere validación jurídica; conservar derechos de sobrevivientes.'),
        ('5. Evaluación económica','Comparar retiro programado, aseguradora y bolsa con prestaciones equivalentes; separar efectos de derechos, rentabilidad, gastos, mutualización y respaldo. La mutualización no implica ahorro automático.'),
        ('6. Sensibilidad','Evaluar mortalidad, rentabilidad, descuento, reajuste del SMMLV, gastos y número de mesadas, con parámetros autorizados y escenarios reproducibles.')]
    graficas = []
    def graf(nombre,titulo,filas,unidad):
        (destino/nombre).write_text(figura(titulo,filas,unidad),encoding='utf-8')
        graficas.append(nombre)
    graf('segmentos.svg','Composición del universo — escenario K(1,3)',[(g,conteos[g],COLORES[g]) for g in GRUPOS],'afiliados')
    for variable, titulo in [(CAP[1],'Capital disponible y K(1)'),(CAP[2],'Capital disponible y K(1,3)')]:
        filas=[]
        for g in ('A','B','fuera'):
            filas.extend([(g+' C',sum(datos[g][CAP[0]]),COLORES[g]),(g+' K',sum(datos[g][variable]),COLORES[g])])
        graf('capital_'+('1' if variable==CAP[1] else '13')+'.svg',titulo,filas,'unidades de origen')
    graf('brechas.svg','Brechas agregadas C − K(1,3)',[(g,sum(datos[g]['brecha_13']),COLORES[g]) for g in ('A','B','fuera')],'unidades de origen')
    graf('mesadas.svg','Mesada actual: mediana por segmento',[(g,percentil(datos[g]['mesada'],.5),COLORES[g]) for g in ('A','B','fuera') if len(datos[g]['mesada']) >= 10 and proteger(conteos[g]-len(datos[g]['mesada']))],'unidades de origen por mesada')
    edades = [x for g in GRUPOS for x in datos[g]['Edad']]
    bins = ((0,60),(60,70),(70,80),(80,200))
    counts = [sum(lo<=x<hi for x in edades) for lo,hi in bins]
    if len(edades)==sum(counts) and publicable(counts+[UNIVERSO-len(edades)],10):
        graf('edades.svg','Distribución de edades del universo',[(f'{lo}–{hi-1}',n,COLORES['A']) for (lo,hi),n in zip(bins,counts)],'afiliados')
    riesgo = distribucion('universo','Riesgo')
    if riesgo and len(riesgo)<=12:
        graf('riesgo.svg','Participación por riesgo registrado',[(n,c,COLORES['A']) for n,c in riesgo],'afiliados')
    img = ''.join(f'<figure><img src="{n}" alt="Gráfico agregado"><figcaption>Fuente: base de control de saldos; corte {CORTE}. Variables y unidades pendientes de confirmación institucional.</figcaption></figure>' for n in graficas)
    intro = (f'Universo reportado de {UNIVERSO:,} afiliados en retiro programado, corte {CORTE}; una fila por afiliado y sin duplicados según confirmación institucional. '
             'Datos reales agregados. El escenario K(1,3) es provisional y no representa elegibilidad definitiva ni viabilidad de la bolsa.')
    encabezado = '<!doctype html><html lang="es"><meta charset="utf-8"><title>Avance pensión mutualizada</title>'+ESTILO_HTML+'<style>body{max-width:1100px;margin:auto;padding:30px;line-height:1.5}table{font-size:13px}figure{margin:20px 0}figcaption{font-size:12px}</style><h1>Avance: pensión mutualizada</h1><p>'+escape(intro)+'</p>'
    hallhtml = '<ul>' + ''.join('<li>'+escape(x)+'</li>' for x in hallazgos) + '</ul>'
    methhtml = ''.join('<h3>'+escape(t)+'</h3><p>'+escape(d)+'</p>' for t,d in metodologia)
    (destino/'informe_ejecutivo.html').write_text(encabezado+'<h2>Resultados y hallazgos</h2>'+tabla('Segmentos',['Segmento','Afiliados','% del universo'],seg)+hallhtml+'<h2>Visualizaciones</h2>'+img+'<h2>Ruta metodológica</h2>'+methhtml+'<h2>Decisiones pendientes</h2><p>'+escape(riesgos)+'</p></html>',encoding='utf-8')
    cathtml = ''
    for g in ('universo','A','B'):
        for campo in CAT:
            d=distribucion(g,campo)
            if d is not None:
                cathtml += tabla(g+' — '+campo,['Categoría','Afiliados'],d)
            else:
                cathtml += '<p>'+escape(g+' — '+campo)+': suprimido o no disponible.</p>'
    formulas = 'A: C &lt; K(1); B: K(1) ≤ C &lt; K(1,3); fuera: C ≥ K(1,3); no evaluable: valor faltante, inválido o K(1,3) &lt; K(1). Brecha individual = C − K; brecha agregada = Σ(C − K) en registros evaluables. Los porcentajes de segmentos usan el universo; medias, desviación estándar muestral y percentiles usan válidos por variable, sin imputación.'
    tecnico = (encabezado+'<h2>Metodología</h2><p>'+formulas+'</p>'+methhtml+'<h2>Diccionario y calidad</h2>'+tabla('Variables',['Campo','Interpretación y validación'],diccionario)
               +'<p>Los conteos válidos y faltantes o inválidos se presentan en la tabla siguiente. Cero es válido y no se usa para reemplazar faltantes. No se analizaron cédulas.</p>'
               +tabla('Indicadores y colas de las distribuciones',cols,indicadores)+'<h2>Selección provisional</h2>'+tabla('Conciliación',['Segmento','Afiliados','% del universo'],seg)
               +'<h2>Hallazgos y discrepancias</h2>'+hallhtml+'<h2>Distribuciones categóricas</h2>'+cathtml+'<h2>Gráficos</h2>'+img+'<h2>Limitaciones</h2><p>'+escape(riesgos)+'</p></html>')
    (destino/'informe_tecnico.html').write_text(tecnico,encoding='utf-8')
    contenidos = [
      ('Propósito y pregunta','Evaluar una posible modalidad independiente de pensión mutualizada, sujeta a viabilidad legal y financiera.','Contexto y alcance','La propuesta está en evaluación.'),
      ('Universo y fuente',intro,'Ficha del universo y corte','Es un universo reportado, no una muestra.'),
      ('Criterio de selección','C < K(1,3) es provisional; A: C < K(1); B: K(1) ≤ C < K(1,3).','segmentos.svg','K(1,3) no sustituye a K(2).'),
      ('Composición del escenario',hallazgos[0]+' '+hallazgos[1],'segmentos.svg','Conciliación completa y criterio exploratorio.'),
      ('Edad y riesgo',hallazgos[2]+(' '+hallazgos[4] if gpm is not None else ''),'edades.svg y riesgo.svg','Las diferencias son descriptivas.'),
      ('Capitales y brechas',hallazgos[3],'capital_1.svg, capital_13.svg y brechas.svg','Una comparación de capitales no es déficit de la bolsa.'),
      ('Calidad y alertas',(' '.join(hallazgos[5:]) if len(hallazgos)>5 else riesgos),'Tabla de calidad del informe técnico','Validar clasificaciones, moneda y bono.'),
      ('De K(1,3) a K(2)',metodologia[1][1],'Diagrama de etapas','K(2) requiere metodología actuarial institucional.'),
      ('Valoración individual y sobrevivientes',metodologia[2][1],'Esquema de flujos y supervivencia','Conservar derechos y valorar toda la vida.'),
      ('Bolsa y comparación económica',metodologia[3][1]+' '+metodologia[4][1],'Flujo de activos y obligaciones','Comparar derechos equivalentes y recursos de respaldo.'),
      ('Sensibilidades y próximos pasos',metodologia[5][1]+' Confirmar variables, clasificaciones, capitales y supuestos con el equipo actuarial.','Matriz de decisiones pendientes','No concluir viabilidad ni ahorro antes de modelar.')]
    presentacion = '# Presentación de avance — pensión mutualizada\n\n'+intro+'\n'
    guion = '# Guion de exposición — pensión mutualizada\n\n'
    explicaciones = [
      'La pregunta de hoy es si vale la pena estudiar esta alternativa y qué información necesitamos antes de evaluar su viabilidad.',
      'La institución confirmó la unidad de observación y la ausencia de duplicados; no se usaron documentos para comprobarlo.',
      'Como aún no tenemos el capital para dos salarios mínimos, usamos uno punto tres solo para tener un primer acercamiento.',
      'Esta tabla separa los dos grupos seleccionados, los que quedan fuera del ejercicio y los registros que no se pueden evaluar.',
      'La diferencia de edades no explica por sí sola el resultado. La etiqueta de riesgo debe contrastarse con el diccionario institucional.',
      'La brecha compara capitales individuales con el mismo criterio de la base; no anticipa cuánto respaldo necesitaría una bolsa.',
      'La clasificación institucional y nuestra comparación no coinciden en parte del grupo. Antes de interpretarlo debemos revisar sus reglas.',
      'El siguiente cálculo debe reproducir la metodología de Protección en su entorno; no vamos a multiplicar automáticamente el capital de un salario mínimo.',
      'La valoración tendrá que considerar tanto al titular como a quienes tengan derecho a sobrevivencia y el número de mesadas aplicable.',
      'Luego proyectaremos activos y obligaciones y compararemos las alternativas manteniendo prestaciones y derechos equivalentes.',
      'El siguiente acuerdo es definir responsables, supuestos autorizados y escenarios para cuantificar los riesgos antes de concluir sobre viabilidad.'
    ]
    for i,(titulo,contenido,visual,mensaje) in enumerate(contenidos,1):
        presentacion += f'\n## {i}. {titulo}\n\n- **Contenido:** {contenido}\n- **Visual recomendado:** {visual}.\n- **Mensaje principal:** {mensaje}\n- **Interpretación oral:** Explicar el alcance del dato, sus condiciones y la decisión que permite abordar.\n'
        guion += f'\n## {i}. {titulo}\n\n{explicaciones[i-1]} {contenido}\n'
    (destino/'presentacion_avance.md').write_text(presentacion,encoding='utf-8')
    (destino/'guion_presentacion.md').write_text(guion,encoding='utf-8')
    print('Entregables:', destino)
    for h in hallazgos: print('HALLAZGO:', h)


if __name__ == '__main__':
    raise SystemExit('Este avance histórico fue reemplazado por scripts/escenario_2.py.')
