"""Descarga el bundle MONAI `prostate_mri_anatomy` y genera `preparacion.json`.

Uso (desde la raíz del repositorio):
    backend/.venv/bin/python scripts/descargar_modelo.py [--destino modelos]

Los archivos se bajan del repositorio del modelo en Hugging Face (organización
MONAI). La configuración de preparación se deriva de `configs/inference.json`
del propio bundle, de modo que entrenamiento e inferencia usen las mismas
transformaciones (RF-09).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

REPO = "MONAI/prostate_mri_anatomy"
REVISION = "2bfceed082de08e9f2b36a50662c99b6243ee794"  # revisión fija del bundle
BASE_URL = f"https://huggingface.co/{REPO}/resolve/{REVISION}"
ARCHIVOS = [
    "models/model.pt",
    "configs/inference.json",
    "configs/metadata.json",
    "docs/README.md",
    "LICENSE",
]

FICHA = """# Ficha del modelo: prostate_mri_anatomy

- Origen: MONAI Model Zoo, bundle `prostate_mri_anatomy` (versión {version}).
- Repositorio: https://huggingface.co/{repo} (revisión {revision}).
- Autor: Keno Bressem.
- Licencia: Apache License 2.0 (ver `LICENSE`). Copyright (c) Keno Bressem.
- Datos de entrenamiento: Prostate158 (https://doi.org/10.5281/zenodo.6481141), solo T2.
- Tarea original: segmentación de zona central (1) y zona periférica (2) de la próstata.
  En Prosta-AI la máscara de próstata completa es la unión de las etiquetas > 0.
- SHA-256 de los pesos: {sha}

## Cita

Adams, L. C., Makowski, M. R., Engel, G., Rattunde, M., Busch, F., Asbach, P.,
... & Bressem, K. K. (2022). Prostate158 - An expert-annotated 3T MRI dataset and
algorithm for prostate cancer detection. Computers in Biology and Medicine, 148,
105817. https://doi.org/10.1016/j.compbiomed.2022.105817

## Aviso

Uso académico y experimental. El modelo no está aprobado para uso clínico.
"""


def _descargar(url: str, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp, open(destino, "wb") as f:
        shutil.copyfileobj(resp, f)


def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def construir_preparacion(inference: dict, version: str) -> dict:
    """Extrae de inference.json los parámetros de preprocesamiento e inferencia."""
    transforms = {t["_target_"]: t for t in inference["preprocessing"]["transforms"]}
    post = {t["_target_"]: t for t in inference["postprocessing"]["transforms"]}
    red = {k: v for k, v in inference["network_def"].items() if k != "_target_"}
    inferer = inference["inferer"]
    return {
        "nombre": "prostate_mri_anatomy",
        "version": version,
        "pesos": "models/model.pt",
        "orientacion": transforms["Orientationd"]["axcodes"],
        "espaciado": transforms["Spacingd"]["pixdim"],
        "modo_remuestreo": transforms["Spacingd"]["mode"],
        "escala_intensidad": {
            "min": transforms["ScaleIntensityd"]["minv"],
            "max": transforms["ScaleIntensityd"]["maxv"],
        },
        "normalizar_intensidad": "NormalizeIntensityd" in transforms,
        "roi_size": inferer["roi_size"],
        "sw_batch_size": inferer["sw_batch_size"],
        "overlap": inferer["overlap"],
        "red": red,
        "etiquetas_prostata": post["KeepLargestConnectedComponentd"]["applied_labels"],
        "conservar_mayor_componente": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destino", type=Path, default=Path("modelos"))
    args = ap.parse_args()
    carpeta = args.destino / "prostate_mri_anatomy"
    for rel in ARCHIVOS:
        destino = carpeta / rel
        if destino.exists() and destino.stat().st_size > 0:
            print(f"Ya existe: {rel}")
            continue
        print(f"Descargando {rel} ...")
        _descargar(f"{BASE_URL}/{rel}", destino)

    inference = json.loads((carpeta / "configs/inference.json").read_text())
    version = json.loads((carpeta / "configs/metadata.json").read_text())["version"]
    prep = construir_preparacion(inference, version)
    (carpeta / "preparacion.json").write_text(
        json.dumps(prep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    sha = _sha256(carpeta / "models/model.pt")
    (carpeta / "FICHA.md").write_text(
        FICHA.format(version=version, repo=REPO, revision=REVISION, sha=sha),
        encoding="utf-8",
    )
    print(f"Modelo listo en {carpeta} (sha256 {sha[:12]}...)")


if __name__ == "__main__":
    main()
