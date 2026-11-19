"""Lectura restringida del XLSX institucional; no incorpora identificadores."""
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET
from xml.sax import make_parser, handler
import pandas as pd

NUM = ('Capital +Bono','capital_necesario_sm','capital_necesario_1.3_sm',
       'capital_necesario_2_sm','capital_necesario_def','Edad','mesada','nmesadas')
CAT = ('Riesgo','Riesgo 3','Rango de Mesada','sexo1','sexo2','sexo3',
       'tipo1','estado1','tipo2','estado2','tipo3','estado3','Descapitalizado','Desfinanciado')
# Los nombres de las fechas no prueban edad ni derecho. Solo se mide cobertura.
FECHAS = ('fn1','fn2','fn3')
PERMITIDOS = NUM + CAT + FECHAS
M = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def indice(ref):
    letras = re.match(r'[A-Z]+', ref).group(); n = 0
    for letra in letras: n = n*26 + ord(letra)-64
    return n-1


class Lector(handler.ContentHandler):
    """Descarta contenido de celdas no autorizadas desde el evento SAX."""
    def __init__(self, columnas):
        super().__init__(); self.columnas=columnas; self.filas=[]; self.referencias=set()
        self.tipos=Counter(); self.col=None; self.tipo=None; self.valor=None; self.en_valor=False; self.fila=None; self.es_cabecera=False

    def startElement(self, name, attrs):
        name=name.split(':')[-1]
        if name=='row':
            self.es_cabecera=attrs.get('r')=='1'; self.fila={}
        elif name=='c' and self.fila is not None and not self.es_cabecera:
            col=indice(attrs.get('r','A1')); self.col=self.columnas.get(col); self.tipo=attrs.get('t','n'); self.valor=None
        elif name=='v' and self.col is not None:
            self.en_valor=True; self.valor=[]

    def characters(self, content):
        if self.en_valor: self.valor.append(content)

    def endElement(self, name):
        name=name.split(':')[-1]
        if name=='v': self.en_valor=False
        elif name=='c':
            if self.col is not None and self.valor:
                value=''.join(self.valor); self.tipos[(self.col,self.tipo)]+=1
                if self.col in NUM:
                    if self.tipo=='n':
                        try: self.fila[self.col]=float(value)
                        except ValueError: pass
                elif self.col in FECHAS:
                    # Solo cobertura, sin conservar fechas individuales.
                    self.fila[self.col] = True
                elif self.tipo=='s':
                    idx=int(value); self.fila[self.col]=('s',idx); self.referencias.add(idx)
                else: self.fila[self.col]=('literal',value)
            self.col=None; self.valor=None; self.en_valor=False
        elif name=='row':
            if not self.es_cabecera: self.filas.append(self.fila)
            self.fila=None


class CadenasSeleccionadas(handler.ContentHandler):
    """Solo retiene textos cuyos índices pertenecen a campos autorizados."""
    def __init__(self, indices):
        super().__init__(); self.indices=indices; self.indice=-1; self.contenido=None; self.resultado={}

    def startElement(self, name, attrs):
        if name.split(':')[-1]=='si':
            self.indice += 1
            self.contenido=[] if self.indice in self.indices else None

    def characters(self, content):
        if self.contenido is not None: self.contenido.append(content)

    def endElement(self, name):
        if name.split(':')[-1]=='si' and self.contenido is not None:
            self.resultado[self.indice]=''.join(self.contenido).strip(); self.contenido=None


def leer_institucional(path=Path('xd.xlsx'), *, universo=95011):
    """Acepta solo los campos de la lista blanca; no usa A ni la cédula B."""
    path=Path(path)
    if path.name.lower() != 'xd.xlsx': raise ValueError('El flujo institucional requiere xd.xlsx')
    with ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        if len(wb.findall(M+'sheets/'+M+'sheet')) != 1 or 'xl/worksheets/sheet1.xml' not in z.namelist():
            raise ValueError('Estructura del libro no admitida')
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _,row in ET.iterparse(f,events=('end',)):
                if row.tag == M+'row':
                    cab={indice(c.attrib['r']):int(c.find(M+'v').text) for c in row.findall(M+'c')
                         if indice(c.attrib['r'])>=2 and c.get('t')=='s' and c.find(M+'v') is not None}
                    break
        def cadenas(indices):
            lector_cadenas=CadenasSeleccionadas(indices)
            parser_cadenas=make_parser(); parser_cadenas.setContentHandler(lector_cadenas)
            with z.open('xl/sharedStrings.xml') as f:
                parser_cadenas.parse(f)
            return lector_cadenas.resultado
        nombres=cadenas(set(cab.values()))
        columnas={col:nombres[i] for col,i in cab.items() if nombres.get(i) in PERMITIDOS}
        for name in PERMITIDOS:
            if list(columnas.values()).count(name)>1: raise ValueError('Columna repetida: '+name)
        lector=Lector(columnas); parser=make_parser(); parser.setContentHandler(lector)
        with z.open('xl/worksheets/sheet1.xml') as f: parser.parse(f)
        etiquetas=cadenas(lector.referencias)
    if len(lector.filas)!=universo: raise ValueError('El total no concilia con el universo institucional')
    for fila in lector.filas:
        for campo in CAT:
            valor=fila.get(campo)
            if valor is not None: fila[campo]=etiquetas.get(valor[1], '') if valor[0]=='s' else valor[1]
    df=pd.DataFrame(lector.filas).reindex(columns=PERMITIDOS)
    df.attrs['tipos_excel']=dict(lector.tipos)
    df.attrs['columnas_presentes']=list(columnas.values())
    return df
