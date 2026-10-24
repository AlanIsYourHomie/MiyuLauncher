from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / 'src'

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from miyu_launcher.core.java import find_java_installations


def main() -> None:
    installations = find_java_installations()

    if not installations:
        print('No se encontraron instalaciones de Java.')
        return

    print(f'Se encontraron {len(installations)} instalación(es) de Java:\n')

    for index, java in enumerate(installations, start=1):
        print(f'[{index}] Java {java.version or "versión desconocida"}')
        print(f'    Major: {java.major if java.major is not None else "desconocido"}')
        print(f'    Ruta: {java.executable}')
        print(f'    Fuente: {java.source}\n')


if __name__ == '__main__':
    main()
