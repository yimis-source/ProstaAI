"""Descarga el conjunto público Medical Segmentation Decathlon, Task05_Prostate.

Uso (desde la raíz del repositorio):
    backend/.venv/bin/python scripts/descargar_datos_ejemplo.py [--destino datos]

Licencia CC-BY-SA 4.0. Escribe `datos/FUENTE.md` con la fuente, la licencia y
la cita (RC-03). Los datos no se versionan en git.
"""
from __future__ import annotations

import argparse
import shutil
import tarfile
import urllib.request
from pathlib import Path

URL = "https://msd-for-monai.s3-us-west-2.amazonaws.com/Task05_Prostate.tar"

FICHA = """# Datos de ejemplo: Medical Segmentation Decathlon, Task05_Prostate

- Fuente: http://medicaldecathlon.com/ (copia usada por MONAI: {url}).
- Licencia: CC-BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).
- Contenido: 32 casos de entrenamiento con MRI multimodal (canal 0 = T2, canal 1 = ADC)
  y etiquetas de zona periférica (1) y zona de transición (2).
- Uso en Prosta-AI: solo ejemplos y pruebas manuales; el canal 0 (T2) se usa como imagen
  y la unión de etiquetas > 0 como referencia.

## Cita

Antonelli, M., Reinke, A., Bakas, S. et al. The Medical Segmentation Decathlon.
Nat Commun 13, 4128 (2022). https://doi.org/10.1038/s41467-022-30695-9

## Aviso

Uso académico y experimental. No se usa para diagnóstico.
"""


def _extraer_seguro(tar: tarfile.TarFile, destino: Path) -> None:
    """Extrae solo miembros que quedan dentro de `destino` (sin path traversal)."""
    raiz = destino.resolve()
    for m in tar:
        objetivo = (destino / m.name).resolve()
        if not str(objetivo).startswith(str(raiz)) or not (m.isfile() or m.isdir()):
            continue
        if m.name.rsplit("/", 1)[-1].startswith("._"):
            continue  # restos de macOS
        tar.extract(m, destino, filter="data")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destino", type=Path, default=Path("datos"))
    args = ap.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)
    tar_path = args.destino / "Task05_Prostate.tar"
    if not (args.destino / "Task05_Prostate" / "dataset.json").exists():
        if not tar_path.exists():
            print("Descargando Task05_Prostate.tar ...")
            with urllib.request.urlopen(URL) as resp, open(tar_path, "wb") as f:
                shutil.copyfileobj(resp, f)
        print("Extrayendo ...")
        with tarfile.open(tar_path) as tar:
            _extraer_seguro(tar, args.destino)
        tar_path.unlink()
    (args.destino / "FUENTE.md").write_text(FICHA.format(url=URL), encoding="utf-8")
    print(f"Datos listos en {args.destino / 'Task05_Prostate'}")


if __name__ == "__main__":
    main()
