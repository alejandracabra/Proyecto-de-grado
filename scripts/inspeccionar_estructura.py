"""Inspección local mínima de estructura XLSX; no imprime celdas de datos."""
import argparse
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("--autorizado", action="store_true")
    args = parser.parse_args()
    if not args.autorizado:
        parser.error("Se requiere autorización institucional")
    with ZipFile(args.archivo) as libro:
        workbook = ET.fromstring(libro.read("xl/workbook.xml"))
        relaciones = ET.fromstring(libro.read("xl/_rels/workbook.xml.rels"))
        destinos = {x.attrib["Id"]: x.attrib["Target"].lstrip("/") for x in relaciones}
        hojas = []
        indices = set()
        for hoja in workbook.findall("m:sheets/m:sheet", NS):
            ruta = destinos[hoja.attrib[f"{{{NS['r']}}}id"]]
            if not ruta.startswith("xl/"):
                ruta = "xl/" + ruta
            with libro.open(ruta) as stream:
                for _, elemento in ET.iterparse(stream, events=("end",)):
                    if elemento.tag == f"{{{NS['m']}}}row":
                        cabecera = []
                        for celda in elemento.findall("m:c", NS):
                            valor = celda.find("m:v", NS)
                            if valor is not None and celda.get("t") == "s":
                                indice = int(valor.text)
                                indices.add(indice)
                                cabecera.append(indice)
                            else:
                                cabecera.append(None)
                        break
                else:
                    cabecera = []
            hojas.append((hoja.attrib.get("name", ""), cabecera))
        textos = {}
        if indices and "xl/sharedStrings.xml" in libro.namelist():
            with libro.open("xl/sharedStrings.xml") as stream:
                i = 0
                for _, elemento in ET.iterparse(stream, events=("end",)):
                    if elemento.tag == f"{{{NS['m']}}}si":
                        if i in indices:
                            textos[i] = "".join(elemento.itertext())
                        elemento.clear()
                        i += 1
        for nombre, cabecera in hojas:
            print("Hoja:", nombre)
            for indice in cabecera:
                texto = textos.get(indice, "[sin encabezado de texto]").strip()
                # Encabezados sospechosos se ocultan; nunca se imprimen datos de filas.
                if len(texto) <= 100 and not re.search(r"\d{6,}|@", texto):
                    print(" -", texto)
                else:
                    print(" - [encabezado oculto]")


if __name__ == "__main__":
    main()
