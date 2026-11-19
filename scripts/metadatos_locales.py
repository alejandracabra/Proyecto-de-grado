"""Inspección optativa de metadatos de archivo, sin abrir su contenido."""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Muestra solo tipo y tamaño del archivo, sin leer su contenido.")
    parser.add_argument("archivo", type=Path)
    parser.add_argument("--autorizado", action="store_true", help="Confirma autorización institucional para esta inspección")
    args = parser.parse_args()
    if not args.autorizado:
        parser.error("Se requiere autorización institucional explícita")
    if not args.archivo.is_file():
        parser.error("No se encontró un archivo regular")
    print(f"Extensión: {args.archivo.suffix.lower()}\nTamaño en bytes: {args.archivo.stat().st_size}")


if __name__ == "__main__":
    main()
