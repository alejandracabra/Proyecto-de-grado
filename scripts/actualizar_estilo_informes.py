"""Actualiza el estilo de informes locales existentes sin acceder a la base."""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from visualization.proteccion_style import AZUL, BLANCO, COLORES, ESTILO_HTML, TIPOGRAFIA


def main():
    raiz = Path('reports/generated')
    modificados = 0
    for archivo in raiz.rglob('*'):
        if not archivo.is_file() or archivo.suffix.lower() not in ('.html', '.svg'):
            continue
        texto = archivo.read_text(encoding='utf-8')
        if archivo.suffix.lower() == '.html':
            texto = re.sub(r'<style id="identidad-proyecto">.*?</style>', '', texto, flags=re.DOTALL)
            posicion = texto.lower().find('<body')
            if posicion < 0:
                posicion = texto.lower().find('<h1')
            if posicion < 0:
                continue
            texto = texto[:posicion] + ESTILO_HTML + texto[posicion:]
            texto = texto.replace('Colores y tipografía son provisionales.', 'La identidad gráfica sigue las indicaciones del proyecto.')
        else:
            for anterior, nuevo in {'#315a72': COLORES['A'], '#bc7a35': COLORES['B'], '#777777': COLORES['fuera'], '#514b65': COLORES['no evaluable'], '#222': AZUL, 'fill="white"': f'fill="{BLANCO}"', 'DejaVu Sans, sans-serif': TIPOGRAFIA}.items():
                texto = texto.replace(anterior, nuevo)
            texto = re.sub(r'(<rect x="220"[^>]*fill="[^"]+")(?=/>)', rf'\1 stroke="{AZUL}"', texto)
        archivo.write_text(texto, encoding='utf-8')
        modificados += 1
    print(f'Archivos de informes actualizados: {modificados}')


if __name__ == '__main__':
    main()
