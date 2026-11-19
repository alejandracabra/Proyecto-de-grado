"""Genera agregados del escenario institucional K(2), sin exportar microdatos."""
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
import math
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from visualization.proteccion_style import AZUL, LIMA, AMARILLO, ESTILO_HTML, configurar
from auditoria_local import M, valores_fila

N = 95011
NUM = ['Capital +Bono', 'capital_necesario_sm', 'capital_necesario_1.3_sm',
       'capital_necesario_2_sm', 'capital_necesario_def', 'Edad', 'mesada', 'nmesadas']
CAT = ['Riesgo', 'Riesgo 3', 'Rango de Mesada', 'sexo1', 'sexo2', 'sexo3', 'tipo1', 'estado1', 'tipo2',
       'estado2', 'tipo3', 'estado3', 'Descapitalizado', 'Desfinanciado']
C, K1, K13, K2, KA = NUM[:5]


def leer(path):
    """Lee solamente columnas autorizadas; no lee ni exporta la columna cc."""
    with ZipFile(path) as z:
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _, row in ET.iterparse(f, events=('end',)):
                if row.tag == M+'row':
                    headers = {col: int(v) for col, t, v in valores_fila(row) if t == 's'}
                    break
        labels = {}
        with z.open('xl/sharedStrings.xml') as f:
            i = 0
            for _, e in ET.iterparse(f, events=('end',)):
                if e.tag == M+'si':
                    if i in headers.values(): labels[i] = ''.join(e.itertext()).strip()
                    i += 1
                    e.clear()
        columns = {col: labels.get(i) for col, i in headers.items() if labels.get(i) in NUM+CAT}
        if any(list(columns.values()).count(x) != 1 for x in (C,K1,K13,K2)):
            raise ValueError('Columnas de capital ausentes o repetidas')
        records, referenced, tipos_k2 = [], set(), Counter()
        numeros_fila, faltantes_numero, duplicados_numero = set(), 0, 0
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _, row in ET.iterparse(f, events=('end',)):
                if row.tag != M+'row': continue
                if row.get('r') == '1': row.clear(); continue
                # La columna A no tiene encabezado. Solo se cuenta la unicidad;
                # sus valores no salen del proceso ni se incorporan al DataFrame.
                numeros = list(valores_fila(row, {0}))
                if not numeros:
                    faltantes_numero += 1
                else:
                    _, tipo_numero, valor_numero = numeros[0]
                    clave = (tipo_numero, valor_numero)
                    if clave in numeros_fila: duplicados_numero += 1
                    numeros_fila.add(clave)
                record = {}
                for col, typ, val in valores_fila(row, columns):
                    name = columns[col]
                    if name == K2: tipos_k2[typ] += 1
                    if name in NUM:
                        if typ == 'n':
                            try: record[name] = float(val)
                            except ValueError: record[name] = np.nan
                        else: record[name] = np.nan
                    elif typ == 's':
                        record[name] = int(val); referenced.add(int(val))
                    else: record[name] = val
                records.append(record); row.clear()
        labels = {}
        with z.open('xl/sharedStrings.xml') as f:
            i = 0
            for _, e in ET.iterparse(f, events=('end',)):
                if e.tag == M+'si':
                    if i in referenced: labels[i] = ''.join(e.itertext()).strip()
                    i += 1; e.clear()
    df = pd.DataFrame(records)
    if len(df) != N: raise ValueError('El universo no concilia con 95.011')
    df.attrs['tipos_k2'] = dict(tipos_k2)
    df.attrs['control_numero_fila'] = {'presentes': len(records)-faltantes_numero,
        'faltantes': faltantes_numero, 'valores_distintos': len(numeros_fila),
        'repeticiones': duplicados_numero}
    for col in CAT:
        if col in df: df[col] = df[col].map(lambda x: labels.get(x, x) if pd.notna(x) else 'Sin dato')
    return df


def clasificar(df):
    c, k1, k13, k2 = (pd.to_numeric(df[x], errors='coerce') for x in (C,K1,K13,K2))
    valid = np.isfinite(c) & (c >= 0) & np.isfinite(k1) & (k1 > 0) & np.isfinite(k13) & (k13 > 0) & np.isfinite(k2) & (k2 > 0)
    valid &= (k1 <= k13) & (k13 <= k2)
    df['grupo'] = np.select([~valid, c < k1, c < k2], ['no evaluable','A','B'], default='fuera')
    for name,k in [('1',k1),('13',k13),('2',k2)]:
        # Base común para una transición mutuamente excluyente.
        df['seleccion_'+name] = valid & (c < k)
        df['brecha_'+name] = (c-k).where(valid)
    return valid


def ejecutar():
    df = leer(Path('xd.xlsx')); valid = clasificar(df)
    for name,denom in [('K1',K1),('K13',K13),('Kdef',KA)]:
        if denom in df:
            df['razon_K2_'+name] = (df[K2] / df[denom]).where(df[denom] > 0)
    out = Path('reports/generated') / ('escenario_2_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True, exist_ok=False)
    def guardar(frame, nombre): frame.to_csv(out/(nombre+'.csv'), index=False, encoding='utf-8-sig')
    k2 = pd.to_numeric(df[K2], errors='coerce')
    calidad = pd.DataFrame([
        ['registros',len(df)], ['tipo_excel_numerico',df.attrs['tipos_k2'].get('n',0)],
        ['tipo_excel_otros',sum(v for k,v in df.attrs['tipos_k2'].items() if k!='n')],
        ['faltante_o_no_numerico',int(k2.isna().sum())], ['no_finito',int((k2.notna() & ~np.isfinite(k2)).sum())],
        ['cero',int((k2==0).sum())], ['negativo',int((k2<0).sum())],
        ['numerico_positivo_finito',int((np.isfinite(k2) & (k2>0)).sum())],
        ['K2_inferior_K1',int((k2<df[K1]).sum())], ['K2_inferior_K13',int((k2<df[K13]).sum())]], columns=['control','resultado'])
    guardar(calidad,'calidad_K2')
    control_numero = df.attrs['control_numero_fila']
    guardar(pd.DataFrame(list(control_numero.items()), columns=['control','resultado']), 'control_numero_fila')
    counts = df.grupo.value_counts().reindex(['A','B','fuera','no evaluable'], fill_value=0)
    assert counts.sum() == N
    seg = pd.DataFrame({'segmento':counts.index,'afiliados':counts.values,'porcentaje_universo':counts.values/N*100})
    guardar(seg,'segmentos')
    escenarios=[]
    for name,k in [('1',K1),('13',K13),('2',K2)]:
        s=df['seleccion_'+name]; d=df.loc[s]
        escenarios.append({'escenario':name,'seleccionados':int(s.sum()),'porcentaje_universo':100*s.sum()/N,
          'fuera':int((valid & ~s).sum()),'no_evaluables':int((~valid).sum()),
          'capital_disponible_agregado':d[C].sum(min_count=1),'capital_requerido_agregado':d[k].sum(min_count=1),
          'mediana_disponible':d[C].median(),'mediana_requerido':d[k].median()})
    esc=pd.DataFrame(escenarios); guardar(esc,'comparacion_escenarios')
    trans=pd.DataFrame({'transicion':['Seleccionados K(1)','Adicionales K(1,3)','Adicionales K(2)','Fuera de los tres','No evaluables'],
      'afiliados':[int(df.seleccion_1.sum()),int((df.seleccion_13 & ~df.seleccion_1).sum()),int((df.seleccion_2 & ~df.seleccion_13).sum()),int((valid & ~df.seleccion_2).sum()),int((~valid).sum())]})
    assert trans.afiliados.sum()==N
    guardar(trans,'transiciones')
    populations={'universo':df,'seleccion_K2':df[df.seleccion_2], 'A':df[df.grupo=='A'],'B':df[df.grupo=='B']}
    populations.update({'seleccion_K'+x:df[df['seleccion_'+x]] for x in ('1','13')})
    df['rango_edad'] = pd.cut(pd.to_numeric(df['Edad'],errors='coerce'), bins=[0,60,70,80,120], right=False, labels=['0–59','60–69','70–79','80–119'])
    ages=[]
    for name,mask in [('universo',pd.Series(True,index=df.index)),('K1',df.seleccion_1),('K13',df.seleccion_13),('K2',df.seleccion_2),('A',df.grupo=='A'),('B',df.grupo=='B')]:
        counts_age=df.loc[mask,'rango_edad'].astype(object).fillna('Sin dato o fuera de rango').value_counts()
        if not ((counts_age>0)&(counts_age<10)).any(): ages.extend([[name,str(x),int(n)] for x,n in counts_age.items()])
    guardar(pd.DataFrame(ages,columns=['poblacion','rango_edad','afiliados']),'edades')
    stats=[]
    for group,d in populations.items():
        for col in NUM+['brecha_1','brecha_13','brecha_2','razon_K2_K1','razon_K2_K13','razon_K2_Kdef']:
            if col not in d: continue
            v=pd.to_numeric(d[col],errors='coerce'); v=v[np.isfinite(v)]
            if len(v)<10 or 0 < len(d)-len(v)<10: continue
            stats.append([group,col,len(v),len(d)-len(v),v.mean(),v.std(),*[v.quantile(p) for p in (.01,.1,.25,.5,.75,.9,.99)],v.sum(),int((v<0).sum()),int((v==0).sum()),int((v>0).sum())])
    st=pd.DataFrame(stats,columns=['poblacion','variable','validos','faltantes_o_invalidos','media','desviacion','p01','p10','p25','mediana','p75','p90','p99','suma','negativos','ceros','positivos']); guardar(st,'estadisticos')
    categories=[]
    for group,d in populations.items():
        for col in CAT:
            if col not in d: continue
            counts=d[col].fillna('Sin dato').value_counts()
            if (counts<10).any(): continue
            categories.extend([[group,col,str(label),int(n)] for label,n in counts.items()])
    cats=pd.DataFrame(categories,columns=['poblacion','variable','categoria','afiliados']); guardar(cats,'categorias')
    cross=[]
    for scenario in ('1','13','2'):
        for flag in ('Descapitalizado','Desfinanciado'):
            if flag not in df: continue
            status=np.where(~valid,'No evaluable',np.where(df['seleccion_'+scenario],'Seleccionado','Fuera'))
            ct=pd.crosstab(status,df[flag].fillna('Sin dato'))
            if ((ct>0)&(ct<10)).any().any(): continue
            for status,row in ct.iterrows():
                for label,n in row.items(): cross.append([scenario,flag,status,label,int(n)])
    cr=pd.DataFrame(cross,columns=['escenario','bandera','seleccion','valor','afiliados']); guardar(cr,'cruces_banderas')
    configurar()
    # La fuente institucional no siempre está instalada en el equipo local.
    from matplotlib import font_manager
    if not any(f.name == 'Sura Sans' for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.family'] = ['DejaVu Sans']
    def bar(name,title,labels,values,unidad='Afiliados'):
        fig,ax=plt.subplots(figsize=(8,4)); ax.bar([str(x) for x in labels],values,color=[AZUL,LIMA,AMARILLO]*((len(values)+2)//3)); ax.set_title(title); ax.set_ylabel(unidad); fig.tight_layout()
        for ext in ('png','svg'): fig.savefig(out/(name+'.'+ext))
        plt.close(fig)
    bar('escenarios','Población seleccionada por escenario',esc.escenario,esc.seleccionados)
    bar('grupos','Grupos de selección',seg.segmento,seg.afiliados)
    for col,title in [('Edad','Edad'),('mesada','Mesada actual'),('brecha_1','Brecha frente a K(1)'),('brecha_13','Brecha frente a K(1,3)'),('brecha_2','Brecha frente a K(2)')]:
        fig,ax=plt.subplots(figsize=(8,4))
        for group,color in [('A',AZUL),('B',LIMA)]:
            v=pd.to_numeric(df.loc[df.grupo==group,col],errors='coerce').dropna(); v=v[np.isfinite(v)]
            if len(v): ax.hist(v.clip(v.quantile(.01),v.quantile(.99)),bins=25,alpha=.6,label=group,color=color)
        ax.set_title(title+' (colas recortadas a P1–P99)'); ax.set_xlabel('Pesos colombianos (COP)' if col != 'Edad' else 'Años'); ax.set_ylabel('Afiliados'); ax.legend(); fig.tight_layout()
        for ext in ('png','svg'): fig.savefig(out/(col+'.'+ext))
        plt.close(fig)
    for name,k in [('1',K1),('13',K13),('2',K2)]:
        d=df[df['seleccion_'+name]]; bar('capital_'+name,'Capital agregado: seleccionados K('+name+')',['Disponible','Requerido'],[d[C].sum(),d[k].sum()],'Pesos colombianos (COP)')
    for col in ('Riesgo','Descapitalizado','Desfinanciado','sexo1'):
        v=cats[(cats.poblacion=='seleccion_K2')&(cats.variable==col)]
        if len(v): bar(col,('Sexo del titular' if col=='sexo1' else col)+' — selección K(2)',v.categoria,v.afiliados)
    if not cr.empty:
        fig,ax=plt.subplots(figsize=(8,4))
        for flag,color in [('Descapitalizado',AZUL),('Desfinanciado',LIMA)]:
            values=[int(cr[(cr.escenario==x)&(cr.bandera==flag)&(cr.seleccion=='Seleccionado')&(cr.valor=='No')].afiliados.sum()) for x in ('1','13','2')]
            ax.plot(['K(1)','K(1,3)','K(2)'],values,marker='o',label=flag+' = No',color=color)
        ax.set_title('Seleccionados con bandera institucional No'); ax.set_ylabel('Afiliados'); ax.legend(); fig.tight_layout()
        for ext in ('png','svg'): fig.savefig(out/('banderas_escenarios.'+ext))
        plt.close(fig)
    control_texto=(f"La columna A sin encabezado tiene {control_numero['presentes']:,} valores presentes, "
        f"{control_numero['faltantes']:,} faltantes y {control_numero['repeticiones']:,} repeticiones. "
        'El número se utiliza exclusivamente para verificar unicidad de valores; no demuestra por sí solo unicidad de afiliados.')
    caution=('Las magnitudes monetarias están expresadas en pesos colombianos (COP), según lo confirmado por el usuario. '
       'Capital +Bono es una aproximación sujeta a confirmación institucional de disponibilidad y doble conteo. '
       'Se exige orden K(1) ≤ K(1,3) ≤ K(2) para la base común; los demás registros son no evaluables y no se corrigen. '
       'La pertenencia a retiro programado y las definiciones de las banderas requieren confirmación institucional. '
       'Las sumas de brechas individuales no son déficit actuarial de una bolsa. No se demuestra viabilidad ni ahorro.')
    summary=(f"K(2): {int(df.seleccion_2.sum()):,} seleccionados ({100*df.seleccion_2.sum()/N:.2f}%); "
      f"A {int((df.grupo=='A').sum()):,}; B {int((df.grupo=='B').sum()):,}. "
      f"K(1,3): {int(df.seleccion_13.sum()):,}; incremento {int(df.seleccion_2.sum()-df.seleccion_13.sum()):,}.")
    discrepancy = ''
    if 'Descapitalizado' in df and 'Desfinanciado' in df:
        discrepancy = (f"Entre los seleccionados con K(1), {int((df.seleccion_1 & (df.Descapitalizado=='No')).sum()):,} tienen bandera de descapitalización No. "
            f"Con K(2), {int((df.seleccion_2 & (df.Descapitalizado=='No')).sum()):,} tienen descapitalización No y "
            f"{int((df.seleccion_2 & (df.Desfinanciado=='No')).sum()):,} tienen desfinanciación No. "
            'No se interpretan como errores: confirmar definiciones, fecha, capitales y parámetros de cada regla institucional.')
    selected=df[df.seleccion_2]
    sexo_seleccion=cats[(cats.poblacion=='seleccion_K2') & (cats.variable=='sexo1')]
    sexo_texto = '; '.join(f"{r.categoria}: {r.afiliados:,}" for r in sexo_seleccion.itertuples()) if not sexo_seleccion.empty else 'distribución suprimida o no disponible'
    character=(f"La mediana de edad de los seleccionados es {selected['Edad'].median():.1f} años; "
      f"la del universo es {df['Edad'].median():.1f} años. "
      f"Sexo del titular (sexo1), seleccionado: {sexo_texto}. "
      'Las distribuciones de riesgo, mesadas y beneficiarios figuran en las tablas de categorías; sus definiciones deben confirmarse.')
    methodology=('1. Caracterización: universo informado de 95.011 afiliados en retiro programado, corte 30 de septiembre de 2026.\n'
      '2. Selección preliminar: C < K(2) institucional; K(1,3) es referencia intermedia.\n'
      '3. Valoración individual: prestación preliminar de 1 SMMLV y prestaciones de sobrevivientes; edad, sexo del titular (sexo1), beneficiarios (sexo2 y sexo3), mortalidad, número de mesadas, reajustes, descuento y gastos.\n'
      '4. Mutualización: integrar los recursos de participantes y asumir conjuntamente el riesgo de longevidad.\n'
      '5. Proyección: capital inicial, aportes, rendimientos, mesadas, sobrevivientes, gastos, activos, obligaciones y necesidades de respaldo.\n'
      '6. Evaluación económica: comparar con retiro programado y renta vitalicia, sin presuponer eficiencias o ahorros.\n')
    definitions={C:'capital disponible provisional; validar disponibilidad del bono y doble conteo', K1:'capital requerido para 1 SMMLV', K13:'capital requerido para 1,3 SMMLV', K2:'capital institucional requerido para 2 SMMLV', KA:'capital requerido en la cuenta de ahorro individual para financiar la mesada actual, confirmado por el usuario', 'mesada':'mesada actual', 'sexo1':'sexo del titular, confirmado por el usuario', 'sexo2':'sexo del siguiente beneficiario, confirmado por el usuario', 'sexo3':'sexo del tercer miembro registrado, confirmado por el usuario'}
    dictionary='\n'.join([f'- {x}: {definitions.get(x, "variable original; definición institucional por confirmar")}.' for x in NUM+CAT])
    actual='capital_necesario_def es el capital requerido en la cuenta de ahorro individual para financiar la mesada vigente, según confirmación del usuario.'
    (out/'metodologia.md').write_text('# Metodología\n\n'+methodology+'\n'+actual+'\n\n'+control_texto+'\n\n'+caution,encoding='utf-8')
    (out/'diccionario_variables.md').write_text('# Diccionario\n\n'+dictionary+'\n\nUnidad monetaria: pesos colombianos (COP). '+actual+'\n\n'+control_texto,encoding='utf-8')
    (out/'hallazgos.md').write_text('# Hallazgos\n\n'+summary+'\n\n'+character+'\n\n'+discrepancy+'\n\n'+actual+'\n\n'+control_texto+'\n\n'+caution,encoding='utf-8')
    (out/'presentacion_avance.md').write_text('# Avance\n\n'+summary+'\n\n'+character+'\n\n'+actual+'\n\n'+control_texto+'\n\n'+methodology+'\n'+caution,encoding='utf-8')
    (out/'guion_exposicion.md').write_text('# Guion de exposición\n\nPresentar el universo y el criterio preliminar. '+summary+' '+character+' Explicar que el umbral de selección es 2 SMMLV y la prestación preliminar es 1 SMMLV. Explicar los pasos de proyección y las limitaciones.\n\n'+actual+'\n\n'+control_texto+'\n\n'+caution,encoding='utf-8')
    base='<!doctype html><html lang="es"><meta charset="utf-8">'+ESTILO_HTML+'<h1>Selección preliminar con K(2)</h1><p>'+escape(summary)+'</p><p>'+escape(character)+'</p><p>'+escape(discrepancy)+'</p><p>'+escape(actual)+'</p><p>'+escape(control_texto)+'</p><p>'+escape(caution)+'</p>'
    (out/'ejecutivo.html').write_text(base+seg.to_html(index=False)+esc.to_html(index=False)+'<img src="escenarios.svg" alt="Escenarios"><img src="grupos.svg" alt="Grupos"></html>',encoding='utf-8')
    (out/'tecnico.html').write_text(base+'<h2>Calidad K(2)</h2>'+calidad.to_html(index=False)+'<h2>Escenarios</h2>'+esc.to_html(index=False)+'<h2>Transiciones</h2>'+trans.to_html(index=False)+'<h2>Estadísticos</h2>'+st.to_html(index=False)+'<h2>Categorías</h2>'+cats.to_html(index=False)+'<h2>Cruces</h2>'+cr.to_html(index=False)+'</html>',encoding='utf-8')
    print('Resultados:',out); print(summary); print(esc.to_string(index=False)); print(trans.to_string(index=False))


if __name__=='__main__': ejecutar()
