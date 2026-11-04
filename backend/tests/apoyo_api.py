"""Utilidades compartidas por las pruebas de la API."""

import gzip
from types import SimpleNamespace

import nibabel as nib
import numpy as np

from prosta_ai.pipeline.errors import AdmissionError, StageError
from prosta_ai.pipeline.stages import STAGES


def nifti_gz(forma=(32, 32, 12), esfera=True) -> bytes:
    """Volumen NIfTI sintético comprimido."""
    rng = np.random.default_rng(0)
    datos = rng.normal(100, 10, forma).astype(np.float32)
    if esfera:
        x, y, z = np.indices(forma)
        centro = [s / 2 for s in forma]
        datos[((x - centro[0]) ** 2 + (y - centro[1]) ** 2 + (z - centro[2]) ** 2) < 64] += 200
    return gzip.compress(nib.Nifti1Image(datos, np.eye(4)).to_bytes())


def admision_falsa(files, max_bytes: int) -> str:
    """Sustituto de validate_upload: solo acepta NIfTI y respeta el tamaño."""
    for f in files:
        if not f.filename.lower().endswith((".nii", ".nii.gz")):
            raise AdmissionError("Formato no compatible. Use DICOM o NIfTI.")
        if f.size_bytes > max_bytes:
            raise AdmissionError("El archivo supera el tamaño máximo permitido.")
    return "NIfTI"


class PipelineFalso:
    """Escribe imagen.nii.gz y mascara.nii.gz sintéticas y notifica las 5 etapas."""

    strategy = SimpleNamespace(name="falso", version="0")

    def __init__(self, falla_en: str | None = None, explota: bool = False):
        self.falla_en, self.explota = falla_en, explota
        self.entradas = []

    def run(self, inp, progress):
        self.entradas.append(inp)
        duraciones = {}
        for etapa in STAGES:
            progress.notify_start(etapa)
            if etapa == self.falla_en:
                progress.notify_failed(etapa, "Volumen no válido")
                raise StageError(etapa, "Volumen no válido para esta etapa.")
            if self.explota and etapa == "preparación":
                raise RuntimeError("detalle interno /home/secreto")
            duraciones[etapa] = 0.1
            progress.notify_end(etapa, 0.1)
        forma = (32, 32, 12)
        x, y, z = np.indices(forma)
        mascara = (((x - 16) ** 2 + (y - 16) ** 2 + (z - 6) ** 2) < 16).astype(np.uint8)
        imagen = np.random.default_rng(1).normal(100, 10, forma).astype(np.float32) + mascara * 200
        nib.save(nib.Nifti1Image(imagen, np.eye(4)), inp.output_dir / "imagen.nii.gz")
        nib.save(nib.Nifti1Image(mascara, np.eye(4)), inp.output_dir / "mascara.nii.gz")
        con_ref = bool(inp.reference_files)
        return SimpleNamespace(
            image_path=inp.output_dir / "imagen.nii.gz", mask_path=inp.output_dir / "mascara.nii.gz",
            dice=0.8765 if con_ref else None, iou=0.78 if con_ref else None, durations=duraciones,
        )
