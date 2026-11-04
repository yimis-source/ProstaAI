"""Validaciones encadenadas del archivo (patrón Chain of Responsibility).

FormatValidator y SizeValidator son la admisión que usa la API;
IntegrityValidator y MetadataValidator son la validación detallada que usa la tarea.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from .errors import AdmissionError, StageError
from .stages import CONTROL_CALIDAD

if TYPE_CHECKING:  # evita importar io (y sus dependencias) al cargar los validadores
    from .io import Volume

MIN_SLICES = 8
MIN_SIDE = 32


@dataclass
class UploadedFileInfo:
    """Datos mínimos de un archivo subido: nombre, tamaño y primeros 512 bytes."""

    filename: str
    size_bytes: int
    head: bytes = b""


@dataclass
class ValidationContext:
    """Datos que viajan por la cadena de validadores."""

    files: list[UploadedFileInfo] = field(default_factory=list)
    max_bytes: int = 0
    fmt: str | None = None  # lo fija FormatValidator
    volume: "Volume | None" = None
    reference: "Volume | None" = None


class Validator(ABC):
    """Eslabón de la cadena: valida y pasa el contexto al siguiente."""

    def __init__(self) -> None:
        self._next: Validator | None = None

    def set_next(self, validator: "Validator") -> "Validator":
        self._next = validator
        return validator

    def handle(self, ctx: ValidationContext) -> None:
        self.check(ctx)
        if self._next is not None:
            self._next.handle(ctx)

    @abstractmethod
    def check(self, ctx: ValidationContext) -> None:
        """Lanza AdmissionError o StageError si el contexto no es válido."""


# ---------------------------------------------------------------- admisión

def _ext(name: str) -> str:
    n = name.lower()
    return ".nii.gz" if n.endswith(".nii.gz") else Path(n).suffix


class FormatValidator(Validator):
    """Reconoce DICOM o NIfTI por extensión y por la firma del archivo."""

    def check(self, ctx: ValidationContext) -> None:
        files = ctx.files
        if not files:
            raise AdmissionError("No se recibió ningún archivo.")
        exts = [_ext(f.filename) for f in files]
        desconocidas = sorted({e or "(sin extensión)" for e in exts} - {".nii", ".nii.gz", ".dcm", ".zip"})
        if desconocidas:
            raise AdmissionError(
                "Formato no admitido: " + ", ".join(desconocidas)
                + ". Use un archivo NIfTI (.nii o .nii.gz) o archivos DICOM (.dcm o un .zip)."
            )
        nifti = [f for f, e in zip(files, exts) if e in (".nii", ".nii.gz")]
        dicom = [f for f, e in zip(files, exts) if e == ".dcm"]
        zips = [f for f, e in zip(files, exts) if e == ".zip"]

        if nifti and (dicom or zips):
            raise AdmissionError("No se pueden mezclar archivos NIfTI con DICOM en un mismo estudio.")
        if nifti:
            if len(files) != 1:
                raise AdmissionError("Un estudio NIfTI debe ser un único archivo .nii o .nii.gz.")
            self._check_nifti(nifti[0])
            ctx.fmt = "NIfTI"
            return
        if zips:
            if dicom or len(zips) > 1:
                raise AdmissionError("Envíe un único archivo .zip o bien archivos .dcm, pero no ambos.")
            if not zips[0].head.startswith(b"PK\x03\x04"):
                raise AdmissionError(f"El archivo {zips[0].filename} no es un .zip válido.")
            ctx.fmt = "DICOM"
            return
        for f in dicom:
            if len(f.head) < 132 or f.head[128:132] != b"DICM":
                raise AdmissionError(f"El archivo {f.filename} no tiene formato DICOM válido.")
        ctx.fmt = "DICOM"

    @staticmethod
    def _check_nifti(f: UploadedFileInfo) -> None:
        if _ext(f.filename) == ".nii.gz":
            if not f.head.startswith(b"\x1f\x8b"):
                raise AdmissionError(f"El archivo {f.filename} no es un .nii.gz válido (no está comprimido con gzip).")
            return
        cabecera = f.head[:4]
        if len(cabecera) < 4 or 348 not in (int.from_bytes(cabecera, "little"), int.from_bytes(cabecera, "big")):
            raise AdmissionError(f"El archivo {f.filename} no tiene una cabecera NIfTI-1 válida.")


class SizeValidator(Validator):
    """Rechaza el estudio si el total supera el máximo permitido."""

    def check(self, ctx: ValidationContext) -> None:
        total = sum(f.size_bytes for f in ctx.files)
        if total > ctx.max_bytes:
            mb = ctx.max_bytes / (1024 * 1024)
            raise AdmissionError(
                f"El estudio pesa {total / (1024 * 1024):.1f} MB y supera el máximo de {mb:.0f} MB."
            )


def validate_upload(files: list[UploadedFileInfo], max_bytes: int) -> str:
    """Admisión de la carga. Devuelve "DICOM" o "NIfTI"; lanza AdmissionError."""
    ctx = ValidationContext(files=files, max_bytes=max_bytes)
    cadena = FormatValidator()
    cadena.set_next(SizeValidator())
    cadena.handle(ctx)
    assert ctx.fmt is not None
    return ctx.fmt


# ------------------------------------------------- validación detallada

class IntegrityValidator(Validator):
    """El volumen debe ser 3D, finito y no constante (RF-10)."""

    def check(self, ctx: ValidationContext) -> None:
        vol = ctx.volume
        if vol is None:
            raise StageError(CONTROL_CALIDAD, "No se pudo leer el volumen.")
        if vol.data.ndim != 3:
            raise StageError(CONTROL_CALIDAD, "El estudio no es un volumen 3D.")
        if not np.isfinite(vol.data).all():
            raise StageError(CONTROL_CALIDAD, "El volumen contiene valores no numéricos (NaN o infinitos).")
        if float(vol.data.max()) == float(vol.data.min()):
            raise StageError(CONTROL_CALIDAD, "El volumen tiene intensidad constante.")


class MetadataValidator(Validator):
    """Tamaño mínimo, espaciado positivo y referencia compatible (RF-10)."""

    def check(self, ctx: ValidationContext) -> None:
        vol = ctx.volume
        assert vol is not None
        x, y, z = vol.data.shape
        if z < MIN_SLICES:
            raise StageError(CONTROL_CALIDAD, f"El volumen tiene {z} cortes; se necesitan al menos {MIN_SLICES}.")
        if x < MIN_SIDE or y < MIN_SIDE:
            raise StageError(
                CONTROL_CALIDAD, f"Los cortes miden {x}x{y} vóxeles; se necesitan al menos {MIN_SIDE}x{MIN_SIDE}."
            )
        if not all(np.isfinite(s) and s > 0 for s in vol.spacing):
            raise StageError(CONTROL_CALIDAD, "El espaciado entre vóxeles no es positivo.")
        ref = ctx.reference
        if ref is not None and ref.data.shape != vol.data.shape:
            raise StageError(
                CONTROL_CALIDAD,
                f"La referencia ({ref.data.shape}) no tiene la misma forma que la imagen ({vol.data.shape}).",
            )


def detailed_validation(volume: "Volume", reference: "Volume | None" = None) -> None:
    """Cadena IntegrityValidator -> MetadataValidator sobre un volumen ya leído."""
    cadena = IntegrityValidator()
    cadena.set_next(MetadataValidator())
    cadena.handle(ValidationContext(volume=volume, reference=reference))
