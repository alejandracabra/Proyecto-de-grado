"""Cobertura agregada; no infiere edades ni derechos de beneficiarios."""
import numpy as np
import pandas as pd
from .ingesta_institucional import NUM, CAT, FECHAS
from .validacion import mascara_capital


def mascaras_validez(df):
    masks={}
    for campo in NUM:
        s=pd.to_numeric(df[campo], errors='coerce')
        v=mascara_capital(df[campo])
        if campo=='Edad': v &= s<=120  # Filtro técnico; requiere validación institucional.
        if campo=='nmesadas': v &= (s>0) & (s%1==0)
        masks[campo]=v
    for campo in CAT:
        v=df[campo].notna() & (df[campo].astype(str).str.strip()!='')
        if campo in ('sexo1','sexo2','sexo3'): v &= df[campo].isin(['F','M'])
        masks[campo]=v
    for campo in FECHAS: masks[campo]=df[campo].fillna(False).astype(bool)
    return masks


def diagnosticar(df):
    masks=mascaras_validez(df)
    grupos={'universo':pd.Series(True,index=df.index),'seleccion_K2':df.seleccion_2,
            'A':df.grupo.eq('A'),'B':df.grupo.eq('B')}
    filas=[]
    for grupo,mask in grupos.items():
        total=int(mask.sum())
        for campo in NUM+CAT+FECHAS:
            if campo in FECHAS:
                presente=df[campo].fillna(False).astype(bool)
            else:
                presente=df[campo].notna() & (df[campo].astype(str).str.strip()!='')
            ok=int((mask & masks[campo]).sum())
            faltante=int((mask & ~presente).sum())
            invalido=int((mask & presente & ~masks[campo]).sum())
            # Suprimir ambos complementos cuando una celda es pequeña.
            if total<10 or any(0<x<10 for x in (ok,faltante,invalido)):
                filas.append([grupo,campo,total,'suprimido','suprimido','suprimido','suprimido'])
            else:
                filas.append([grupo,campo,total,ok,faltante,invalido,round(100*ok/total,2) if total else None])
    cobertura=pd.DataFrame(filas,columns=['poblacion','variable','total','validos_o_presentes','ausentes_o_no_numericos','invalidos_observados','porcentaje'])
    categorias=[]
    for grupo,mask in grupos.items():
        for campo in ('sexo1','sexo2','sexo3','tipo2','estado2','tipo3','estado3','Riesgo','Descapitalizado','Desfinanciado'):
            valores=df.loc[mask,campo].fillna('Sin dato').astype(str).str.strip().replace('','Sin dato')
            counts=valores.value_counts()
            if len(valores)<10 or ((counts>0)&(counts<10)).any(): continue
            categorias.extend([[grupo,campo,str(k),int(v)] for k,v in counts.items()])
        edades=pd.to_numeric(df.loc[mask,'Edad'],errors='coerce')
        edades=pd.cut(edades,bins=[0,60,70,80,121],right=False,
                      labels=['0–59','60–69','70–79','80–120']).astype(object).fillna('No válido o sin dato')
        counts=edades.value_counts()
        if len(edades)>=10 and not ((counts>0)&(counts<10)).any():
            categorias.extend([[grupo,'rango_edad',str(k),int(v)] for k,v in counts.items()])
    distribuciones=pd.DataFrame(categorias,columns=['poblacion','variable','categoria','afiliados'])
    # Son campos mínimos observables, no una valoración actuarial ni prueba de derechos.
    titular=masks['Edad'] & masks['sexo1'] & masks['nmesadas'] & masks['mesada']
    titular &= masks['Capital +Bono'] & masks['capital_necesario_def'] & masks['capital_necesario_sm']
    readiness={'seleccionados':int(df.seleccion_2.sum()),
        'campos_minimos_titular':int((df.seleccion_2 & titular).sum()),
        'valorables_efectivamente':0}
    return cobertura,distribuciones,readiness
