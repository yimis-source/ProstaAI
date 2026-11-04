"""Admisión de archivos (formato y tamaño) antes de guardarlos."""
from dataclasses import dataclass
from typing import Callable

# Firma: (archivos, max_bytes) -> "DICOM" | "NIfTI"; lanza AdmissionError si se rechaza
Admision = Callable[[list, int], str]


@dataclass
class ArchivoInfo:
    """Respaldo con la misma forma que pipeline.validators.UploadedFileInfo."""
    filename: str
    size_bytes: int
    head: bytes


def crear_info(filename: str, size_bytes: int, head: bytes):
    try:
        from prosta_ai.pipeline.validators import UploadedFileInfo
    except ImportError:
        return ArchivoInfo(filename, size_bytes, head)
    return UploadedFileInfo(filename=filename, size_bytes=size_bytes, head=head)


def admitir_con_pipeline(files: list, max_bytes: int) -> str:
    # Importación perezosa para no cargar el pipeline al arrancar la API
    from prosta_ai.pipeline.validators import validate_upload

    return validate_upload(files, max_bytes)
