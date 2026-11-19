"""Etapas 1 y 2: ejecución institucional local, únicamente resultados agregados."""
from datetime import datetime
from html import escape
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from actuarial.ingesta_institucional import leer_institucional, NUM, CAT, FECHAS
from actuarial.seleccion import C,K1,K13,K2,clasificar_escenarios,capital_valido
from actuarial.diagnostico import diagnosticar, mascaras_validez
from visualization.proteccion_style import AZUL,LIMA,AMARILLO,ESTILO_HTML,configurar

N=95011


def publicable(conteos):
    return all(n == 0 or n >= 10 for n in conteos)


def ejecutar():
    df=leer_institucional(Path('xd.xlsx'))
    clas=clasificar_escenarios(df)
    for columna in clas: df[columna]=clas[columna]
    destino=Path('reports/generated')/('etapa_2_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    destino.mkdir(parents=True,exist_ok=False)
    def guardar(frame,name): frame.to_csv(destino/(name+'.csv'),index=False,encoding='utf-8-sig')
    counts=df.grupo.value_counts().reindex(['A','B','seleccionado sin grupo','fuera','no evaluable'],fill_value=0)
    if counts.sum()!=N: raise ValueError('La clasificación interna no concilia')
    if not publicable(counts): raise ValueError('Segmentos requieren supresión complementaria antes de generar el informe')
    seg=pd.DataFrame({'segmento':counts.index,'afiliados':counts.values,'porcentaje_universo':100*counts.values/N})
    guardar(seg,'segmentos')
    escenarios=[]
    for name,k in [('1',K1),('13',K13),('2',K2)]:
        sel=df['seleccion_'+name]; valid=df['evaluables_'+name]; d=df.loc[sel]
        row=[name,int(sel.sum()),int((valid & ~sel).sum()),int((~valid).sum())]
        if not publicable(row[1:]): raise ValueError('Escenario requiere supresión complementaria')
        escenarios.append(row+[float(d[C].sum(min_count=1)),float(d[k].sum(min_count=1)),float(d[C].median()),float(d[k].median())])
    esc=pd.DataFrame(escenarios,columns=['escenario','seleccionados','fuera','no_evaluables','capital_disponible_COP','capital_requerido_COP','mediana_C_COP','mediana_K_COP'])
    esc['porcentaje_universo']=100*esc.seleccionados/N; guardar(esc,'escenarios')
    comparable=df.evaluables_1 & df.evaluables_13 & df.evaluables_2
    orden=comparable & ~df.orden_inconsistente
    estados=np.select([~comparable,comparable & df.orden_inconsistente,orden & df.seleccion_1,
        orden & df.seleccion_13,orden & df.seleccion_2],
        ['no comparable','orden inconsistente','seleccionado K1','adicional K13','adicional K2'],default='fuera de los tres')
    trans=pd.Series(estados).value_counts().reindex(['seleccionado K1','adicional K13','adicional K2','fuera de los tres','orden inconsistente','no comparable'],fill_value=0)
    if trans.sum()!=N or not publicable(trans): raise ValueError('Transiciones requieren supresión o no concilian')
    trans=pd.DataFrame({'transicion':trans.index,'afiliados':trans.values}); guardar(trans,'transiciones')
    quality=[]
    for campo in [C,K1,K13,K2,'capital_necesario_def']:
        serie=pd.to_numeric(df[campo],errors='coerce'); valid=capital_valido(df[campo])
        grupos=[int(valid.sum()),int(serie.isna().sum()),int((serie.notna() & ~np.isfinite(serie)).sum()),int((serie<0).sum()),int((serie==0).sum())]
        if publicable(grupos): quality.append([campo]+grupos)
    qa=pd.DataFrame(quality,columns=['variable','validos','faltantes_o_no_numericos','no_finitos','negativos','ceros']); guardar(qa,'calidad_capitales')
    inconsistent=int(df.orden_inconsistente.sum()); comparable_n=int(df.orden_comparable.sum())
    if not publicable([inconsistent,comparable_n-inconsistent,N-comparable_n]): raise ValueError('Control de orden requiere supresión')
    orden_df=pd.DataFrame([['comparables',comparable_n],['orden_inconsistente',inconsistent],['no_comparables',N-comparable_n]],columns=['control','afiliados']); guardar(orden_df,'orden_capitales')
    cobertura,categorias,readiness=diagnosticar(df)
    guardar(cobertura,'cobertura_actuarial'); guardar(categorias,'categorias')
    cruces=[]
    for escenario in ('1','13','2'):
        estado=np.select([~df['evaluables_'+escenario],df['seleccion_'+escenario]],['no evaluable','seleccionado'],default='fuera')
        for bandera in ('Descapitalizado','Desfinanciado'):
            tabla=pd.crosstab(estado,df[bandera].fillna('Sin dato'))
            if not publicable(tabla.to_numpy().ravel()): continue
            for estado_grupo,fila in tabla.iterrows():
                for valor,n in fila.items(): cruces.append([escenario,bandera,estado_grupo,valor,int(n)])
    cruces=pd.DataFrame(cruces,columns=['escenario','bandera','seleccion','valor','afiliados']); guardar(cruces,'cruces_banderas')
    selected=int(df.seleccion_2.sum()); sufficient=readiness['campos_minimos_titular']
    if not publicable([sufficient,selected-sufficient]):
        sufficient='suprimido por confidencialidad'
    indicadores=pd.DataFrame([['elegibilidad preliminar K2',selected],['campos mínimos observables del titular',sufficient],
        ['valoración actuarial efectiva',0]],columns=['indicador','afiliados']); guardar(indicadores,'preparacion')
    stats=[]
    validaciones=mascaras_validez(df)
    for grupo,mask in [('universo',pd.Series(True,index=df.index)),('seleccion_K2',df.seleccion_2),('A',df.grupo=='A'),('B',df.grupo=='B')]:
        for campo in NUM+('brecha_1','brecha_13','brecha_2'):
            poblacion=mask & validaciones[campo] if campo in validaciones else mask
            v=pd.to_numeric(df.loc[poblacion,campo],errors='coerce'); v=v[np.isfinite(v)]
            if len(v)<10 or not publicable([len(v),int(mask.sum())-len(v)]): continue
            stats.append([grupo,campo,len(v),v.mean(),v.std(),v.quantile(.1),v.median(),v.quantile(.9)])
    stats=pd.DataFrame(stats,columns=['poblacion','variable','n','media','desviacion','p10','mediana','p90']); guardar(stats,'estadisticos')
    anterior=Path('reports/generated/escenario_2_20261119_083002_181850/segmentos.csv')
    comparacion='No se encontró antecedente local para comparar.'
    reglas_equivalentes=bool(comparable.all()) and not bool(df.orden_inconsistente.any()) and all(bool((df[c]>0).all()) for c in (K1,K13,K2))
    if anterior.exists() and reglas_equivalentes:
        prev=pd.read_csv(anterior).set_index('segmento')['afiliados']
        coinciden=all(int(prev.get(g,-1))==int(counts[g]) for g in ('A','B','fuera','no evaluable'))
        comparacion='Comparación de conteos con la ejecución anterior, bajo reglas equivalentes: '+('coincide.' if coinciden else 'difiere; revisar cambios de datos y criterios.')
    # Datos de beneficiarios son descriptivos, no prueban existencia de derecho.
    advertencia=('Cada fila corresponde a un afiliado, sin duplicados, según confirmación institucional; '
       'se cuentan filas y no se usa la primera columna ni la cédula. COP. Capital +Bono es el capital disponible confirmado. '
       'K(1,3) no condiciona selección K(2); el orden entre capitales se controla por separado. '
       'Cero es válido; faltantes, no numéricos, negativos y no finitos son no evaluables para cada par correspondiente. '
       'Una selección sin K(1) válido permanece seleccionada pero sin grupo A/B. '
       'Sexo, tipo y estado registrados no demuestran derechos de sobrevivencia. '
       'Las brechas individuales y su suma no son déficit de una bolsa. No se demuestra viabilidad ni ahorro.')
    metodologia=('''# Metodología de valoración individual — pendiente de parametrización

La prestación preliminar es 1 SMMLV y el criterio de selección es C < K(2).
Para cada periodo t y estado conjunto s (titular y beneficiarios), sea p_i,s(t)
su probabilidad conjunta, obtenida de tablas y supuestos institucionales, y sean
b_T,i,s(t) y b_S,i,s(t) los pagos en COP, tras aplicar calendario de mesadas,
reajustes, derechos, sustitución y concurrencia. Para cada t, Σ_s p_i,s(t)=1.
No se presume independencia entre vidas ni se asignan mesadas completas a cada beneficiario.

VPA_T,i = Σ_t (1+j)^(-t) Σ_s p_i,s(t) b_T,i,s(t)

VPA_S,i = Σ_t (1+j)^(-t) Σ_s p_i,s(t) b_S,i,s(t)

VPA_obligaciones,i = VPA_T,i + VPA_S,i. Los gastos esperados se descuentan
por separado; el total con gastos suma ese valor. El motor recibe distribuciones
conjuntas exhaustivas y pagos explícitos para cada periodo; supone pagos al final
del periodo y una tasa efectiva periódica constante suministrada. La unidad de
periodo, calendario, mesadas adicionales, reajustes y horizonte deben definirse
antes de construir sus entradas. Las probabilidades deben ser coherentes entre
periodos y con las tablas y reglas aprobadas; el motor valida rango y suma por
periodo, no demuestra por sí mismo esa coherencia actuarial.

Faltan tablas de mortalidad y su fuente, tasa y convención de descuento,
calendario y fecha de valoración confirmados, trayectoria SMMLV y reajustes,
horizonte y cola residual, edades o fechas válidas de beneficiarios, derechos,
porcentajes, reglas de concurrencia y extinción, dependencia entre vidas y gastos.
Sin ellos se bloquea la valoración efectiva. Los campos fn1, fn2 y fn3 se
contabilizan solo como presencia y no se interpretan como fechas de nacimiento.
El motor implementa la agregación matemática, no genera probabilidades de
supervivencia ni decide derechos. Requiere revisión actuarial y jurídica.
''')
    prep=('''# Diagnóstico de preparación actuarial

La selección por capital, la cobertura de campos y la valoración efectiva son
conceptos distintos. Los campos mínimos de titular cuentan edad entre 0 y 120
(filtro técnico provisional), sexo F/M, número entero positivo de mesadas,
mesada y capitales disponibles válidos. El conteo es un control de cobertura,
no garantiza que los datos sean adecuados actuarialmente ni acredita derechos.
La valoración efectiva está bloqueada para todos mientras falten parámetros y
reglas; el cero no indica que ninguno pueda valorarse una vez se suministren.

Las variables sexo2/sexo3, tipo2/tipo3 y estado2/estado3 se describen como
registros disponibles, sin asumir parentesco, edad o derecho a sobrevivencia.
La interpretación y completitud de los campos fn requiere confirmación; no se
calculan edades de beneficiarios. Solicitar a Protección el diccionario y fecha de
corte de beneficiarios, edades/fechas válidas, relaciones, condiciones y derechos,
reglas de sustitución y concurrencia y todos los parámetros de la metodología.
Las tablas cobertura_actuarial.csv y categorias.csv presentan cobertura por
universo, seleccionados, A y B; tablas pequeñas se suprimen preventivamente.
''')
    (destino/'metodologia_valoracion.md').write_text(metodologia,encoding='utf-8')
    (destino/'diagnostico_actuarial.md').write_text(prep+'\n'+advertencia,encoding='utf-8')
    definiciones={C:'capital disponible institucional en COP',K1:'capital requerido para 1 SMMLV',K13:'capital requerido para 1,3 SMMLV',K2:'capital requerido para 2 SMMLV','capital_necesario_def':'capital requerido para la mesada actual',
        'Edad':'edad del titular; confirmar convención','sexo1':'sexo del titular','sexo2':'sexo del siguiente beneficiario','sexo3':'sexo del tercer miembro registrado','mesada':'mesada actual COP','nmesadas':'mesadas anuales'}
    dic='\n'.join('- '+x+': '+definiciones.get(x,'cobertura observada; significado o derechos pendientes de confirmación') for x in NUM+CAT+FECHAS)
    (destino/'diccionario.md').write_text('# Diccionario de variables\n\n'+dic,encoding='utf-8')
    configurar()
    from matplotlib import font_manager
    if not any(x.name=='Sura Sans' for x in font_manager.fontManager.ttflist): plt.rcParams['font.family']=['DejaVu Sans']
    fig,ax=plt.subplots(figsize=(7,4)); ax.bar(['K(1)','K(1,3)','K(2)'],esc.seleccionados,color=[AZUL,LIMA,AMARILLO]); ax.set_ylabel('Afiliados'); ax.set_title('Seleccionados por escenario'); fig.tight_layout()
    for ext in ('png','svg'): fig.savefig(destino/('escenarios.'+ext))
    plt.close(fig)
    for variable,titulo in [('sexo1','Sexo del titular'),('Riesgo','Riesgo'),('rango_edad','Rango de edad')]:
        v=categorias[(categorias.poblacion=='seleccion_K2') & (categorias.variable==variable)]
        if v.empty: continue
        fig,ax=plt.subplots(figsize=(8,4)); ax.bar(v.categoria,v.afiliados,color=AZUL); ax.set_title(titulo+' — seleccionados K(2)'); ax.set_ylabel('Afiliados'); ax.tick_params(axis='x',rotation=20); fig.tight_layout()
        for ext in ('png','svg'): fig.savefig(destino/(variable+'.'+ext))
        plt.close(fig)
    resumen=(f'Universo {N:,}; seleccionados K(2) {selected:,} ({100*selected/N:.2f}%); '
       f'A {int(counts["A"]):,}; B {int(counts["B"]):,}; seleccionados sin grupo {int(counts["seleccionado sin grupo"]):,}; '
       f'fuera {int(counts["fuera"]):,}; no evaluables {int(counts["no evaluable"]):,}. '
       f'Campos mínimos observables de titular: {sufficient}; valoración efectiva bloqueada para todos.')
    tabla=lambda x:x.to_html(index=False,escape=True,border=0)
    inicio='<!doctype html><html lang="es"><meta charset="utf-8">'+ESTILO_HTML+'<h1>Selección K(2) y preparación actuarial</h1><p>'+escape(resumen)+'</p><p>'+escape(advertencia)+'</p><p>'+escape(comparacion)+'</p>'
    cobertura_beneficiarios=cobertura[(cobertura.poblacion=='seleccion_K2') & cobertura.variable.isin(['sexo2','sexo3','tipo2','tipo3','estado2','estado3','fn2','fn3'])]
    demografia=categorias[(categorias.poblacion=='seleccion_K2') & categorias.variable.isin(['sexo1','Riesgo','rango_edad'])]
    (destino/'ejecutivo.html').write_text(inicio+tabla(seg)+tabla(esc)+'<img src="escenarios.svg" alt="Escenarios"><h2>Caracterización disponible</h2>'+tabla(demografia)+'<p>Las distribuciones con celdas pequeñas se suprimen.</p><h2>Información registrada de beneficiarios</h2>'+tabla(cobertura_beneficiarios)+'<p>'+escape(prep)+'</p></html>',encoding='utf-8')
    (destino/'tecnico.html').write_text(inicio+'<h2>Calidad</h2>'+tabla(qa)+'<h2>Orden</h2>'+tabla(orden_df)+'<h2>Escenarios</h2>'+tabla(esc)+'<h2>Transiciones</h2>'+tabla(trans)+'<h2>Estadísticos</h2>'+tabla(stats)+'<h2>Cobertura</h2>'+tabla(cobertura)+'<h2>Categorías</h2>'+tabla(categorias)+'<h2>Banderas institucionales</h2>'+tabla(cruces)+'<h2>Preparación</h2><pre>'+escape(prep)+'</pre><h2>Metodología</h2><pre>'+escape(metodologia)+'</pre></html>',encoding='utf-8')
    (destino/'hallazgos.md').write_text('# Hallazgos\n\n'+resumen+'\n\n'+comparacion+'\n\n'+advertencia,encoding='utf-8')
    print('Resultados:',destino); print(resumen); print(comparacion); print(esc.to_string(index=False)); print(orden_df.to_string(index=False))


if __name__=='__main__': ejecutar()
